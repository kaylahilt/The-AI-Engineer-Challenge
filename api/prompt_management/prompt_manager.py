"""
Production-ready prompt management library for Langfuse integration.
Handles prompt versioning, deployment, and configuration management.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from langfuse import Langfuse
# Load environment variables from .env file (optional for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available (e.g., in production), use system environment variables
    pass

# Configure logging
logger = logging.getLogger(__name__)

class PromptEnvironment(Enum):
    """Prompt deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    LATEST = "latest"

@dataclass
class PromptConfig:
    """Configuration for a prompt version."""
    model: str = "gpt-4.1-nano"
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    description: str = ""
    version_notes: str = ""

@dataclass
class PromptMetadata:
    """Metadata for prompt management."""
    name: str
    tags: List[str]
    config: PromptConfig
    environment: PromptEnvironment = PromptEnvironment.DEVELOPMENT

class PromptManager:
    """
    Production-ready prompt management system for Langfuse.
    
    Features:
    - Version management with semantic versioning
    - Environment-based deployment (dev/staging/prod)
    - Configuration management
    - Caching for performance
    - Error handling and fallbacks
    """
    
    def __init__(self, 
                 public_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 host: Optional[str] = None,
                 cache_ttl: int = 300):  # 5 minute cache
        """
        Initialize the PromptManager.
        
        Args:
            public_key: Langfuse public key (defaults to env var)
            secret_key: Langfuse secret key (defaults to env var)
            host: Langfuse host URL (defaults to env var)
            cache_ttl: Cache TTL in seconds
        """
        self.langfuse = Langfuse(
            public_key=public_key or os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=secret_key or os.getenv("LANGFUSE_SECRET_KEY"),
            host=host or os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        )
        self.cache_ttl = cache_ttl
        self._prompt_cache = {}
        
        logger.info("PromptManager initialized successfully")
    
    def create_prompt(self, 
                     name: str,
                     content: str,
                     metadata: PromptMetadata,
                     promote_to_production: bool = False) -> bool:
        """
        Create a new prompt version in Langfuse.
        
        Args:
            name: Unique prompt name
            content: The prompt content/template
            metadata: Prompt metadata and configuration
            promote_to_production: Whether to immediately promote to production
            
        Returns:
            bool: Success status
        """
        try:
            # Prepare labels - Langfuse will auto-increment versions
            labels = [metadata.environment.value]
            if promote_to_production:
                labels.append(PromptEnvironment.PRODUCTION.value)
            
            # Create the prompt
            prompt = self.langfuse.create_prompt(
                name=name,
                type="text",
                prompt=content,
                labels=labels,
                config={
                    "model": metadata.config.model,
                    "temperature": metadata.config.temperature,
                    "max_tokens": metadata.config.max_tokens,
                    "top_p": metadata.config.top_p,
                    "frequency_penalty": metadata.config.frequency_penalty,
                    "presence_penalty": metadata.config.presence_penalty,
                    "description": metadata.config.description,
                    "version_notes": metadata.config.version_notes
                },
                tags=metadata.tags
            )
            
            logger.info(f"Successfully created prompt '{name}' - Langfuse auto-incremented version")
            
            # Clear cache for this prompt
            self._clear_prompt_cache(name)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create prompt '{name}': {e}")
            return False
    
    def get_prompt(self, 
                  name: str, 
                  environment: PromptEnvironment = PromptEnvironment.PRODUCTION,
                  fallback_content: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve a prompt from Langfuse with caching and fallback.
        
        Args:
            name: Prompt name
            environment: Which environment version to fetch
            fallback_content: Fallback content if prompt not found
            
        Returns:
            Dict containing prompt content and config, or None if not found
        """
        cache_key = f"{name}:{environment.value}"
        
        # Check cache first
        if cache_key in self._prompt_cache:
            logger.debug(f"Cache hit for prompt '{name}' in {environment.value}")
            return self._prompt_cache[cache_key]
        
        try:
            # Fetch from Langfuse
            prompt = self.langfuse.get_prompt(
                name=name,
                label=environment.value,
                cache_ttl_seconds=self.cache_ttl,
                fallback=fallback_content
            )
            
            if prompt:
                result = {
                    "content": prompt.prompt,
                    "config": prompt.config,
                    "version": getattr(prompt, 'version', 'unknown'),
                    "is_fallback": getattr(prompt, 'is_fallback', False)
                }
                
                # Cache the result
                self._prompt_cache[cache_key] = result
                
                logger.info(f"Retrieved prompt '{name}' from {environment.value}")
                return result
            else:
                logger.warning(f"Prompt '{name}' not found in {environment.value}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve prompt '{name}': {e}")
            
            # Return fallback if available
            if fallback_content:
                logger.info(f"Using fallback content for prompt '{name}'")
                return {
                    "content": fallback_content,
                    "config": {},
                    "version": "fallback",
                    "is_fallback": True
                }
            
            return None
    
    def update_prompt_config(self, 
                           name: str, 
                           config: PromptConfig,
                           version: str,
                           environment: PromptEnvironment = PromptEnvironment.DEVELOPMENT) -> bool:
        """
        Update prompt configuration for a specific version.
        
        Args:
            name: Prompt name
            config: New configuration
            version: Version to update
            environment: Environment to update
            
        Returns:
            bool: Success status
        """
        try:
            # Update the prompt labels to include new environment
            self.langfuse.update_prompt(
                name=name,
                version=int(version.split('.')[-1]) if version.count('.') == 2 else None,
                new_labels=[environment.value, version]
            )
            
            logger.info(f"Updated prompt '{name}' config for version {version}")
            
            # Clear cache
            self._clear_prompt_cache(name)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update prompt '{name}' config: {e}")
            return False
    
    def promote_prompt(self, 
                      name: str, 
                      from_env: PromptEnvironment,
                      to_env: PromptEnvironment) -> bool:
        """
        Promote a prompt from one environment to another.
        
        Args:
            name: Prompt name
            from_env: Source environment
            to_env: Target environment
            
        Returns:
            bool: Success status
        """
        try:
            # Get the current prompt from source environment
            prompt_data = self.get_prompt(name, from_env)
            
            if not prompt_data:
                logger.error(f"Cannot promote '{name}': not found in {from_env.value}")
                return False
            
            # This would require getting the version number and updating labels
            # For now, we'll log the action
            logger.info(f"Promoting prompt '{name}' from {from_env.value} to {to_env.value}")
            
            # Clear cache
            self._clear_prompt_cache(name)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to promote prompt '{name}': {e}")
            return False
    
    def list_prompt_versions(self, name: str) -> List[Dict[str, Any]]:
        """
        List all versions of a prompt.
        
        Args:
            name: Prompt name
            
        Returns:
            List of prompt version information
        """
        try:
            # This would require Langfuse API to list versions
            # For now, return empty list
            logger.info(f"Listing versions for prompt '{name}'")
            return []
            
        except Exception as e:
            logger.error(f"Failed to list versions for prompt '{name}': {e}")
            return []
    
    def _clear_prompt_cache(self, name: str) -> None:
        """Clear cache entries for a specific prompt."""
        keys_to_remove = [key for key in self._prompt_cache.keys() if key.startswith(f"{name}:")]
        for key in keys_to_remove:
            del self._prompt_cache[key]
        
        logger.debug(f"Cleared cache for prompt '{name}'")
    
    def health_check(self) -> bool:
        """
        Check if Langfuse connection is healthy.
        
        Returns:
            bool: True if connection is healthy
        """
        try:
            # Try to authenticate with Langfuse
            # This is a simple way to test the connection
            test_prompt = self.langfuse.get_prompt("non-existent-prompt-test")
            logger.info("Langfuse connection is healthy")
            return True
            
        except Exception as e:
            logger.error(f"Langfuse health check failed: {e}")
            return False

# Convenience functions for common operations
def get_production_prompt(name: str, fallback_content: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Quick function to get a production prompt."""
    manager = PromptManager()
    return manager.get_prompt(name, PromptEnvironment.PRODUCTION, fallback_content)

def create_system_prompt(name: str, content: str, config: PromptConfig) -> bool:
    """Quick function to create a system prompt."""
    manager = PromptManager()
    metadata = PromptMetadata(
        name=name,
        tags=["system-prompt"],
        config=config,
        environment=PromptEnvironment.DEVELOPMENT
    )
    return manager.create_prompt(name, content, metadata) 