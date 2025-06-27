# Langfuse Setup & Prompt Quality Measurement

## Overview

Langfuse is our observability platform for tracking prompt changes, measuring quality improvements, and running A/B tests. When properly configured, it automatically captures:

- Every prompt version change
- User interactions and responses
- Performance metrics
- Quality scores through LLM-as-Judge evaluators

## Setup Instructions

### 1. Create Langfuse Account

1. Go to [https://cloud.langfuse.com](https://cloud.langfuse.com)
2. Sign up for a free account
3. Create a new project for "Aethon AI Assistant"

### 2. Get API Keys

In your Langfuse project dashboard:
1. Navigate to Settings → API Keys
2. Create a new API key pair
3. Copy the Public and Secret keys

### 3. Configure Environment Variables

Add these to your Vercel project:

```bash
# Required
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# Optional (defaults to cloud.langfuse.com)
LANGFUSE_HOST=https://cloud.langfuse.com

# Control whether advanced features are required
REQUIRE_ADVANCED_FEATURES=true
```

### 4. Set Up in Vercel

```bash
vercel env add LANGFUSE_PUBLIC_KEY production
vercel env add LANGFUSE_SECRET_KEY production
vercel env add REQUIRE_ADVANCED_FEATURES production
```

## Measuring Prompt Quality Improvements

### 1. Automatic Tracking

With Langfuse configured, every chat interaction automatically tracks:

- **Prompt Version**: Which version of Aethon's prompt was used
- **Response Time**: How long the generation took
- **Token Usage**: Cost metrics
- **User ID**: For cohort analysis
- **Conversation ID**: For session tracking

### 2. Setting Up Quality Evaluators

In Langfuse Dashboard:

1. Go to "Evaluators" section
2. Create these LLM-as-Judge evaluators:

#### Clarity Score (0-10)
```
Evaluate if the response clearly explains the concept.
- Does it start with the core concept?
- Is the explanation structured?
- Are technical terms properly explained?
```

#### Helpfulness Score (0-10)
```
Evaluate if the response is helpful to the user.
- Does it answer the question asked?
- Is it at the appropriate level?
- Does it provide actionable information?
```

#### Personality Balance Score (0-10)
```
Evaluate the personality balance.
- Is it engaging without being overwhelming?
- Do metaphors enhance understanding?
- Is the tone appropriate?
```

### 3. Comparing Prompt Versions

1. **Deploy New Prompt Version**
   - Make changes to `aethon_prompt.py`
   - Deploy to production
   - Langfuse automatically assigns version numbers

2. **Collect Data**
   - Let the system run for 100-200 conversations
   - Ensure mix of different question types

3. **Analyze in Langfuse**
   - Go to "Prompts" → "aethon-system-prompt"
   - Compare versions side-by-side
   - View aggregate scores for each evaluator

### 4. Key Metrics to Track

| Metric | What It Measures | Target |
|--------|------------------|--------|
| Clarity Score | How clear the explanation is | > 8.0 |
| Helpfulness | Did it answer the question | > 8.5 |
| Personality Balance | Right amount of whimsy | 7.0-8.0 |
| Response Length | Tokens in response | 150-400 |
| User Satisfaction | Manual feedback scores | > 4.5/5 |

### 5. A/B Testing

When enabled, the system automatically:
1. Splits traffic between prompt versions
2. Tracks performance by variant
3. Provides statistical significance

## Troubleshooting

### "Advanced features not available" Error

This means Langfuse couldn't initialize. Check:

1. **Environment Variables**: Ensure all are set correctly
2. **API Keys**: Verify they're valid in Langfuse dashboard
3. **Network**: Ensure Vercel can reach cloud.langfuse.com

### Fallback Mode

If you need to run without Langfuse temporarily:
```bash
vercel env add REQUIRE_ADVANCED_FEATURES production
# Enter: false
```

## Best Practices

1. **Version Control**: Always commit prompt changes with descriptive messages
2. **Testing**: Run `test_prompt_quality.py` locally before deploying
3. **Gradual Rollout**: Use A/B testing for major changes
4. **Monitor**: Check Langfuse dashboard daily during changes
5. **Iterate**: Use data to guide improvements

## Example Workflow

1. **Baseline**: Current prompt is v1, averaging 7.5 clarity score
2. **Hypothesis**: Adding structure will improve clarity
3. **Change**: Update prompt with structural guidelines
4. **Deploy**: New version (v2) goes live
5. **Measure**: After 200 conversations, v2 averages 8.7 clarity
6. **Decision**: 16% improvement validates the change
7. **Document**: Record what worked for future iterations 