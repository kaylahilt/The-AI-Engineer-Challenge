"""
A/B Test Manager using Langfuse Native Capabilities

This module implements A/B testing using Langfuse's recommended approach:
1. Version-based prompt variants (e.g., version 1, version 2)
2. Weighted random selection
3. Automatic analytics via Langfuse dashboard
"""

import random
import logging
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from langfuse import Langfuse
from prompt_management.aethon_prompt import AETHON_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

@dataclass
class ABTestConfig:
    """Configuration for a single A/B test"""
    enabled: bool
    variants: List[Union[int, str]]  # Can be version numbers or special labels
    weights: List[float]
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if len(self.variants) != len(self.weights):
            raise ValueError("Number of variants must match number of weights")
        
        if abs(sum(self.weights) - 1.0) > 0.001:
            raise ValueError("Weights must sum to 1.0")

class ABTestManager:
    """
    Manages A/B testing using Langfuse native capabilities.
    
    This class provides a clean interface for:
    - Configuring A/B tests with version numbers
    - Selecting prompt variants
    - Managing test states
    """
    
    def __init__(self, langfuse_client: Optional[Langfuse] = None):
        """
        Initialize the A/B test manager.
        
        Args:
            langfuse_client: Optional Langfuse client. If None, creates a new one.
        """
        self.langfuse = langfuse_client or Langfuse()
        self.tests: Dict[str, ABTestConfig] = {}
        self._setup_default_tests()
    
    def _setup_default_tests(self):
        """Set up default A/B test configurations from environment variables"""
        # Get A/B testing configuration from environment
        ab_testing_enabled = os.getenv("AB_TESTING_ENABLED", "false").lower() == "true"
        ab_testing_split = float(os.getenv("AB_TESTING_SPLIT", "0.1"))  # Default 10% test traffic
        
        # Use version numbers instead of labels
        self.tests = {
            "aethon-personality": ABTestConfig(
                enabled=False,  # A/B testing disabled
                variants=[3, 4],  # Version 3 (standard adaptive) vs Version 4 (concise)
                weights=[1.0 - ab_testing_split, ab_testing_split],  # e.g., 90/10 split
                description=f"Aethon personality A/B test - currently disabled"
            )
        }
    
    def get_prompt_variant(self, prompt_name: str, test_name: str) -> tuple[Any, Union[int, str]]:
        """
        Get a prompt variant for A/B testing using version numbers.
        
        Args:
            prompt_name: Name of the prompt in Langfuse
            test_name: Name of the A/B test configuration
            
        Returns:
            Tuple of (prompt_object_or_content, selected_version)
        """
        # Get the selected variant (version number)
        selected_variant = self._select_variant(test_name)
        
        try:
            # Fetch prompt by version number
            if selected_variant == "latest":
                prompt = self.langfuse.get_prompt(prompt_name)
                logger.info(f"Using latest prompt version {prompt.version}")
                return prompt, prompt.version
            else:
                prompt = self.langfuse.get_prompt(prompt_name, version=selected_variant)
                logger.info(f"A/B Test '{test_name}': Using version {selected_variant}")
                return prompt, selected_variant
                
        except Exception as e:
            logger.warning(f"Failed to fetch prompt '{prompt_name}' version {selected_variant}: {e}")
            try:
                # Try fallback to latest version
                prompt = self.langfuse.get_prompt(prompt_name)
                logger.info(f"Fallback: Using latest prompt (version {prompt.version})")
                return prompt, prompt.version
            except Exception as fallback_error:
                # Ultimate fallback: use local AETHON_SYSTEM_PROMPT
                logger.warning(f"Langfuse fallback failed: {fallback_error}")
                logger.info("Using local AETHON_SYSTEM_PROMPT as final fallback")
                
                # Create a mock prompt object with the local content
                class LocalPrompt:
                    def __init__(self, content: str):
                        self.prompt = content
                        self.version = "local-fallback"
                        self.config = {
                            "model": "gpt-4o-mini",
                            "temperature": 0.7,
                            "max_tokens": 1000
                        }
                    
                    def compile(self):
                        return self.prompt
                
                return LocalPrompt(AETHON_SYSTEM_PROMPT), "local-fallback"
    
    def _select_variant(self, test_name: str) -> Union[int, str]:
        """
        Select a variant using weighted random selection.
        
        Args:
            test_name: Name of the A/B test
            
        Returns:
            Selected variant (version number or "latest")
        """
        if test_name not in self.tests:
            logger.info(f"A/B test '{test_name}' not found, using latest version")
            return "latest"
        
        test_config = self.tests[test_name]
        
        if not test_config.enabled:
            logger.info(f"A/B test '{test_name}' is disabled, using latest version")
            return "latest"
        
        # Weighted random selection
        selected = random.choices(test_config.variants, weights=test_config.weights)[0]
        logger.debug(f"A/B test '{test_name}': Selected version {selected}")
        return selected
    
    def get_test_status(self, test_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the status of A/B tests.
        
        Args:
            test_name: Optional specific test name. If None, returns all tests.
            
        Returns:
            Dictionary with test status information
        """
        if test_name:
            if test_name not in self.tests:
                return {"error": f"Test '{test_name}' not found"}
            
            config = self.tests[test_name]
            return {
                "test_name": test_name,
                "enabled": config.enabled,
                "variants": config.variants,
                "weights": config.weights,
                "description": config.description
            }
        
        # Return all tests
        return {
            "approach": "Langfuse version-based A/B testing",
            "method": "Weighted random selection between prompt versions",
            "analytics": "Automatic metrics comparison in Langfuse dashboard by version",
            "tests": {
                name: {
                    "enabled": config.enabled,
                    "variants": config.variants,
                    "weights": config.weights,
                    "description": config.description
                }
                for name, config in self.tests.items()
            }
        }
    
    def toggle_test(self, test_name: str, enabled: bool) -> Dict[str, Any]:
        """
        Enable or disable an A/B test.
        
        Args:
            test_name: Name of the test to toggle
            enabled: Whether to enable or disable the test
            
        Returns:
            Dictionary with operation result
        """
        if test_name not in self.tests:
            return {
                "success": False,
                "error": f"Test '{test_name}' not found",
                "available_tests": list(self.tests.keys())
            }
        
        self.tests[test_name].enabled = enabled
        
        logger.info(f"A/B test '{test_name}' {'enabled' if enabled else 'disabled'}")
        
        return {
            "success": True,
            "test_name": test_name,
            "enabled": enabled,
            "message": f"Version-based A/B test '{test_name}' {'enabled' if enabled else 'disabled'}",
            "note": "Analytics automatically available in Langfuse dashboard grouped by version"
        }
    
    def update_test_versions(self, test_name: str, versions: List[int], weights: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Update the versions being tested in an A/B test.
        
        Args:
            test_name: Name of the test to update
            versions: List of version numbers to test
            weights: Optional weights for each version (defaults to equal distribution)
            
        Returns:
            Dictionary with operation result
        """
        if test_name not in self.tests:
            return {
                "success": False,
                "error": f"Test '{test_name}' not found",
                "available_tests": list(self.tests.keys())
            }
        
        # Default to equal weights if not provided
        if weights is None:
            weights = [1.0 / len(versions)] * len(versions)
        
        try:
            # Update the test configuration
            self.tests[test_name].variants = versions
            self.tests[test_name].weights = weights
            
            logger.info(f"Updated A/B test '{test_name}' with versions: {versions}")
            
            return {
                "success": True,
                "test_name": test_name,
                "message": f"Updated test to compare versions: {versions}",
                "weights": weights
            }
            
        except Exception as e:
            logger.error(f"Failed to update A/B test '{test_name}': {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_test(self, test_name: str, config: ABTestConfig) -> Dict[str, Any]:
        """
        Add a new A/B test configuration.
        
        Args:
            test_name: Name of the new test
            config: Test configuration
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Validate config
            if len(config.variants) != len(config.weights):
                raise ValueError("Number of variants must match number of weights")
            
            if abs(sum(config.weights) - 1.0) > 0.001:
                raise ValueError("Weights must sum to 1.0")
            
            self.tests[test_name] = config
            
            logger.info(f"Added A/B test '{test_name}' with versions: {config.variants}")
            
            return {
                "success": True,
                "test_name": test_name,
                "message": f"A/B test '{test_name}' added successfully",
                "config": {
                    "variants": config.variants,
                    "weights": config.weights,
                    "enabled": config.enabled,
                    "description": config.description
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to add A/B test '{test_name}': {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_metadata_for_trace(self, test_name: str, selected_version: Union[int, str], user_id: str, conversation_id: str) -> Dict[str, Any]:
        """
        Get metadata to attach to Langfuse traces for analytics.
        
        Args:
            test_name: Name of the A/B test
            selected_version: The selected prompt version
            user_id: User identifier
            conversation_id: Conversation identifier
            
        Returns:
            Dictionary with metadata for Langfuse tracing
        """
        return {
            "ab_test_name": test_name,
            "ab_test_version": selected_version,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "ab_test_enabled": self.tests.get(test_name, ABTestConfig(False, [], [])).enabled
        } 