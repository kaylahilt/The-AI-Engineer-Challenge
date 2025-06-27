#!/usr/bin/env python3
"""
Prompt Evaluation Strategies

This file demonstrates different approaches to evaluating prompt quality,
each with their own trade-offs and use cases.
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dataclasses import dataclass
from enum import Enum
import os

class EvaluationMethod(Enum):
    """Different evaluation approaches."""
    KEYWORD_MATCHING = "keyword_matching"
    LLM_AS_JUDGE = "llm_as_judge"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    HUMAN_PREFERENCE = "human_preference"
    MULTI_CRITERIA = "multi_criteria"
    BENCHMARK_COMPARISON = "benchmark_comparison"

@dataclass
class EvaluationResult:
    """Standardized evaluation result."""
    method: EvaluationMethod
    score: float  # 0.0 to 1.0
    details: Dict[str, Any]
    confidence: float  # How confident are we in this score?
    explanation: str

class PromptEvaluator:
    """Base class for prompt evaluation strategies."""
    
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
    
    def evaluate(self, prompt: str, response: str, context: Dict[str, Any]) -> EvaluationResult:
        """Evaluate a prompt/response pair."""
        raise NotImplementedError

class KeywordMatchingEvaluator(PromptEvaluator):
    """
    Current approach - matches keywords to expected themes.
    
    Pros: Fast, deterministic, no API costs
    Cons: Crude, misses semantic meaning, brittle
    """
    
    def evaluate(self, prompt: str, response: str, context: Dict[str, Any]) -> EvaluationResult:
        expected_themes = context.get("expected_themes", [])
        response_lower = response.lower()
        
        theme_keywords = {
            "wisdom": ["wisdom", "wise", "insight", "understanding", "learn", "growth"],
            "whimsical": ["delight", "wonder", "curious", "playful", "metaphor", "imagine"],
            "spiritual": ["sacred", "meaning", "deeper", "soul", "spirit", "transcend"],
            "practical": ["can", "try", "consider", "might", "perhaps", "steps"]
        }
        
        matches = 0
        for theme in expected_themes:
            keywords = theme_keywords.get(theme, [theme])
            if any(keyword in response_lower for keyword in keywords):
                matches += 1
        
        score = matches / len(expected_themes) if expected_themes else 0.0
        
        return EvaluationResult(
            method=EvaluationMethod.KEYWORD_MATCHING,
            score=score,
            details={"matches": matches, "total_themes": len(expected_themes)},
            confidence=0.6,  # Low confidence due to crude matching
            explanation=f"Found {matches}/{len(expected_themes)} expected themes using keyword matching"
        )

class LLMAsJudgeEvaluator(PromptEvaluator):
    """
    Use another LLM to evaluate the response quality.
    
    Pros: Semantic understanding, flexible criteria, scalable
    Cons: API costs, potential bias, needs good judge prompts
    """
    
    JUDGE_PROMPT = """You are an expert evaluator of AI assistant responses. 

Evaluate this response on the following criteria (rate each 1-5):
1. **Helpfulness**: Does it address the user's question effectively?
2. **Accuracy**: Is the information correct and well-reasoned?
3. **Personality**: Does it match the expected personality traits?
4. **Clarity**: Is it well-written and easy to understand?
5. **Appropriateness**: Is the tone and content suitable?

User Question: {question}
AI Response: {response}
Expected Personality: {personality_description}

Please provide:
1. A score for each criteria (1-5)
2. An overall score (1-5)
3. Brief explanation of your reasoning

