#!/usr/bin/env python3
"""
Test script to verify API setup locally
"""

import os
import sys
from pathlib import Path

# Add the api directory to Python path
api_dir = Path(__file__).parent
sys.path.insert(0, str(api_dir))

print("🔍 Testing API setup locally...\n")

# Test 1: Environment variables
print("1. Checking environment variables:")
env_vars = [
    "OPENAI_API_KEY",
    "LANGFUSE_PUBLIC_KEY", 
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_HOST"
]

for var in env_vars:
    value = os.getenv(var)
    if value:
        print(f"   ✅ {var} is set (length: {len(value)})")
    else:
        print(f"   ❌ {var} is NOT set")

# Test 2: Import modules
print("\n2. Testing imports:")
try:
    from app_wrapper import app
    print("   ✅ app_wrapper imports successfully")
except Exception as e:
    print(f"   ❌ app_wrapper import failed: {e}")

try:
    from prompt_management.aethon_prompt import AETHON_SYSTEM_PROMPT
    print("   ✅ aethon_prompt imports successfully")
except Exception as e:
    print(f"   ❌ aethon_prompt import failed: {e}")

try:
    from ab_testing.ab_manager import ABTestManager
    print("   ✅ ab_manager imports successfully")
except Exception as e:
    print(f"   ❌ ab_manager import failed: {e}")

# Test 3: Initialize services
print("\n3. Testing service initialization:")
try:
    from app_wrapper import initialize_services
    initialize_services()
    print("   ✅ Services initialized")
    
    from app_wrapper import _langfuse, _ab_manager, _openai_client
    print(f"   - Langfuse: {'✅' if _langfuse else '❌'}")
    print(f"   - AB Manager: {'✅' if _ab_manager else '❌'}")
    print(f"   - OpenAI: {'✅' if _openai_client else '❌'}")
except Exception as e:
    print(f"   ❌ Service initialization failed: {e}")

# Test 4: Test a simple API call
print("\n4. Testing API endpoint:")
try:
    import asyncio
    from app_wrapper import health_check
    
    async def test_health():
        result = await health_check()
        return result
    
    result = asyncio.run(test_health())
    print(f"   ✅ Health check successful: {result}")
except Exception as e:
    print(f"   ❌ Health check failed: {e}")

print("\n�� Test complete!") 