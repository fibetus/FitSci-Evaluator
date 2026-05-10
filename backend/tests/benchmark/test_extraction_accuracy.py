import json
import os
from pathlib import Path
from typing import Any

import httpx
import pytest

from src.adapters.ai.gemma_ollama import GemmaOllamaAdapter
from src.adapters.scrapers.pmc import PMCAdapter
from src.domain.errors import ExtractionError

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "benchmark"

def compute_f1(expected: dict[str, Any], actual: dict[str, Any]) -> float:
    """
    Computes field-level F1 score for the nested JSON structures.
    Uses exact match for most fields, and partial/overlap match for strings and lists.
    """
    tp = 0
    fp = 0
    fn = 0

    def flatten(d: dict[str, Any], parent_key: str = "", sep: str = ".") -> dict[str, Any]:
        items: list[tuple[str, Any]] = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict) and v:
                items.extend(flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    flat_exp = flatten(expected)
    flat_act = flatten(actual)

    for k, v_exp in flat_exp.items():
        v_act = flat_act.get(k)
        
        # Both empty/null: neither TP nor FN/FP to avoid inflation.
        exp_empty = v_exp is None or v_exp == "" or v_exp == []
        act_empty = v_act is None or v_act == "" or v_act == []
        if exp_empty and act_empty:
            continue

        if v_exp is None or v_exp == "" or v_exp == []:
            fp += 1
            continue

        if v_act is None or v_act == "" or v_act == []:
            fn += 1
            continue

        if isinstance(v_exp, list):
            if isinstance(v_act, list):
                exp_set = {str(x).lower() for x in v_exp}
                act_set = {str(x).lower() for x in v_act}
                if exp_set.intersection(act_set):
                    tp += 1
                else:
                    fn += 1
                    fp += 1
            else:
                fn += 1
                fp += 1
        elif isinstance(v_exp, str):
            if isinstance(v_act, str):
                if v_exp.lower() in v_act.lower() or v_act.lower() in v_exp.lower():
                    tp += 1
                else:
                    fn += 1
                    fp += 1
            else:
                fn += 1
                fp += 1
        else:
            if v_exp == v_act:
                tp += 1
            else:
                fn += 1
                fp += 1

    for k, v_act in flat_act.items():
        if k not in flat_exp:
            if v_act is not None and v_act != "" and v_act != []:
                fp += 1

    if tp == 0:
        return 0.0

    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    return 2 * (precision * recall) / (precision + recall)


@pytest.mark.anyio
@pytest.mark.skipif(
    not os.environ.get("RUN_BENCHMARK"),
    reason="Set RUN_BENCHMARK=1 to run expensive extraction harness.",
)
async def test_extraction_accuracy() -> None:
    pmc_adapter = PMCAdapter()
    evaluator = GemmaOllamaAdapter()
    
    f1_scores: list[float] = []
    
    fixture_files = list(FIXTURES_DIR.glob("*.json"))
    if not fixture_files:
        pytest.skip("No benchmark fixtures found.")

    try:
        for fixture_file in fixture_files:
            with open(fixture_file, "r", encoding="utf-8") as f:
                gold_data = json.load(f)
                
            pmc_id = gold_data["id"]
            try:
                raw_text = await pmc_adapter.fetch_by_id(pmc_id)
            except Exception as e:
                print(f"Skipping {pmc_id}: could not fetch PMC data ({e})")
                continue
                
            try:
                actual_study = await evaluator.evaluate_text(raw_text)
            except ExtractionError as e:
                if isinstance(e.__cause__, (httpx.ConnectError, httpx.RequestError)):
                    pytest.skip("Ollama is not running. Start Ollama to run this test.")
                raise
            except Exception as e:
                pytest.fail(f"Evaluator failed on {pmc_id}: {e}")
                
            actual_data = actual_study.model_dump()
            
            # Remove deterministic scoring fields and non-extracted metadata
            fields_to_ignore = [
                "score", "confidence", "quality_tier", "score_breakdown", 
                "scraped_at", "id", "pmc_url"
            ]
            for field in fields_to_ignore:
                gold_data.pop(field, None)
                actual_data.pop(field, None)
                
            f1 = compute_f1(gold_data, actual_data)
            f1_scores.append(f1)
            
        if not f1_scores:
            pytest.skip("No benchmark fixtures could be evaluated successfully.")

        avg_f1 = sum(f1_scores) / len(f1_scores)
        assert avg_f1 >= 0.80, f"Average F1 score is {avg_f1:.2f}, expected >= 0.80"
        
    finally:
        await pmc_adapter.aclose()
