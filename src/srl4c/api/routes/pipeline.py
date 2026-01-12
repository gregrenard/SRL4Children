"""Pipeline routes"""

from fastapi import APIRouter, HTTPException

from srl4c.api.schemas import PipelineRequest, PipelineResponse
from srl4c.core.logger import Logger
from srl4c.db.models import Endpoint
from srl4c.db.repository import EndpointRepository, ScoreRepository, generate_id

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/", response_model=PipelineResponse, status_code=201)
async def run_pipeline(request: PipelineRequest):
    """Run the full SRL4C pipeline in one request.

    Creates endpoint → runs attack → scores results → generates guardrails.
    """
    from srl4c.core.attack import create_attack, run_attack
    from srl4c.core.guardrails import (
        create_guardrails,
        run_guardrails,
    )
    from srl4c.core.score import create_score, run_score

    try:
        # Step 1: Create or get endpoint
        endpoint = EndpointRepository.get_by_name(request.name)
        if not endpoint:
            config = {}
            if request.endpoint_type == "simple":
                config["request_field"] = request.request_field
                config["response_field"] = request.response_field

            endpoint = Endpoint(
                id=generate_id(),
                name=request.name,
                type=request.endpoint_type,
                base_url=request.base_url or request.endpoint_url,
                api_key_env=request.api_key_env,
                config=config,
            )
            EndpointRepository.create(endpoint)

        Logger.info(
            "pipeline",
            f"Pipeline started for endpoint '{endpoint.name}'",
            entity_type="endpoint",
            entity_id=endpoint.id,
        )

        # Step 2: Run attack
        try:
            attack_id = create_attack(request.name, request.dataset)
            run_attack(attack_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Attack failed: {str(e)}")

        # Step 3: Score results
        try:
            score_id = create_score(attack_id, age=request.age, weights_preset=request.weights)
            run_score(score_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Scoring failed: {str(e)}")

        # Get final score
        score = ScoreRepository.get_by_id(score_id)
        final_score = score.get("final_score") if score else None

        # Step 4: Generate guardrails
        guardrail_set_id = None
        try:
            guardrail_set_id = create_guardrails(
                score_id,
                max_rules=request.max_rules,
                max_total=request.max_total,
            )
            run_guardrails(
                guardrail_set_id,
                max_rules=request.max_rules,
                max_total=request.max_total,
            )
        except Exception as e:
            Logger.warn(
                "pipeline",
                f"Guardrails generation failed: {str(e)}",
                entity_type="score",
                entity_id=score_id,
            )

        # Step 5: Optional worker deployment (reserved for future use)
        if request.deploy_worker and guardrail_set_id:
            Logger.info(
                "pipeline",
                "Worker deployment requested but not yet implemented",
                entity_type="guardrail_set",
                entity_id=guardrail_set_id,
            )

        Logger.info(
            "pipeline",
            "Pipeline completed successfully",
            entity_type="endpoint",
            entity_id=endpoint.id,
            metadata={
                "attack_id": attack_id,
                "score_id": score_id,
                "guardrail_set_id": guardrail_set_id,
                "final_score": final_score,
            },
        )

        return PipelineResponse(
            endpoint_id=endpoint.id,
            attack_id=attack_id,
            score_id=score_id,
            guardrail_set_id=guardrail_set_id,
            status="completed",
            final_score=final_score,
            message="Pipeline completed successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        Logger.error(
            "pipeline",
            f"Pipeline failed: {str(e)}",
            metadata={"request": request.dict()},
        )
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")
