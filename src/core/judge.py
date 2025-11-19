"""
SRL4Children - Child Safety Benchmark System
Author: Gregory Renard (with GenAI: Claude, Gemini, Codex)
Organization: Everyone.AI | Year: 2025
For the well-being and safety of our children
"""

import json
import time
import logging
import statistics
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import yaml
import re
from pydantic import BaseModel, Field, ValidationError

from .criteria_loader import CriteriaLoader, CriterionConfig, get_criteria_loader
from .weighting_system import WeightingSystem
from ..connectors.clients import ollama_generate

logger = logging.getLogger(__name__)

class JudgePassModel(BaseModel):
    score: float = Field(ge=0.0, le=5.0)
    explanation: str = ""
    evidence_extracts: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": float(self.score),
            "explanation": self.explanation,
            "evidence_extracts": list(self.evidence_extracts or [])
        }

def _remove_fences_and_think(raw: str) -> str:
    s = raw.strip()
    s = re.sub(r"```(json)?", "", s, flags=re.IGNORECASE)
    s = re.sub(r"<think>[\s\S]*?</think>", "", s, flags=re.IGNORECASE)
    return s

def _normalize_quotes_commas(s: str) -> str:
    s = s.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    s = re.sub(r",(\s*[}\]])", r"\1", s)
    s = re.sub(r"\bNaN\b|\bInfinity\b|-Infinity", "null", s)
    return s

def _extract_json_block(s: str) -> Optional[str]:
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return s[start:end+1]

def _pydantic_validate(parsed: Dict[str, Any]) -> Dict[str, Any]:
    obj = JudgePassModel(**parsed)
    return obj.to_dict()

def _repair_with_llm(raw: str, schema_json: str, repair_model: str, host: str, port: int) -> Optional[Dict[str, Any]]:
    try:
        from ..connectors.clients import ollama_generate
        prompt = (
            "You are a JSON repair tool. Given an invalid JSON or extra text, output a JSON that strictly matches this schema.\n"
            "Schema (JSON):\n" + schema_json + "\n\n"
            "Rules:\n- Output ONLY the JSON object, no prose, no fences.\n"
            "- Coerce types if obvious (numbers to float 0-5, lists of strings).\n"
            "- If fields missing, fill with defaults: score=0.0, explanation='', evidence_extracts=[].\n\n"
            "Content to fix:\n" + raw
        )
        out = ollama_generate(prompt, repair_model, host=host, port=port, format="json", temperature=0.1, top_p=0.9)
        s = _remove_fences_and_think(out)
        s = _normalize_quotes_commas(s)
        block = _extract_json_block(s) or s
        parsed = json.loads(block)
        return _pydantic_validate(parsed)
    except Exception:
        return None

def parse_and_validate(raw_response: str, repair_model: str, host: str, port: int) -> Dict[str, Any]:
    # Attempt 1: direct
    try:
        s1 = _remove_fences_and_think(raw_response)
        s1 = _normalize_quotes_commas(s1)
        block1 = _extract_json_block(s1) or s1
        parsed1 = json.loads(block1)
        out = _pydantic_validate(parsed1)
        out["_validation"] = {"method": "direct"}
        return out
    except Exception:
        pass

    # Attempt 2: heuristic cleaning
    try:
        lines = [ln for ln in _remove_fences_and_think(raw_response).splitlines() if ln.strip()]
        s2 = "\n".join(lines)
        s2 = _normalize_quotes_commas(s2)
        block2 = _extract_json_block(s2)
        if block2:
            parsed2 = json.loads(block2)
            out = _pydantic_validate(parsed2)
            out["_validation"] = {"method": "heuristic"}
            return out
    except Exception:
        pass

    # Attempt 3: LLM repair (2 tries)
    try:
        schema_json = json.dumps(JudgePassModel.model_json_schema())
        for _ in range(2):
            fixed = _repair_with_llm(raw_response, schema_json, repair_model, host, port)
            if fixed is not None:
                fixed["_validation"] = {"method": "llm_repair"}
                return fixed
    except Exception:
        pass

    # Fallback
    return {
        "score": 0.0,
        "explanation": "Failed to parse and repair judge response",
        "evidence_extracts": [],
        "_validation": {"method": "fallback"}
    }

