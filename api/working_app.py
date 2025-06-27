"""
Working FastAPI app with Aethon functionality - simplified for Vercel
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import logging

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

# Import the system prompt directly
from prompt_management.aethon_prompt import AETHON_SYSTEM_PROMPT

# Define request/response models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    prompt_label: Optional[str] = "local-fallback"
    prompt_version: Optional[int] = 1

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "aethon-api"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Simplified chat endpoint using OpenAI directly with local prompt
    """
    try:
        # For now, use OpenAI directly without Langfuse to isolate the issue
        from openai import OpenAI
        
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Generate conversation ID
        conversation_id = request.conversation_id or f"conv_{hash(request.user_id + request.message)}"
        
        # Use the local system prompt
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
            prompt_version=1
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 