# Systematic Prompt Management with Langfuse

## Overview

This document outlines the optimal workflow for managing prompts with Langfuse to ensure full tracking, versioning, and systematic improvements.

## 🎯 Core Principles

1. **Prompts as Code**: Keep prompt source in version control
2. **Automatic Sync**: Deploy prompts to Langfuse as part of CI/CD
3. **Version Everything**: Every change creates a new version
4. **Test Before Deploy**: Validate prompts before production
5. **Monitor & Iterate**: Use data to drive improvements

## 📋 Recommended Workflow

### 1. **Prompt Development Structure**

```
api/
├── prompts/
│   ├── __init__.py
│   ├── base_prompts.py      # Core prompt definitions
│   ├── variants/            # A/B test variants
│   │   ├── concise.py
│   │   ├── detailed.py
│   │   └── creative.py
│   └── configs/             # Model configurations
│       └── default.yaml
```

### 2. **Prompt Definition Format**

Create prompts as Python modules with metadata:

```python
# prompts/base_prompts.py
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class PromptDefinition:
    name: str
    content: str
    labels: list[str]
    config: Dict[str, Any]
    description: str

AETHON_BASE = PromptDefinition(
    name="aethon-system-prompt",
    content="""...""",
    labels=["production", "v2"],
    config={
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1000
    },
    description="Base Aethon personality with structured response format"
)
```

### 3. **Automatic Deployment Pipeline**

#### Option A: GitHub Actions (Recommended)

```yaml
# .github/workflows/deploy-prompts.yml
name: Deploy Prompts to Langfuse

on:
  push:
    paths:
      - 'api/prompts/**'
    branches:
      - main

jobs:
  deploy-prompts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install langfuse pyyaml
      
      - name: Deploy prompts
        env:
          LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
          LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}
        run: |
          python api/scripts/deploy_prompts.py
```

#### Option B: Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
if git diff --cached --name-only | grep -q "prompts/"; then
    echo "Prompt changes detected. Validating..."
    python api/scripts/validate_prompts.py
fi
```

### 4. **Deployment Script**

```python
# scripts/deploy_prompts.py
import os
import sys
from pathlib import Path
from langfuse import Langfuse

sys.path.append(str(Path(__file__).parent.parent))

from prompts import ALL_PROMPTS

def deploy_prompts():
    """Deploy all prompts to Langfuse with proper versioning"""
    langfuse = Langfuse()
    
    for prompt_def in ALL_PROMPTS:
        try:
            # Check if prompt exists
            existing = langfuse.get_prompt(
                name=prompt_def.name,
                label=prompt_def.labels[0]
            )
            
            # Compare content
            if existing and existing.prompt == prompt_def.content:
                print(f"✓ {prompt_def.name} is up to date")
                continue
                
        except:
            pass  # Prompt doesn't exist yet
        
        # Create new version
        prompt = langfuse.create_prompt(
            name=prompt_def.name,
            prompt=prompt_def.content,
            labels=prompt_def.labels,
            config=prompt_def.config
        )
        
        print(f"✅ Deployed {prompt_def.name} v{prompt.version}")

if __name__ == "__main__":
    deploy_prompts()
```

### 5. **Testing Prompts Before Production**

```python
# scripts/test_prompts.py
async def test_prompt(prompt_def: PromptDefinition):
    """Test prompt with sample inputs"""
    test_cases = [
        "Explain quantum computing",
        "What is love?",
        "How do I learn programming?"
    ]
    
    for test in test_cases:
        response = await generate_with_prompt(prompt_def, test)
        
        # Validate response structure
        assert response.startswith("**Core Truth First**")
        assert len(response) < prompt_def.config["max_tokens"]
        
    return True
```

### 6. **Monitoring & Iteration Process**

1. **Weekly Review**:
   ```python
   # scripts/analyze_performance.py
   def weekly_prompt_review():
       metrics = langfuse.get_prompt_metrics(
           name="aethon-system-prompt",
           days=7
       )
       
       print(f"Avg Clarity Score: {metrics.clarity_score}")
       print(f"Avg Response Time: {metrics.response_time}")
       print(f"User Satisfaction: {metrics.satisfaction}")
   ```

2. **A/B Test Analysis**:
   ```python
   def compare_variants():
       results = langfuse.get_ab_test_results(
           test_name="aethon-personality"
       )
       
       if results.variant_b.clarity > results.variant_a.clarity:
           promote_variant("b")
   ```

## 🚀 Implementation Steps

1. **Initial Setup**:
   ```bash
   # Create prompt structure
   mkdir -p api/prompts/variants
   mkdir -p api/scripts
   
   # Install dependencies
   pip install langfuse pyyaml pytest
   ```

2. **Environment Configuration**:
   ```bash
   # .env
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_SYNC_ENABLED=true
   ```

3. **CI/CD Integration**:
   - Add GitHub secrets for Langfuse keys
   - Create deployment workflow
   - Set up monitoring alerts

## 📊 Best Practices

1. **Version Control Everything**:
   - Prompt content
   - Model configurations
   - Test cases
   - Performance benchmarks

2. **Semantic Versioning**:
   - Major: Breaking changes to response format
   - Minor: New features or improvements
   - Patch: Small tweaks or fixes

3. **Gradual Rollout**:
   - Start with 10% traffic
   - Monitor for 24 hours
   - Increase to 50% if metrics are good
   - Full rollout after 48 hours

4. **Rollback Strategy**:
   ```python
   def rollback_prompt(name: str, to_version: int):
       """Quick rollback to previous version"""
       langfuse.set_prompt_labels(
           name=name,
           version=to_version,
           labels=["production"]
       )
   ```

## 🔄 Continuous Improvement Loop

1. **Collect Data** → Langfuse tracks all interactions
2. **Analyze** → Weekly performance reviews
3. **Hypothesize** → What changes might improve metrics?
4. **Test** → Create variant and A/B test
5. **Measure** → Compare performance
6. **Deploy** → Promote winning variant
7. **Repeat** → Continue iterating

This systematic approach ensures:
- ✅ All prompts are versioned
- ✅ Changes are tracked in git
- ✅ Deployment is automated
- ✅ Performance is monitored
- ✅ Improvements are data-driven 