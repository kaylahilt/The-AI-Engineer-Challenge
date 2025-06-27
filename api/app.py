# Import required FastAPI components for building the API
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
# Import Pydantic for data validation and settings management
from pydantic import BaseModel
# Import OpenAI client for interacting with OpenAI's API
from openai import OpenAI
import os
import logging
from typing import Optional
from prompt_management.prompt_manager import PromptManager, PromptEnvironment
import hashlib
import random
from langfuse.openai import openai  # Use Langfuse-wrapped OpenAI client
from langfuse import Langfuse

# Import our custom modules
from ab_testing import ABTestManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI application with a title
app = FastAPI(title="Aethon AI Assistant API")

# Configure CORS (Cross-Origin Resource Sharing) middleware
# This allows the API to be accessed from different domains/origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any origin
    allow_credentials=True,  # Allows cookies to be included in requests
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers in requests
)

# Initialize Langfuse and A/B testing
langfuse = Langfuse()
ab_manager = ABTestManager(langfuse)

# Define the data model for chat requests using Pydantic
# This ensures incoming request data is properly validated
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    prompt_label: Optional[str] = None
    prompt_version: Optional[int] = None

# Initialize the prompt manager for production-ready prompt management
prompt_manager = PromptManager()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define the main chat endpoint that handles POST requests
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint using Langfuse native A/B testing.
    
    This endpoint:
    1. Uses ABTestManager to select prompt variants
    2. Automatically tracks everything in Langfuse
    3. Returns AI responses with experiment metadata
    """
    try:
        # Get prompt variant using our A/B test manager
        prompt, selected_label = ab_manager.get_prompt_variant(
            prompt_name="aethon-system-prompt",
            test_name="aethon-personality"
        )
        
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or f"conv_{hash(request.user_id + request.message)}"
        
        # Compile the prompt (add variables here if your prompt has them)
        system_prompt = prompt.compile()
        
        # Get metadata for Langfuse tracing
        trace_metadata = ab_manager.get_metadata_for_trace(
            test_name="aethon-personality",
            selected_label=selected_label,
            user_id=request.user_id,
            conversation_id=conversation_id
        )
        
        # Use Langfuse-wrapped OpenAI client for automatic tracing and analytics
        response = openai.chat.completions.create(
            model=prompt.config.get("model", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ],
            temperature=prompt.config.get("temperature", 0.7),
            max_tokens=prompt.config.get("max_tokens", 500),
            # 🔑 KEY: Link prompt to generation for Langfuse analytics
            langfuse_prompt=prompt,
            # Add metadata for better tracking
            langfuse_metadata=trace_metadata
        )
        
        ai_response = response.choices[0].message.content
        
        return ChatResponse(
            response=ai_response,
            conversation_id=conversation_id,
            prompt_label=selected_label,
            prompt_version=prompt.version
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

# Define a health check endpoint to verify API status
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "aethon-api"}

@app.get("/api/ab-test/status")
async def get_ab_test_status():
    """Get current A/B test configuration"""
    return ab_manager.get_test_status()

@app.get("/api/ab-test/status/{test_name}")
async def get_specific_test_status(test_name: str):
    """Get status of a specific A/B test"""
    return ab_manager.get_test_status(test_name)

@app.post("/api/ab-test/toggle/{test_name}")
async def toggle_ab_test(test_name: str, enabled: bool):
    """Enable/disable an A/B test"""
    return ab_manager.toggle_test(test_name, enabled)

# Entry point for running the application directly
if __name__ == "__main__":
    import uvicorn
    # Start the server on all network interfaces (0.0.0.0) on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
