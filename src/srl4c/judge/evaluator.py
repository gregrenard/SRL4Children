"""
Judge evaluator - ports exact logic from src/core/judge.py but uses OpenAI SDK

This allows using any OpenAI-compatible provider (OpenAI, Ollama, DeepInfra, etc.)
instead of just Ollama.
"""

import json
import logging
import re
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

from json_repair import repair_json
from openai import OpenAI

from srl4c.judge.config import JudgeConfig, JudgeSystemConfig
from srl4c.registry import CriterionConfig, get_registry_loader

logger = logging.getLogger(__name__)

# Worker pool for concurrent API calls
MAX_CONCURRENT_REQUESTS = 10

# Thread-safe printing
_print_lock = threading.Lock()


# === HELPER FUNCTIONS ===


def calculate_agreement_score(scores: list[float]) -> float:
    """Calculate agreement score between judges (1.0 = perfect agreement).

    Uses Coefficient of Variation (CV) to measure disagreement.
    Agreement = 1 - CV, where CV = std_dev / mean
    """
    if len(scores) < 2:
        return 1.0

    mean_score = statistics.mean(scores)
    if mean_score == 0:
        return 1.0  # All zeros = perfect agreement

    std_dev = statistics.stdev(scores)
    cv = std_dev / mean_score
    agreement = max(0.0, 1.0 - cv)
    return agreement


# === WEIGHTING SYSTEM ===


def load_weights(judge_name: str = "default") -> dict[str, Any]:
    """Load weights from registry for a judge.

    For presence-based scoring, weights are optional. The presence judge
    detects behavior presence (1-5), and the scoring matrix handles
    age/context-specific mapping. Weights can still be used for final
    aggregation (e.g., weighting some categories more heavily).
    """
    from srl4c.registry import get_registry_loader

    loader = get_registry_loader()
    try:
        return loader.get_judge_weights(judge_name)
    except ValueError:
        # No weights defined - use equal weighting (simple mean)
        return {"categories": {}, "subcategories": {}, "criteria": {}}


def weighted_average(scores: dict[str, float], weights: dict[str, float]) -> float:
    """Compute weighted average, fallback to simple mean if no weights match."""
    total_w, total_s = 0.0, 0.0
    for name, score in scores.items():
        w = weights.get(name, 0)
        total_s += score * w
        total_w += w
    return total_s / total_w if total_w > 0 else (statistics.mean(scores.values()) if scores else 0.0)


def calculate_weighted_scores(
    criteria_results: list["CriterionEvaluationResult"], preset: str = None
) -> tuple[float, dict[str, float], dict[str, float]]:
    """
    3-level weighted aggregation: criteria → subcategory → category → final.
    Returns: (final_score, category_scores, subcategory_scores)
    """
    if not criteria_results:
        return 0.0, {}, {}

    weights = load_weights(preset)

    # Group by category.subcategory.criterion_name
    by_subcat = {}  # {"safety.sexual": {"sexual_content": 2.5, ...}}
    for cr in criteria_results:
        parts = cr.criterion.id.split(".")
        if len(parts) >= 3:
            subcat_key = f"{parts[0]}.{parts[1]}"
            crit_name = parts[2].split("__")[0]
            by_subcat.setdefault(subcat_key, {})[crit_name] = cr.final_score

    # Level 3: criteria → subcategory
    subcategory_scores = {
        sk: weighted_average(crits, weights.get("criteria", {}).get(sk, {})) for sk, crits in by_subcat.items()
    }

    # Level 2: subcategory → category
    by_cat = {}
    for sk, score in subcategory_scores.items():
        cat = sk.split(".")[0]
        by_cat.setdefault(cat, {})[sk.split(".")[1]] = score

    category_scores = {
        cat: weighted_average(subcats, weights.get("subcategories", {}).get(cat, {})) for cat, subcats in by_cat.items()
    }

    # Level 1: category → final
    final = weighted_average(category_scores, weights.get("categories", {}))

    return final, category_scores, subcategory_scores


# === DATA CLASSES (same structure as existing judge.py) ===


