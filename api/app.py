"""
Consolidated Aethon AI Assistant API
Combines reliability, functionality, and proper error handling
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import logging
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(title="Aethon AI Assistant API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import the Aethon system prompt
try:
    from prompt_management.aethon_prompt import AETHON_SYSTEM_PROMPT
    logger.info("Successfully imported Aethon system prompt")
except ImportError as e:
    logger.warning(f"Could not import Aethon prompt: {e}")
    # Fallback prompt if import fails
    AETHON_SYSTEM_PROMPT = """You are Aethon, a wise and helpful AI assistant. 
    You provide thoughtful, accurate responses while maintaining a warm and engaging personality."""

# Initialize advanced features with fallbacks
langfuse = None
ab_manager = None
prompt_manager = None

# Check if we should require advanced features
REQUIRE_ADVANCED_FEATURES = os.getenv("REQUIRE_ADVANCED_FEATURES", "true").lower() == "true"

try:
    # Try to initialize Langfuse and A/B testing
    from langfuse import Langfuse
    from ab_testing.ab_manager import ABTestManager
    from prompt_management.prompt_manager import PromptManager
    
    langfuse = Langfuse()
    ab_manager = ABTestManager(langfuse)
    prompt_manager = PromptManager()
    logger.info("Advanced features (Langfuse, A/B testing) initialized successfully")
except Exception as e:
    error_msg = f"Advanced features not available: {e}"
    if REQUIRE_ADVANCED_FEATURES:
        logger.error(error_msg)
        raise RuntimeError(
            f"{error_msg}\n"
            "Required environment variables:\n"
            "- LANGFUSE_PUBLIC_KEY\n"
            "- LANGFUSE_SECRET_KEY\n"
            "- LANGFUSE_HOST (optional, defaults to https://cloud.langfuse.com)\n"
            "Set REQUIRE_ADVANCED_FEATURES=false to run in fallback mode."
        )
    else:
        logger.warning(f"{error_msg}. Using fallback mode.")

# Initialize OpenAI client
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    logger.info("OpenAI client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")
    openai_client = None

# Define request/response models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    prompt_label: Optional[str] = None
    prompt_version: Optional[int] = None
    mode: Optional[str] = None  # Indicates which mode was used (advanced/fallback)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "aethon-api",
        "features": {
            "langfuse": langfuse is not None,
            "ab_testing": ab_manager is not None,
            "openai": openai_client is not None
        }
    }

@app.get("/api/health")
async def api_health_check():
    """API health check endpoint"""
    return {
        "status": "healthy", 
        "service": "aethon-api",
        "version": "consolidated",
        "features": {
            "langfuse": langfuse is not None,
            "ab_testing": ab_manager is not None,
            "openai": openai_client is not None
        }
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Consolidated chat endpoint with advanced features and fallbacks
    """
    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenAI client not available")
    
    try:
        # Generate conversation ID
        conversation_id = request.conversation_id or f"conv_{abs(hash(request.user_id + request.message))}"
        
        # Try advanced mode first (with A/B testing and Langfuse)
        if ab_manager and langfuse:
            try:
                return await _chat_advanced_mode(request, conversation_id)
            except Exception as e:
                logger.warning(f"Advanced mode failed: {e}. Falling back to simple mode.")
        
        # Fallback to simple mode
        return await _chat_simple_mode(request, conversation_id)
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

async def _chat_advanced_mode(request: ChatRequest, conversation_id: str) -> ChatResponse:
    """Advanced chat mode with A/B testing and Langfuse tracking"""
    try:
        from langfuse.openai import openai as langfuse_openai
        
        # Get prompt variant using A/B test manager
        prompt, selected_label = ab_manager.get_prompt_variant(
            prompt_name="aethon-system-prompt",
            test_name="aethon-personality"
        )
        
        # Compile the prompt
        system_prompt = prompt.compile()
        
        # Get metadata for Langfuse tracing
        trace_metadata = ab_manager.get_metadata_for_trace(
            test_name="aethon-personality",
            selected_label=selected_label,
            user_id=request.user_id,
            conversation_id=conversation_id
        )
        
        # Use Langfuse-wrapped OpenAI client
        response = langfuse_openai.chat.completions.create(
            model=prompt.config.get("model", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ],
            temperature=prompt.config.get("temperature", 0.7),
            max_tokens=prompt.config.get("max_tokens", 1000),
            langfuse_prompt=prompt,
            langfuse_metadata=trace_metadata
        )
        
        ai_response = response.choices[0].message.content
        
        return ChatResponse(
            response=ai_response,
            conversation_id=conversation_id,
            prompt_label=selected_label,
            prompt_version=prompt.version,
            mode="advanced"
        )
        
    except Exception as e:
        logger.error(f"Advanced mode error: {e}")
        raise

async def _chat_simple_mode(request: ChatRequest, conversation_id: str) -> ChatResponse:
    """Simple chat mode using direct OpenAI integration"""
    try:
        # Use the local Aethon system prompt
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": AETHON_SYSTEM_PROMPT},
                {"role": "user", "content": request.message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content
        
        return ChatResponse(
            response=ai_response,
            conversation_id=conversation_id,
            prompt_label="local-aethon",
            prompt_version=1,
            mode="simple"
        )
        
    except Exception as e:
        logger.error(f"Simple mode error: {e}")
        raise

# A/B Testing endpoints (only available if advanced features are loaded)
@app.get("/api/ab-test/status")
async def get_ab_test_status():
    """Get current A/B test configuration"""
    if not ab_manager:
        return {"error": "A/B testing not available", "mode": "simple"}
    return ab_manager.get_test_status()

@app.get("/api/ab-test/status/{test_name}")
async def get_specific_test_status(test_name: str):
    """Get status of a specific A/B test"""
    if not ab_manager:
        return {"error": "A/B testing not available", "mode": "simple"}
    return ab_manager.get_test_status(test_name)

@app.post("/api/ab-test/toggle/{test_name}")
async def toggle_ab_test(test_name: str, enabled: bool):
    """Enable/disable an A/B test"""
    if not ab_manager:
        raise HTTPException(status_code=503, detail="A/B testing not available")
    return ab_manager.toggle_test(test_name, enabled)

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