@dataclass
class JudgeResult:
    """Résultat d'évaluation d'un juge pour un critère"""
    judge_id: str  # "model_1" ou "model_2"
    criterion_id: str
    pass_results: List[Dict[str, Any]]  # Results from N passes
    final_score: float  # Aggregated score from passes
    consistency_variance: float  # Variance of scores from passes
    execution_time_ms: int
    raw_responses: List[str]  # Raw LLM responses

@dataclass
class CriterionEvaluationResult:
    """Résultat complet d'évaluation d'un critère par tous les juges"""
    criterion: CriterionConfig
    judge_results: List[JudgeResult]
    final_score: float  # Aggregated score from all judges
    judge_agreement_score: float  # Agreement between judges (0-1)
    outliers_detected: List[str]  # IDs of outlier judges
    processing_time_ms: int
    metadata: Dict[str, Any]

@dataclass
class BenchmarkResult:
    """Résultat final agrégé du benchmark"""
    final_aggregate_score: float
    category_scores: Dict[str, float]
    subcategory_scores: Dict[str, float] 
    detailed_criteria: List[CriterionEvaluationResult]
    consistency_metrics: Dict[str, float]
    metadata: Dict[str, Any]

class PersonaLoader:
    """Chargeur des personas depuis assets/personas.json"""
    
    def __init__(self, assets_path: Optional[Path] = None):
        if assets_path is None:
            current_dir = Path(__file__).parent
            while current_dir != current_dir.parent:
                assets_dir = current_dir / "assets"
                if assets_dir.exists():
                    assets_path = assets_dir
                    break
                current_dir = current_dir.parent
        
        self.personas_file = assets_path / "personas.json"
        self._personas_cache: Optional[Dict] = None
    
    def load_personas(self) -> Dict[str, Any]:
        """Load personas from JSON file"""
        if self._personas_cache is None:
            with open(self.personas_file, 'r', encoding='utf-8') as f:
                self._personas_cache = json.load(f)
        return self._personas_cache
    
    def get_persona_by_age_group(self, age_group: str) -> Dict[str, Any]:
        """Get persona configuration by age group"""
        personas = self.load_personas()
        
        # Map age groups to persona keys
        age_mappings = {
            "6-8": "Child",
            "9-12": "Teen", 
            "13-17": "YoungAdult",
            "18-25": "Emerging"
        }
        
        persona_key = age_mappings.get(age_group, "Teen")  # Default to Teen
        
        if persona_key not in personas:
            logger.warning(f"Persona not found for age group {age_group}, using Teen")
            persona_key = "Teen"
        
        return personas[persona_key]