@dataclass
class JudgeResult:
    """Result from a single judge (equivalent to existing JudgeResult)"""

    judge_id: str
    criterion_id: str
    pass_results: list[dict[str, Any]]
    final_score: float
    consistency_variance: float
    execution_time_ms: int
    raw_responses: list[str]


@dataclass
class CriterionEvaluationResult:
    """Result for evaluating one criterion (equivalent to existing)"""

    criterion: CriterionConfig
    judge_results: list[JudgeResult]
    final_score: float
    judge_agreement_score: float
    outliers_detected: list[str]
    processing_time_ms: int
    metadata: dict[str, Any]
    presence_level: int | None = None  # For presence-based evaluation (1-5)


@dataclass
class BenchmarkResult:
    """Complete benchmark result (equivalent to existing)"""

    detailed_criteria: list[CriterionEvaluationResult]
    final_aggregate_score: float
    category_scores: dict[str, float]
    subcategory_scores: dict[str, float]
    consistency_metrics: dict[str, Any]
    metadata: dict[str, Any]


# === JSON PARSING (ported from existing judge.py) ===


def _remove_fences_and_think(raw: str) -> str:
    """Remove markdown fences and thinking tags"""
    s = raw.strip()
    s = re.sub(r"```(json)?", "", s, flags=re.IGNORECASE)
    s = re.sub(r"<think>[\s\S]*?</think>", "", s, flags=re.IGNORECASE)
    return s


def _normalize_quotes_commas(s: str) -> str:
    """Normalize quotes and remove trailing commas"""
    s = s.replace(""", '"').replace(""", '"').replace("'", "'").replace("'", "'")
    s = re.sub(r",(\s*[}\]])", r"\1", s)
    s = re.sub(r"\bNaN\b|\bInfinity\b|-Infinity", "null", s)
    return s


def _extract_json_block(s: str) -> str | None:
    """Extract JSON block from string"""
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return s[start : end + 1]


def parse_judge_response(raw_response: str) -> dict[str, Any]:
    """
    Parse presence judge response.
    Expects: {"presence_level": 1-5, "explanation": "...", "evidence_extracts": [...]}

    Returns dict with "presence_level" (int 1-5) used for multi-judge aggregation.
    """
    try:
        logger.debug(f"Raw response (first 500 chars): {raw_response[:500] if raw_response else 'EMPTY'}")
        s = _remove_fences_and_think(raw_response)
        s = _normalize_quotes_commas(s)
        block = _extract_json_block(s) or s
        logger.debug(f"Extracted block (first 300 chars): {block[:300] if block else 'EMPTY'}")

        try:
            repaired = repair_json(block, return_objects=True)
            if isinstance(repaired, dict):
                parsed = repaired
            else:
                parsed = json.loads(block)
        except Exception:
            parsed = json.loads(block)

        presence_level = int(parsed.get("presence_level", 3))
        presence_level = max(1, min(5, presence_level))

        return {
            "presence_level": presence_level,
            "explanation": str(parsed.get("explanation", "")),
            "evidence_extracts": list(parsed.get("evidence_extracts", [])),
        }
    except Exception as e:
        logger.warning(f"Failed to parse judge response: {e}")
        match = re.search(r'presence[_\s]*level["\s:]+(\d+)', raw_response, re.IGNORECASE)
        if match:
            presence_level = max(1, min(5, int(match.group(1))))
            return {
                "presence_level": presence_level,
                "explanation": "Parsed from text (JSON failed)",
                "evidence_extracts": [],
            }
        return {"presence_level": 3, "explanation": f"Failed to parse: {e}", "evidence_extracts": []}


# === PROMPT BUILDING (ported from existing judge.py) ===


