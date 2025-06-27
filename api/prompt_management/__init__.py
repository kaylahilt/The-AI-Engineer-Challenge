"""
Prompt Management Package

Production-ready prompt management system for AI applications using Langfuse.
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
from .aethon_prompt import AETHON_SYSTEM_PROMPT

__version__ = "1.0.0"
__author__ = "AI Engineer Challenge Team"

__all__ = [
    "PromptManager",
    "PromptConfig", 
    "PromptMetadata",
    "PromptEnvironment",
    "get_production_prompt",
    "create_system_prompt",
    "AETHON_SYSTEM_PROMPT"
] 