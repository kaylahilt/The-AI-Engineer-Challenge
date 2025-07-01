#!/usr/bin/env python3
"""
Prompt Variant Management Tool

This script helps you create, test, and manage different prompt variants
for iterative improvements based on data and feedback.
"""

import os
import sys
from typing import Dict, List, Optional
from langfuse import Langfuse
import json
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prompt_management.aethon_prompt import AETHON_SYSTEM_PROMPT

class PromptVariantManager:
    """Manages prompt variants for A/B testing and iteration"""
    
    def __init__(self):
        self.langfuse = Langfuse()
        self.prompt_name = "aethon-system-prompt"
    
    def list_versions(self) -> List[Dict]:
        """List all versions of the prompt"""
        print(f"\n📋 Fetching all versions of '{self.prompt_name}'...")
        
        # This is a simplified version - in practice you'd need to iterate
        # through all versions using the Langfuse API
        versions = []
        version = 1
        
        while True:
            try:
                prompt = self.langfuse.get_prompt(self.prompt_name, version=version)
                versions.append({
                    "version": prompt.version,
                    "labels": prompt.labels,
                    "created": "Recently",  # Langfuse doesn't expose this directly
                    "config": prompt.config
                })
                version += 1
            except:
                break
        
        return versions
    
    def create_variant(self, variant_type: str, custom_prompt: Optional[str] = None) -> Dict:
        """Create a new prompt variant based on type"""
        
        base_prompt = custom_prompt or AETHON_SYSTEM_PROMPT
        
        variants = {
            "structured": {
                "prompt": f"""{base_prompt}

IMPORTANT: Structure every response using this format:
1. **Opening Wisdom** (1-2 sentences): A metaphorical or philosophical greeting
2. **Core Insight** (2-3 sentences): Direct answer to the question  
3. **Deeper Understanding** (2-3 sentences): Expand with examples
4. **Practical Application** (1-2 sentences): How to apply this wisdom
5. **Closing Reflection** (1 sentence): A thought-provoking question""",
                "labels": ["structured"],
                "config": {
                    "model": "gpt-4o-mini",
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            },
            "balanced": {
                "prompt": f"""{base_prompt}

BALANCE GUIDELINES:
- Use metaphors sparingly (max 1 per response)
- Focus 70% on practical wisdom, 30% on whimsical elements
- Keep responses between 100-200 words
- Always end with actionable advice""",
                "labels": ["balanced"],
                "config": {
                    "model": "gpt-4o-mini",
                    "temperature": 0.6,
                    "max_tokens": 800
                }
            },
            "ultra-concise": {
                "prompt": f"""{base_prompt}

CONCISENESS RULES:
- Maximum 3 sentences per response
- One key insight per message
- Skip elaborate metaphors
- Direct, impactful wisdom only""",
                "labels": ["ultra-concise"],
                "config": {
                    "model": "gpt-4o-mini",
                    "temperature": 0.5,
                    "max_tokens": 300
                }
            },
            "adaptive": {
                "prompt": f"""{base_prompt}

ADAPTIVE RESPONSE GUIDELINES:
- For simple questions: Brief, direct answers (50-100 words)
- For complex/philosophical questions: Deeper exploration (200-300 words)
- For technical questions: Clear explanations with examples
- Match the user's tone and energy level""",
                "labels": ["adaptive"],
                "config": {
                    "model": "gpt-4o-mini",
                    "temperature": 0.8,
                    "max_tokens": 1200
                }
            }
        }
        
        if variant_type not in variants:
            print(f"❌ Unknown variant type: {variant_type}")
            print(f"Available types: {', '.join(variants.keys())}")
            return {}
        
        variant_config = variants[variant_type]
        
        try:
            prompt = self.langfuse.create_prompt(
                name=self.prompt_name,
                prompt=variant_config["prompt"],
                labels=variant_config["labels"],
                config=variant_config["config"]
            )
            
            print(f"✅ Created {variant_type} variant!")
            print(f"   Version: {prompt.version}")
            print(f"   Labels: {prompt.labels}")
            
            return {
                "version": prompt.version,
                "type": variant_type,
                "labels": prompt.labels
            }
            
        except Exception as e:
            print(f"❌ Error creating variant: {e}")
            return {}
    
    def compare_versions(self, version1: int, version2: int):
        """Display a comparison between two versions"""
        try:
            prompt1 = self.langfuse.get_prompt(self.prompt_name, version=version1)
            prompt2 = self.langfuse.get_prompt(self.prompt_name, version=version2)
            
            print(f"\n📊 Comparing Version {version1} vs Version {version2}")
            print("="*60)
            
            print(f"\n🏷️  Version {version1} Labels: {prompt1.labels}")
            print(f"🏷️  Version {version2} Labels: {prompt2.labels}")
            
            print(f"\n⚙️  Version {version1} Config: {json.dumps(prompt1.config, indent=2)}")
            print(f"⚙️  Version {version2} Config: {json.dumps(prompt2.config, indent=2)}")
            
            # Show prompt differences (simplified)
            if prompt1.prompt != prompt2.prompt:
                print("\n📝 Prompts are different")
                print(f"Version {version1} length: {len(prompt1.prompt)} characters")
                print(f"Version {version2} length: {len(prompt2.prompt)} characters")
            else:
                print("\n📝 Prompts are identical")
                
        except Exception as e:
            print(f"❌ Error comparing versions: {e}")
    
    def update_ab_test(self, version1: int, version2: int, split: float = 0.5):
        """Update the A/B test configuration"""
        print(f"\n🔧 Updating A/B test configuration...")
        print(f"Version {version1}: {(1-split)*100:.0f}% of traffic")
        print(f"Version {version2}: {split*100:.0f}% of traffic")
        
        # This would integrate with your AB test manager
        # For now, just show what would happen
        print(f"\n💡 To apply this configuration:")
        print(f"1. Set AB_TESTING_ENABLED=true in your environment")
        print(f"2. Set AB_TESTING_SPLIT={split}")
        print(f"3. Restart your API")
        
        return {
            "versions": [version1, version2],
            "weights": [1-split, split]
        }

def main():
    """Interactive prompt management CLI"""
    manager = PromptVariantManager()
    
    while True:
        print("\n" + "="*60)
        print("🎯 Aethon Prompt Variant Manager")
        print("="*60)
        print("1. List all versions")
        print("2. Create new variant")
        print("3. Compare two versions")
        print("4. Update A/B test configuration")
        print("5. Exit")
        
        choice = input("\nSelect an option (1-5): ").strip()
        
        if choice == "1":
            versions = manager.list_versions()
            print(f"\n📚 Found {len(versions)} versions:")
            for v in versions:
                print(f"  Version {v['version']}: {v['labels']} - Model: {v['config'].get('model', 'N/A')}")
        
        elif choice == "2":
            print("\nAvailable variant types:")
            print("- structured: Enforces clear response structure")
            print("- balanced: Balances whimsy with practicality")
            print("- ultra-concise: Very brief responses")
            print("- adaptive: Adapts length to question complexity")
            
            variant_type = input("\nEnter variant type: ").strip()
            manager.create_variant(variant_type)
        
        elif choice == "3":
            v1 = int(input("Enter first version number: "))
            v2 = int(input("Enter second version number: "))
            manager.compare_versions(v1, v2)
        
        elif choice == "4":
            v1 = int(input("Enter version 1 (control): "))
            v2 = int(input("Enter version 2 (variant): "))
            split = float(input("Enter traffic % for version 2 (e.g., 0.2 for 20%): "))
            manager.update_ab_test(v1, v2, split)
        
        elif choice == "5":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid option, please try again")

if __name__ == "__main__":
    main() 