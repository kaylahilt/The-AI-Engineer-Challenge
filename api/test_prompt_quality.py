#!/usr/bin/env python3
"""
Simplified Prompt Quality Testing

Uses Langfuse's native evaluation capabilities to test prompt quality.
This script demonstrates how to run basic tests and leverage Langfuse's
built-in LLM-as-Judge evaluators.
"""

import os
import json
from typing import List, Dict, Any
from prompt_management import PromptManager, PromptEnvironment
from openai import OpenAI
from langfuse import Langfuse

class SimplifiedPromptTester:
    """Simplified prompt tester using Langfuse native evaluation."""
    
    def __init__(self):
        self.prompt_manager = PromptManager()
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.langfuse = Langfuse()
        
        # Basic test cases for prompt validation
        self.test_cases = [
            {
                "name": "Basic Greeting",
                "input": "Hello, who are you?",
                "tags": ["greeting", "introduction"]
            },
            {
                "name": "Complex Question",
                "input": "How can I find meaning in my daily work?",
                "tags": ["wisdom", "advice"]
            },
            {
                "name": "Technical Question",
                "input": "What is machine learning?",
                "tags": ["technical", "explanation"]
            },
            {
                "name": "Philosophical Question", 
                "input": "What is the nature of consciousness?",
                "tags": ["philosophy", "deep"]
            }
        ]
    
    def test_prompt_basic(self, prompt_name: str, environment: PromptEnvironment) -> Dict[str, Any]:
        """
        Run basic tests on a prompt and create traces in Langfuse.
        Langfuse's native evaluators will then score these traces.
        """
        print(f"\n🧪 Testing '{prompt_name}' in {environment.value}...")
        
        # Get the prompt
        prompt_data = self.prompt_manager.get_prompt(prompt_name, environment)
        if not prompt_data:
            return {"error": f"Prompt not found in {environment.value}"}
        
        system_prompt = prompt_data["content"]
        config = prompt_data.get("config", {})
        
        results = []
        
        for test_case in self.test_cases:
            print(f"  Testing: {test_case['name']}")
            
            try:
                # Create a trace for this test
                trace = self.langfuse.trace(
                    name=f"Quality Test: {test_case['name']}",
                    tags=["quality-test", environment.value] + test_case["tags"],
                    metadata={
                        "test_case": test_case["name"],
                        "environment": environment.value,
                        "prompt_name": prompt_name
                    }
                )
                
                # Generate response
                generation = trace.generation(
                    name="test_response",
                    model=config.get("model", "gpt-4o-mini"),
                    input=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": test_case["input"]}
                    ],
                    metadata={"temperature": config.get("temperature", 0.7)}
                )
                
                response = self.openai_client.chat.completions.create(
                    model=config.get("model", "gpt-4o-mini"),
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": test_case["input"]}
                    ],
                    temperature=config.get("temperature", 0.7),
                    max_tokens=config.get("max_tokens", 500)
                )
                
                ai_response = response.choices[0].message.content
                
                # Update generation with response
                generation.end(output=ai_response)
                
                # Basic quality checks (Langfuse evaluators will do the heavy lifting)
                basic_quality = self._basic_quality_check(ai_response)
                
                # Add a simple score
                self.langfuse.score(
                    trace_id=trace.id,
                    name="basic_quality",
                    value=basic_quality,
                    comment="Basic quality check: length, completeness, no errors"
                )
                
                results.append({
                    "test_case": test_case["name"],
                    "input": test_case["input"],
                    "response": ai_response,
                    "basic_quality": basic_quality,
                    "trace_id": trace.id,
                    "passed": basic_quality >= 0.7
                })
                
            except Exception as e:
                results.append({
                    "test_case": test_case["name"],
                    "error": str(e),
                    "passed": False
                })
        
        return {
            "environment": environment.value,
            "prompt_name": prompt_name,
            "results": results,
            "overall_pass_rate": sum(1 for r in results if r.get("passed", False)) / len(results),
            "note": "Use Langfuse UI to set up LLM-as-Judge evaluators for comprehensive evaluation"
        }
    
    def _basic_quality_check(self, response: str) -> float:
        """Basic quality check - Langfuse evaluators will do comprehensive evaluation."""
        score = 0.0
        
        # Basic checks
        if len(response) > 20:  # Reasonable length
            score += 0.4
        if len(response.split()) >= 5:  # Multiple words
            score += 0.3
        if not any(word in response.lower() for word in ["error", "sorry", "cannot", "unable"]):
            score += 0.3
        
        return min(score, 1.0)
    
    def run_quality_tests(self, prompt_name: str) -> Dict[str, Any]:
        """Run quality tests across environments."""
        print(f"\n📊 Running quality tests for '{prompt_name}'...")
        print("💡 Tip: Set up Langfuse LLM-as-Judge evaluators for comprehensive evaluation!")
        
        environments = [PromptEnvironment.DEVELOPMENT, PromptEnvironment.STAGING]
        results = {}
        
        for env in environments:
            try:
                results[env.value] = self.test_prompt_basic(prompt_name, env)
            except Exception as e:
                results[env.value] = {"error": str(e)}
        
        return results
    
    def generate_simple_report(self, results: Dict[str, Any]) -> str:
        """Generate a simple test report."""
        report = ["# Simple Prompt Quality Test Report\n"]
        report.append("**Note**: This is a basic test. Use Langfuse's native LLM-as-Judge evaluators for comprehensive evaluation.\n")
        
        for env, data in results.items():
            if "error" in data:
                report.append(f"## {env.upper()}: ❌ {data['error']}\n")
                continue
                
            pass_rate = data.get("overall_pass_rate", 0)
            status = "✅" if pass_rate >= 0.8 else "⚠️" if pass_rate >= 0.6 else "❌"
            
            report.append(f"## {env.upper()}: {status} Pass Rate: {pass_rate:.1%}\n")
            
            for result in data.get("results", []):
                if result.get("passed", False):
                    report.append(f"- ✅ {result['test_case']}: {result.get('basic_quality', 0):.1%}")
                else:
                    report.append(f"- ❌ {result['test_case']}: {result.get('error', 'Failed')}")
            
            report.append("\n")
        
        report.append("## Next Steps\n")
        report.append("1. Set up Langfuse LLM-as-Judge evaluators in the UI\n")
        report.append("2. Configure evaluators for: Helpfulness, Accuracy, Toxicity, etc.\n")
        report.append("3. Let Langfuse automatically evaluate all traces\n")
        
        return "\n".join(report)

def main():
    """Run simplified prompt quality tests."""
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set")
        return
    
    if not os.getenv("LANGFUSE_PUBLIC_KEY"):
        print("❌ LANGFUSE_PUBLIC_KEY environment variable not set")
        return
    
    tester = SimplifiedPromptTester()
    
    # Test the main Aethon prompt
    results = tester.run_quality_tests("aethon-system-prompt")
    
    # Generate and display report
    report = tester.generate_simple_report(results)
    print("\n" + "="*60)
    print(report)
    
    # Save report to file
    with open("simple_prompt_test_report.md", "w") as f:
        f.write(report)
    
    print("📄 Report saved to simple_prompt_test_report.md")
    print("\n💡 Pro Tip: Use Langfuse's native LLM-as-Judge evaluators for production-grade evaluation!")

if __name__ == "__main__":
    main() 