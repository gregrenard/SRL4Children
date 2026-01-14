"""
SRL4C Registry Module

Provides unified access to criteria, judges, datasets, and presets.
"""

from srl4c.registry.loader import (
    RegistryLoader,
    get_registry_loader,
    CriteriaConfig,
    JudgeConfig,
    JudgeImplementation,
    DatasetConfig,
    DatasetPrompt,
)

__all__ = [
    "RegistryLoader",
    "get_registry_loader",
    "CriteriaConfig",
    "JudgeConfig",
    "JudgeImplementation",
    "DatasetConfig",
    "DatasetPrompt",
]
