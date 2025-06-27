# 🎯 Langfuse Prompt Versioning Workflow

This document outlines the **operationally rigorous workflow** for managing, testing, and deploying prompt changes using Langfuse.

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

### 3. Initial Deployment
```bash
cd api
python3 -m prompt_management.manage_prompts setup-aethon --promote
```

## 🔄 Development Workflow

### Phase 1: Development
**Goal**: Create and test new prompt versions safely

```bash
# 1. Edit your prompt in aethon_prompt.py
# 2. Create new version in development (Langfuse auto-increments version)
python3 -m prompt_management.manage_prompts create aethon-system-prompt \
  --file prompt_management/aethon_prompt.py \
  --model gpt-4.1-nano \
  --temperature 0.7 \
  --environment development \
  --description "Improved reasoning and reduced hallucinations" \
  --notes "Added better context handling based on user feedback"

# 3. Test locally
python3 test_prompt_quality.py
```

### Phase 2: Staging
**Goal**: Validate prompt changes in a production-like environment

```bash
# 1. Promote to staging
python3 -m prompt_management.manage_prompts promote aethon-system-prompt \
  --from-env development \
  --to-env staging

# 2. Run comprehensive tests
python3 test_prompt_quality.py > staging_test_results.md

# 3. Manual testing (optional)
python3 -m prompt_management.manage_prompts get aethon-system-prompt \
  --environment staging \
  --show-content
```

### Phase 3: Production
**Goal**: Deploy only after thorough validation

```bash
# 1. Review test results
cat staging_test_results.md

# 2. If tests pass (>80% pass rate), promote to production
python3 -m prompt_management.manage_prompts promote aethon-system-prompt \
  --from-env staging \
  --to-env production

# 3. Verify production deployment
python3 -m prompt_management.manage_prompts get aethon-system-prompt \
  --environment production \
  --show-config
```

## 🧪 Quality Assurance Process

### Automated Testing
Run the quality test suite before any promotion:

```bash
# Test all environments
python3 test_prompt_quality.py

# Test specific environment
python3 -c "
from test_prompt_quality import PromptQualityTester
from prompt_management import PromptEnvironment
tester = PromptQualityTester()
result = tester.test_prompt_environment('aethon-system-prompt', PromptEnvironment.STAGING)
print(f'Pass rate: {result[\"overall_pass_rate\"]:.1%}')
"
```

### Quality Gates
- **Development → Staging**: No specific requirements (experimentation phase)
- **Staging → Production**: Minimum 80% pass rate on quality tests
- **Production**: Monitor performance metrics in Langfuse dashboard

### Test Cases
The quality tester evaluates:
1. **Basic Greeting**: Tests personality introduction
2. **Complex Question**: Tests wisdom and practical advice
3. **Technical Question**: Tests metaphor usage and accessibility
4. **Philosophical Question**: Tests spiritual depth and intellectual grace

## 📊 Monitoring & Rollback

### Monitoring
1. **Langfuse Dashboard**: Monitor cost, latency, and usage patterns
2. **Quality Metrics**: Track response quality over time
3. **User Feedback**: Collect and analyze user satisfaction

### Rollback Process
If issues are detected in production:

```bash
# 1. Identify last known good version
python3 -m prompt_management.manage_prompts list-versions aethon-system-prompt

# 2. Promote previous version to production
python3 -m prompt_management.manage_prompts promote aethon-system-prompt-v1.0.0 \
  --from-env staging \
  --to-env production

# 3. Verify rollback
python3 test_prompt_quality.py
```

## 🔧 Configuration Management

### Model Parameters
Manage these through Langfuse configuration:

```python
config = PromptConfig(
    model="gpt-4.1-nano",           # Model selection
    temperature=0.7,                # Creativity vs consistency
    max_tokens=1000,                # Response length limit
    top_p=1.0,                      # Nucleus sampling
    frequency_penalty=0.0,          # Repetition control
    presence_penalty=0.0,           # Topic diversity
    description="Version description",
    version_notes="Change details"
)
```

### A/B Testing
For comparing prompt versions:

```bash
# Deploy version A to staging
python3 -m prompt_management.manage_prompts create aethon-v2a \
  --content "Version A content..." \
  --environment staging

# Deploy version B to development  
python3 -m prompt_management.manage_prompts create aethon-v2b \
  --content "Version B content..." \
  --environment development

# Compare results
python3 test_prompt_quality.py
```

## 🚨 Emergency Procedures

### Immediate Issues
1. **Rollback to last known good version**
2. **Check Langfuse logs for error patterns**
3. **Verify OpenAI API status**

### Investigation
1. **Review quality test results**
2. **Check configuration changes**
3. **Analyze user feedback patterns**

## 📋 Checklist for Prompt Changes

### Before Development
- [ ] Define clear success criteria
- [ ] Update test cases if needed
- [ ] Document expected changes

### Before Staging
- [ ] All development tests pass
- [ ] Code review completed
- [ ] Version notes documented

### Before Production
- [ ] Staging tests pass (>80%)
- [ ] Manual testing completed
- [ ] Stakeholder approval obtained
- [ ] Rollback plan prepared

### After Production
- [ ] Monitor metrics for 24 hours
- [ ] Collect user feedback
- [ ] Document lessons learned

## 🎓 Best Practices

1. **Version Semantically**: Use semantic versioning (1.0.0, 1.1.0, 2.0.0)
2. **Test Thoroughly**: Never skip staging environment
3. **Document Changes**: Always include meaningful version notes
4. **Monitor Continuously**: Watch metrics after each deployment
5. **Fail Fast**: Use quality gates to catch issues early
6. **Keep History**: Maintain old versions for rollback capability

## 🔗 Quick Reference

```bash
# Health check
python3 -m prompt_management.manage_prompts health

# Create prompt
python3 -m prompt_management.manage_prompts create [name] --content "..." --environment development

# Promote prompt
python3 -m prompt_management.manage_prompts promote [name] --from-env staging --to-env production

# Get prompt
python3 -m prompt_management.manage_prompts get [name] --environment production --show-content

# Test quality
python3 test_prompt_quality.py
```

This workflow ensures **reliable, traceable, and reversible** prompt deployments while maintaining high quality standards. 