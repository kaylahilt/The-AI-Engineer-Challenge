"""
Vercel serverless function handler for the Aethon API
"""

import os
import sys
from pathlib import Path

# Add the api directory to Python path for proper imports
api_dir = Path(__file__).parent
sys.path.insert(0, str(api_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import the wrapped app that handles initialization better
from app_wrapper import app

# Export the handler for Vercel
handler = app 