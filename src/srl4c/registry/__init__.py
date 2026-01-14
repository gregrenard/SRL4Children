"""
SRL4C Registry Module

Provides unified access to criteria, judges, datasets, and presets.
"""

from srl4c.registry.loader import (
    RegistryLoader,
    get_registry_loader,
    CriteriaConfig,
    CriterionConfig,  # Alias for evaluator compatibility
    JudgeConfig,
    JudgeImplementation,
    DatasetConfig,
    DatasetPrompt,
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
    "DatasetConfig",
    "DatasetPrompt",
]
