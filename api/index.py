"""
Vercel serverless function handler for the Aethon API
"""

import os
from dotenv import load_dotenv

# Load environment variables in development
load_dotenv()

# Import the FastAPI app
from app import app

# Export the FastAPI app instance for Vercel
# This allows Vercel to properly handle the serverless function
handler = app 