from pathlib import Path

import httpx
import pytest

from src.adapters.scrapers.pmc import PMCAdapter
from src.domain.errors import IngestionError

SAMPLE_XML = b"""
<article>
  <front>
    <article-meta>
      <title-group>
        <article-title>Resistance Training Study</article-title>
      </title-group>
      <abstract>
        <p>Weekly volume impacts hypertrophy outcomes.</p>
      </abstract>
    </article-meta>
  </front>
  <body>
    <sec><title>Methods</title><p>Randomized design with trained men.</p></sec>
    <sec><title>Results</title><p>High-volume group showed larger gains.</p></sec>
    <sec><title>Discussion</title><p>Findings support progressive overload.</p></sec>
  </body>
</article>
"""


@pytest.mark.anyio
async def test_fetch_by_id_reads_and_writes_cache(tmp_path: Path) -> None:
    requests_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests_count
        requests_count += 1
        assert request.url.path.endswith("/efetch.fcgi")
        return httpx.Response(200, content=SAMPLE_XML)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = PMCAdapter(client=client, cache_dir=tmp_path)

        first = await adapter.fetch_by_id("PMC12345")
        second = await adapter.fetch_by_id("12345")

    assert "Abstract" in first
    assert "Methods" in first
    assert "Results" in first
    assert "Discussion" in first
    assert first == second
    assert requests_count == 1
    assert (tmp_path / "PMC12345.xml").exists()


@pytest.mark.anyio
async def test_fetch_by_id_raises_on_non_xml_payload(tmp_path: Path) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not xml")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = PMCAdapter(client=client, cache_dir=tmp_path)
        with pytest.raises(IngestionError):
            await adapter.fetch_by_id("PMC12345")


@pytest.mark.anyio
async def test_search_returns_normalized_pmcids() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/esearch.fcgi")
        return httpx.Response(
            200,
            json={"esearchresult": {"idlist": ["100", "200", "300"]}},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = PMCAdapter(client=client)
        results = await adapter.search("resistance training", limit=3)

    assert results == ["PMC100", "PMC200", "PMC300"]


@pytest.mark.anyio
async def test_search_empty_query_returns_empty_list() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(500))
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = PMCAdapter(client=client)
        results = await adapter.search("   ")

    assert results == []
