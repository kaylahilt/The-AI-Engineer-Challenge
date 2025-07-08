"""
PDF Handler for RAG functionality using aimakerspace library
"""

import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
import hashlib
import json

# PDF processing
from PyPDF2 import PdfReader

# Aimakerspace imports
from aimakerspace.text_utils import TextFileLoader, CharacterTextSplitter
from aimakerspace.vectordatabase import VectorDatabase
from aimakerspace.openai_utils.embedding import EmbeddingModel

logger = logging.getLogger(__name__)

class PDFHandler:
    """Handles PDF upload, indexing, and RAG operations"""
    
    def __init__(self, upload_dir: str = "uploads", index_dir: str = "indexes"):
        self.upload_dir = Path(upload_dir)
        self.index_dir = Path(index_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.index_dir.mkdir(exist_ok=True)
        
        # Initialize embedding model
        self.embedding_model = EmbeddingModel(
            embeddings_model_name="text-embedding-ada-002"
        )
        
        # Current loaded PDF info
        self.current_pdf_id: Optional[str] = None
        self.vector_db: Optional[VectorDatabase] = None
        self.chunks: List[str] = []
        
    def generate_pdf_id(self, filename: str, content: bytes) -> str:
        """Generate unique ID for PDF based on filename and content hash"""
        content_hash = hashlib.md5(content).hexdigest()[:8]
        return f"{Path(filename).stem}_{content_hash}"
        
    def save_pdf(self, filename: str, content: bytes) -> str:
        """Save uploaded PDF and return its ID"""
        pdf_id = self.generate_pdf_id(filename, content)
        pdf_path = self.upload_dir / f"{pdf_id}.pdf"
        
        # Save the PDF
        with open(pdf_path, "wb") as f:
            f.write(content)
            
        logger.info(f"Saved PDF: {pdf_path}")
        return pdf_id
        
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text content from PDF"""
        try:
            reader = PdfReader(str(pdf_path))
            text_content = []
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():
                    text_content.append(f"Page {page_num + 1}:\n{text}")
                    
            return "\n\n".join(text_content)
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
            
    def index_pdf(self, pdf_id: str) -> Dict[str, Any]:
        """Index a PDF for RAG operations"""
        pdf_path = self.upload_dir / f"{pdf_id}.pdf"
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_id}")
            
        # Extract text
        logger.info(f"Extracting text from PDF: {pdf_id}")
        text_content = self.extract_text_from_pdf(pdf_path)
        
        # Split into chunks
        logger.info(f"Splitting text into chunks")
        text_splitter = CharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separator="\n"
        )
        self.chunks = text_splitter.split_text(text_content)
        
        # Create embeddings
        logger.info(f"Creating embeddings for {len(self.chunks)} chunks")
        embeddings = []
        for chunk in self.chunks:
            embedding = self.embedding_model.get_embedding(chunk)
            embeddings.append(embedding)
            
        # Create vector database
        self.vector_db = VectorDatabase()
        for i, (chunk, embedding) in enumerate(zip(self.chunks, embeddings)):
            self.vector_db.add_document(
                document_id=str(i),
                text=chunk,
                embedding=embedding,
                metadata={"chunk_index": i, "pdf_id": pdf_id}
            )
            
        # Save index
        index_path = self.index_dir / f"{pdf_id}_index.json"
        self.save_index(index_path, pdf_id)
        
        self.current_pdf_id = pdf_id
        
        return {
            "pdf_id": pdf_id,
            "num_chunks": len(self.chunks),
            "status": "indexed"
        }
        
    def save_index(self, index_path: Path, pdf_id: str):
        """Save the index data"""
        index_data = {
            "pdf_id": pdf_id,
            "chunks": self.chunks,
            "vector_db": self.vector_db.to_dict() if hasattr(self.vector_db, 'to_dict') else {}
        }
        
        with open(index_path, "w") as f:
            json.dump(index_data, f)
            
    def load_index(self, pdf_id: str) -> bool:
        """Load a previously indexed PDF"""
        index_path = self.index_dir / f"{pdf_id}_index.json"
        if not index_path.exists():
            return False
            
        with open(index_path, "r") as f:
            index_data = json.load(f)
            
        self.chunks = index_data["chunks"]
        self.current_pdf_id = pdf_id
        
        # Recreate vector database
        self.vector_db = VectorDatabase()
        for i, chunk in enumerate(self.chunks):
            embedding = self.embedding_model.get_embedding(chunk)
            self.vector_db.add_document(
                document_id=str(i),
                text=chunk,
                embedding=embedding,
                metadata={"chunk_index": i, "pdf_id": pdf_id}
            )
            
        return True
        
    def query_pdf(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Query the indexed PDF using semantic search"""
        if not self.vector_db or not self.current_pdf_id:
            raise ValueError("No PDF is currently indexed")
            
        # Get query embedding
        query_embedding = self.embedding_model.get_embedding(query)
        
        # Search for similar chunks
        results = self.vector_db.search(
            query_embedding=query_embedding,
            top_k=top_k
        )
        
        return [
            {
                "text": result["text"],
                "score": result["score"],
                "metadata": result.get("metadata", {})
            }
            for result in results
        ]
        
    def generate_rag_context(self, query: str, top_k: int = 3) -> str:
        """Generate context for RAG from the PDF"""
        results = self.query_pdf(query, top_k)
        
        context_parts = []
        for i, result in enumerate(results):
            context_parts.append(f"[Excerpt {i+1}]:\n{result['text']}")
            
        return "\n\n".join(context_parts)
        
    def clear_current_pdf(self):
        """Clear the currently loaded PDF"""
        self.current_pdf_id = None
        self.vector_db = None
        self.chunks = [] 