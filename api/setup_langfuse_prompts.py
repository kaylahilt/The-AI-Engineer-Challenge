#!/usr/bin/env python3
"""
Setup script to create and version the Aethon prompt in Langfuse
"""

import os
import sys
from langfuse import Langfuse

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prompt_management.aethon_prompt import AETHON_SYSTEM_PROMPT

def setup_langfuse_prompts():
    """Create or update the Aethon system prompt in Langfuse"""
    
    # Initialize Langfuse client
    langfuse = Langfuse()
    
    print("🚀 Setting up Aethon prompt in Langfuse...")
    
    try:
        # Create the main prompt
        prompt = langfuse.create_prompt(
            name="aethon-system-prompt",
            prompt=AETHON_SYSTEM_PROMPT,
            labels=["latest"],
            config={
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 1000
            }
        )
        
        print(f"✅ Successfully created/updated prompt: {prompt.name}")
        print(f"   Version: {prompt.version}")
        print(f"   Labels: {prompt.labels}")
        
        print("\n🎉 Langfuse prompt setup complete!")
        print(f"\nPrompt version created: {prompt.version}")
        print("\nYou can now:")
        print("1. View your prompt at https://cloud.langfuse.com")
        print("2. Deploy the API to use the latest prompt")
        print("3. Monitor performance and iterate on the prompt")
        
    except Exception as e:
        print(f"❌ Error setting up prompts: {e}")
        print("\nMake sure you have set:")
        print("- LANGFUSE_PUBLIC_KEY")
        print("- LANGFUSE_SECRET_KEY")
        sys.exit(1)

if __name__ == "__main__":
    setup_langfuse_prompts() 