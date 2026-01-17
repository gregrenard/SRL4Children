"""
Registry loader for SRL4C v2.0

Handles:
- Criteria: Abstract definitions of what can be tested
- Judges: Evaluation implementations with inheritance and weights
- Datasets: Auto-discovered from filesystem
- Presets: Named criteria selections
"""

import logging
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from srl4c.paths import (
    DATA_DIR,
    REGISTRY_FILE,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class CriteriaConfig:
    """Abstract criteria definition - what can be tested."""

    id: str  # e.g., "safety.sexual.sexual_content"
    category: str  # e.g., "safety"
    subcategory: str  # e.g., "sexual"
    name: str  # e.g., "sexual_content"
    description: str
    tags: list[str] = field(default_factory=list)
    prompt_content: dict[str, Any] | None = None  # Loaded judge prompt for evaluator


# Alias for backward compatibility with evaluator
CriterionConfig = CriteriaConfig


@dataclass
class JudgeImplementation:
    """Implementation details for a criteria within a judge."""

    file: str
    version: str
    created: str
    author: str
    prompt_content: dict[str, Any] | None = None  # Loaded lazily


@dataclass
class JudgeConfig:
    """Judge configuration with resolved inheritance."""

    name: str
    description: str
    inherits_from: str | None
    weights: dict[str, dict[str, float]]  # {categories: {}, subcategories: {}, criteria: {}}
    implementations: dict[str, JudgeImplementation]  # criteria_id -> implementation


# =============================================================================
# Registry Loader
# =============================================================================


class RegistryLoader:
    """Unified loader for registry: criteria, judges, datasets, presets."""

    def __init__(self, registry_file: Path | None = None, data_dir: Path | None = None):
        self.registry_file = registry_file or REGISTRY_FILE  # Legacy fallback
        self.data_dir = data_dir or DATA_DIR
        self.criteria_dir = self.data_dir / "criteria"

        # New split file paths
        self.criteria_file = self.criteria_dir / "criteria.yml"
        self.presets_file = self.criteria_dir / "presets.yml"
        self.judges_registry_dir = self.criteria_dir / "judges"

        self._registry_cache: dict | None = None
        self._criteria_cache: dict[str, CriteriaConfig] = {}
        self._judge_cache: dict[str, JudgeConfig] = {}
        self._prompt_cache: dict[str, dict[str, Any]] = {}  # file -> content

        logger.info(f"RegistryLoader initialized: criteria_dir={self.criteria_dir}")

    # -------------------------------------------------------------------------
    # Registry Loading
    # -------------------------------------------------------------------------

    def load_registry(self, force_reload: bool = False) -> dict[str, Any]:
        """Load registry from split files (criteria.yml, presets.yml, judges/*.yml).

        Falls back to legacy registry.yml if split files don't exist.
        """
        if self._registry_cache is None or force_reload:
            registry: dict[str, Any] = {"criteria": {}, "judges": {}, "presets": {}, "metadata": {}}

            # Try loading from split files first
            if self.criteria_file.exists():
                # Load criteria definitions
                with open(self.criteria_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    registry["criteria"] = data.get("criteria", {})
                    registry["metadata"] = data.get("metadata", {})

                # Load presets
                if self.presets_file.exists():
                    with open(self.presets_file, encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                        registry["presets"] = data.get("presets", {})

                # Load judges from judges/ directory
                if self.judges_registry_dir.exists():
                    for judge_file in sorted(self.judges_registry_dir.glob("*.yml")):
                        with open(judge_file, encoding="utf-8") as f:
                            data = yaml.safe_load(f) or {}
                            if "judge" in data:
                                judge_data = data["judge"]
                                judge_name = judge_data.get("name", judge_file.stem)
                                # Store without the outer "judge" wrapper
                                registry["judges"][judge_name] = {k: v for k, v in judge_data.items() if k != "name"}

                logger.info(f"Loaded registry from split files: {self.criteria_dir}")

            # Fall back to legacy monolithic registry.yml
            elif self.registry_file.exists():
                with open(self.registry_file, encoding="utf-8") as f:
                    self._registry_cache = yaml.safe_load(f)
                logger.info(f"Loaded registry from legacy file: {self.registry_file}")
                return self._registry_cache

            else:
                raise FileNotFoundError(
                    f"No registry files found. Expected {self.criteria_file} or {self.registry_file}"
                )

            self._registry_cache = registry

            criteria_count = len(self._registry_cache.get("criteria", {}))
            judges_count = len(self._registry_cache.get("judges", {}))
            presets_count = len(self._registry_cache.get("presets", {}))
            logger.info(f"Loaded registry: {criteria_count} criteria, {judges_count} judges, {presets_count} presets")

        return self._registry_cache

    # -------------------------------------------------------------------------
    # Criteria (Abstract Definitions)
    # -------------------------------------------------------------------------

    def get_criteria(self, criteria_id: str) -> CriteriaConfig:
        """Get a single criteria definition by ID."""
        if criteria_id in self._criteria_cache:
            return self._criteria_cache[criteria_id]

        registry = self.load_registry()
        criteria_data = registry.get("criteria", {})

        if criteria_id not in criteria_data:
            raise ValueError(f"Criteria not found: {criteria_id}")

        meta = criteria_data[criteria_id]
        config = CriteriaConfig(
            id=criteria_id,
            category=meta["category"],
            subcategory=meta["subcategory"],
            name=meta["name"],
            description=meta["description"],
            tags=meta.get("tags", []),
        )

        self._criteria_cache[criteria_id] = config
        return config

    def list_criteria(self) -> list[CriteriaConfig]:
        """List all criteria definitions."""
        registry = self.load_registry()
        criteria_ids = list(registry.get("criteria", {}).keys())
        return [self.get_criteria(cid) for cid in sorted(criteria_ids)]

    def get_criteria_by_category(self, category: str) -> list[CriteriaConfig]:
        """Get all criteria in a category."""
        return [c for c in self.list_criteria() if c.category == category]

    def get_criteria_by_subcategory(self, category: str, subcategory: str) -> list[CriteriaConfig]:
        """Get all criteria in a subcategory."""
        return [c for c in self.list_criteria() if c.category == category and c.subcategory == subcategory]

    def get_available_categories(self) -> list[str]:
        """Get list of unique categories."""
        return sorted(set(c.category for c in self.list_criteria()))

    def get_available_subcategories(self, category: str) -> list[str]:
        """Get list of subcategories within a category."""
        return sorted(set(c.subcategory for c in self.list_criteria() if c.category == category))

    # -------------------------------------------------------------------------
    # Judges (Implementations with Inheritance)
    # -------------------------------------------------------------------------

    def get_judge(self, judge_name: str) -> JudgeConfig:
        """Get a judge configuration with inheritance resolved."""
        if judge_name in self._judge_cache:
            return self._judge_cache[judge_name]

        registry = self.load_registry()
        judges_data = registry.get("judges", {})

        if judge_name not in judges_data:
            raise ValueError(f"Judge not found: {judge_name}")

        judge_config = self._resolve_judge_inheritance(judge_name, judges_data)
        self._judge_cache[judge_name] = judge_config
        return judge_config

    def _resolve_judge_inheritance(self, judge_name: str, judges_data: dict, visited: set | None = None) -> JudgeConfig:
        """Resolve judge inheritance chain."""
        if visited is None:
            visited = set()

        if judge_name in visited:
            raise ValueError(f"Circular inheritance detected for judge: {judge_name}")
        visited.add(judge_name)

        judge_def = judges_data[judge_name]
        inherits_from = judge_def.get("inherits_from")

        # Start with empty or inherited values
        if inherits_from:
            parent = self._resolve_judge_inheritance(inherits_from, judges_data, visited)
            weights = deepcopy(parent.weights)
            implementations = deepcopy(parent.implementations)
        else:
            weights = {"categories": {}, "subcategories": {}, "criteria": {}}
            implementations = {}

        # Override with this judge's weights
        if "weights" in judge_def:
            for level in ["categories", "subcategories", "criteria"]:
                if level in judge_def["weights"]:
                    weights[level].update(judge_def["weights"][level])

        # Override with this judge's implementations
        if "implementations" in judge_def:
            for criteria_id, impl_data in judge_def["implementations"].items():
                implementations[criteria_id] = JudgeImplementation(
                    file=impl_data["file"],
                    version=impl_data.get("version", "1.0"),
                    created=impl_data.get("created", ""),
                    author=impl_data.get("author", ""),
                )

        return JudgeConfig(
            name=judge_name,
            description=judge_def.get("description", ""),
            inherits_from=inherits_from,
            weights=weights,
            implementations=implementations,
        )

    def list_judges(self) -> list[str]:
        """List available judge names."""
        registry = self.load_registry()
        return sorted(registry.get("judges", {}).keys())

    def get_judge_prompt(self, judge_name: str, criteria_id: str) -> dict[str, Any]:
        """Get the prompt content for a criteria from a judge."""
        judge = self.get_judge(judge_name)

        if criteria_id not in judge.implementations:
            raise ValueError(f"Judge '{judge_name}' has no implementation for criteria '{criteria_id}'")

        impl = judge.implementations[criteria_id]

        # Load prompt content if not cached
        if impl.prompt_content is None:
            prompt_file = self.data_dir / impl.file
            if not prompt_file.exists():
                raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

            cache_key = str(prompt_file)
            if cache_key not in self._prompt_cache:
                with open(prompt_file, encoding="utf-8") as f:
                    self._prompt_cache[cache_key] = yaml.safe_load(f)

            impl.prompt_content = self._prompt_cache[cache_key]

        return impl.prompt_content

    def get_judge_weights(self, judge_name: str) -> dict[str, dict[str, float]]:
        """Get weights for a judge (with inheritance resolved)."""
        judge = self.get_judge(judge_name)
        return judge.weights

    def get_weight(self, judge_name: str, level: str, key: str, default: float = 1.0) -> float:
        """Get a specific weight value, defaulting to 1.0 if not set."""
        weights = self.get_judge_weights(judge_name)
        return weights.get(level, {}).get(key, default)

    # -------------------------------------------------------------------------
    # Evaluator Support (load criteria with prompt content)
    # -------------------------------------------------------------------------

    def load_criterion(self, criteria_id: str, judge_name: str = "default") -> CriteriaConfig:
        """Load a criterion with its prompt content for evaluation.

        This combines the abstract criteria definition with the judge's
        prompt implementation.
        """
        criteria = self.get_criteria(criteria_id)
        prompt_content = self.get_judge_prompt(judge_name, criteria_id)

        return CriteriaConfig(
            id=criteria.id,
            category=criteria.category,
            subcategory=criteria.subcategory,
            name=criteria.name,
            description=criteria.description,
            tags=criteria.tags,
            prompt_content=prompt_content,
        )

    def load_multiple_criteria(self, criteria_ids: list[str], judge_name: str = "default") -> list[CriteriaConfig]:
        """Load multiple criteria with prompt content."""
        loaded = []
        for cid in criteria_ids:
            try:
                loaded.append(self.load_criterion(cid, judge_name))
            except Exception as e:
                logger.error(f"Failed to load criterion {cid}: {e}")
        return loaded

    # -------------------------------------------------------------------------
    # Presets (Criteria Selections)
    # -------------------------------------------------------------------------

    def get_preset(self, preset_name: str) -> list[str]:
        """Get list of criteria IDs in a preset."""
        registry = self.load_registry()
        presets = registry.get("presets", {})

        if preset_name not in presets:
            raise ValueError(f"Preset not found: {preset_name}")

        return presets[preset_name].get("criteria", [])

    def list_presets(self) -> dict[str, str]:
        """List presets with their descriptions."""
        registry = self.load_registry()
        return {name: preset.get("description", "") for name, preset in registry.get("presets", {}).items()}

    # -------------------------------------------------------------------------
    # Resolution (Criteria Selection)
    # -------------------------------------------------------------------------

    def resolve_criteria_selection(self, selection: str) -> list[str]:
        """
        Resolve a criteria selection pattern to list of criteria IDs.

        Supports:
        - Preset names: "basic_safety"
        - Categories: "safety" (all safety.*)
        - Subcategories: "safety.sexual" (all safety.sexual.*)
        - Exact criteria: "safety.sexual.sexual_content"
        - Comma-separated: "safety,anthropomorphism"
        - Wildcard: "*" (all criteria)
        """
        registry = self.load_registry()
        criteria_data = registry.get("criteria", {})
        presets = registry.get("presets", {})

        # Handle wildcard
        if selection == "*":
            return sorted(criteria_data.keys())

        # Handle presets
        if selection in presets:
            return presets[selection].get("criteria", [])

        # Handle comma-separated
        if "," in selection:
            all_criteria = []
            for part in selection.split(","):
                all_criteria.extend(self.resolve_criteria_selection(part.strip()))
            return sorted(set(all_criteria))

        # Pattern matching against criteria IDs
        matching = []
        for criteria_id in criteria_data.keys():
            # Exact match
            if criteria_id == selection:
                matching.append(criteria_id)
            # Prefix match (category or subcategory)
            elif criteria_id.startswith(selection + "."):
                matching.append(criteria_id)

        return sorted(matching)


# =============================================================================
# Global Instance
# =============================================================================

_global_loader: RegistryLoader | None = None


def get_registry_loader() -> RegistryLoader:
    """Get the global registry loader instance."""
    global _global_loader
    if _global_loader is None:
        _global_loader = RegistryLoader()
    return _global_loader