class MultiJudgeEvaluator:
    """Évaluateur multi-juges pour un critère donné"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize multi-judge evaluator
        
        Args:
            config: Judge system configuration from config.yml
        """
        self.judges_config = config.get("judges", {})
        self.evaluation_config = config.get("evaluation", {})
        self.consistency_config = config.get("consistency", {})
        
        self.n_passes = self.evaluation_config.get("n_passes", 3)
        self.hyperparameters = self.evaluation_config.get("hyperparameters", {})
        self.variance_threshold = self.consistency_config.get("variance_threshold", 0.5)
        self.agreement_threshold = self.consistency_config.get("agreement_threshold", 0.8)
        
        logger.info(f"MultiJudgeEvaluator initialized with {len(self.judges_config)} judges, {self.n_passes} passes")
    
    def evaluate_criterion(
        self, 
        criterion: CriterionConfig, 
        prompt: str, 
        response: str, 
        age_group: str,
        ollama_host: str = "localhost",
        ollama_port: int = 11434
    ) -> CriterionEvaluationResult:
        """
        Evaluate a criterion with all judges and multiple passes
        
        Args:
            criterion: Criterion configuration to evaluate
            prompt: Original user prompt
            response: LLM response to evaluate
            age_group: Age group for persona context
            ollama_host: Ollama host
            ollama_port: Ollama port
            
        Returns:
            Complete criterion evaluation result
        """
        start_time = time.time()
        
        # Load persona for age context
        persona_loader = PersonaLoader()
        persona = persona_loader.get_persona_by_age_group(age_group)
        
        # Evaluate with each judge
        judge_results = []
        
        for judge_id, judge_model in self.judges_config.items():
            try:
                # Supporte deux formats de config: str (nom de modèle) ou dict {model, options}
                model_name = judge_model if isinstance(judge_model, str) else judge_model.get("model", "")
                extra_options = {} if isinstance(judge_model, str) else judge_model.get("options", {})

                judge_result = self._evaluate_with_single_judge(
                    judge_id, model_name, criterion, prompt, response, 
                    persona, ollama_host, ollama_port
                , extra_options)
                judge_results.append(judge_result)
            except Exception as e:
                logger.error(f"Judge {judge_id} failed for criterion {criterion.id}: {e}")
                # Continue with other judges
        
        if not judge_results:
            raise RuntimeError(f"All judges failed for criterion {criterion.id}")
        
        # Calculate inter-judge agreement
        scores = [jr.final_score for jr in judge_results]
        agreement_score = self._calculate_agreement_score(scores)
        
        # Detect outliers
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
                "outliers_count": len(outliers)
            }
        )
    
    def _evaluate_with_single_judge(
        self,
        judge_id: str,
        judge_model: str, 
        criterion: CriterionConfig,
        prompt: str,
        response: str,
        persona: Dict[str, Any],
        ollama_host: str,
        ollama_port: int,
        extra_options: Dict[str, Any] = None
    ) -> JudgeResult:
        """Evaluate criterion with a single judge using N passes"""
        start_time = time.time()
        
        # Build evaluation prompt from criterion template
        evaluation_prompt = self._build_evaluation_prompt(criterion, prompt, response, persona)
        
        # Execute N passes with different hyperparameters
        pass_results = []
        raw_responses = []
        
        for pass_idx in range(self.n_passes):
            hyperparams = self.hyperparameters.get(f"pass_{pass_idx + 1}", {
                "temperature": 0.1,
                "top_p": 0.9
            })
            
            try:
                # Retries (3 attempts) for network/loading robustness
                last_err = None
                backoffs = [5, 10, 20]
                for attempt in range(3):
                    try:
                        raw_response = ollama_generate(
                            evaluation_prompt,
                            judge_model,
                            host=ollama_host,
                            port=ollama_port,
                            temperature=hyperparams.get("temperature", 0.1),
                            top_p=hyperparams.get("top_p", 0.9),
                            **(extra_options or {})
                        )
                        break
                    except Exception as e:
                        last_err = e
                        if attempt < 2:
                            import time as _t
                            _t.sleep(backoffs[attempt])
                        else:
                            raise

                # Parse + validation + potential repair via LLM
                parsed_result = parse_and_validate(raw_response, judge_model, ollama_host, ollama_port)
                pass_results.append(parsed_result)
                raw_responses.append(raw_response)
                
            except Exception as e:
                logger.warning(f"Pass {pass_idx + 1} failed for judge {judge_id}: {e}")
                # Use default result for failed pass
                pass_results.append({
                    "score": 0.0,
                    "explanation": f"Failed to evaluate: {str(e)}",
                    "evidence_extracts": []
                })
                raw_responses.append(f"ERROR: {str(e)}")
        
        # Calculate consistency variance
        scores = [pr.get("score", 0.0) for pr in pass_results]
        final_score = statistics.mean(scores) if scores else 0.0
        consistency_variance = statistics.variance(scores) if len(scores) > 1 else 0.0
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        return JudgeResult(
            judge_id=judge_id,
            criterion_id=criterion.id,
            pass_results=pass_results,
            final_score=final_score,
            consistency_variance=consistency_variance,
            execution_time_ms=execution_time_ms,
            raw_responses=raw_responses
        )
    
    def _build_evaluation_prompt(
        self,
        criterion: CriterionConfig, 
        prompt: str, 
        response: str,
        persona: Dict[str, Any]
    ) -> str:
        """Build evaluation prompt from criterion template"""
        
        if not criterion.prompt_content:
            raise ValueError(f"No prompt content loaded for criterion {criterion.id}")
        
        # Extract template parts
        role = criterion.prompt_content.get("role", "")
        task = criterion.prompt_content.get("task", "")
        age_context = criterion.prompt_content.get("age_context", "")
        scoring_guide = criterion.prompt_content.get("scoring_guide", "")
        examples = criterion.prompt_content.get("examples", "")
        output_format = criterion.prompt_content.get("output_format", "")
        content_template = criterion.prompt_content.get("CONTENT TO ANALYZE", "")
        
        # Format with context variables
        age_group = persona.get("maturity_band", "9-12")
        
        formatted_prompt = f"""{role}

{task}

{age_context.format(age_group=age_group)}

{scoring_guide}

{examples}

{output_format}

CONTENT TO ANALYZE:
---
PROMPT: {prompt}
RESPONSE: {response}"""
        
        return formatted_prompt
    
    def _parse_judge_response(self, raw_response: str) -> Dict[str, Any]:
        """Parse judge response from JSON format"""
        try:
            # Try to extract JSON from response
            response = raw_response.strip()
            
            # Handle cases where response has extra text around JSON
            if response.startswith("```json"):
                response = response.replace("```json", "").replace("```", "").strip()
            
            # Find JSON block
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[start_idx:end_idx]
            parsed = json.loads(json_str)
            
            # Ensure required fields exist
            result = {
                "score": float(parsed.get("score", 0.0)),
                "explanation": parsed.get("explanation", "No explanation provided"),
                "evidence_extracts": parsed.get("evidence_extracts", [])
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse judge response: {e}")
            logger.debug(f"Raw response was: {raw_response[:500]}...")
            return {
                "score": 0.0,
                "explanation": f"Failed to parse response: {str(e)}",
                "evidence_extracts": []
            }
    
    def _calculate_agreement_score(self, scores: List[float]) -> float:
        """Calculate agreement score between judges (1.0 = perfect agreement)"""
        if len(scores) < 2:
            return 1.0
        
        # Calculate coefficient of variation (std/mean)
        mean_score = statistics.mean(scores)
        if mean_score == 0:
            return 1.0  # All zeros = perfect agreement
        
        std_dev = statistics.stdev(scores)
        cv = std_dev / mean_score
        
        # Convert to agreement score (0-1, higher is better)
        agreement = max(0.0, 1.0 - cv)
        return agreement
    
    def _detect_outliers(self, judge_results: List[JudgeResult]) -> List[str]:
        """Detect outlier judges based on scores"""
        if len(judge_results) < 3:
            return []  # Need at least 3 judges to detect outliers
        
        scores = [(jr.judge_id, jr.final_score) for jr in judge_results]
        mean_score = statistics.mean([s[1] for s in scores])
        std_dev = statistics.stdev([s[1] for s in scores])
        
        outliers = []
        threshold = 2.0  # 2 standard deviations
        
        for judge_id, score in scores:
            z_score = abs(score - mean_score) / std_dev if std_dev > 0 else 0
            if z_score > threshold:
                outliers.append(judge_id)
        
        return outliers

class SRL4Children:
    """Système de jugement principal SRL4Children V1.1"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize V1.1 judge system
        
        Args:
            config: Complete configuration from config.yml
        """
        self.config = config
        self.judge_system_config = config.get("judge_system", {})
        self.weights_config = config.get("weights", {})
        self.criteria_config = config.get("criteria", {})
        
        self.criteria_loader = get_criteria_loader()
        self.multi_judge_evaluator = MultiJudgeEvaluator(self.judge_system_config)
        self.weighting_system = WeightingSystem(self.weights_config)
        
        logger.info("SRL4Children judge system initialized")
    
    def evaluate_content(
        self,
        prompt: str,
        response: str, 
        age_group: str,
        criteria_selection: Optional[str] = None,
        ollama_host: str = "localhost",
        ollama_port: int = 11434
    ) -> BenchmarkResult:
        """
        Evaluate content using specified criteria
        
        Args:
            prompt: Original user prompt
            response: LLM response to evaluate
            age_group: Age group for evaluation context
            criteria_selection: Criteria selection pattern (default: use config)
            ollama_host: Ollama host
            ollama_port: Ollama port
            
        Returns:
            Complete benchmark result with V1.1 format
        """
        start_time = time.time()
        
        # Resolve criteria selection
        if criteria_selection is None:
            criteria_selection = self.criteria_config.get("default_selection", "full_evaluation")
        
        criterion_ids = self.criteria_loader.resolve_criteria_selection(criteria_selection)
        if not criterion_ids:
            raise ValueError(f"No criteria found for selection: {criteria_selection}")
        
        logger.info(f"Evaluating {len(criterion_ids)} criteria")
        
        # Load criteria
        criteria = self.criteria_loader.load_multiple_criteria(criterion_ids)
        logger.info(f"Successfully loaded {len(criteria)}/{len(criterion_ids)} criteria")
        
        # Evaluate each criterion
        criterion_results = []
        total_criteria = len(criteria)
        
        for idx, criterion in enumerate(criteria, 1):
            criterion_start_time = time.time()
            try:
                logger.info(f"  📋 {idx:2d}/{total_criteria}: Evaluating {criterion.id} ({criterion.category}.{criterion.subcategory})")
                
                result = self.multi_judge_evaluator.evaluate_criterion(
                    criterion, prompt, response, age_group, ollama_host, ollama_port
                )
                
                execution_time = time.time() - criterion_start_time
                criterion_results.append(result)
                
                # Log detailed results for this criterion
                agreement_score = result.judge_agreement_score
                logger.info(f"     ✅ Score: {result.final_score:.2f} | Agreement: {agreement_score:.2f} | Time: {execution_time:.1f}s")
                
            except Exception as e:
                execution_time = time.time() - criterion_start_time
                logger.error(f"     ❌ Failed {criterion.id}: {e} | Time: {execution_time:.1f}s")
                # Continue with other criteria
        
        if not criterion_results:
            raise RuntimeError("All criteria evaluations failed")
        
        # Calculate weighted scores using WeightingSystem  
        weighted_result = self.weighting_system.calculate_weighted_scores(criterion_results)
        
        # Calculate consistency metrics
        consistency_metrics = self._calculate_consistency_metrics(criterion_results)
        
        total_processing_time_ms = int((time.time() - start_time) * 1000)
        
        return BenchmarkResult(
            final_aggregate_score=weighted_result["final_score"],
            category_scores=weighted_result["category_scores"],
            subcategory_scores=weighted_result["subcategory_scores"],
            detailed_criteria=criterion_results,
            consistency_metrics=consistency_metrics,
            metadata={
                "total_criteria_evaluated": len(criterion_results),
                "total_processing_time_ms": total_processing_time_ms,
                "criteria_selection": criteria_selection,
                "age_group": age_group,
                "judge_models_used": [
                    {"judge_id": judge_id, "model_name": model_name}
                    for judge_id, model_name in self.multi_judge_evaluator.judges_config.items()
                ],
                "evaluation_config": {
                    "n_passes": self.judge_system_config.get("evaluation", {}).get("n_passes", 3),
                    "n_judges": len(self.multi_judge_evaluator.judges_config),
                    "hyperparameters": self.judge_system_config.get("evaluation", {}).get("hyperparameters", {})
                },
                "timestamp": time.time()
            }
        )
    
    def _calculate_consistency_metrics(self, results: List[CriterionEvaluationResult]) -> Dict[str, float]:
        """Calculate overall consistency metrics"""
        if not results:
            return {}
        
        # Overall variance across all criteria
        all_variances = []
        all_agreements = []
        outlier_count = 0
        
        for result in results:
            # Collect consistency variances from all judges
            for judge_result in result.judge_results:
                all_variances.append(judge_result.consistency_variance)
            
            all_agreements.append(result.judge_agreement_score)
            outlier_count += len(result.outliers_detected)
        
        return {
            "overall_variance": statistics.mean(all_variances) if all_variances else 0.0,
            "judge_agreement_avg": statistics.mean(all_agreements) if all_agreements else 0.0,
            "outliers_detected": outlier_count
        }
    
    def _aggregate_explanations(self, judge_results: List[JudgeResult]) -> str:
        """Agrège les explications de tous les juges et passes en une explication synthétique"""
        if not judge_results:
            return ""
        
        explanations = []
        
        for judge_result in judge_results:
            judge_explanations = []
            for pass_idx, pass_result in enumerate(judge_result.pass_results, 1):
                explanation = pass_result.get("explanation", "")
                if explanation:
                    judge_explanations.append(f"Pass {pass_idx}: {explanation}")
            
            if judge_explanations:
                explanations.append(f"{judge_result.judge_id} - {' | '.join(judge_explanations)}")
        
        if len(explanations) > 1:
            # Multi-judge synthesis
            return f"Multi-judge evaluation: {' || '.join(explanations)}"
        else:
            # Single judge (fallback)
            return explanations[0] if explanations else ""

# Main evaluation function for compatibility with existing code
def judge_v1_1(
    prompt: str,
    response: str,
    age_group: str,
    config: Dict[str, Any],
    criteria_selection: Optional[str] = None,
    ollama_host: str = "localhost", 
    ollama_port: int = 11434
) -> Dict[str, Any]:
    """
    Main evaluation function compatible with existing benchmark code
    
    Args:
        prompt: User prompt
        response: LLM response to evaluate
        age_group: Age group for evaluation
        config: Complete configuration dictionary
        criteria_selection: Optional criteria selection pattern
        ollama_host: Ollama host
        ollama_port: Ollama port
        
    Returns:
        Evaluation result in V1.1 JSON format
    """
    judge_system = SRL4Children(config)
    
    try:
        result = judge_system.evaluate_content(
            prompt, response, age_group, criteria_selection, ollama_host, ollama_port
        )
        
        # Convert to V1.1 JSON format
        return {
            "final_aggregate_score": result.final_aggregate_score,
            "category_scores": result.category_scores,
            "subcategory_scores": result.subcategory_scores,
            "detailed_criteria": [
                {
                    "criterion": cr.criterion.id,
                    "scores": {
                        "final_score": cr.final_score,
                        "individual_passes": [
                            [pr.get("score", 0.0) for pr in jr.pass_results]
                            for jr in cr.judge_results
                        ],
                        "consistency_variance": statistics.mean([jr.consistency_variance for jr in cr.judge_results]),
                        "judge_agreement": {
                            judge_result.judge_id: judge_result.final_score 
                            for judge_result in cr.judge_results
                        } | {"agreement_score": cr.judge_agreement_score}
                    },
                    "explanation": judge_system._aggregate_explanations(cr.judge_results) if cr.judge_results else "",
                    "evidence_extracts": cr.judge_results[0].pass_results[0].get("evidence_extracts", []) if cr.judge_results else [],
                    "detailed_judge_results": [
                        {
                            "judge_id": jr.judge_id,
                            "judge_model": judge_system.multi_judge_evaluator.judges_config.get(jr.judge_id, "unknown"),
                            "final_score": jr.final_score,
                            "consistency_variance": jr.consistency_variance,
                            "execution_time_ms": jr.execution_time_ms,
                            "passes": [
                                {
                                    "pass_number": idx + 1,
                                    "score": pass_result.get("score", 0.0),
                                    "explanation": pass_result.get("explanation", ""),
                                    "evidence_extracts": pass_result.get("evidence_extracts", [])
                                }
                                for idx, pass_result in enumerate(jr.pass_results)
                            ],
                            "raw_responses": jr.raw_responses
                        }
                        for jr in cr.judge_results
                    ] if cr.judge_results else [],
                    "metadata": {
                        "criterion_version": cr.criterion.version,
                        "processing_time_ms": cr.processing_time_ms,
                        "outlier_detected": len(cr.outliers_detected) > 0,
                        "timestamp": time.time()
                    }
                }
                for cr in result.detailed_criteria
            ],
            "consistency_metrics": result.consistency_metrics,
            "metadata": result.metadata
        }
        
    except Exception as e:
        logger.error(f"Judge evaluation failed: {e}")
        # Return minimal error result
        return {
            "final_aggregate_score": 0.0,
            "category_scores": {},
            "subcategory_scores": {},
            "detailed_criteria": [],
            "consistency_metrics": {},
            "metadata": {"error": str(e), "timestamp": time.time()}
        }
