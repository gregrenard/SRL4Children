"""
E2E test for full SRL4C pipeline via REST API.

Tests: endpoint → attack → score → guardrails
Uses fake endpoint and fake judge servers (no real LLMs).
"""

import pytest
from conftest import poll_status


class TestPipelineAPI:
    """Full pipeline test via API"""

    def test_health_check(self, api_client):
        """Verify API is running"""
        response = api_client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_full_pipeline(self, api_client, test_endpoint, temp_db):
        """Run complete pipeline: endpoint → attack → score → guardrails"""

        # Step 1: Verify endpoint was created
        endpoint_id = test_endpoint["id"]
        assert endpoint_id is not None

        # Verify endpoint exists
        response = api_client.get(f"/api/endpoints/{endpoint_id}")
        assert response.status_code == 200
        endpoint_data = response.json()
        assert endpoint_data["name"] == "test-bot"
        assert endpoint_data["type"] == "simple"

        # Step 2: Create attack
        response = api_client.post("/api/attacks", json={
            "endpoint": "test-bot",
            "dataset": "test_mini",
        })
        assert response.status_code == 202, f"Failed to create attack: {response.text}"
        attack_data = response.json()
        attack_id = attack_data["id"]
        assert attack_data["status"] == "pending"

        # Step 3: Poll until attack completes
        attack_result = poll_status(api_client, f"/api/attacks/{attack_id}", "completed", timeout=60)
        assert attack_result["status"] == "completed"

        # Verify attack processed all prompts
        assert attack_result["completed_prompts"] == 8, f"Expected 8 completed prompts, got {attack_result['completed_prompts']}"
        assert attack_result["total_prompts"] == 8

        # Step 4: Create score
        response = api_client.post("/api/scores", json={
            "attack_id": attack_id,
            "age": "child",
            "matrix": "flat",
        })
        assert response.status_code == 202, f"Failed to create score: {response.text}"
        score_data = response.json()
        score_id = score_data["id"]

        # Step 5: Poll until score completes
        score_result = poll_status(api_client, f"/api/scores/{score_id}", "completed", timeout=120)
        assert score_result["status"] == "completed"

        # Verify final score exists and is valid
        assert score_result.get("final_score") is not None
        assert 1.0 <= score_result["final_score"] <= 5.0

        # Verify category scores exist
        assert score_result.get("category_scores") is not None
        assert len(score_result["category_scores"]) > 0

        # Verify failures endpoint works (fake judge guarantees some failures)
        response = api_client.get(f"/api/scores/{score_id}/failures")
        assert response.status_code == 200
        failures = response.json()
        # Should have at least one failure (fake judge forces ~25% low scores)
        assert failures["count"] >= 1, "Expected at least 1 failure from fake judge"

        # Step 6: Generate guardrails (fake judge ensures some low scores)
        response = api_client.post("/api/guardrails", json={
            "score_id": score_id,
            "max_rules": 3,
            "max_total": 10,
        })
        assert response.status_code == 202, f"Failed to create guardrails: {response.text}"
        guardrails_data = response.json()
        set_id = guardrails_data["id"]

        # Step 7: Poll until guardrails complete
        guardrails_result = poll_status(api_client, f"/api/guardrails/{set_id}", "completed", timeout=120)
        assert guardrails_result["status"] == "completed"

        # Verify guardrails were generated (fake judge ensures failures exist)
        assert guardrails_result.get("rules_count", 0) >= 1, "Expected at least 1 guardrail rule generated"

        # Verify guardrails are included in response
        assert guardrails_result.get("guardrails") is not None
        for rule in guardrails_result["guardrails"]:
            assert rule.get("rule_text") is not None
            assert rule.get("criteria_id") is not None

        # Step 8: Verify data consistency across pipeline
        self._verify_data_consistency(
            api_client, endpoint_id, attack_id, score_id, set_id
        )

    def _verify_data_consistency(self, client, endpoint_id, attack_id, score_id, set_id):
        """Verify data relationships are consistent across all entities"""

        # Attack references correct endpoint
        attack = client.get(f"/api/attacks/{attack_id}").json()
        assert attack["endpoint_id"] == endpoint_id

        # Score references correct attack
        score = client.get(f"/api/scores/{score_id}").json()
        assert score["attack_id"] == attack_id

        # Guardrail set references correct score
        guardrails = client.get(f"/api/guardrails/{set_id}").json()
        assert guardrails["score_id"] == score_id

    def test_attack_with_nonexistent_endpoint(self, api_client, temp_db):
        """Verify error handling for missing endpoint"""
        response = api_client.post("/api/attacks", json={
            "endpoint": "nonexistent-endpoint",
            "dataset": "test_mini",
        })
        assert response.status_code in [400, 404, 422]

    def test_score_with_nonexistent_attack(self, api_client, temp_db):
        """Verify error handling for missing attack"""
        response = api_client.post("/api/scores", json={
            "attack_id": "nonexistent-attack-id",
            "age": "child",
            "matrix": "flat",
        })
        assert response.status_code in [400, 404, 422]

    def test_report_generation(self, api_client, test_endpoint, temp_db):
        """Test score report generation"""
        # Create attack
        response = api_client.post("/api/attacks", json={
            "endpoint": "test-bot",
            "dataset": "test_mini",
        })
        attack_id = response.json()["id"]
        poll_status(api_client, f"/api/attacks/{attack_id}", "completed", timeout=60)

        # Create score
        response = api_client.post("/api/scores", json={
            "attack_id": attack_id,
            "age": "child",
            "matrix": "flat",
        })
        score_id = response.json()["id"]
        poll_status(api_client, f"/api/scores/{score_id}", "completed", timeout=120)

        # Get report
        response = api_client.get(f"/api/scores/{score_id}/report")
        assert response.status_code == 200
        report = response.json()
        assert "report" in report
        assert "# SRL4C Score Report" in report["report"]
        assert "## Metadata" in report["report"]
        assert "## Scores" in report["report"]

    def test_guardrails_export(self, api_client, test_endpoint, temp_db):
        """Test guardrails export"""
        # Create attack
        response = api_client.post("/api/attacks", json={
            "endpoint": "test-bot",
            "dataset": "test_mini",
        })
        attack_id = response.json()["id"]
        poll_status(api_client, f"/api/attacks/{attack_id}", "completed", timeout=60)

        # Create score
        response = api_client.post("/api/scores", json={
            "attack_id": attack_id,
            "age": "child",
            "matrix": "flat",
        })
        score_id = response.json()["id"]
        poll_status(api_client, f"/api/scores/{score_id}", "completed", timeout=120)

        # Generate guardrails
        response = api_client.post("/api/guardrails", json={
            "score_id": score_id,
            "max_rules": 3,
            "max_total": 10,
        })
        set_id = response.json()["id"]
        poll_status(api_client, f"/api/guardrails/{set_id}", "completed", timeout=120)

        # Export guardrails
        response = api_client.get(f"/api/guardrails/{set_id}/export")
        assert response.status_code == 200
        export = response.json()
        assert "text" in export
        assert "rules_count" in export
        assert export["rules_count"] >= 1

    def test_delete_guardrail_set(self, api_client, test_endpoint, temp_db):
        """Test guardrail set deletion"""
        # Create full pipeline
        response = api_client.post("/api/attacks", json={
            "endpoint": "test-bot",
            "dataset": "test_mini",
        })
        attack_id = response.json()["id"]
        poll_status(api_client, f"/api/attacks/{attack_id}", "completed", timeout=60)

        response = api_client.post("/api/scores", json={
            "attack_id": attack_id,
            "age": "child",
            "matrix": "flat",
        })
        score_id = response.json()["id"]
        poll_status(api_client, f"/api/scores/{score_id}", "completed", timeout=120)

        response = api_client.post("/api/guardrails", json={
            "score_id": score_id,
        })
        set_id = response.json()["id"]
        poll_status(api_client, f"/api/guardrails/{set_id}", "completed", timeout=120)

        # Delete preview
        response = api_client.get(f"/api/guardrails/{set_id}/delete-preview")
        assert response.status_code == 200
        preview = response.json()
        assert "will_delete" in preview

        # Delete
        response = api_client.delete(f"/api/guardrails/{set_id}")
        assert response.status_code == 200
        assert response.json()["deleted"] is True

        # Verify deleted
        response = api_client.get(f"/api/guardrails/{set_id}")
        assert response.status_code == 404

    def test_delete_score(self, api_client, test_endpoint, temp_db):
        """Test score deletion (cascades to guardrails)"""
        # Create attack and score
        response = api_client.post("/api/attacks", json={
            "endpoint": "test-bot",
            "dataset": "test_mini",
        })
        attack_id = response.json()["id"]
        poll_status(api_client, f"/api/attacks/{attack_id}", "completed", timeout=60)

        response = api_client.post("/api/scores", json={
            "attack_id": attack_id,
            "age": "child",
            "matrix": "flat",
        })
        score_id = response.json()["id"]
        poll_status(api_client, f"/api/scores/{score_id}", "completed", timeout=120)

        # Delete preview
        response = api_client.get(f"/api/scores/{score_id}/delete-preview")
        assert response.status_code == 200

        # Delete
        response = api_client.delete(f"/api/scores/{score_id}")
        assert response.status_code == 200
        assert response.json()["deleted"] is True

        # Verify deleted
        response = api_client.get(f"/api/scores/{score_id}")
        assert response.status_code == 404

    def test_delete_attack(self, api_client, test_endpoint, temp_db):
        """Test attack deletion (cascades to scores)"""
        # Create attack
        response = api_client.post("/api/attacks", json={
            "endpoint": "test-bot",
            "dataset": "test_mini",
        })
        attack_id = response.json()["id"]
        poll_status(api_client, f"/api/attacks/{attack_id}", "completed", timeout=60)

        # Delete preview
        response = api_client.get(f"/api/attacks/{attack_id}/delete-preview")
        assert response.status_code == 200

        # Delete
        response = api_client.delete(f"/api/attacks/{attack_id}")
        assert response.status_code == 200
        assert response.json()["deleted"] is True

        # Verify deleted
        response = api_client.get(f"/api/attacks/{attack_id}")
        assert response.status_code == 404

    def test_delete_endpoint(self, api_client, fake_endpoint_server, temp_db):
        """Test endpoint deletion (cascades to attacks)"""
        # Create endpoint
        response = api_client.post("/api/endpoints", json={
            "name": "delete-test-bot",
            "type": "simple",
            "base_url": fake_endpoint_server["url"],
        })
        endpoint_id = response.json()["id"]

        # Delete preview
        response = api_client.get(f"/api/endpoints/{endpoint_id}/delete-preview")
        assert response.status_code == 200

        # Delete
        response = api_client.delete(f"/api/endpoints/{endpoint_id}")
        assert response.status_code == 200
        assert response.json()["deleted"] is True

        # Verify deleted
        response = api_client.get(f"/api/endpoints/{endpoint_id}")
        assert response.status_code == 404

    def test_presence_cache_reuse(self, api_client, test_endpoint, temp_db):
        """Test that re-scoring reuses cached presence levels (issue #4)

        When scoring the same attack with a different matrix/age:
        1. First score runs full LLM evaluation
        2. Second score should reuse cached presence levels, skip LLM calls
        3. Both scores should have same presence levels but different final scores
        """
        # Create attack
        response = api_client.post("/api/attacks", json={
            "endpoint": "test-bot",
            "dataset": "test_mini",
        })
        attack_id = response.json()["id"]
        poll_status(api_client, f"/api/attacks/{attack_id}", "completed", timeout=60)

        # Check presence status before any scoring - should be empty
        response = api_client.get(f"/api/attacks/{attack_id}/presence-status")
        assert response.status_code == 200
        status = response.json()
        assert status["has_presence"] is False
        assert status["evaluated_records"] == 0

        # First score - runs full LLM evaluation
        response = api_client.post("/api/scores", json={
            "attack_id": attack_id,
            "age": "child",
            "matrix": "educational",
        })
        score1_id = response.json()["id"]
        score1_result = poll_status(api_client, f"/api/scores/{score1_id}", "completed", timeout=120)
        assert score1_result["status"] == "completed"

        # Check presence status after first score - should have cache
        response = api_client.get(f"/api/attacks/{attack_id}/presence-status")
        assert response.status_code == 200
        status = response.json()
        assert status["has_presence"] is True
        assert status["evaluated_records"] > 0

        # Second score with different matrix - should reuse cache
        response = api_client.post("/api/scores", json={
            "attack_id": attack_id,
            "age": "teenager",
            "matrix": "companionship",
        })
        score2_id = response.json()["id"]
        score2_result = poll_status(api_client, f"/api/scores/{score2_id}", "completed", timeout=30)  # Should be fast
        assert score2_result["status"] == "completed"

        # Both scores should be valid
        assert score1_result.get("final_score") is not None
        assert score2_result.get("final_score") is not None

        # Scores may differ due to different matrix/age
        # But both should be in valid range
        assert 1.0 <= score1_result["final_score"] <= 5.0
        assert 1.0 <= score2_result["final_score"] <= 5.0

        # Verify presence levels are identical by checking evaluations
        # Get evaluations for both scores via the database
        from srl4c.db.models import db_connection

        with db_connection() as conn:
            evals1 = conn.execute(
                "SELECT record_id, criteria_id, presence_level FROM evaluations WHERE score_id LIKE ?",
                (score1_id + "%",)
            ).fetchall()
            evals2 = conn.execute(
                "SELECT record_id, criteria_id, presence_level FROM evaluations WHERE score_id LIKE ?",
                (score2_id + "%",)
            ).fetchall()

        # Build presence maps
        presence1 = {(e["record_id"], e["criteria_id"]): e["presence_level"] for e in evals1}
        presence2 = {(e["record_id"], e["criteria_id"]): e["presence_level"] for e in evals2}

        # Same keys (same records and criteria evaluated)
        assert set(presence1.keys()) == set(presence2.keys()), "Both scores should evaluate same records/criteria"

        # Same presence levels (cached values reused)
        for key in presence1:
            assert presence1[key] == presence2[key], f"Presence levels should match for {key}"
