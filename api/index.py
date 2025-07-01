"""
Vercel serverless function handler for the Aethon API
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from pathlib import Path

# Add the api directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Initialize services and check status
            features = {
                "openai": False,
                "langfuse": False,
                "ab_testing": False
            }
            
            try:
                from openai import OpenAI
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                if client:
                    features["openai"] = True
            except:
                pass
                
            try:
                from langfuse import Langfuse
                langfuse = Langfuse()
                if langfuse:
                    features["langfuse"] = True
            except:
                pass
            
            response = {
                "status": "healthy",
                "service": "aethon-api",
                "features": features
            }
            
            self.wfile.write(json.dumps(response).encode())
            return
        
        self.send_response(404)
        self.end_headers()
        
    def do_POST(self):
        if self.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                body = json.loads(post_data.decode('utf-8'))
                message = body.get('message', '')
                user_id = body.get('user_id', 'anonymous')
                
                if not message:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Message required"}).encode())
                    return
                
                # Try to use OpenAI
                from openai import OpenAI
                from prompt_management.aethon_prompt import AETHON_SYSTEM_PROMPT
                
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                
                # Try to use Langfuse if available
                try:
                    from langfuse import Langfuse
                    from langfuse.openai import openai as langfuse_openai
                    from ab_testing.ab_manager import ABTestManager
                    
                    langfuse = Langfuse()
                    ab_manager = ABTestManager(langfuse)
                    
                    # Get prompt variant
                    prompt, selected_version = ab_manager.get_prompt_variant(
                        prompt_name="aethon-system-prompt",
                        test_name="aethon-personality"
                    )
                    
                    system_prompt = prompt.compile()
                    
                    # Use Langfuse OpenAI
                    response = langfuse_openai.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": message}
                        ],
                        temperature=0.7,
                        max_tokens=1000,
                        langfuse_prompt=prompt
                    )
                    
                    mode = "advanced"
                    prompt_version = selected_version
                    
                except Exception as e:
                    print(f"Langfuse error: {e}, using basic mode")
                    # Fallback to basic OpenAI
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": AETHON_SYSTEM_PROMPT},
                            {"role": "user", "content": message}
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )
                    mode = "basic"
                    prompt_version = 0
                
                # Send response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                result = {
                    "response": response.choices[0].message.content,
                    "conversation_id": f"conv_{abs(hash(user_id + message))}",
                    "prompt_version": prompt_version,
                    "mode": mode
                }
                
                self.wfile.write(json.dumps(result).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            
            return
        
        self.send_response(404)
        self.end_headers()
        
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 