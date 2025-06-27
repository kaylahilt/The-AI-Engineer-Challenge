# 🎯 Langfuse Prompt Management & A/B Testing Workflow

This document outlines the **current implementation** for managing prompts and A/B testing using Langfuse native features.

## 🏗️ Environment Setup

### 1. Langfuse Account Setup
1. Sign up at https://cloud.langfuse.com
2. Create a new project
3. Get your API keys from project settings

### 2. Environment Variables
Set these in your development environment and Vercel:

```bash
# Required
export LANGFUSE_PUBLIC_KEY="pk_..."
export LANGFUSE_SECRET_KEY="sk_..."
export OPENAI_API_KEY="sk-..."

# Optional
export LANGFUSE_HOST="https://cloud.langfuse.com"
```

### 3. Verify Connection
```bash
# Test the connection
cd api
python3 test_prompt_quality.py
```

## 🔄 Current Workflow

### Phase 1: Development
**Goal**: Test prompt changes locally before deployment

```python
# Edit prompts in prompt_management/aethon_prompt.py
# Test locally using the quality tester
python3 test_prompt_quality.py
```

### Phase 2: Production A/B Testing
**Goal**: Deploy and test with real users using Langfuse native A/B testing

```python
# A/B testing is automatic via ABTestManager
# Variants are managed through Langfuse labels: prod-a, prod-b
# Traffic split: 90% prod-a, 10% prod-b
```

### Phase 3: Monitoring & Optimization
**Goal**: Monitor performance and iterate based on real data

```bash
# Check A/B test status
curl "localhost:8000/api/ab-test/status/aethon-personality"

# Monitor in Langfuse dashboard
# Compare metrics between prod-a and prod-b variants
```

## 🧪 Quality Assurance Process

### Automated Testing
```python
# Run quality tests (current implementation)
python3 test_prompt_quality.py

# Tests evaluate:
# 1. Basic Greeting - Personality introduction
# 2. Complex Question - Wisdom and practical advice  
# 3. Technical Question - Metaphor usage and accessibility
# 4. Philosophical Question - Spiritual depth and intellectual grace
```

### A/B Testing Quality Gates
- **Automatic Monitoring**: Langfuse dashboard tracks latency, cost, errors
- **Statistical Significance**: Monitor conversion metrics over time
- **Quality Thresholds**: Set alerts for performance degradation

## 📊 A/B Testing Implementation

### Current Configuration
```python
# In api/ab_testing/ab_manager.py
TEST_CONFIG = {
    "aethon-personality": {
        "enabled": True,
        "variants": ["prod-a", "prod-b"],
        "weights": [0.9, 0.1],  # 90/10 traffic split
        "prompt_name": "aethon-system-prompt"
    }
}
```

### How It Works
1. **Variant Selection**: Weighted random choice between `prod-a` and `prod-b`
2. **Prompt Fetching**: `langfuse.get_prompt(name, label=selected_label)`
3. **Automatic Tracing**: `langfuse.openai` wrapper tracks all interactions
4. **Analytics**: Dashboard compares performance between variants

### Managing Variants
```python
# Variants are managed through Langfuse UI or API
# Create different versions and assign labels:
# - Version 1 → label "prod-a" (current production)
# - Version 2 → label "prod-b" (test variant)
```

## 🔧 Configuration Management

### Model Parameters
Current configuration in the system:

```python
# Model settings (in app.py)
model="gpt-4o-mini"
temperature=0.7
max_tokens=1000
```

### Prompt Structure
```python
# System prompt loaded from aethon_prompt.py
def create_system_prompt():
    return """You are Aethon, a digital sage..."""
```

## 📊 Monitoring & Analytics

### Langfuse Dashboard Metrics
- **Latency**: Response time by variant
- **Cost**: Token usage and API costs per variant
- **Volume**: Request patterns and traffic distribution
- **Quality**: Custom evaluation scores

### API Endpoints
```bash
# Check A/B test status
GET /api/ab-test/status/aethon-personality

# Toggle A/B testing
POST /api/ab-test/toggle/aethon-personality
Content-Type: application/json
{"enabled": true/false}
```

## 🚨 Emergency Procedures

### Immediate Issues
```bash
# 1. Disable A/B testing (fallback to prod-a only)
curl -X POST "localhost:8000/api/ab-test/toggle/aethon-personality" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'

# 2. Check system status
curl "localhost:8000/api/ab-test/status/aethon-personality"

# 3. Verify Langfuse connection
python3 -c "
from langfuse import Langfuse
langfuse = Langfuse()
print('Connection:', 'OK' if langfuse.auth_check() else 'FAILED')
"
```

### Rollback Process
1. **Disable A/B testing** to stop traffic to problematic variant
2. **Check Langfuse traces** for error patterns
3. **Update prompt labels** if needed through Langfuse UI
4. **Re-enable testing** once issues are resolved

## 📋 Development Checklist

### Before Making Changes
- [ ] Understand current prompt performance baseline
- [ ] Define success criteria for changes
- [ ] Plan testing approach

### During Development
- [ ] Edit prompts in `prompt_management/aethon_prompt.py`
- [ ] Test locally with `test_prompt_quality.py`
- [ ] Verify no syntax or logical errors

### Before Production
- [ ] Create new prompt version in Langfuse
- [ ] Assign appropriate label (`prod-b` for testing)
- [ ] Monitor initial traffic for issues
- [ ] Set up alerts for key metrics

### After Deployment
- [ ] Monitor A/B test results in Langfuse dashboard
- [ ] Track statistical significance
- [ ] Document findings and decisions
- [ ] Plan next iteration based on results

## 🎓 Best Practices

### Prompt Versioning
1. **Use Semantic Labels**: `prod-a` (stable), `prod-b` (test), `dev` (development)
2. **Document Changes**: Include clear descriptions in Langfuse
3. **Gradual Rollout**: Start with small traffic percentages
4. **Monitor Closely**: Watch metrics for first 24-48 hours

### A/B Testing
1. **Statistical Rigor**: Wait for sufficient sample size
2. **Single Variable**: Test one change at a time
3. **Clear Hypotheses**: Define what success looks like
4. **Time Boundaries**: Set test duration limits

### Emergency Response
1. **Quick Disable**: Always have a way to quickly disable tests
2. **Monitoring Alerts**: Set up automated alerts for key metrics
3. **Rollback Plan**: Know how to revert changes quickly
4. **Communication**: Keep stakeholders informed of issues

## 🔗 Quick Reference

### Key Files
- `api/app.py` - Main FastAPI application with A/B testing integration
- `api/ab_testing/ab_manager.py` - A/B testing logic and configuration
- `api/prompt_management/aethon_prompt.py` - System prompt definition
- `api/test_prompt_quality.py` - Quality testing suite

### Key Commands
```bash
# Test prompt quality
python3 test_prompt_quality.py

# Check A/B test status
curl "localhost:8000/api/ab-test/status/aethon-personality"

# Start development server
python3 -m uvicorn app:app --reload --port 8000
```

### Key URLs
- **Langfuse Dashboard**: https://cloud.langfuse.com
- **Local API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

*This workflow reflects the current implementation using Langfuse native A/B testing. For evaluation strategies, see `EVALUATION_RECOMMENDATIONS.md`.* 