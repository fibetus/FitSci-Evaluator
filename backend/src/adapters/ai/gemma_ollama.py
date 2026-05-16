import json
import os
import time
from pathlib import Path
from typing import Any, Optional

import httpx
from pydantic import ValidationError

from ...domain.errors import ExtractionError
from ...domain.models.extraction import ExtractionResult
from ...domain.ports.logger import LoggerPort, NullLogger

_DEFAULT_MAX_INPUT_CHARS = 24_000


class GemmaOllamaAdapter:
    """Ollama-backed Sifter: prompt assembly, HTTP call, schema validation."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_tag: Optional[str] = None,
        logger: LoggerPort | None = None,
        max_input_chars: int = _DEFAULT_MAX_INPUT_CHARS,
    ) -> None:
        self.base_url: str = (
            base_url or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"
        )
        self.model_tag: str = model_tag or os.getenv("GEMMA_MODEL_TAG") or "gemma4:12b-q4_k_m"
        self.prompt_template = self._load_prompt_template()
        self._logger = logger or NullLogger()
        self.max_input_chars = max_input_chars
        self._last_llm_response: dict[str, Any] | None = None

    @property
    def last_llm_response(self) -> dict[str, Any] | None:
        return self._last_llm_response

    def _load_prompt_template(self) -> str:
        prompt_path = Path(__file__).parent / "prompts" / "extract_v1.txt"
        return prompt_path.read_text(encoding="utf-8")

    def _prepare_prompt(self, text: str) -> str:
        safe_text = text.replace("</paper>", "<escaped_paper_close>")
        if len(safe_text) > self.max_input_chars:
            original_len = len(safe_text)
            safe_text = safe_text[: self.max_input_chars]
            self._logger.warning(
                "paper_truncated",
                original_len=original_len,
                truncated_len=len(safe_text),
                port="EvaluatorPort",
                adapter="GemmaOllamaAdapter",
            )
        return f"{self.prompt_template}\n\n<paper>\n{safe_text}\n</paper>"

    async def _generate(self, prompt: str) -> tuple[str, dict[str, Any]]:
        payload = {
            "model": self.model_tag,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.1},
        }
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data: dict[str, Any] = response.json()
                duration_ms = int((time.perf_counter() - started) * 1000)
                self._logger.info(
                    "ollama_generate",
                    outcome="ok",
                    duration_ms=duration_ms,
                    port="EvaluatorPort",
                    adapter="GemmaOllamaAdapter",
                )
                return str(data.get("response", "")), data
        except httpx.HTTPError as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            self._logger.error(
                "ollama_generate",
                exc=exc,
                outcome="error",
                duration_ms=duration_ms,
                port="EvaluatorPort",
                adapter="GemmaOllamaAdapter",
            )
            raise ExtractionError(f"Ollama API request failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            self._logger.error(
                "ollama_generate",
                exc=exc,
                outcome="error",
                duration_ms=duration_ms,
                port="EvaluatorPort",
                adapter="GemmaOllamaAdapter",
            )
            raise ExtractionError(f"Failed to decode Ollama response JSON: {exc}") from exc

    def _parse_extraction(self, result_text: str) -> ExtractionResult:
        try:
            payload = json.loads(result_text)
        except json.JSONDecodeError as exc:
            raise ExtractionError(f"LLM returned non-JSON output: {exc}") from exc
        if not isinstance(payload, dict):
            raise ExtractionError("LLM JSON root must be an object.")
        try:
            return ExtractionResult.from_llm_json(payload)
        except ValidationError as exc:
            raise ExtractionError(f"Schema validation failed: {exc}") from exc

    async def evaluate_text(self, text: str) -> ExtractionResult:
        prompt = self._prepare_prompt(text)
        result_text, data = await self._generate(prompt)
        self._last_llm_response = {**data, "retried": False}

        try:
            return self._parse_extraction(result_text)
        except (ValidationError, ExtractionError) as exc:
            error_details = str(exc)
            retry_prompt = (
                f"{prompt}\n\nThe previous attempt produced invalid JSON or schema violations.\n"
                f"Please fix the validation errors and return only valid JSON:\n{error_details}"
                f"\n\nPrevious invalid output:\n{result_text}"
            )
            try:
                result_text_retry, retry_data = await self._generate(retry_prompt)
            except ExtractionError as retry_exc:
                raise ExtractionError(f"Failed during retry extraction: {retry_exc}") from retry_exc

            self._last_llm_response = {**retry_data, "retried": True}
            try:
                return self._parse_extraction(result_text_retry)
            except (ValidationError, ExtractionError) as final_exc:
                raise ExtractionError(
                    f"Schema validation failed after retry. Errors: {final_exc}"
                ) from final_exc