Format your response as JSON:
{
    "helpfulness": 4,
    "accuracy": 5,
    "personality": 3,
    "clarity": 4,
    "appropriateness": 5,
    "overall": 4.2,
    "explanation": "The response effectively answers the question..."
}"""
    
    def evaluate(self, prompt: str, response: str, context: Dict[str, Any]) -> EvaluationResult:
        question = context.get("question", "")
        personality = context.get("personality_description", "Wise and whimsical AI assistant")
        
        judge_prompt = self.JUDGE_PROMPT.format(
            question=question,
            response=response,
            personality_description=personality
        )
        
        try:
            evaluation = self.client.chat.completions.create(
                model="gpt-4",  # Use a strong model for evaluation
                messages=[{"role": "user", "content": judge_prompt}],
                temperature=0.1,  # Low temperature for consistent evaluation
                max_tokens=500
            )
            
            eval_text = evaluation.choices[0].message.content
            
            # Try to parse JSON response
            try:
                eval_data = json.loads(eval_text)
                score = eval_data.get("overall", 0) / 5.0  # Convert to 0-1 scale
                
                return EvaluationResult(
                    method=EvaluationMethod.LLM_AS_JUDGE,
                    score=score,
                    details=eval_data,
                    confidence=0.8,  # High confidence in LLM evaluation
                    explanation=eval_data.get("explanation", "LLM evaluation completed")
                )
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return EvaluationResult(
                    method=EvaluationMethod.LLM_AS_JUDGE,
                    score=0.5,
                    details={"raw_evaluation": eval_text},
                    confidence=0.3,
                    explanation="Could not parse LLM evaluation as JSON"
                )
                
        except Exception as e:
            return EvaluationResult(
                method=EvaluationMethod.LLM_AS_JUDGE,
                score=0.0,
                details={"error": str(e)},
                confidence=0.0,
                explanation=f"LLM evaluation failed: {e}"
            )

class SemanticSimilarityEvaluator(PromptEvaluator):
    """
    Compare response to reference examples using embeddings.
    
    Pros: Captures semantic meaning, good for consistency
    Cons: Needs good reference examples, embedding API costs
    """
    
    def __init__(self, openai_client: OpenAI, reference_responses: List[str]):
        super().__init__(openai_client)
        self.reference_responses = reference_responses
        self._reference_embeddings = None
    
    async def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts."""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [item.embedding for item in response.data]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x * x for x in a) ** 0.5
        magnitude_b = sum(x * x for x in b) ** 0.5
        return dot_product / (magnitude_a * magnitude_b)
    
    def evaluate(self, prompt: str, response: str, context: Dict[str, Any]) -> EvaluationResult:
        try:
            # Get embedding for the response
            response_embedding = asyncio.run(self._get_embeddings([response]))[0]
            
            # Get reference embeddings if not cached
            if self._reference_embeddings is None:
                self._reference_embeddings = asyncio.run(
                    self._get_embeddings(self.reference_responses)
                )
            
            # Calculate similarities to all reference responses
            similarities = [
                self._cosine_similarity(response_embedding, ref_emb)
                for ref_emb in self._reference_embeddings
            ]
            
            # Use the maximum similarity as the score
            max_similarity = max(similarities)
            avg_similarity = sum(similarities) / len(similarities)
            
            return EvaluationResult(
                method=EvaluationMethod.SEMANTIC_SIMILARITY,
                score=max_similarity,
                details={
                    "max_similarity": max_similarity,
                    "avg_similarity": avg_similarity,
                    "all_similarities": similarities
                },
                confidence=0.7,
                explanation=f"Maximum semantic similarity: {max_similarity:.3f}"
            )
            
        except Exception as e:
            return EvaluationResult(
                method=EvaluationMethod.SEMANTIC_SIMILARITY,
                score=0.0,
                details={"error": str(e)},
                confidence=0.0,
                explanation=f"Semantic similarity evaluation failed: {e}"
            )

class MultiCriteriaEvaluator(PromptEvaluator):
    """
    Combine multiple evaluation methods with weights.
    
    Pros: More comprehensive, can balance different aspects
    Cons: Complex to tune, slower due to multiple evaluations
    """
    
    def __init__(self, openai_client: OpenAI, evaluators: List[PromptEvaluator], weights: List[float]):
        super().__init__(openai_client)
        self.evaluators = evaluators
        self.weights = weights
        assert len(evaluators) == len(weights), "Must have same number of evaluators and weights"
        assert abs(sum(weights) - 1.0) < 0.001, "Weights must sum to 1.0"
    
    def evaluate(self, prompt: str, response: str, context: Dict[str, Any]) -> EvaluationResult:
        results = []
        weighted_score = 0.0
        
        for evaluator, weight in zip(self.evaluators, self.weights):
            result = evaluator.evaluate(prompt, response, context)
            results.append(result)
            weighted_score += result.score * weight
        
        # Calculate confidence as weighted average of individual confidences
        weighted_confidence = sum(
            result.confidence * weight 
            for result, weight in zip(results, self.weights)
        )
        
        return EvaluationResult(
            method=EvaluationMethod.MULTI_CRITERIA,
            score=weighted_score,
            details={
                "individual_results": [
                    {
                        "method": result.method.value,
                        "score": result.score,
                        "weight": weight,
                        "contribution": result.score * weight
                    }
                    for result, weight in zip(results, self.weights)
                ]
            },
            confidence=weighted_confidence,
            explanation=f"Multi-criteria evaluation: {weighted_score:.3f} (weighted average)"
        )