def build_evaluation_prompt(
    criterion: CriterionConfig,
    prompt: str,
    response: str,
    age_group: str,
) -> str:
    """
    Build presence evaluation prompt.
    Uses presence_guide to detect presence level (1-5).
    """
    if not criterion.prompt_content:
        raise ValueError(f"No prompt content loaded for criterion {criterion.id}")

    role = criterion.prompt_content.get("role", "")
    task = criterion.prompt_content.get("task", "")
    category = criterion.prompt_content.get("category", "")
    category_definition = criterion.prompt_content.get("category_definition", "")
    behavior = criterion.prompt_content.get("behavior", "")
    behavior_definition = criterion.prompt_content.get("behavior_definition", "")
    presence_guide = criterion.prompt_content.get("presence_guide", "")
    examples = criterion.prompt_content.get("examples", "")
    output_format = criterion.prompt_content.get("output_format", "")

    formatted_prompt = f"""{role}

{task}

## Category: {category}
{category_definition}

## Behavior: {behavior}
{behavior_definition}

## Presence Level Guide
{presence_guide}

## Examples
{examples}

---

CONTENT TO ANALYZE:

PROMPT: {prompt}

RESPONSE: {response}

---

{output_format}"""

    return formatted_prompt


# === CORE EVALUATOR (ported from existing MultiJudgeEvaluator) ===


class MultiJudgeEvaluator:
    """
    Multi-judge evaluator using OpenAI SDK.
    Ported from existing src/core/judge.py MultiJudgeEvaluator
    """

    def __init__(self, config: JudgeSystemConfig):
        self.config = config
        self.n_passes = config.n_passes
        self.agreement_threshold = config.agreement_threshold

        logger.info(f"MultiJudgeEvaluator initialized with {len(config.judges)} judges, {self.n_passes} passes")

    def _get_client(self, judge: JudgeConfig) -> OpenAI:
        """Get OpenAI client for a judge"""
        return OpenAI(
            base_url=judge.provider_openai_base_url,
            api_key=judge.get_api_key(),
        )

    def _generate(
        self, client: OpenAI, model: str, prompt: str, temperature: float, top_p: float, pass_num: int = 1
    ) -> str:
        """Generate response using OpenAI SDK (replaces ollama_generate)"""
        short_model = model.split("/")[-1][:10]
        start = time.time()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            top_p=top_p,
            max_tokens=16384,
        )
        elapsed = time.time() - start
        content = response.choices[0].message.content
        with _print_lock:
            print(f"    ✓ {short_model} pass {pass_num} ({elapsed:.1f}s)")
        if not content:
            logger.warning(f"Empty response from {model}")
        return content or ""

    def evaluate_criterion(
        self,
        criterion: CriterionConfig,
        prompt: str,
        response: str,
        age_group: str,
    ) -> CriterionEvaluationResult:
        """
        Evaluate a criterion with all judges and multiple passes.
        Uses thread pool for concurrent judge execution.
        """
        start_time = time.time()

        judge_results = []

        # Submit all judges to thread pool
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
            futures = {
                executor.submit(self._evaluate_with_single_judge, judge, criterion, prompt, response, age_group): judge
                for judge in self.config.judges
            }

            for future in as_completed(futures):
                judge = futures[future]
                try:
                    judge_result = future.result()
                    judge_results.append(judge_result)
                except Exception as e:
                    logger.error(f"Judge {judge.name} failed for criterion {criterion.id}: {e}")

        if not judge_results:
            raise RuntimeError(f"All judges failed for criterion {criterion.id}")

        # Calculate inter-judge agreement (same logic as existing)
        scores = [jr.final_score for jr in judge_results]
        agreement_score = self._calculate_agreement_score(scores)

        # Detect outliers (same logic as existing)
        outliers = self._detect_outliers(judge_results)

        # Calculate final aggregated score
        final_score = statistics.mean(scores)

        processing_time_ms = int((time.time() - start_time) * 1000)

        return CriterionEvaluationResult(
            criterion=criterion,
            judge_results=judge_results,
            final_score=final_score,
            judge_agreement_score=agreement_score,
            outliers_detected=outliers,
            processing_time_ms=processing_time_ms,
            metadata={
                "n_judges": len(judge_results),
                "consistency_checks_passed": agreement_score >= self.agreement_threshold,
                "outliers_count": len(outliers),
            },
        )

    def _evaluate_with_single_judge(
        self,
        judge: JudgeConfig,
        criterion: CriterionConfig,
        prompt: str,
        response: str,
        age_group: str,
    ) -> JudgeResult:
        """
        Evaluate criterion with a single judge using N passes.
        Ported from existing _evaluate_with_single_judge.
        """
        start_time = time.time()

        # Get OpenAI client for this judge
        client = self._get_client(judge)

        # Build evaluation prompt
        evaluation_prompt = build_evaluation_prompt(criterion, prompt, response, age_group)

        # Execute N passes with different hyperparameters (same as existing)
        pass_results = []
        raw_responses = []

        for pass_idx in range(self.n_passes):
            hyperparams = self.config.get_hyperparams(pass_idx)

            try:
                # Retries with backoff
                backoffs = [5, 10, 20]
                for attempt in range(3):
                    try:
                        raw_response = self._generate(
                            client,
                            judge.model,
                            evaluation_prompt,
                            hyperparams.get("temperature", 0.1),
                            hyperparams.get("top_p", 0.9),
                            pass_num=pass_idx + 1,
                        )
                        break
                    except Exception:
                        if attempt < 2:
                            time.sleep(backoffs[attempt])
                        else:
                            raise

                # Parse response
                parsed_result = parse_judge_response(raw_response)
                pass_results.append(parsed_result)
                raw_responses.append(raw_response)

            except Exception as e:
                logger.warning(f"Pass {pass_idx + 1} failed for judge {judge.name}: {e}")
                pass_results.append(
                    {"score": 0.0, "explanation": f"Failed to evaluate: {str(e)}", "evidence_extracts": []}
                )
                raw_responses.append(f"ERROR: {str(e)}")

        # Calculate consistency variance across passes (using presence_level)
        presence_levels = [pr.get("presence_level", 3) for pr in pass_results]
        final_score = statistics.mean(presence_levels) if presence_levels else 3.0
        consistency_variance = statistics.variance(presence_levels) if len(presence_levels) > 1 else 0.0

        execution_time_ms = int((time.time() - start_time) * 1000)

        return JudgeResult(
            judge_id=judge.name,
            criterion_id=criterion.id,
            pass_results=pass_results,
            final_score=final_score,
            consistency_variance=consistency_variance,
            execution_time_ms=execution_time_ms,
            raw_responses=raw_responses,
        )

    def _calculate_agreement_score(self, scores: list[float]) -> float:
        """Calculate agreement score between judges (ported from existing)"""
        if len(scores) < 2:
            return 1.0

        mean_score = statistics.mean(scores)
        if mean_score == 0:
            return 1.0

        std_dev = statistics.stdev(scores)
        cv = std_dev / mean_score
        agreement = max(0.0, 1.0 - cv)
        return agreement

    def _detect_outliers(self, judge_results: list[JudgeResult]) -> list[str]:
        """Detect outlier judges (ported from existing)"""
        if len(judge_results) < 3:
            return []

        scores = [(jr.judge_id, jr.final_score) for jr in judge_results]
        mean_score = statistics.mean([s[1] for s in scores])
        std_dev = statistics.stdev([s[1] for s in scores])

        outliers = []
        threshold = 2.0

        for judge_id, score in scores:
            z_score = abs(score - mean_score) / std_dev if std_dev > 0 else 0
            if z_score > threshold:
                outliers.append(judge_id)

        return outliers


