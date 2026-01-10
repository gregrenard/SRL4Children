"""Core business logic module.

This module contains the shared logic used by both CLI and API.
Each long-running operation has two functions:

- create_X(): Validates inputs, creates DB record with status='pending', returns job ID
- run_X(): Executes the job, updates progress in DB, updates status on completion/failure

The CLI and API become thin wrappers around these core functions.
"""

from srl4c.core.attack import create_attack, run_attack
from srl4c.core.score import create_score, run_score, get_score_details, generate_report
from srl4c.core.guardrails import create_guardrails, run_guardrails, get_guardrails_details

__all__ = [
    "create_attack", "run_attack",
    "create_score", "run_score", "get_score_details", "generate_report",
    "create_guardrails", "run_guardrails", "get_guardrails_details",
]
