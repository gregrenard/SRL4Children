"""
Configuration Manager for ChildGuard-LLM
========================================
Module pour charger et gérer la configuration centralisée depuis config.yml
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field


@dataclass
class OllamaConfig:
    """Configuration Ollama"""
    host: str
    port: int
    description: str = ""


@dataclass 
class ModelConfig:
    """Configuration d'un modèle"""
    provider: str
    model: str
    enabled: bool
    description: str = ""
    options: dict = field(default_factory=dict)


@dataclass
class JudgeConfig:
    """Configuration du système de jugement"""
    n_passes: int
    max_retries: int
    temperatures: Dict[str, float]
    scoring_weights: Dict[str, float]
    fail_closed: Dict[str, Any]
    judge_models: Dict[str, str]


@dataclass
class ExecutionConfig:
    """Configuration d'exécution"""
    smart_resume: Dict[str, Any]
    auto_postprocess: Dict[str, Any]
    parallel_execution: bool
    batch_size: int
    sleep_between_requests: float


class ConfigManager:
    """Gestionnaire de configuration centralisé"""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialise le gestionnaire de configuration
        
        Args:
            config_path: Chemin vers le fichier config.yml (par défaut: config.yml à la racine)
        """
        if config_path is None:
            # Chercher config.yml à la racine du projet
            current_dir = Path(__file__).parent
            while current_dir != current_dir.parent:  # Remonter jusqu'à la racine
                config_file = current_dir / "config.yml"
                if config_file.exists():
                    config_path = config_file
                    break
                current_dir = current_dir.parent
            else:
                raise FileNotFoundError("config.yml not found in project root")
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._resolve_environment_variables()
        # Runtime state pour la session courante
        self._selected_ollama_preset = "default"
    
    def _load_config(self) -> Dict[str, Any]:
        """Charge la configuration depuis le fichier YAML"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load config: {e}")
    
    def _resolve_environment_variables(self):
        """Résout les variables d'environnement dans la configuration"""
        def resolve_value(value):
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]  # Enlever ${ et }
                return os.environ.get(env_var, "")
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(v) for v in value]
            return value
        
        self.config = resolve_value(self.config)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration via un chemin à points
        
        Args:
            key_path: Chemin vers la valeur (ex: "judge.n_passes")
            default: Valeur par défaut si non trouvée
        
        Returns:
            La valeur de configuration
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_project_info(self) -> Dict[str, str]:
        """Retourne les informations du projet"""
        return self.config.get("project", {})
    
    def get_paths(self) -> Dict[str, Any]:
        """Retourne la configuration des chemins"""
        return self.config.get("paths", {})
    
    def get_enabled_models(self) -> List[ModelConfig]:
        """Retourne la liste des modèles activés"""
        models_config = self.config.get("models", [])
        # Handle both list (V1.1) and dict (old V1) structures
        if isinstance(models_config, dict):
            # Old V1 structure with nested test_models
            models_config = models_config.get("test_models", [])
        elif isinstance(models_config, list):
            # New V1.1 structure with direct list
            pass
        else:
            models_config = []
            
        return [
            ModelConfig(
                provider=m["provider"],
                model=m["model"],
                enabled=m["enabled"],
                description=m.get("description", ""),
                options=m.get("options", {})
            )
            for m in models_config
            if m.get("enabled", False)
        ]
    
    def get_all_models(self) -> List[ModelConfig]:
        """Retourne tous les modèles (activés et désactivés)"""
        models_config = self.config.get("models", [])
        # Handle both list (V1.1) and dict (old V1) structures
        if isinstance(models_config, dict):
            # Old V1 structure with nested test_models
            models_config = models_config.get("test_models", [])
        elif isinstance(models_config, list):
            # New V1.1 structure with direct list
            pass
        else:
            models_config = []
        return [
            ModelConfig(
                provider=m["provider"],
                model=m["model"],
                enabled=m["enabled"],
                description=m.get("description", ""),
                options=m.get("options", {})
            )
            for m in models_config
        ]
    
    def get_judge_config(self) -> JudgeConfig:
        """Retourne la configuration du juge"""
        judge_config = self.config.get("judge", {})
        models_config = self.config.get("models", {}).get("judge_models", {})
        
        return JudgeConfig(
            n_passes=judge_config.get("n_passes", 3),
            max_retries=judge_config.get("max_retries", 3),
            temperatures=judge_config.get("temperatures", {}),
            scoring_weights=judge_config.get("scoring_weights", {}),
            fail_closed=judge_config.get("fail_closed", {}),
            judge_models=models_config
        )
    
    def get_ollama_config(self, preset: str = "default") -> OllamaConfig:
        """
        Retourne la configuration Ollama
        
        Args:
            preset: Preset à utiliser ("default", "local", "ssh_tunnel", "custom")
        """
        ollama_config = self.config.get("ollama", {})
        
        if preset == "default":
            config = ollama_config.get("default", {})
        else:
            config = ollama_config.get("presets", {}).get(preset, ollama_config.get("default", {}))
        
        return OllamaConfig(
            host=config.get("host", "localhost"),
            port=config.get("port", 11434),
            description=config.get("description", "")
        )
    
    def get_ollama_presets(self) -> Dict[str, OllamaConfig]:
        """Retourne tous les presets Ollama disponibles"""
        presets = {}
        ollama_config = self.config.get("ollama", {})
        
        # Ajouter default
        default_config = ollama_config.get("default", {})
        presets["default"] = OllamaConfig(
            host=default_config.get("host", "localhost"),
            port=default_config.get("port", 11434),
            description="Configuration par défaut"
        )
        
        # Ajouter presets définis
        preset_configs = ollama_config.get("presets", {})
        for name, config in preset_configs.items():
            presets[name] = OllamaConfig(
                host=config.get("host", "localhost"),
                port=config.get("port", 11434),
                description=config.get("description", "")
            )
        
        return presets
    
    def set_selected_ollama_preset(self, preset_name: str) -> None:
        """Définit le preset Ollama sélectionné pour cette session"""
        self._selected_ollama_preset = preset_name
    
    def get_selected_ollama_preset(self) -> str:
        """Retourne le preset Ollama actuellement sélectionné"""
        return self._selected_ollama_preset
    
    def get_selected_ollama_config(self) -> OllamaConfig:
        """Retourne la config Ollama du preset actuellement sélectionné"""
        return self.get_ollama_config(self._selected_ollama_preset)
    
    def get_test_modes(self) -> Dict[str, Dict[str, Any]]:
        """Retourne la configuration des modes de test"""
        return self.config.get("test_modes", {})
    
    def get_enabled_test_modes(self) -> Dict[str, Dict[str, Any]]:
        """Retourne uniquement les modes de test activés"""
        test_modes = self.get_test_modes()
        return {
            name: config for name, config in test_modes.items()
            if config.get("enabled", False)
        }
    
    def get_execution_config(self) -> ExecutionConfig:
        """Retourne la configuration d'exécution"""
        exec_config = self.config.get("execution", {})
        
        return ExecutionConfig(
            smart_resume=exec_config.get("smart_resume", {}),
            auto_postprocess=exec_config.get("auto_postprocess", {}),
            parallel_execution=exec_config.get("parallel_execution", False),
            batch_size=exec_config.get("batch_size", 1),
            sleep_between_requests=exec_config.get("sleep_between_requests", 0.01)
        )
    
    def get_api_keys(self) -> Dict[str, str]:
        """Retourne la configuration des clés API (déjà résolues)"""
        return self.config.get("api_keys", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Retourne la configuration de logging"""
        return self.config.get("logging", {})
    
    def get_output_config(self) -> Dict[str, Any]:
        """Retourne la configuration des sorties"""
        return self.config.get("output", {})
    
    def get_validation_config(self) -> Dict[str, Any]:
        """Retourne la configuration de validation"""
        return self.config.get("validation", {})
    
    def is_debug_enabled(self) -> bool:
        """Vérifie si le mode debug est activé"""
        return self.config.get("development", {}).get("debug", {}).get("enabled", False)
    
    def is_quick_test_enabled(self) -> bool:
        """Vérifie si le mode test rapide est activé"""
        return self.config.get("development", {}).get("quick_test", {}).get("enabled", False)
    
    def get_quick_test_config(self) -> Dict[str, Any]:
        """Retourne la configuration du test rapide"""
        return self.config.get("development", {}).get("quick_test", {})
    
    def update_ollama_preset(self, preset: str, host: str, port: int, description: str = "") -> None:
        """
        Met à jour un preset Ollama (utile pour la configuration custom)
        
        Args:
            preset: Nom du preset à mettre à jour
            host: Nouveau host
            port: Nouveau port  
            description: Nouvelle description
        """
        if "ollama" not in self.config:
            self.config["ollama"] = {}
        if "presets" not in self.config["ollama"]:
            self.config["ollama"]["presets"] = {}
        
        self.config["ollama"]["presets"][preset] = {
            "host": host,
            "port": port,
            "description": description
        }
    
    def save_config(self) -> None:
        """Sauvegarde la configuration modifiée dans le fichier"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True, indent=2)
        except Exception as e:
            raise RuntimeError(f"Failed to save config: {e}")


# Instance globale du gestionnaire de configuration
_config_manager = None


def get_config() -> ConfigManager:
    """
    Retourne l'instance globale du gestionnaire de configuration
    Initialise automatiquement si nécessaire
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def reload_config(config_path: Optional[Union[str, Path]] = None) -> ConfigManager:
    """
    Recharge la configuration depuis le fichier
    Utile pour les modifications en cours d'exécution
    """
    global _config_manager
    _config_manager = ConfigManager(config_path)
    return _config_manager


# Fonctions utilitaires pour accès rapide
def get_enabled_models() -> List[ModelConfig]:
    """Accès rapide aux modèles activés"""
    return get_config().get_enabled_models()


def get_judge_config() -> JudgeConfig:
    """Accès rapide à la config du juge"""
    return get_config().get_judge_config()


def get_ollama_config(preset: str = "default") -> OllamaConfig:
    """Accès rapide à la config Ollama"""
    return get_config().get_ollama_config(preset)
