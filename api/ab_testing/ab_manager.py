"""
A/B Test Manager using Langfuse Native Capabilities

This module implements A/B testing using Langfuse's recommended approach:
1. Label-based prompt variants (e.g., prod-a, prod-b)
2. Weighted random selection
3. Automatic analytics via Langfuse dashboard
"""

import random
import logging
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from langfuse import Langfuse
from prompt_management.aethon_prompt import AETHON_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

@dataclass
class ABTestConfig:
    """Configuration for a single A/B test"""
    enabled: bool
    variants: List[str]
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
    - Configuring A/B tests
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
        
        self.tests = {
            "aethon-personality": ABTestConfig(
                enabled=ab_testing_enabled,
                variants=["prod-a", "prod-b"],
                weights=[1.0 - ab_testing_split, ab_testing_split],  # e.g., 90/10 split
                description=f"Aethon personality A/B test ({'enabled' if ab_testing_enabled else 'disabled'} via env)"
            )
        }
    
    def get_prompt_variant(self, prompt_name: str, test_name: str) -> tuple[Any, str]:
        """
        Get a prompt variant for A/B testing using Langfuse native approach.
        
        Args:
            prompt_name: Name of the prompt in Langfuse
            test_name: Name of the A/B test configuration
            
        Returns:
            Tuple of (prompt_object_or_content, selected_label)
        """
        # Get the selected variant label
        selected_label = self._select_variant(test_name)
        
        try:
            # Fetch prompt with the selected label
            if selected_label == "production":
                prompt = self.langfuse.get_prompt(prompt_name, label="production")
            else:
                prompt = self.langfuse.get_prompt(prompt_name, label=selected_label)
            
            logger.info(f"A/B Test '{test_name}': Using variant '{selected_label}' (version {prompt.version})")
            return prompt, selected_label
            
        except Exception as e:
            logger.warning(f"Failed to fetch prompt '{prompt_name}' with label '{selected_label}': {e}")
            try:
                # Try fallback to production
                prompt = self.langfuse.get_prompt(prompt_name, label="production")
                logger.info(f"Fallback: Using production prompt (version {prompt.version})")
                return prompt, "production"
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
    
    def _select_variant(self, test_name: str) -> str:
        """
        Select a variant using weighted random selection (Langfuse native approach).
        
        Args:
            test_name: Name of the A/B test
            
        Returns:
            Selected variant label (defaults to "production" when A/B testing is disabled)
        """
        if test_name not in self.tests:
            logger.info(f"A/B test '{test_name}' not found, using single production prompt")
            return "production"
        
        test_config = self.tests[test_name]
        
        if not test_config.enabled:
            logger.info(f"A/B test '{test_name}' is disabled, using single production prompt")
            return "production"
        
        # Weighted random selection (Langfuse recommended approach)
        selected = random.choices(test_config.variants, weights=test_config.weights)[0]
        logger.debug(f"A/B test '{test_name}': Selected variant '{selected}'")
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
            "approach": "Langfuse native A/B testing",
            "method": "Weighted random selection between labeled prompt variants",
            "analytics": "Automatic metrics comparison in Langfuse dashboard",
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
            "message": f"Langfuse A/B test '{test_name}' {'enabled' if enabled else 'disabled'}",
            "note": "Analytics automatically available in Langfuse dashboard"
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
            
            logger.info(f"Added A/B test '{test_name}' with variants: {config.variants}")
            
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
    
    def get_metadata_for_trace(self, test_name: str, selected_label: str, user_id: str, conversation_id: str) -> Dict[str, Any]:
        """
        Get metadata to attach to Langfuse traces for analytics.
        
        Args:
            test_name: Name of the A/B test
            selected_label: The selected prompt variant label
            user_id: User identifier
            conversation_id: Conversation identifier
            
        Returns:
            Dictionary with metadata for Langfuse tracing
        """
        return {
            "ab_test_name": test_name,
            "ab_test_variant": selected_label,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "ab_test_enabled": self.tests.get(test_name, ABTestConfig(False, [], [])).enabled
        } 