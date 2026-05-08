import json
import os
from pathlib import Path
from typing import Optional

import httpx
from pydantic import ValidationError

from ...domain.errors import ExtractionError
from ...domain.models.study import Study
from ...domain.ports.evaluator import EvaluatorPort


class GemmaOllamaAdapter(EvaluatorPort):
    def __init__(self, base_url: Optional[str] = None, model_tag: Optional[str] = None):
        """
        Initializes the GemmaOllamaAdapter.
        
        Args:
            base_url: The Ollama API base URL. Defaults to OLLAMA_BASE_URL or http://localhost:11434.
            model_tag: The Gemma model tag. Defaults to GEMMA_MODEL_TAG or gemma4:12b-q4_k_m.
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_tag = model_tag or os.getenv("GEMMA_MODEL_TAG", "gemma4:12b-q4_k_m")
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        prompt_path = Path(__file__).parent / "prompts" / "extract_v1.txt"
        return prompt_path.read_text(encoding="utf-8")

    def _prepare_prompt(self, text: str) -> str:
        safe_text = text.replace("</paper>", "<escaped_paper_close>")
        return f"{self.prompt_template}\n\n<paper>\n{safe_text}\n</paper>"

    async def _generate(self, prompt: str) -> str:
        payload = {
            "model": self.model_tag,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.1}
        }
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
                return str(data.get("response", ""))
        except httpx.HTTPError as e:
            raise ExtractionError(f"Ollama API request failed: {e}") from e
        except json.JSONDecodeError as e:
            raise ExtractionError(f"Failed to decode Ollama response JSON: {e}") from e

    async def evaluate_text(self, text: str) -> Study:
        """
        Takes raw text from a publication and uses Gemma 4 
        to extract structured data matching the Study model.
        """
        prompt = self._prepare_prompt(text)
        
        # First attempt
        result_text = await self._generate(prompt)
        
        try:
            return Study.model_validate_json(result_text)
        except ValidationError as e:
            # Retry once with feedback
            error_details = str(e)
            retry_prompt = (
                f"{prompt}\n\nThe previous attempt produced invalid JSON or schema violations.\n"
                f"Please fix the validation errors and return only valid JSON:\n{error_details}"
                f"\n\nPrevious invalid output:\n{result_text}"
            )
            
            try:
                result_text_retry = await self._generate(retry_prompt)
            except ExtractionError as e2:
                raise ExtractionError(f"Failed during retry extraction: {e2}") from e2
            
            try:
                return Study.model_validate_json(result_text_retry)
            except ValidationError as e3:
                raise ExtractionError(f"Schema validation failed after retry. Errors: {e3}") from e3
