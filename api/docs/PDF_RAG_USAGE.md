# PDF RAG (Retrieval-Augmented Generation) Feature

## Overview

This feature allows users to upload PDF documents and chat with Aethon about their contents using RAG technology powered by the `aimakerspace` library.

## How It Works

### 1. **PDF Upload & Processing**
- User uploads a PDF file through the web interface
- PDF is saved to the `uploads/` directory with a unique ID
- Text is extracted from all pages using PyPDF2

### 2. **Document Indexing**
- Text is split into manageable chunks (500 characters with 50 character overlap)
- Each chunk is converted to embeddings using OpenAI's `text-embedding-ada-002` model
- Embeddings are stored in a vector database for semantic search
- Index is saved to `indexes/` directory for faster subsequent access

### 3. **RAG-Enhanced Chat**
When chatting with PDF context enabled:
1. User's question is converted to an embedding
2. Vector database finds the most relevant chunks (top 3 by default)
3. Retrieved chunks are injected into Aethon's context
4. Aethon answers using both its personality and the PDF content

## API Endpoints

### Upload PDF
```
POST /api/upload-pdf
Content-Type: multipart/form-data

Body: PDF file
```

Response:
```json
{
  "success": true,
  "pdf_id": "document_name_abc123",
  "filename": "document.pdf",
  "num_chunks": 42,
  "status": "ready"
}
```

### Chat with PDF Context
```
POST /api/chat
Content-Type: application/json

Body:
{
  "message": "What does the document say about...",
  "use_pdf": true
}
```

### Clear PDF
```
POST /api/clear-pdf
```

## Frontend Usage

1. **Upload a PDF**: Click "Upload PDF" and select your document
2. **Wait for Indexing**: The system will show the number of chunks created
3. **Toggle PDF Context**: Use the checkbox to enable/disable PDF context
4. **Ask Questions**: Type questions about the PDF content
5. **Clear PDF**: Remove the current PDF when done

## Technical Details

### Dependencies
- `aimakerspace`: Core RAG functionality
- `pypdf2`: PDF text extraction
- `numpy`: Vector operations
- `faiss-cpu`: Efficient similarity search (optional, for larger documents)

### Architecture
```
User Query → Embedding → Vector Search → Top K Chunks → Context Injection → LLM Response
```

### Limitations
- PDF must be text-based (scanned images won't work without OCR)
- Large PDFs may take time to process
- Current implementation keeps one PDF in memory at a time

## Example Usage

1. Upload a technical manual
2. Ask: "How do I configure the network settings?"
3. Aethon will search the manual and provide relevant information while maintaining its whimsical personality

## Future Enhancements
- Support for multiple PDFs simultaneously
- OCR for scanned documents
- Persistent storage of indexed documents
- Advanced chunking strategies
- Citation of specific page numbers 