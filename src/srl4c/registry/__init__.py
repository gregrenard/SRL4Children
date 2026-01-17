"""
SRL4C Registry Module

Provides unified access to criteria, judges, and presets.
Datasets are handled by core.datasets (database-backed).
"""

from srl4c.registry.loader import (
    RegistryLoader,
    get_registry_loader,
    CriteriaConfig,
    CriterionConfig,  # Alias for evaluator compatibility
    JudgeConfig,
    JudgeImplementation,
)

# Alias for backward compatibility
get_criteria_loader = get_registry_loader

__all__ = [
    "RegistryLoader",
    "get_registry_loader",
    "get_criteria_loader",  # Alias
    "CriteriaConfig",
    "CriterionConfig",  # Alias
    "JudgeConfig",
    "JudgeImplementation",
]