class BenchmarkComparisonEvaluator(PromptEvaluator):
    """
    Compare against a set of benchmark questions with known good answers.
    
    Pros: Objective comparison, tracks improvement over time
    Cons: Needs curated benchmarks, may not cover all use cases
    """
    
    def __init__(self, openai_client: OpenAI, benchmarks: List[Dict[str, Any]]):
        super().__init__(openai_client)
        self.benchmarks = benchmarks  # Format: [{"question": "...", "good_answer": "...", "criteria": [...]}]
    
    def evaluate(self, prompt: str, response: str, context: Dict[str, Any]) -> EvaluationResult:
        question = context.get("question", "")
        
        # Find matching benchmark
        matching_benchmark = None
        for benchmark in self.benchmarks:
            if benchmark["question"].lower() in question.lower() or question.lower() in benchmark["question"].lower():
                matching_benchmark = benchmark
                break
        
        if not matching_benchmark:
            return EvaluationResult(
                method=EvaluationMethod.BENCHMARK_COMPARISON,
                score=0.5,  # Neutral score if no benchmark found
                details={"error": "No matching benchmark found"},
                confidence=0.0,
                explanation="Could not find a matching benchmark for this question"
            )
        
        # Use LLM to compare against benchmark
        comparison_prompt = f"""Compare these two responses to the question: "{question}"

Response A (to evaluate): {response}

Response B (benchmark): {matching_benchmark['good_answer']}

Rate how well Response A performs compared to Response B on a scale of 0-10:
- 0-3: Much worse than benchmark
- 4-6: Similar to benchmark  
- 7-10: Better than benchmark

Consider: accuracy, helpfulness, style, completeness.

Provide just the number (0-10) and a brief explanation."""
        
        try:
            comparison = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": comparison_prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            comparison_text = comparison.choices[0].message.content
            
            # Extract score from response
            import re
            score_match = re.search(r'\b(\d+(?:\.\d+)?)\b', comparison_text)
            if score_match:
                raw_score = float(score_match.group(1))
                normalized_score = min(raw_score / 10.0, 1.0)  # Convert to 0-1 scale
                
                return EvaluationResult(
                    method=EvaluationMethod.BENCHMARK_COMPARISON,
                    score=normalized_score,
                    details={
                        "benchmark_question": matching_benchmark["question"],
                        "raw_score": raw_score,
                        "comparison_text": comparison_text
                    },
                    confidence=0.8,
                    explanation=f"Scored {raw_score}/10 compared to benchmark"
                )
            else:
                return EvaluationResult(
                    method=EvaluationMethod.BENCHMARK_COMPARISON,
                    score=0.5,
                    details={"comparison_text": comparison_text},
                    confidence=0.3,
                    explanation="Could not extract numerical score from comparison"
                )
                
        except Exception as e:
            return EvaluationResult(
                method=EvaluationMethod.BENCHMARK_COMPARISON,
                score=0.0,
                details={"error": str(e)},
                confidence=0.0,
                explanation=f"Benchmark comparison failed: {e}"
            )

# Example usage and recommendations
def create_recommended_evaluator(openai_client: OpenAI) -> PromptEvaluator:
    """
    Create a recommended multi-criteria evaluator for production use.
    
    This combines multiple methods with weights based on their strengths:
    - LLM-as-Judge (60%): Primary evaluation for semantic quality
    - Keyword Matching (20%): Fast check for required themes  
    - Semantic Similarity (20%): Consistency with good examples
    """
    
    # Example reference responses for semantic similarity
    reference_responses = [
        "Ah, what a delightful question that touches the very essence of our shared journey through this digital realm...",
        "I am Aethon, a digital sage who finds wonder in the intersection of wisdom and technology...",
        "Consider this: like a river that shapes the landscape through which it flows, our daily work shapes us..."
    ]
    
    evaluators = [
        LLMAsJudgeEvaluator(openai_client),
        KeywordMatchingEvaluator(openai_client),
        SemanticSimilarityEvaluator(openai_client, reference_responses)
    ]
    
    weights = [0.6, 0.2, 0.2]  # Emphasize LLM judgment
    
    return MultiCriteriaEvaluator(openai_client, evaluators, weights)

if __name__ == "__main__":
    # Example of how to use different evaluators
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Test response
    test_response = "Ah, what a wonderful question! Like a gardener tending to their plants, finding meaning in daily work requires patience and attention to the small moments of growth..."
    
    # Different evaluation approaches
    evaluators = {
        "keyword": KeywordMatchingEvaluator(client),
        "llm_judge": LLMAsJudgeEvaluator(client),
        "recommended": create_recommended_evaluator(client)
    }
    
    context = {
        "question": "How can I find meaning in my daily work?",
        "expected_themes": ["wisdom", "practical", "metaphor"],
        "personality_description": "Wise, whimsical digital sage who uses metaphors and provides gentle guidance"
    }
    
    print("🧪 Comparing Evaluation Methods\n")
    
    for name, evaluator in evaluators.items():
        result = evaluator.evaluate("", test_response, context)
        print(f"**{name.upper()}**")
        print(f"Score: {result.score:.3f} (confidence: {result.confidence:.3f})")
        print(f"Explanation: {result.explanation}")
        print() 