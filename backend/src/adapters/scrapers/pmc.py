from __future__ import annotations

import time
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import httpx

from src.domain.errors import IngestionError
from src.domain.ports.ingestor import IngestorPort
from src.domain.ports.logger import LoggerPort, NullLogger


class PMCAdapter(IngestorPort):
    """
    NCBI PMC ingestor with local raw-response caching.
    """

    EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        cache_dir: Path | None = None,
        tool: str = "fitsci-evaluator",
        logger: LoggerPort | None = None,
    ) -> None:
        self._client = client
        self._owns_client = client is None
        self._cache_dir = cache_dir or (Path.home() / ".fitsci" / "cache" / "pmc")
        self._tool = tool
        self._logger = logger or NullLogger()
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    async def fetch_by_id(self, study_id: str) -> str:
        pmc_id = _normalize_pmc_id(study_id)
        cache_path = self._cache_dir / f"{pmc_id}.xml"
        started = time.perf_counter()

        if cache_path.exists():
            raw_bytes = cache_path.read_bytes()
            self._logger.info(
                "pmc_fetch",
                outcome="ok",
                duration_ms=int((time.perf_counter() - started) * 1000),
                port="IngestorPort",
                adapter="PMCAdapter",
                source="disk_cache",
            )
        else:
            client = await self._get_client()
            try:
                response = await client.get(
                    f"{self.EUTILS_BASE_URL}/efetch.fcgi",
                    params={
                        "db": "pmc",
                        "id": pmc_id.replace("PMC", ""),
                        "rettype": "full",
                        "retmode": "xml",
                        "tool": self._tool,
                    },
                )
                response.raise_for_status()
                raw_bytes = response.content
            except httpx.HTTPError as exc:
                self._logger.error(
                    "pmc_fetch",
                    exc=exc,
                    outcome="error",
                    duration_ms=int((time.perf_counter() - started) * 1000),
                    port="IngestorPort",
                    adapter="PMCAdapter",
                )
                raise IngestionError(f"Unable to fetch PMCID {pmc_id}: {exc}") from exc

            if not raw_bytes.strip():
                raise IngestionError(f"PMCID {pmc_id} returned an empty payload.")

            cache_path.write_bytes(raw_bytes)
            self._logger.info(
                "pmc_fetch",
                outcome="ok",
                duration_ms=int((time.perf_counter() - started) * 1000),
                port="IngestorPort",
                adapter="PMCAdapter",
                source="network",
            )

        try:
            return _xml_to_clean_text(raw_bytes)
        except IngestionError:
            raise
        except Exception as exc:  # pragma: no cover - defensive wrapper
            raise IngestionError(f"Failed to parse PMCID {pmc_id} XML payload.") from exc

    async def search(self, query: str, limit: int = 10) -> list[str]:
        if not query.strip():
            return []

        client = await self._get_client()
        try:
            response = await client.get(
                f"{self.EUTILS_BASE_URL}/esearch.fcgi",
                params={
                    "db": "pmc",
                    "term": query.strip(),
                    "retmax": str(limit),
                    "retmode": "json",
                    "tool": self._tool,
                },
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise IngestionError(f"Unable to search PMC for query {query!r}: {exc}") from exc

        id_list = payload.get("esearchresult", {}).get("idlist", [])
        if not isinstance(id_list, list):
            raise IngestionError("Malformed search response from PMC.")

        return [f"PMC{identifier}" for identifier in id_list if isinstance(identifier, str)]

    async def aclose(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client


def _normalize_pmc_id(study_id: str) -> str:
    candidate = study_id.strip().upper()
    if not candidate:
        raise IngestionError("Study ID cannot be empty.")

    if candidate.startswith("PMC"):
        suffix = candidate.removeprefix("PMC")
    else:
        suffix = candidate

    if not suffix.isdigit():
        raise IngestionError(f"Invalid PMCID format: {study_id!r}")

    return f"PMC{suffix}"


def _xml_to_clean_text(raw_bytes: bytes) -> str:
    try:
        root = ElementTree.fromstring(raw_bytes)
    except ElementTree.ParseError as exc:
        raise IngestionError(f"Invalid PMC XML payload: {exc}") from exc

    title = _extract_first_text(root, ".//article-title")
    abstract = _collect_named_section(root, ".//abstract", "Abstract")
    methods = _collect_body_section(root, "Methods")
    results = _collect_body_section(root, "Results")
    discussion = _collect_body_section(root, "Discussion")

    chunks = [chunk for chunk in [title, abstract, methods, results, discussion] if chunk]
    if not chunks:
        fallback = " ".join(_clean_text(text) for text in root.itertext())
        cleaned = _clean_text(fallback)
        if not cleaned:
            raise IngestionError("PMC XML did not contain readable text.")
        return cleaned

    return "\n\n".join(chunks)


def _extract_first_text(root: ElementTree.Element, xpath: str) -> str | None:
    element = root.find(xpath)
    if element is None:
        return None

    text = _clean_text(" ".join(element.itertext()))
    return text if text else None


def _collect_named_section(root: ElementTree.Element, xpath: str, heading: str) -> str | None:
    blocks: list[str] = []
    for node in root.findall(xpath):
        text = _clean_text(" ".join(node.itertext()))
        if text:
            blocks.append(text)

    if not blocks:
        return None

    return f"{heading}\n" + "\n".join(blocks)


def _collect_body_section(root: ElementTree.Element, heading: str) -> str | None:
    heading_lower = heading.lower()
    section_paragraphs: list[str] = []

    for sec in root.findall(".//body//sec"):
        title = sec.find("title")
        if title is None:
            continue
        title_text = _clean_text(" ".join(title.itertext())).lower()
        if heading_lower not in title_text:
            continue

        for paragraph in sec.findall(".//p"):
            text = _clean_text(" ".join(paragraph.itertext()))
            if text:
                section_paragraphs.append(text)

    if not section_paragraphs:
        return None

    return f"{heading}\n" + "\n".join(section_paragraphs)


def _clean_text(value: str) -> str:
    return " ".join(value.split())
