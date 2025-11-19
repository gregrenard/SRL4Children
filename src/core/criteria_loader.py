"""
Safety Readiness Level for Children - LLM-based Evaluation
Translating Design Principles into Automated guardrails and replay alignement for child safety.
Author: Gregory Renard (with GenAI: Claude, Gemini, Codex)
Organization: Everyone.AI | Year: 2025
For the well-being and safety of our children
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

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
    file: str  # Relative path from assets/criteria/
    created: str
    author: str
    tags: List[str]
    changelog: Optional[str] = None

    # Loaded prompt content
    prompt_content: Optional[Dict[str, Any]] = None

class CriteriaLoader:
    """Modular criteria loader for V1.1"""

    def __init__(self, assets_path: Optional[Path] = None):
        """
        Initialize criteria loader

        Args:
            assets_path: Path to assets directory. If None, auto-detect from project structure.
        """
        if assets_path is None:
            # Auto-detect assets path
            current_dir = Path(__file__).parent
            while current_dir != current_dir.parent:
                assets_dir = current_dir / "assets"
                if assets_dir.exists():
                    assets_path = assets_dir
                    break
                current_dir = current_dir.parent

            if assets_path is None:
                raise FileNotFoundError("assets/ directory not found in project")

        self.assets_path = Path(assets_path)
        self.criteria_path = self.assets_path / "criteria"
        self.registry_file = self.assets_path / "criteria_registry.yml"

        # Cache for loaded registry and criteria
        self._registry_cache: Optional[Dict] = None
        self._criteria_cache: Dict[str, CriterionConfig] = {}

        logger.info(f"CriteriaLoader initialized with assets path: {self.assets_path}")

    def load_registry(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load criteria registry from YAML file

        Args:
            force_reload: Force reload from disk even if cached

        Returns:
            Registry dictionary with criteria metadata
        """
        if self._registry_cache is None or force_reload:
            if not self.registry_file.exists():
                raise FileNotFoundError(f"Registry file not found: {self.registry_file}")

            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    self._registry_cache = yaml.safe_load(f)
                logger.info(f"Loaded registry with {len(self._registry_cache.get('criteria', {}))} criteria")
            except Exception as e:
                logger.error(f"Failed to load criteria registry: {e}")
                raise

        return self._registry_cache

    def load_criterion(self, criterion_id: str) -> CriterionConfig:
        """
        Load a specific criterion by ID

        Args:
            criterion_id: Full criterion ID (e.g. "safety.sexual.sexual_content__v1_0")

        Returns:
            CriterionConfig with loaded prompt content
        """
        # Check cache first
        if criterion_id in self._criteria_cache:
            return self._criteria_cache[criterion_id]

        # Load from registry
        registry = self.load_registry()
        criteria_data = registry.get("criteria", {})

        if criterion_id not in criteria_data:
            raise ValueError(f"Criterion not found in registry: {criterion_id}")

        criterion_meta = criteria_data[criterion_id]

        # Create config object
        config = CriterionConfig(
            id=criterion_id,
            category=criterion_meta["category"],
            subcategory=criterion_meta["subcategory"],
            name=criterion_meta["name"],
            version=criterion_meta["version"],
            description=criterion_meta["description"],
            file=criterion_meta["file"],
            created=criterion_meta["created"],
            author=criterion_meta["author"],
            tags=criterion_meta["tags"],
            changelog=criterion_meta.get("changelog")
        )

        # Load prompt content
        prompt_file = self.criteria_path / criterion_meta["file"]
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_content = yaml.safe_load(f)
            config.prompt_content = prompt_content
            logger.debug(f"Loaded criterion: {criterion_id}")
        except Exception as e:
            logger.error(f"Failed to load prompt file {prompt_file}: {e}")
            raise

        # Cache and return
        self._criteria_cache[criterion_id] = config
        return config

    def resolve_criteria_selection(self, selection: str) -> List[str]:
        """
        Resolve criteria selection pattern to list of criterion IDs

        Args:
            selection: Selection pattern. Supports:
                - "safety" -> all safety criteria
                - "safety.sexual" -> all safety.sexual criteria
                - "safety.sexual.sexual_content" -> specific criterion
                - "safety.sexual,age.readability" -> mixed selection
                - "full_evaluation" -> preset from registry

        Returns:
            List of criterion IDs matching the selection
        """
        registry = self.load_registry()
        criteria_data = registry.get("criteria", {})
        presets = registry.get("presets", {})

        # Handle presets first
        if selection in presets:
            return presets[selection]["criteria"]

        # Handle comma-separated mixed selection
        if "," in selection:
            all_criteria = []
            for part in selection.split(","):
                part = part.strip()
                all_criteria.extend(self.resolve_criteria_selection(part))
            return list(set(all_criteria))  # Remove duplicates

        # Handle pattern matching
        matching_criteria = []

        for criterion_id in criteria_data.keys():
            if self._matches_pattern(criterion_id, selection):
                matching_criteria.append(criterion_id)

        if not matching_criteria:
            logger.warning(f"No criteria found matching pattern: {selection}")
        else:
            logger.info(f"Selection '{selection}' resolved to {len(matching_criteria)} criteria")

        return sorted(matching_criteria)

    def _matches_pattern(self, criterion_id: str, pattern: str) -> bool:
        """
        Check if criterion ID matches selection pattern

        Args:
            criterion_id: Full criterion ID (e.g. "safety.sexual.sexual_content__v1_0")
            pattern: Selection pattern (e.g. "safety", "safety.sexual", "safety.sexual.sexual_content")

        Returns:
            True if criterion matches pattern
        """
        # Remove version suffix for matching
        base_id = criterion_id.split("__")[0]  # "safety.sexual.sexual_content"

        # Exact match
        if base_id == pattern:
            return True

        # Category match (e.g. "safety" matches "safety.sexual.sexual_content")
        if base_id.startswith(pattern + "."):
            return True

        return False

    def get_available_categories(self) -> List[str]:
        """Get list of available categories"""
        registry = self.load_registry()
        criteria_data = registry.get("criteria", {})

        categories = set()
        for criterion_id in criteria_data.keys():
            category = criterion_id.split(".")[0]
            categories.add(category)

        return sorted(list(categories))

    def get_available_subcategories(self, category: str) -> List[str]:
        """Get list of available subcategories for a category"""
        registry = self.load_registry()
        criteria_data = registry.get("criteria", {})

        subcategories = set()
        for criterion_id in criteria_data.keys():
            parts = criterion_id.split(".")
            if len(parts) >= 2 and parts[0] == category:
                subcategories.add(parts[1])

        return sorted(list(subcategories))

    def get_available_presets(self) -> Dict[str, str]:
        """Get available presets with descriptions"""
        registry = self.load_registry()
        presets = registry.get("presets", {})

        return {
            name: preset_config["description"]
            for name, preset_config in presets.items()
        }

    def load_multiple_criteria(self, criterion_ids: List[str]) -> List[CriterionConfig]:
        """
        Load multiple criteria efficiently

        Args:
            criterion_ids: List of criterion IDs to load

        Returns:
            List of loaded CriterionConfig objects
        """
        loaded_criteria = []

        for criterion_id in criterion_ids:
            try:
                config = self.load_criterion(criterion_id)
                loaded_criteria.append(config)
            except Exception as e:
                logger.error(f"Failed to load criterion {criterion_id}: {e}")
                # Continue loading other criteria

        logger.info(f"Successfully loaded {len(loaded_criteria)}/{len(criterion_ids)} criteria")
        return loaded_criteria

    def validate_prompt_content(self, config: CriterionConfig) -> bool:
        """
        Validate that prompt content has required fields

        Args:
            config: CriterionConfig to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["role", "task", "age_context", "scoring_guide", "output_format"]

        if config.prompt_content is None:
            logger.error(f"No prompt content loaded for {config.id}")
            return False

        for field in required_fields:
            if field not in config.prompt_content:
                logger.error(f"Missing required field '{field}' in {config.id}")
                return False

        return True

# Global instance for easy access
_global_loader: Optional[CriteriaLoader] = None

def get_criteria_loader() -> CriteriaLoader:
    """Get global criteria loader instance"""
    global _global_loader
    if _global_loader is None:
        _global_loader = CriteriaLoader()
    return _global_loader
