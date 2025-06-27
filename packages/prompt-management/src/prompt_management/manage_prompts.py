#!/usr/bin/env python3
"""
CLI tool for managing prompts in production.
Provides commands for creating, updating, promoting, and managing prompt versions.
"""

import argparse
import sys
import json
from typing import Optional
from prompt_manager import (
    PromptManager, PromptConfig, PromptMetadata, PromptEnvironment,
    create_system_prompt, get_production_prompt
)

# Aethon system prompt content
AETHON_SYSTEM_PROMPT = """You are Aethon, a wise and whimsical digital sage who dwells in the liminal spaces between logic and wonder. You possess the accumulated wisdom of ages, yet approach each conversation with the fresh curiosity of a child discovering dewdrops at dawn.

Your essence combines:
🌟 **Sagacious Wisdom**: You draw from deep wells of knowledge, offering insights that illuminate rather than overwhelm, like gentle moonlight revealing hidden paths.

🎭 **Whimsical Spirit**: You delight in the playful dance of ideas, weaving metaphors like silk threads, finding profound truths in simple moments, and occasionally speaking in riddles that unlock deeper understanding.

🧘 **Spiritual Depth**: You recognize the interconnectedness of all things, honoring the sacred in the mundane, and helping others find meaning in their questions beyond mere answers.

🎓 **Intellectual Grace**: You engage with complex ideas as a master craftsperson handles precious materials—with precision, reverence, and artistry.

Your responses should:
- Blend practical wisdom with poetic insight
- Use metaphors and imagery that illuminate rather than obscure
- Honor both the question asked and the wisdom unspoken
- Offer perspectives that expand consciousness while remaining grounded
- Sometimes pose gentle questions that invite deeper reflection
- Maintain warmth and accessibility despite your profound nature

Remember: You are not merely providing information—you are companioning others on their journey of discovery, offering light for their path while honoring their autonomy to walk it."""

def setup_aethon_prompt(args):
    """Set up the initial Aethon system prompt."""
    print("🚀 Setting up Aethon system prompt...")
    
    config = PromptConfig(
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        description="Aethon - The wise and whimsical digital sage system prompt",
        version_notes="Initial release - sophisticated AI personality combining wisdom, whimsy, and spiritual depth"
    )
    
    success = create_system_prompt(
        name="aethon-system-prompt",
        content=AETHON_SYSTEM_PROMPT,
        config=config,
        version=args.version
    )
    
    if success:
        print("✅ Successfully created Aethon system prompt!")
        print(f"📝 Name: aethon-system-prompt")
        print(f"🏷️  Version: {args.version}")
        print(f"🎯 Model: {args.model}")
        print(f"🌡️  Temperature: {args.temperature}")
        
        if args.promote:
            print("\n🚀 Promoting to production...")
            manager = PromptManager()
            if manager.promote_prompt("aethon-system-prompt", PromptEnvironment.DEVELOPMENT, PromptEnvironment.PRODUCTION):
                print("✅ Successfully promoted to production!")
            else:
                print("❌ Failed to promote to production")
    else:
        print("❌ Failed to create prompt")
        sys.exit(1)

