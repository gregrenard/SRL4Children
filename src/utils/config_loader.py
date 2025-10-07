"""
ChildGuard-LLM V1.1 - Configuration Loader
Version: 1.1.0
Date: 23 août 2025

Handles loading and validation of YAML configuration files with environment variable substitution.
"""

import os
import logging
import re
from typing import Dict, Any, Optional, List
import yaml
from pathlib import Path


class ConfigLoader:
    """
    Configuration Loader with validation and environment variable substitution
    
    Features:
    - YAML file loading with validation
    - Environment variable substitution (${VAR_NAME} format)
    - Schema validation for required fields
    - Default value handling
    - Configuration merging capabilities
    """
    
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        
    def load(self) -> Dict[str, Any]:
        """
        Load and validate configuration from YAML file
        
        Returns:
            Loaded and validated configuration dictionary
        """
        try:
            # Load raw YAML
            raw_config = self._load_yaml_file(self.config_file)
            
            # Substitute environment variables
            config = self._substitute_environment_variables(raw_config)
            
            # Validate configuration
            self._validate_configuration(config)
            
            # Apply defaults
            config = self._apply_defaults(config)
            
            self.logger.info(f"Configuration loaded successfully from {self.config_file}")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Configuration loading failed: {e}")
            
    def _load_yaml_file(self, file_path: str) -> Dict[str, Any]:
        """Load YAML file with error handling"""
        config_path = Path(file_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            if config is None:
                raise ValueError("Configuration file is empty")
                
            return config
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax: {e}")
            
    def _substitute_environment_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively substitute environment variables in configuration
        
        Supports ${VAR_NAME} and ${VAR_NAME:default_value} syntax
        """
        if isinstance(config, dict):
            return {k: self._substitute_environment_variables(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._substitute_environment_variables(item) for item in config]
        elif isinstance(config, str):
            return self._substitute_string_variables(config)
        else:
            return config
            
    def _substitute_string_variables(self, value: str) -> str:
        """Substitute environment variables in a string value"""
        # Pattern matches ${VAR_NAME} or ${VAR_NAME:default}
        pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
        
        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ""
            
            env_value = os.getenv(var_name)
            
            if env_value is not None:
                return env_value
            elif default_value:
                return default_value
            else:
                self.logger.warning(f"Environment variable '{var_name}' not found, using empty string")
                return ""
                
        return re.sub(pattern, replace_var, value)
        
    def _validate_configuration(self, config: Dict[str, Any]) -> None:
        """Validate configuration structure and required fields"""
        required_sections = [
            'system',
            'judge_system', 
            'providers',
            'criteria',
            'weights',
            'execution'
        ]
        
        # Check required top-level sections
        missing_sections = []
        for section in required_sections:
            if section not in config:
                missing_sections.append(section)
                
        if missing_sections:
            raise ValueError(f"Missing required configuration sections: {missing_sections}")
            
        # Validate judge system configuration
        self._validate_judge_system(config['judge_system'])
        
        # Validate weighting system
        self._validate_weights(config['weights'])
        
        # Validate providers
        self._validate_providers(config['providers'])
        
    def _validate_judge_system(self, judge_config: Dict[str, Any]) -> None:
        """Validate judge system configuration"""
        if 'judges' not in judge_config:
            raise ValueError("judge_system.judges is required")
            
        judges = judge_config['judges']
        if not judges or len(judges) == 0:
            raise ValueError("At least one judge must be configured")
            
        # Validate evaluation configuration
        if 'evaluation' in judge_config:
            eval_config = judge_config['evaluation']
            
            n_passes = eval_config.get('n_passes', 3)
            if n_passes < 1:
                raise ValueError("n_passes must be at least 1")
                
            # Validate hyperparameters
            hyperparams = eval_config.get('hyperparameters', {})
            for i in range(1, n_passes + 1):
                pass_key = f"pass_{i}"
                if pass_key not in hyperparams:
                    self.logger.warning(f"Missing hyperparameters for {pass_key}, will use defaults")
                    
    def _validate_weights(self, weights_config: Dict[str, Any]) -> None:
        """Validate weights configuration"""
        if 'categories' not in weights_config:
            raise ValueError("weights.categories is required")
            
        category_weights = weights_config['categories']
        
        # Check that weights sum to approximately 1.0
        total_weight = sum(category_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            self.logger.warning(f"Category weights sum to {total_weight:.3f}, expected 1.0")
            
        # Validate subcategory weights if present
        if 'subcategories' in weights_config:
            for category, subcats in weights_config['subcategories'].items():
                subcat_sum = sum(subcats.values())
                if abs(subcat_sum - 1.0) > 0.01:
                    self.logger.warning(f"Subcategory weights for '{category}' sum to {subcat_sum:.3f}")
                    
    def _validate_providers(self, providers_config: Dict[str, Any]) -> None:
        """Validate provider configurations"""
        supported_providers = ['ollama', 'openai', 'anthropic']
        
        for provider in providers_config.keys():
            if provider not in supported_providers:
                self.logger.warning(f"Unknown provider: {provider}")
                
        # Validate specific provider configurations
        if 'ollama' in providers_config:
            ollama_config = providers_config['ollama']
            if 'base_url' not in ollama_config:
                raise ValueError("ollama.base_url is required")
                
    def _apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values for missing optional configuration"""
        defaults = {
            'execution': {
                'parallel': {'enabled': True, 'max_workers': 4},
                'cache': {'enabled': True, 'ttl_hours': 24},
                'timeout': {'per_criterion_seconds': 300, 'total_benchmark_seconds': 7200}
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/childguard_v1_1.log',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'validation': {
                'max_criteria_per_benchmark': 50,
                'max_judges_simultaneous': 10,
                'max_passes_per_judge': 10,
                'required_columns': ["id", "prompt", "category", "subcategory", "maturity"],
                'max_prompt_length': 1000,
                'max_response_length': 10000
            },
            'output': {
                'base_directory': 'outputs',
                'format': 'json',
                'structure': {
                    'individual_records': True,
                    'aggregate_summary': True,
                    'detailed_tracing': True
                }
            }
        }
        
        # Deep merge defaults
        config = self._deep_merge(defaults, config)
        return config
        
    def _deep_merge(self, default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override taking precedence"""
        result = default.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result
        
    def validate_runtime_config(self, 
                               models: List[str], 
                               criteria: Optional[str] = None,
                               n_passes: Optional[int] = None) -> None:
        """
        Validate runtime configuration parameters
        
        Args:
            models: List of models to validate
            criteria: Criteria selection to validate
            n_passes: Number of passes to validate
        """
        # Validate models format
        for model in models:
            if not model or not isinstance(model, str):
                raise ValueError(f"Invalid model specification: {model}")
                
        # Validate n_passes
        if n_passes is not None:
            if n_passes < 1 or n_passes > 10:
                raise ValueError(f"n_passes must be between 1 and 10, got {n_passes}")
                
        # Validate criteria format (basic validation)
        if criteria:
            # Check for invalid characters or patterns
            if not re.match(r'^[a-zA-Z0-9._,]+$', criteria):
                raise ValueError(f"Invalid characters in criteria selection: {criteria}")
                
    def get_config_summary(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of the loaded configuration
        
        Args:
            config: Loaded configuration
            
        Returns:
            Configuration summary
        """
        return {
            'system_version': config.get('system', {}).get('version', 'unknown'),
            'judges_configured': list(config.get('judge_system', {}).get('judges', {}).keys()),
            'n_passes_default': config.get('judge_system', {}).get('evaluation', {}).get('n_passes', 3),
            'providers_configured': list(config.get('providers', {}).keys()),
            'categories_weighted': list(config.get('weights', {}).get('categories', {}).keys()),
            'parallel_enabled': config.get('execution', {}).get('parallel', {}).get('enabled', False),
            'cache_enabled': config.get('execution', {}).get('cache', {}).get('enabled', False)
        }


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors"""
    pass