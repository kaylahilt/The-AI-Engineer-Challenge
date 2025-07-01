"""
Wrapper for the FastAPI app to handle serverless initialization
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

# Create the FastAPI app
app = FastAPI(title="Aethon AI Assistant API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for lazy initialization
_initialized = False
_langfuse = None
_ab_manager = None
_prompt_manager = None
_openai_client = None

def initialize_services():
    """Initialize services lazily on first request"""
    global _initialized, _langfuse, _ab_manager, _prompt_manager, _openai_client
    
    if _initialized:
        return
    
    logger.info("Initializing services...")
    
    # Check if we should require advanced features
    REQUIRE_ADVANCED_FEATURES = os.getenv("REQUIRE_ADVANCED_FEATURES", "true").lower() == "true"
    
    # Initialize OpenAI client
    try:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info("OpenAI client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        _openai_client = None
    
    # Initialize advanced features
    try:
        from langfuse import Langfuse
        from ab_testing.ab_manager import ABTestManager
        from prompt_management.prompt_manager import PromptManager
        
        _langfuse = Langfuse()
        _ab_manager = ABTestManager(_langfuse)
        _prompt_manager = PromptManager()
        logger.info("Advanced features (Langfuse, A/B testing) initialized successfully")
    except Exception as e:
        error_msg = f"Advanced features not available: {e}"
        if REQUIRE_ADVANCED_FEATURES:
            logger.error(error_msg)
            # Don't raise here, let endpoints handle the error
        else:
            logger.warning(f"{error_msg}. Using fallback mode.")
    
    _initialized = True

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
    mode: Optional[str] = None

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Aethon AI Assistant API"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    initialize_services()
    return {
        "status": "healthy", 
        "service": "aethon-api",
        "features": {
            "langfuse": _langfuse is not None,
            "ab_testing": _ab_manager is not None,
            "openai": _openai_client is not None
        }
    }

@app.get("/api/health")
async def api_health_check():
    """API health check endpoint"""
    initialize_services()
    return {
        "status": "healthy", 
        "service": "aethon-api",
        "version": "wrapped",
        "features": {
            "langfuse": _langfuse is not None,
            "ab_testing": _ab_manager is not None,
            "openai": _openai_client is not None
        }
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint"""
    initialize_services()
    
    if not _openai_client:
        raise HTTPException(status_code=500, detail="OpenAI client not available. Please check OPENAI_API_KEY.")
    
    if not _ab_manager or not _langfuse:
        # Fallback to basic mode
        return await _chat_basic_mode(request)
    
    try:
        # Generate conversation ID
        conversation_id = request.conversation_id or f"conv_{abs(hash(request.user_id + request.message))}"
        
        # Use advanced mode with Langfuse
        return await _chat_advanced_mode(request, conversation_id)
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        # Fallback to basic mode
        return await _chat_basic_mode(request)

async def _chat_basic_mode(request: ChatRequest) -> ChatResponse:
    """Basic chat mode without Langfuse"""
    try:
        from openai import OpenAI
        from prompt_management.aethon_prompt import AETHON_SYSTEM_PROMPT
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": AETHON_SYSTEM_PROMPT},
                {"role": "user", "content": request.message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return ChatResponse(
            response=response.choices[0].message.content,
            conversation_id=f"conv_{abs(hash(request.user_id + request.message))}",
            prompt_label="fallback",
            prompt_version=0,
            mode="basic"
        )
    except Exception as e:
        logger.error(f"Basic mode error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

async def _chat_advanced_mode(request: ChatRequest, conversation_id: str) -> ChatResponse:
    """Advanced chat mode with A/B testing and Langfuse tracking"""
    try:
        from langfuse.openai import openai as langfuse_openai
        
        # Get prompt variant using A/B test manager
        prompt, selected_version = _ab_manager.get_prompt_variant(
            prompt_name="aethon-system-prompt",
            test_name="aethon-personality"
        )
        
        # Compile the prompt
        system_prompt = prompt.compile()
        
        # Get metadata for Langfuse tracing
        trace_metadata = _ab_manager.get_metadata_for_trace(
            test_name="aethon-personality",
            selected_version=selected_version,
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
            prompt_label=f"version-{selected_version}",
            prompt_version=selected_version if isinstance(selected_version, int) else prompt.version,
            mode="advanced"
        )
        
    except Exception as e:
        logger.error(f"Advanced mode error: {e}")
        raise HTTPException(status_code=500, detail=f"Error in advanced mode: {str(e)}") 