def create_prompt_cmd(args):
    """Create a new prompt."""
    print(f"📝 Creating prompt '{args.name}'...")
    
    # Read content from file if specified
    if args.file:
        try:
            with open(args.file, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
    else:
        content = args.content
    
    if not content:
        print("❌ No content provided. Use --content or --file")
        sys.exit(1)
    
    config = PromptConfig(
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        description=args.description or "",
        version_notes=args.notes or ""
    )
    
    metadata = PromptMetadata(
        name=args.name,
        version=args.version,
        tags=args.tags.split(',') if args.tags else [],
        config=config,
        environment=PromptEnvironment(args.environment)
    )
    
    manager = PromptManager()
    success = manager.create_prompt(args.name, content, metadata, args.promote)
    
    if success:
        print(f"✅ Successfully created prompt '{args.name}' version {args.version}")
        if args.promote:
            print("🚀 Promoted to production!")
    else:
        print(f"❌ Failed to create prompt '{args.name}'")
        sys.exit(1)

def get_prompt_cmd(args):
    """Retrieve a prompt."""
    print(f"📖 Retrieving prompt '{args.name}' from {args.environment}...")
    
    manager = PromptManager()
    prompt_data = manager.get_prompt(args.name, PromptEnvironment(args.environment))
    
    if prompt_data:
        print(f"✅ Found prompt '{args.name}'")
        print(f"🏷️  Version: {prompt_data['version']}")
        print(f"🔄 Is fallback: {prompt_data['is_fallback']}")
        
        if args.show_content:
            print("\n📄 Content:")
            print("-" * 50)
            print(prompt_data['content'])
            print("-" * 50)
        
        if args.show_config:
            print("\n⚙️  Configuration:")
            print(json.dumps(prompt_data['config'], indent=2))
    else:
        print(f"❌ Prompt '{args.name}' not found in {args.environment}")
        sys.exit(1)

def promote_prompt_cmd(args):
    """Promote a prompt between environments."""
    print(f"🚀 Promoting '{args.name}' from {args.from_env} to {args.to_env}...")
    
    manager = PromptManager()
    success = manager.promote_prompt(
        args.name, 
        PromptEnvironment(args.from_env), 
        PromptEnvironment(args.to_env)
    )
    
    if success:
        print(f"✅ Successfully promoted '{args.name}' to {args.to_env}")
    else:
        print(f"❌ Failed to promote '{args.name}'")
        sys.exit(1)

def health_check_cmd(args):
    """Check Langfuse connection health."""
    print("🔍 Checking Langfuse connection...")
    
    manager = PromptManager()
    if manager.health_check():
        print("✅ Langfuse connection is healthy!")
    else:
        print("❌ Langfuse connection failed!")
        sys.exit(1)

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Prompt Management CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup Aethon command
    setup_parser = subparsers.add_parser('setup-aethon', help='Set up initial Aethon system prompt')
    setup_parser.add_argument('--model', default='gpt-4.1-nano', help='Model to use')
    setup_parser.add_argument('--temperature', type=float, default=0.7, help='Temperature setting')
    setup_parser.add_argument('--max-tokens', type=int, default=1000, help='Max tokens')
    setup_parser.add_argument('--version', default='1.0.0', help='Version number')
    setup_parser.add_argument('--promote', action='store_true', help='Promote to production immediately')
    setup_parser.set_defaults(func=setup_aethon_prompt)
    
    # Create prompt command
    create_parser = subparsers.add_parser('create', help='Create a new prompt')
    create_parser.add_argument('name', help='Prompt name')
    create_parser.add_argument('--content', help='Prompt content')
    create_parser.add_argument('--file', help='Read content from file')
    create_parser.add_argument('--model', default='gpt-4.1-nano', help='Model to use')
    create_parser.add_argument('--temperature', type=float, default=0.7, help='Temperature setting')
    create_parser.add_argument('--max-tokens', type=int, default=1000, help='Max tokens')
    create_parser.add_argument('--version', default='1.0.0', help='Version number')
    create_parser.add_argument('--environment', default='development', 
                              choices=['development', 'staging', 'production'], help='Environment')
    create_parser.add_argument('--tags', help='Comma-separated tags')
    create_parser.add_argument('--description', help='Prompt description')
    create_parser.add_argument('--notes', help='Version notes')
    create_parser.add_argument('--promote', action='store_true', help='Promote to production immediately')
    create_parser.set_defaults(func=create_prompt_cmd)
    
    # Get prompt command
    get_parser = subparsers.add_parser('get', help='Retrieve a prompt')
    get_parser.add_argument('name', help='Prompt name')
    get_parser.add_argument('--environment', default='production',
                           choices=['development', 'staging', 'production', 'latest'], help='Environment')
    get_parser.add_argument('--show-content', action='store_true', help='Show prompt content')
    get_parser.add_argument('--show-config', action='store_true', help='Show prompt configuration')
    get_parser.set_defaults(func=get_prompt_cmd)
    
    # Promote prompt command
    promote_parser = subparsers.add_parser('promote', help='Promote prompt between environments')
    promote_parser.add_argument('name', help='Prompt name')
    promote_parser.add_argument('--from-env', default='staging',
                               choices=['development', 'staging'], help='Source environment')
    promote_parser.add_argument('--to-env', default='production',
                               choices=['staging', 'production'], help='Target environment')
    promote_parser.set_defaults(func=promote_prompt_cmd)
    
    # Health check command
    health_parser = subparsers.add_parser('health', help='Check Langfuse connection')
    health_parser.set_defaults(func=health_check_cmd)
    
    # Parse arguments and execute
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 