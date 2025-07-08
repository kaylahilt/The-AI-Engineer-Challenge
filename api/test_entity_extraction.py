#!/usr/bin/env python3
"""
Test script for named entity extraction functionality
"""

import sys
from pathlib import Path

# Add the api directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from pdf_handler import PDFHandler

def test_entity_extraction():
    """Test the entity extraction functionality"""
    
    # Sample text with various entities
    test_text = """
    Apple Inc. is a technology company founded by Steve Jobs, Steve Wozniak, and Ronald Wayne 
    in April 1976. The company is headquartered in Cupertino, California. Tim Cook has been 
    the CEO since 2011. Apple's products include the iPhone, iPad, and Mac computers.
    
    Microsoft Corporation, founded by Bill Gates and Paul Allen, is another major tech company
    based in Redmond, Washington. Satya Nadella is the current CEO. Microsoft is known for
    Windows, Office, and Azure cloud services.
    
    Both Apple and Microsoft are among the most valuable companies in the United States.
    They compete in various markets including operating systems, productivity software,
    and cloud computing services.
    """
    
    print("Testing Named Entity Extraction...")
    print("-" * 50)
    
    # Initialize PDF handler
    pdf_handler = PDFHandler()
    
    # Extract entities
    entities = pdf_handler.extract_named_entities(test_text, top_k=5)
    
    if entities:
        print(f"Found {len(entities)} top entities:\n")
        for i, entity in enumerate(entities, 1):
            print(f"{i}. {entity['text']} ({entity['label']}) - {entity['count']} occurrences")
    else:
        print("No entities found or spaCy not available")
    
    print("\nTest completed!")

def test_pdf_entity_extraction(pdf_path):
    """Test entity extraction on an actual PDF file"""
    
    print(f"\nTesting Named Entity Extraction on {pdf_path}")
    print("=" * 60)
    
    # Initialize PDF handler
    pdf_handler = PDFHandler()
    
    try:
        # Read the PDF file
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        # Save and extract text from PDF
        pdf_id = pdf_handler.save_pdf(Path(pdf_path).name, pdf_content)
        pdf_full_path = pdf_handler.upload_dir / f"{pdf_id}.pdf"
        text_content = pdf_handler.extract_text_from_pdf(pdf_full_path)
        
        print(f"PDF loaded successfully: {Path(pdf_path).name}")
        print(f"Text length: {len(text_content)} characters")
        print("-" * 60)
        
        # Extract entities
        entities = pdf_handler.extract_named_entities(text_content, top_k=10)
        
        if entities:
            print(f"\nTop {len(entities)} Named Entities found:\n")
            for i, entity in enumerate(entities, 1):
                print(f"{i:2d}. {entity['text']:<30} ({entity['label']:<10}) - {entity['count']} occurrences")
        else:
            print("No entities found or spaCy not available")
            
        # Show a sample of the extracted text
        print("\n" + "-" * 60)
        print("First 500 characters of extracted text:")
        print(text_content[:500] + "...")
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    # Test with sample text
    test_entity_extraction()
    
    # Test with actual PDF
    pdf_path = Path(__file__).parent.parent / "SRPT.pdf"
    if pdf_path.exists():
        test_pdf_entity_extraction(pdf_path)
    else:
        print(f"\nPDF not found at: {pdf_path}") 