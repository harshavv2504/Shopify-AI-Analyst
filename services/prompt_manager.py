"""
Prompt Manager
Loads and manages LLM prompts from external configuration files
"""
import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PromptManager:
    """
    Manages LLM prompts loaded from external configuration files
    Allows easy modification of prompts without changing code
    """
    
    DEFAULT_PROMPTS_PATH = "config/prompts.json"
    
    def __init__(self, prompts_path: str = None):
        """
        Initialize prompt manager
        
        Args:
            prompts_path: Path to prompts configuration file
        """
        self.prompts_path = prompts_path or self.DEFAULT_PROMPTS_PATH
        self.prompts = self._load_prompts()
        logger.info(f"Prompt manager initialized with {len(self.prompts)} prompt sets")
    
    def _load_prompts(self) -> Dict[str, Any]:
        """
        Load prompts from JSON configuration file
        
        Returns:
            Dictionary of prompts
        
        Raises:
            FileNotFoundError: If prompts file doesn't exist
            json.JSONDecodeError: If prompts file is invalid JSON
        """
        try:
            # Get the directory of this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up one level to python-service directory
            base_dir = os.path.dirname(current_dir)
            # Construct full path
            full_path = os.path.join(base_dir, self.prompts_path)
            
            with open(full_path, 'r', encoding='utf-8') as f:
                prompts = json.load(f)
            
            logger.info(f"Loaded prompts from {full_path}")
            return prompts
        
        except FileNotFoundError:
            logger.error(f"Prompts file not found: {self.prompts_path}")
            raise
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in prompts file: {e}")
            raise
    
    def get_system_message(self, service_name: str) -> str:
        """
        Get system message for a service
        
        Args:
            service_name: Name of the service (e.g., "intent_classifier")
        
        Returns:
            System message string
        
        Raises:
            KeyError: If service not found in prompts
        """
        if service_name not in self.prompts:
            raise KeyError(f"Service '{service_name}' not found in prompts configuration")
        
        return self.prompts[service_name].get("system_message", "")
    
    def get_user_prompt_template(self, service_name: str) -> str:
        """
        Get user prompt template for a service
        
        Args:
            service_name: Name of the service
        
        Returns:
            User prompt template string
        
        Raises:
            KeyError: If service not found in prompts
        """
        if service_name not in self.prompts:
            raise KeyError(f"Service '{service_name}' not found in prompts configuration")
        
        return self.prompts[service_name].get("user_prompt_template", "")
    
    def format_user_prompt(self, service_name: str, **kwargs) -> str:
        """
        Format user prompt template with provided variables
        
        Args:
            service_name: Name of the service
            **kwargs: Variables to substitute in template
        
        Returns:
            Formatted prompt string
        
        Raises:
            KeyError: If service not found or required variable missing
        """
        template = self.get_user_prompt_template(service_name)
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing required variable for prompt: {e}")
            raise
    
    def reload_prompts(self):
        """
        Reload prompts from file
        Useful for updating prompts without restarting the application
        """
        self.prompts = self._load_prompts()
        logger.info("Prompts reloaded from file")
    
    def get_all_services(self) -> list:
        """
        Get list of all available services
        
        Returns:
            List of service names
        """
        return list(self.prompts.keys())
    
    def validate_prompts(self) -> Dict[str, bool]:
        """
        Validate that all prompts have required fields
        
        Returns:
            Dictionary mapping service names to validation status
        """
        validation_results = {}
        
        for service_name, config in self.prompts.items():
            has_system = "system_message" in config and config["system_message"]
            has_user = "user_prompt_template" in config and config["user_prompt_template"]
            validation_results[service_name] = has_system and has_user
        
        return validation_results


# Global instance for easy access
_prompt_manager = None


def get_prompt_manager() -> PromptManager:
    """
    Get global prompt manager instance (singleton pattern)
    
    Returns:
        PromptManager instance
    """
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