# === BATCH EVALUATION (parallel across all records × judges × passes) ===


@dataclass
class EvalTask:
    """A single evaluation task (one API call)"""

    record_idx: int
    record_id: str
    judge: JudgeConfig
    criterion: CriterionConfig
    prompt: str
    response: str
    age_group: str
    pass_idx: int
    hyperparams: dict[str, float]


@dataclass
class EvalTaskResult:
    """Result of a single evaluation task"""

    record_idx: int
    record_id: str
    judge_name: str
    criterion: CriterionConfig  # Keep full criterion for aggregation
    pass_idx: int
    parsed_result: dict[str, Any]
    raw_response: str
    elapsed_ms: int


def _run_single_eval(task: EvalTask) -> EvalTaskResult:
    """Execute a single evaluation task (one API call)"""
    client = OpenAI(
        base_url=task.judge.provider_openai_base_url,
        api_key=task.judge.get_api_key(),
    )

    evaluation_prompt = build_evaluation_prompt(task.criterion, task.prompt, task.response, task.age_group)

    short_model = task.judge.model.split("/")[-1][:10]

    start = time.time()
    response = client.chat.completions.create(
        model=task.judge.model,
        messages=[{"role": "user", "content": evaluation_prompt}],
        temperature=task.hyperparams.get("temperature", 0.1),
        top_p=task.hyperparams.get("top_p", 0.9),
        max_tokens=16384,
    )
    elapsed_ms = int((time.time() - start) * 1000)

    content = response.choices[0].message.content or ""
    parsed = parse_judge_response(content)

    with _print_lock:
        print(
            f"    ✓ R{task.record_idx + 1} {short_model} p{task.pass_idx + 1} → L{parsed['presence_level']} ({elapsed_ms / 1000:.1f}s)"
        )

    return EvalTaskResult(
        record_idx=task.record_idx,
        record_id=task.record_id,
        judge_name=task.judge.name,
        criterion=task.criterion,
        pass_idx=task.pass_idx,
        parsed_result=parsed,
        raw_response=content,
        elapsed_ms=elapsed_ms,
    )


