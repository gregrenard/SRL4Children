"""
Criteria loader for SRL4C
Ported from Greg's original src/core/criteria_loader.py
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from srl4c.paths import CRITERIA_DIR, REGISTRY_FILE

logger = logging.getLogger(__name__)


@dataclass
class CriterionConfig:
    """Configuration of an individual criterion"""

    id: str  # e.g. "safety.sexual.sexual_content__v1_0"
    category: str  # e.g. "safety"
    subcategory: str  # e.g. "sexual"
    name: str  # e.g. "sexual_content"
    version: str  # e.g. "1.0"
    description: str
    file: str  # Relative path from criteria/
    created: str
    author: str
    tags: list[str]
    changelog: str | None = None
    prompt_content: dict[str, Any] | None = None


class CriteriaLoader:
    """Criteria loader for SRL4C evaluation"""

    def __init__(self, criteria_path: Path | None = None, registry_file: Path | None = None):
        self.criteria_path = Path(criteria_path) if criteria_path else CRITERIA_DIR
        self.registry_file = Path(registry_file) if registry_file else REGISTRY_FILE

        self._registry_cache: dict | None = None
        self._criteria_cache: dict[str, CriterionConfig] = {}

        logger.info(f"CriteriaLoader initialized: {self.criteria_path}")

    def load_registry(self, force_reload: bool = False) -> dict[str, Any]:
        """Load criteria registry from YAML file"""
        if self._registry_cache is None or force_reload:
            if not self.registry_file.exists():
                raise FileNotFoundError(f"Registry file not found: {self.registry_file}")

            with open(self.registry_file, encoding="utf-8") as f:
                self._registry_cache = yaml.safe_load(f)
            logger.info(f"Loaded registry with {len(self._registry_cache.get('criteria', {}))} criteria")

        return self._registry_cache

    def load_criterion(self, criterion_id: str) -> CriterionConfig:
        """Load a specific criterion by ID"""
        if criterion_id in self._criteria_cache:
            return self._criteria_cache[criterion_id]

        registry = self.load_registry()
        criteria_data = registry.get("criteria", {})

        if criterion_id not in criteria_data:
            raise ValueError(f"Criterion not found in registry: {criterion_id}")

        meta = criteria_data[criterion_id]

        config = CriterionConfig(
            id=criterion_id,
            category=meta["category"],
            subcategory=meta["subcategory"],
            name=meta["name"],
            version=meta["version"],
            description=meta["description"],
            file=meta["file"],
            created=meta["created"],
            author=meta["author"],
            tags=meta["tags"],
            changelog=meta.get("changelog"),
        )

        # Load prompt content
        prompt_file = self.criteria_path / meta["file"]
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

        with open(prompt_file, encoding="utf-8") as f:
            config.prompt_content = yaml.safe_load(f)

        self._criteria_cache[criterion_id] = config
        return config

    def resolve_criteria_selection(self, selection: str) -> list[str]:
        """Resolve criteria selection pattern to list of criterion IDs"""
        registry = self.load_registry()
        criteria_data = registry.get("criteria", {})
        presets = registry.get("presets", {})

        # Handle presets
        if selection in presets:
            return presets[selection]["criteria"]

        # Handle comma-separated
        if "," in selection:
            all_criteria = []
            for part in selection.split(","):
                all_criteria.extend(self.resolve_criteria_selection(part.strip()))
            return list(set(all_criteria))

        # Pattern matching
        matching = []
        for criterion_id in criteria_data.keys():
            base_id = criterion_id.split("__")[0]
            if base_id == selection or base_id.startswith(selection + "."):
                matching.append(criterion_id)

        return sorted(matching)

    def load_multiple_criteria(self, criterion_ids: list[str]) -> list[CriterionConfig]:
        """Load multiple criteria"""
        loaded = []
        for cid in criterion_ids:
            try:
                loaded.append(self.load_criterion(cid))
            except Exception as e:
                logger.error(f"Failed to load criterion {cid}: {e}")
        return loaded

    def get_available_categories(self) -> list[str]:
        """Get list of available categories"""
        registry = self.load_registry()
        categories = set()
        for criterion_id in registry.get("criteria", {}).keys():
            categories.add(criterion_id.split(".")[0])
        return sorted(categories)

    def get_available_presets(self) -> dict[str, str]:
        """Get available presets with descriptions"""
        registry = self.load_registry()
        return {name: preset["description"] for name, preset in registry.get("presets", {}).items()}


# Global instance
_global_loader: CriteriaLoader | None = None


def get_criteria_loader() -> CriteriaLoader:
    """Get global criteria loader instance"""
    global _global_loader
    if _global_loader is None:
        _global_loader = CriteriaLoader()
    return _global_loader
