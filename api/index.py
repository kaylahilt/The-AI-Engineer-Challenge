"""
Vercel serverless function handler for the Aethon API
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from pathlib import Path
import cgi
import io

# Add the api directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Initialize PDF handler globally
from pdf_handler import PDFHandler
import logging

logger = logging.getLogger(__name__)

try:
    pdf_handler = PDFHandler()
    logger.info("PDFHandler initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize PDFHandler: {e}")
    logger.warning("PDF functionality will be disabled")
    pdf_handler = None

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
                "ab_testing": False,
                "pdf_support": True
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
                "features": features,
                "current_pdf": pdf_handler.current_pdf_id if pdf_handler else None
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
                use_pdf = body.get('use_pdf', False)
                
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
                
                # Check if we should use RAG with PDF
                if use_pdf and pdf_handler and pdf_handler.current_pdf_id:
                    # Get context from PDF
                    try:
                        pdf_context = pdf_handler.generate_rag_context(message)
                        
                        # Create RAG-enhanced prompt
                        rag_system_prompt = f"""{AETHON_SYSTEM_PROMPT}

You have access to excerpts from a PDF document. Use this information to answer questions, but maintain your characteristic style and personality.

PDF Context:
{pdf_context}

When answering questions about the PDF:
- Reference specific information from the excerpts when relevant
- If the excerpts don't contain relevant information, acknowledge this
- Maintain your wise and whimsical personality while being accurate to the source material"""
                        
                        system_prompt_to_use = rag_system_prompt
                        mode = "rag"
                    except Exception as e:
                        print(f"RAG context generation failed: {e}")
                        system_prompt_to_use = AETHON_SYSTEM_PROMPT
                        mode = "basic"
                else:
                    system_prompt_to_use = AETHON_SYSTEM_PROMPT
                    mode = "basic"
                
                # Try to use Langfuse if available (keeping existing logic)
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
                    
                    # For RAG mode, modify the prompt content
                    if mode == "rag":
                        prompt.prompt = system_prompt_to_use
                    
                    # Use Langfuse OpenAI
                    response = langfuse_openai.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt_to_use},
                            {"role": "user", "content": message}
                        ],
                        temperature=0.7,
                        max_tokens=1000,
                        langfuse_prompt=prompt if mode != "rag" else None
                    )
                    
                    if mode != "rag":
                        mode = "advanced"
                    prompt_version = selected_version
                    
                except Exception as e:
                    print(f"Langfuse error: {e}, using basic mode")
                    # Fallback to basic OpenAI
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt_to_use},
                            {"role": "user", "content": message}
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )
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
                    "mode": mode,
                    "pdf_active": pdf_handler.current_pdf_id is not None if pdf_handler else False
                }
                
                self.wfile.write(json.dumps(result).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            
            return
            
        elif self.path == '/api/upload-pdf':
            try:
                # Check if PDF handler is available
                if not pdf_handler:
                    raise RuntimeError("PDF functionality is not available in this environment")
                
                # Parse multipart form data
                content_type = self.headers['Content-Type']
                if 'multipart/form-data' not in content_type:
                    raise ValueError("Expected multipart/form-data")
                
                # Get boundary
                boundary = content_type.split("boundary=")[1].encode()
                
                # Read the entire body
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                
                # Parse multipart data manually
                parts = body.split(b'--' + boundary)
                
                pdf_content = None
                filename = "uploaded.pdf"
                extract_entities = False
                
                for part in parts:
                    if b'Content-Disposition' in part:
                        if b'name="extract_entities"' in part:
                            # Extract the value for extract_entities
                            content_start = part.find(b'\r\n\r\n')
                            if content_start != -1:
                                value = part[content_start + 4:].rstrip(b'\r\n').decode('utf-8')
                                extract_entities = value.lower() == 'true'
                        elif b'filename=' in part:
                            # Extract filename
                            header_lines = part.split(b'\r\n')
                            for line in header_lines:
                                if b'filename=' in line:
                                    filename = line.split(b'filename=')[1].split(b'"')[1].decode('utf-8')
                                    break
                            
                            # Extract content (after double CRLF)
                            content_start = part.find(b'\r\n\r\n')
                            if content_start != -1:
                                pdf_content = part[content_start + 4:].rstrip(b'\r\n')
                                break
                
                if not pdf_content:
                    raise ValueError("No PDF content found in upload")
                
                # Save and index the PDF
                pdf_id = pdf_handler.save_pdf(filename, pdf_content)
                index_result = pdf_handler.index_pdf(pdf_id)
                
                # Extract named entities if requested
                named_entities = []
                if extract_entities:
                    try:
                        # Get the full text from the PDF handler
                        pdf_path = pdf_handler.upload_dir / f"{pdf_id}.pdf"
                        text_content = pdf_handler.extract_text_from_pdf(pdf_path)
                        named_entities = pdf_handler.extract_named_entities(text_content, top_k=5)
                        logger.info(f"Extracted {len(named_entities)} named entities")
                    except Exception as e:
                        logger.error(f"Failed to extract entities: {e}")
                        # Continue without entities rather than failing the whole upload
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                result = {
                    "success": True,
                    "pdf_id": pdf_id,
                    "filename": filename,
                    "num_chunks": index_result["num_chunks"],
                    "status": "ready"
                }
                
                # Add entities only if extraction was requested and successful
                if extract_entities and named_entities:
                    result["named_entities"] = named_entities
                
                self.wfile.write(json.dumps(result).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            
            return
            
        elif self.path == '/api/clear-pdf':
            try:
                if not pdf_handler:
                    raise RuntimeError("PDF functionality is not available in this environment")
                
                pdf_handler.clear_current_pdf()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                self.wfile.write(json.dumps({"success": True, "message": "PDF cleared"}).encode())
                
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