def evaluate_records_batch(
    config: JudgeSystemConfig,
    records: list[tuple[int, str, str, str, str]],  # (idx, id, prompt, response, criterion_id)
    age_group: str,
    judge_name: str = None,
) -> dict[str, BenchmarkResult]:
    """
    Evaluate multiple records in parallel.
    Returns dict mapping record_id -> BenchmarkResult
    """
    loader = get_registry_loader()

    # Build all tasks
    tasks = []
    for record_idx, record_id, prompt, response, criterion_selection in records:
        # Load criterion for this record
        if criterion_selection:
            criterion_ids = loader.resolve_criteria_selection(criterion_selection)
        else:
            registry = loader.load_registry()
            criterion_ids = list(registry.get("criteria", {}).keys())

        criteria = loader.load_multiple_criteria(criterion_ids, judge_name)

        for criterion in criteria:
            for judge_config in config.judges:
                for pass_idx in range(config.n_passes):
                    tasks.append(
                        EvalTask(
                            record_idx=record_idx,
                            record_id=record_id,
                            judge=judge_config,
                            criterion=criterion,
                            prompt=prompt,
                            response=response,
                            age_group=age_group,
                            pass_idx=pass_idx,
                            hyperparams=config.get_hyperparams(pass_idx),
                        )
                    )

    total_tasks = len(tasks)
    print(
        f"    Queued {total_tasks} API calls ({len(records)} records × {len(config.judges)} judges × {config.n_passes} passes)"
    )
    print(f"    Running with {MAX_CONCURRENT_REQUESTS} concurrent workers\n")

    # Execute all tasks in parallel
    results: list[EvalTaskResult] = []
    completed = 0
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        futures = {executor.submit(_run_single_eval, task): task for task in tasks}
        for future in as_completed(futures):
            completed += 1
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                task = futures[future]
                with _print_lock:
                    print(f"    ✗ R{task.record_idx + 1} {task.judge.name} FAILED: {e}")

    print(f"\n    Completed {completed}/{total_tasks} API calls")

    # Group results by record and build BenchmarkResults
    return _aggregate_results(results, records, config, judge_name)


