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
from prompt_management import PromptManager, PromptEnvironment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI application with a title
app = FastAPI(title="OpenAI Chat API")

# Configure CORS (Cross-Origin Resource Sharing) middleware
# This allows the API to be accessed from different domains/origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any origin
    allow_credentials=True,  # Allows cookies to be included in requests
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers in requests
)

# Define the data model for chat requests using Pydantic
# This ensures incoming request data is properly validated
class ChatRequest(BaseModel):
    user_message: str      # Message from the user
    model: Optional[str] = "gpt-4.1-nano"  # Optional model selection with default

# Initialize the prompt manager for production-ready prompt management
prompt_manager = PromptManager()

# Define the main chat endpoint that handles POST requests
@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        # Get OpenAI API key from environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Get the system prompt from Langfuse (no fallback - fail fast if not configured)
        prompt_data = prompt_manager.get_prompt(
            name="aethon-system-prompt",
            environment=PromptEnvironment.PRODUCTION
        )
        
        if not prompt_data:
            logger.error("Aethon system prompt not found in Langfuse production environment")
            raise HTTPException(
                status_code=503, 
                detail="AI system is temporarily unavailable. Please ensure prompts are properly configured in Langfuse."
            )
        
        system_prompt = prompt_data["content"]
        # Use configuration from Langfuse
        prompt_config = prompt_data.get("config", {})
        model = prompt_config.get("model", request.model)
        temperature = prompt_config.get("temperature", 0.7)
        max_tokens = prompt_config.get("max_tokens", 1000)
        
        logger.info(f"Using prompt version: {prompt_data['version']}, model: {model}, temp: {temperature}")
        
        # Initialize OpenAI client with the environment API key
        client = OpenAI(api_key=api_key)
        
        # Create an async generator function for streaming responses
        async def generate():
            # Create a streaming chat completion request with the managed system prompt
            stream = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True  # Enable streaming response
            )
            
            # Yield each chunk of the response as it becomes available
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        # Return a streaming response to the client
        return StreamingResponse(generate(), media_type="text/plain")
    
    except Exception as e:
        # Handle any errors that occur during processing
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Define a health check endpoint to verify API status
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Entry point for running the application directly
if __name__ == "__main__":
    import uvicorn
    # Start the server on all network interfaces (0.0.0.0) on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
