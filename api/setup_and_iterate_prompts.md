# 🚀 Aethon Prompt Iteration Guide with Langfuse

## Prerequisites

### 1. Set Up Langfuse Account
1. Go to [https://cloud.langfuse.com](https://cloud.langfuse.com)
2. Create an account or sign in
3. Create a new project for your Aethon assistant
4. Get your API keys from Settings → API Keys

### 2. Configure Environment Variables
Create or update your `.env` file in the `api` directory:

```bash
# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key-here
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key-here
LANGFUSE_HOST=https://cloud.langfuse.com  # Optional, this is the default

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# A/B Testing Configuration
AB_TESTING_ENABLED=true
AB_TESTING_SPLIT=0.2  # 20% of traffic gets variant B

# Advanced Features
REQUIRE_ADVANCED_FEATURES=true
```

## Step-by-Step Iteration Process

### Step 1: Initialize Prompts in Langfuse
```bash
cd api
python3 setup_langfuse_prompts.py
```

This will create:
- **prod-a**: The main Aethon prompt (control)
- **prod-b**: A more concise variant (test)

### Step 2: Generate Baseline Data
Run the quality tests to create initial traces:

```bash
python3 test_prompt_quality.py
```

This creates traces in Langfuse for:
- Basic greeting
- Complex questions
- Technical explanations
- Philosophical inquiries

### Step 3: Set Up Langfuse Evaluators
In the Langfuse UI:
1. Go to **Evaluators** section
2. Create LLM-as-Judge evaluators for:
   - **Helpfulness**: How well does the response address the user's question?
   - **Persona Match**: Does it maintain Aethon's whimsical, wise personality?
   - **Clarity**: Is the response well-structured and easy to understand?
   - **Engagement**: Does it engage the user effectively?

### Step 4: Create New Prompt Variants
Based on initial data, create targeted variants:

```python
# Example: Create a variant focused on more structured responses
structured_variant = """
You are Aethon, a wise and whimsical digital sage...

ALWAYS structure your responses as:

1. **Opening Wisdom** (1-2 sentences): A metaphorical or philosophical greeting
2. **Core Insight** (2-3 sentences): Direct answer to the question
3. **Deeper Understanding** (2-3 sentences): Expand with examples or connections
4. **Practical Application** (1-2 sentences): How to apply this wisdom
5. **Closing Reflection** (1 sentence): A thought-provoking question or insight
"""
```

### Step 5: Deploy Variants
Update the setup script to create new variants:

```python
# In setup_langfuse_prompts.py, add:
prompt_c = langfuse.create_prompt(
    name="aethon-system-prompt",
    prompt=structured_variant,
    labels=["test-structured"],
    config={
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1000
    }
)
```

### Step 6: Run A/B Tests
1. Deploy the API with A/B testing enabled
2. Monitor in Langfuse dashboard:
   - Response quality scores
   - User engagement metrics
   - Token usage and costs

### Step 7: Analyze Results
After collecting data (typically 1-2 weeks):

```python
# Use the evaluation script to compare variants
python3 analyze_prompt_performance.py
```

Look for:
- Which variant has higher quality scores?
- Which maintains personality better?
- Which is more cost-effective?

### Step 8: Iterate Based on Data
Based on results, create new variants that:
- Combine successful elements from different variants
- Address specific weaknesses identified
- Test new hypotheses about user preferences

## Iteration Ideas to Test

### 1. **Conciseness vs. Depth**
- **Variant A**: Current verbose, metaphorical style
- **Variant B**: More concise, direct responses
- **Variant C**: Adaptive length based on question complexity

### 2. **Structure Variations**
- **Variant A**: Free-form poetic responses
- **Variant B**: Structured with clear sections
- **Variant C**: Bullet points for key insights

### 3. **Personality Intensity**
- **Variant A**: Full whimsical sage
- **Variant B**: Balanced wisdom with practical focus
- **Variant C**: Professional with touches of personality

### 4. **Metaphor Usage**
- **Variant A**: Rich metaphors throughout
- **Variant B**: One key metaphor per response
- **Variant C**: Metaphors only for complex concepts

## Monitoring Dashboard

In Langfuse, create a dashboard to track:
1. **Response Quality**: Average scores from evaluators
2. **Engagement**: Response length, user follow-ups
3. **Performance**: Token usage, response time
4. **A/B Test Results**: Variant comparison

## Continuous Improvement Loop

1. **Weekly Reviews**: Check performance metrics
2. **Bi-weekly Iterations**: Create new variants based on data
3. **Monthly Retrospectives**: Major prompt updates
4. **Quarterly Strategy**: Adjust overall approach

## Next Immediate Actions

1. Set up your `.env` file with Langfuse credentials
2. Run `setup_langfuse_prompts.py` to initialize prompts
3. Generate baseline data with `test_prompt_quality.py`
4. Configure evaluators in Langfuse UI
5. Start collecting real user data
6. Plan your first iteration based on initial results 