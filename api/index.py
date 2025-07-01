"""
Vercel serverless function handler for the Aethon API
"""

import os
import sys
from pathlib import Path

# Add the api directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the FastAPI app
from app_wrapper import app

# Use Mangum to create a handler for serverless environments
from mangum import Mangum

# Create the handler that Vercel can use
handler = Mangum(app, lifespan="off")

# Also expose the app directly
app = app 