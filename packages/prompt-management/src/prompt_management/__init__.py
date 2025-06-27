"""
Prompt Management Package

A production-ready prompt management system for AI applications using Langfuse.
Provides versioning, environment management, caching, and fallback handling.
"""

from .prompt_manager import (
    PromptManager,
    PromptConfig,
    PromptMetadata,
    PromptEnvironment,
    get_production_prompt,
    create_system_prompt
)

__version__ = "1.0.0"
__author__ = "AI Engineer Challenge Team"

__all__ = [
    "PromptManager",
    "PromptConfig", 
    "PromptMetadata",
    "PromptEnvironment",
    "get_production_prompt",
    "create_system_prompt"
] 