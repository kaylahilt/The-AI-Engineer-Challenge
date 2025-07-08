"""
PDF Handler for RAG functionality using aimakerspace library

Note: In Vercel's serverless environment, we use /tmp directory which is:
- The only writable directory
- Ephemeral (cleared between invocations)
- Limited to 512MB

For production, consider using cloud storage (S3, etc.) for persistence.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
import hashlib
import json
import numpy as np
from collections import Counter

# PDF processing
from PyPDF2 import PdfReader

# Named entity recognition
# Disabled for Vercel deployment due to size limits
# To enable locally, uncomment and install: pip install spacy && python -m spacy download en_core_web_sm
nlp = None
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except:
    nlp = None
    logging.info("spaCy not available. Named entity extraction is disabled in production.")

# Aimakerspace imports
from aimakerspace.text_utils import TextFileLoader, CharacterTextSplitter
from aimakerspace.vectordatabase import VectorDatabase
from aimakerspace.openai_utils.embedding import EmbeddingModel

logger = logging.getLogger(__name__)

class PDFHandler:
    """Handles PDF upload, indexing, and RAG operations"""
    
    def __init__(self, upload_dir: str = "/tmp/uploads", index_dir: str = "/tmp/indexes"):
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
            chunk_overlap=50
        )
        self.chunks = text_splitter.split(text_content)
        
        # Create embeddings
        logger.info(f"Creating embeddings for {len(self.chunks)} chunks")
        embeddings = []
        for chunk in self.chunks:
            embedding = self.embedding_model.get_embedding(chunk)
            embeddings.append(embedding)
            
        # Create vector database
        self.vector_db = VectorDatabase(embedding_model=self.embedding_model)
        for i, (chunk, embedding) in enumerate(zip(self.chunks, embeddings)):
            # VectorDatabase uses text as key and embedding as value
            self.vector_db.insert(chunk, np.array(embedding))
            
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
            "chunks": self.chunks
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
        self.vector_db = VectorDatabase(embedding_model=self.embedding_model)
        for chunk in self.chunks:
            embedding = self.embedding_model.get_embedding(chunk)
            self.vector_db.insert(chunk, np.array(embedding))
            
        return True
        
    def query_pdf(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Query the indexed PDF using semantic search"""
        if not self.vector_db or not self.current_pdf_id:
            raise ValueError("No PDF is currently indexed")
            
        # Get query embedding
        query_embedding = self.embedding_model.get_embedding(query)
        
        # Search for similar chunks
        # VectorDatabase.search returns List[Tuple[str, float]] where str is the text and float is the score
        results = self.vector_db.search(
            query_vector=np.array(query_embedding),
            k=top_k
        )
        
        return [
            {
                "text": text,
                "score": score,
                "metadata": {"pdf_id": self.current_pdf_id}
            }
            for text, score in results
        ]
        
    def generate_rag_context(self, query: str, top_k: int = 3) -> str:
        """Generate context for RAG from the PDF"""
        results = self.query_pdf(query, top_k)
        
        context_parts = []
        for i, result in enumerate(results):
            context_parts.append(f"[Excerpt {i+1}]:\n{result['text']}")
            
        return "\n\n".join(context_parts)
        
    def extract_named_entities(self, text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Extract named entities from text using spaCy"""
        if not nlp:
            logger.warning("spaCy not available, using simple extraction")
            return self.extract_named_entities_simple(text, top_k)
            
        try:
            # Process text with spaCy
            doc = nlp(text)
            
            # Extract entities and count occurrences
            entity_counter = Counter()
            entity_labels = {}
            
            for ent in doc.ents:
                # Normalize entity text (strip whitespace, convert to title case)
                entity_text = ent.text.strip()
                if entity_text and ent.label_ not in ["DATE", "TIME", "PERCENT", "MONEY", "QUANTITY", "ORDINAL", "CARDINAL"]:
                    entity_counter[entity_text] += 1
                    entity_labels[entity_text] = ent.label_
            
            # Get top K entities
            top_entities = []
            for entity_text, count in entity_counter.most_common(top_k):
                top_entities.append({
                    "text": entity_text,
                    "label": entity_labels[entity_text],
                    "count": count
                })
            
            return top_entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []
    
    def extract_named_entities_simple(self, text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Simple regex-based entity extraction for when spaCy is not available"""
        import re
        
        # Improved patterns for common entities (ordered by specificity)
        patterns = [
            # Exclude patterns first (these should NOT be extracted)
            ("EXCLUDE", r'\b(?:Research Division|Marketing Division|Sales Division|Engineering Division|Content|LLC|Inc|Corp|Ltd|Scientific Officer|Head of Research)\b'),
            # Most specific patterns
            ("PERSON_TITLE", r'\b(?:Mr|Mrs|Ms|Dr|Prof)\.?\s+[A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?(?:\s+[A-Z][a-z]+)+\b'),
            ("PERSON_MI", r'\b[A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z-]+\b'),
            # Investment firms and financial companies (more specific)
            ("ORG_FINANCE", r'\b(?:JPMorgan Chase & Co|Piper Sandler & Co|Robert W\. Baird & Co|RBC Capital Markets|Sarepta Therapeutics)(?:\s*[,.]?\s*(?:Inc|Research Division))?\b'),
            ("ORG", r'\b[A-Z][a-zA-Z\s&,]+(?:\s+(?:Inc|Corp|Corporation|LLC|Ltd|Limited|Company|Co|Group|Therapeutics|Pharmaceuticals|Foundation|Institute|Agency|Association|Society|Organization|University|College|School|Hospital|Bank|Fund|Trust)\.?)\b'),
            ("ORG_ACRONYM", r'\b(?:FDA|EPA|FBI|CIA|NASA|WHO|UN|EU|NATO|NASDAQ|NYSE|SEC)\b'),
            ("PERSON_FULL", r'\b[A-Z][a-z]+\s+(?:[A-Z]\.?\s+)?[A-Z][a-z-]+\b')
        ]
        
        entity_counter = Counter()
        entity_labels = {}
        all_matches = []  # Collect all matches first
        
        # Extract entities using patterns
        for label, pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE if label == "ORG_ACRONYM" else 0)
            for match in matches:
                entity_text = match.group().strip()
                match_start, match_end = match.span()
                all_matches.append((match_start, match_end, entity_text, label))
        
        # Sort matches by start position and length (longer matches first)
        all_matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))
        
        # Process matches, avoiding overlaps but counting all occurrences
        used_positions = set()
        for match_start, match_end, entity_text, label in all_matches:
            # Check if this position overlaps with a previously processed match
            overlap = any(match_start < end and match_end > start for start, end in used_positions)
            
            if not overlap:
                # Skip if this is an EXCLUDE pattern
                if label == "EXCLUDE":
                    continue
                    
                # Skip common words that match patterns
                skip_words = {'the', 'this', 'that', 'these', 'those', 'content', 'page', 
                             'executive', 'research', 'division', 'analyst', 'analysts',
                             'page', 'edited', 'special', 'call', 'participants', 'version',
                             'officer', 'head', 'content', 'and', 'or', 'but', 'president',
                             'director', 'manager', 'operator', 'our', 'your', 'their',
                             'chief', 'vice', 'senior', 'assistant', 'associate', 'llc',
                             'inc', 'corp', 'ltd', 'executives', 'summary', 'overview'}
                if entity_text.lower() in skip_words:
                    continue
                    
                # Skip standalone company suffixes
                if entity_text.upper() in ['LLC', 'INC', 'CORP', 'LTD', 'CO']:
                    continue
                    
                # Skip titles that include "Officer", "Head of", etc.
                title_patterns = ['officer', 'head of', 'director of', 'president of', 'chief of']
                if any(pattern in entity_text.lower() for pattern in title_patterns):
                    continue
                    
                # Skip single letters or very short words
                if len(entity_text) <= 2:
                    continue
                
                # Additional filtering for false positives
                # Skip if it's just a single common word (even if capitalized)
                single_word_skip = {'and', 'or', 'the', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 
                                   'from', 'up', 'about', 'into', 'through', 'after', 'over',
                                   'between', 'out', 'against', 'during', 'without', 'before',
                                   'under', 'around', 'among'}
                if entity_text.lower() in single_word_skip:
                    continue
                
                # Skip if it contains common non-entity words or is a generic term
                non_entity_phrases = ['operator our', 'and the', 'or the', 'in the', 'on the', 
                                     'at the', 'to the', 'for the', 'of the', 'with the',
                                     'research division', 'content', 'scientific officer',
                                     'head of research', 'research & develop']
                if any(phrase in entity_text.lower() for phrase in non_entity_phrases):
                    continue
                    
                # Skip generic organizational terms without company names
                generic_org_terms = ['research division', 'marketing division', 'sales division',
                                    'engineering division', 'content division', 'it division']
                if entity_text.lower() in generic_org_terms:
                    continue
                
                # Normalize label
                if "PERSON" in label:
                    # Additional check for person names
                    # Skip if it's just a title without a proper name
                    if entity_text.lower() in ['president', 'director', 'manager', 'executive', 'chief']:
                        continue
                    # For single-word names, we'll check frequency later
                    final_label = "PERSON"
                elif label in ["ORG", "ORG_ACRONYM", "ORG_FINANCE"] or any(org_word in entity_text for org_word in ['Inc', 'Corp', 'LLC', 'Company', 'Therapeutics', 'Pharmaceuticals', 'Bank', 'Capital', 'Markets', 'Division']):
                    final_label = "ORG"
                else:
                    # For single-word entities, only keep known meaningful ones
                    known_entities = ['fda', 'sec', 'nasdaq', 'nyse', 'epa', 'fbi', 'cia', 'nasa', 'who']
                    if len(entity_text.split()) == 1:
                        if entity_text.lower() not in known_entities:
                            continue
                    final_label = "ENTITY"
                
                # Mark this position as used
                used_positions.add((match_start, match_end))
                
                # Count this occurrence
                entity_counter[entity_text] += 1
                entity_labels[entity_text] = final_label
        
        # Post-process entities to filter out likely false positives
        filtered_counter = Counter()
        filtered_labels = {}
        
        for entity_text, count in entity_counter.items():
            label = entity_labels[entity_text]
            
            # Filter single-word person names unless they appear frequently
            if label == "PERSON" and len(entity_text.split()) == 1:
                if count < 5:  # Skip single names with low frequency
                    continue
                    
            # Filter organizations that are just generic divisions
            if label == "ORG":
                lower_text = entity_text.lower()
                if any(term in lower_text for term in ['research division', 'marketing division', 
                                                       'sales division', 'content', 'llc']):
                    continue
                # Skip if it's just "Division" or similar
                if lower_text in ['division', 'department', 'office', 'bureau', 'llc', 'content']:
                    continue
                    
            # Filter out truncated or malformed entities
            if any(char in entity_text for char in ['ﬃ', 'ﬁ', 'ﬂ']):  # PDF encoding issues
                continue
            if entity_text.endswith(' &') or entity_text.endswith(' t'):  # Truncated text
                continue
                
            filtered_counter[entity_text] = count
            filtered_labels[entity_text] = label
        
        # Get top K entities
        top_entities = []
        for entity_text, count in filtered_counter.most_common(top_k):
            top_entities.append({
                "text": entity_text,
                "label": filtered_labels[entity_text],
                "count": count
            })
        
        return top_entities
    
    def clear_current_pdf(self):
        """Clear the currently loaded PDF"""
        self.current_pdf_id = None
        self.vector_db = None
        self.chunks = [] 