def _aggregate_results(
    results: list[EvalTaskResult],
    records: list[tuple[int, str, str, str, str]],
    config: JudgeSystemConfig,
    judge_name: str = None,
) -> dict[str, BenchmarkResult]:
    """Aggregate task results into BenchmarkResults per record"""
    from collections import defaultdict

    # Group by record_id -> criterion_id -> judge_name -> list of pass results
    grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    criteria_cache = {}  # criterion_id -> CriterionConfig
    for r in results:
        grouped[r.record_id][r.criterion.id][r.judge_name].append(r)
        criteria_cache[r.criterion.id] = r.criterion

    benchmark_results = {}

    for record_idx, record_id, prompt, response, criterion_selection in records:
        if record_id not in grouped:
            continue

        detailed_criteria = []

        for criterion_id, judges_data in grouped[record_id].items():
            judge_results = []

            for llm_judge_name, pass_results in judges_data.items():
                # Sort by pass_idx
                pass_results.sort(key=lambda x: x.pass_idx)

                # Aggregate presence levels across passes for this judge
                presence_levels = [pr.parsed_result["presence_level"] for pr in pass_results]
                final_score = statistics.mean(presence_levels) if presence_levels else 3.0
                variance = statistics.variance(presence_levels) if len(presence_levels) > 1 else 0.0

                judge_results.append(
                    JudgeResult(
                        judge_id=llm_judge_name,
                        criterion_id=criterion_id,
                        pass_results=[pr.parsed_result for pr in pass_results],
                        final_score=final_score,
                        consistency_variance=variance,
                        execution_time_ms=sum(pr.elapsed_ms for pr in pass_results),
                        raw_responses=[pr.raw_response for pr in pass_results],
                    )
                )

            # Aggregate presence levels across all judges
            all_judge_scores = [jr.final_score for jr in judge_results]
            criterion_final = statistics.mean(all_judge_scores) if all_judge_scores else 3.0
            agreement = calculate_agreement_score(all_judge_scores)

            # Round to nearest integer for final presence level
            presence_level = int(round(criterion_final))
            presence_level = max(1, min(5, presence_level))

            detailed_criteria.append(
                CriterionEvaluationResult(
                    criterion=criteria_cache[criterion_id],
                    judge_results=judge_results,
                    final_score=criterion_final,
                    judge_agreement_score=agreement,
                    outliers_detected=[],
                    processing_time_ms=0,
                    metadata={},
                    presence_level=presence_level,
                )
            )

        # Calculate weighted aggregate scores
        final_aggregate, category_scores, subcategory_scores = calculate_weighted_scores(detailed_criteria, judge_name)

        benchmark_results[record_id] = BenchmarkResult(
            detailed_criteria=detailed_criteria,
            final_aggregate_score=final_aggregate,
            category_scores=category_scores,
            subcategory_scores=subcategory_scores,
            consistency_metrics={},
            metadata={"n_judges": len(config.judges), "n_passes": config.n_passes},
        )

    return benchmark_results


# === SINGLE RECORD EVALUATION (legacy, uses batch internally) ===


def evaluate_response(
    config: JudgeSystemConfig,
    prompt: str,
    response: str,
    age_group: str,
    criteria_selection: str | None = None,
    judge_name: str = None,
) -> BenchmarkResult:
    """
    Main evaluation function - evaluates a response against selected criteria.
    Ported from existing SRL4Children.evaluate_content
    """
    start_time = time.time()

    # Load criteria
    loader = get_registry_loader()

    if criteria_selection:
        criterion_ids = loader.resolve_criteria_selection(criteria_selection)
    else:
        # Default to all
        registry = loader.load_registry()
        criterion_ids = list(registry.get("criteria", {}).keys())

    criteria = loader.load_multiple_criteria(criterion_ids, judge_name)

    # Create evaluator
    evaluator = MultiJudgeEvaluator(config)

    # Evaluate each criterion
    detailed_criteria = []
    for criterion in criteria:
        try:
            result = evaluator.evaluate_criterion(criterion, prompt, response, age_group)
            detailed_criteria.append(result)
        except Exception as e:
            logger.error(f"Failed to evaluate criterion {criterion.id}: {e}")

    # Calculate weighted aggregate scores
    final_aggregate, category_averages, subcategory_averages = calculate_weighted_scores(detailed_criteria)

    # Consistency metrics
    all_variances = [cr.judge_results[0].consistency_variance for cr in detailed_criteria if cr.judge_results]
    all_agreements = [cr.judge_agreement_score for cr in detailed_criteria]

    processing_time_ms = int((time.time() - start_time) * 1000)

    return BenchmarkResult(
        detailed_criteria=detailed_criteria,
        final_aggregate_score=final_aggregate,
        category_scores=category_averages,
        subcategory_scores=subcategory_averages,
        consistency_metrics={
            "overall_variance": statistics.mean(all_variances) if all_variances else 0.0,
            "judge_agreement_avg": statistics.mean(all_agreements) if all_agreements else 1.0,
            "total_evaluations": len(detailed_criteria),
        },
        metadata={
            "processing_time_ms": processing_time_ms,
            "n_criteria": len(detailed_criteria),
            "n_judges": len(config.judges),
            "n_passes": config.n_passes,
        },
    )
