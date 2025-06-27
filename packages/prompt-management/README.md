# Prompt Management Package

A production-ready prompt management system for AI applications using Langfuse. This package provides versioning, environment management, caching, and robust error handling for AI prompts.

## Features

🚀 **Production Ready**
- Environment-based deployment (development → staging → production)
- Caching for optimal performance
- Robust error handling and logging
- Health checks and monitoring

🎯 **Version Management**
- Semantic versioning support
- Easy promotion between environments
- Rollback capabilities
- Configuration management (model, temperature, max_tokens, etc.)

🛠 **Developer Experience**
- CLI tool for prompt management
- Clean Python API
- Type hints throughout
- Comprehensive error messages

## Quick Start

### Installation

```bash
# Install in development mode from the monorepo root
pip install -e packages/prompt-management
```

### Basic Usage

```python
from prompt_management import PromptManager, PromptEnvironment

# Initialize the manager
manager = PromptManager()

# Get a production prompt
prompt_data = manager.get_prompt(
    name="my-system-prompt",
    environment=PromptEnvironment.PRODUCTION
)

if prompt_data:
    content = prompt_data["content"]
    config = prompt_data["config"]
    print(f"Using prompt version: {prompt_data['version']}")
```

### CLI Usage

```bash
# Set up your first prompt
manage-prompts setup-aethon --promote

# Create a new prompt
manage-prompts create my-prompt --content "You are a helpful assistant" --promote

# Get a prompt
manage-prompts get my-prompt --show-content --show-config

# Promote from staging to production
manage-prompts promote my-prompt --from-env staging --to-env production

# Health check
manage-prompts health
```

## Configuration

Set up your Langfuse credentials as environment variables:

```bash
export LANGFUSE_PUBLIC_KEY="pk_..."
export LANGFUSE_SECRET_KEY="sk_..."
export LANGFUSE_HOST="https://cloud.langfuse.com"  # Optional
```

## API Reference

### PromptManager

The main class for managing prompts.

```python
from prompt_management import PromptManager, PromptEnvironment

manager = PromptManager()

# Get a prompt
prompt_data = manager.get_prompt("prompt-name", PromptEnvironment.PRODUCTION)

# Create a prompt
success = manager.create_prompt(name, content, metadata)

# Promote between environments
success = manager.promote_prompt(name, from_env, to_env)
```

### PromptConfig

Configuration class for prompt settings:

```python
from prompt_management import PromptConfig

config = PromptConfig(
    model="gpt-4.1-nano",
    temperature=0.7,
    max_tokens=1000,
    description="My custom prompt",
    version_notes="Initial release"
)
```

### PromptEnvironment

Environment enumeration:

```python
from prompt_management import PromptEnvironment

PromptEnvironment.DEVELOPMENT
PromptEnvironment.STAGING  
PromptEnvironment.PRODUCTION
PromptEnvironment.LATEST
```

## Development

### Running Tests

```bash
cd packages/prompt-management
pip install -e ".[dev]"
pytest
```

### Code Formatting

```bash
black src/
isort src/
mypy src/
```

## Architecture

The package follows these principles:

- **Fail Fast**: No hardcoded fallbacks - ensures proper Langfuse setup
- **Single Source of Truth**: All prompts managed centrally in Langfuse
- **Environment Isolation**: Clear separation between dev/staging/production
- **Performance**: Client-side caching with configurable TTL
- **Observability**: Comprehensive logging and health checks

## License

MIT License - see LICENSE file for details. 