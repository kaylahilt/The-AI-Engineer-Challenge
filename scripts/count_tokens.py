#!/usr/bin/env python3
"""
Token counting utility for text files
Supports multiple token counting methods
"""

import sys
import os
from pathlib import Path
import argparse

def count_tokens_simple(text):
    """Simple approximation: ~1 token per 4 characters"""
    return len(text) / 4

def count_tokens_words(text):
    """Word-based approximation: ~1.3 tokens per word"""
    words = text.split()
    return len(words) * 1.3

def count_tokens_tiktoken(text, model="gpt-4"):
    """Accurate token count using OpenAI's tiktoken"""
    try:
        import tiktoken
    except ImportError:
        print("❌ tiktoken not installed. Install with: pip install tiktoken")
        return None
    
    # Get encoding for the model
    encodings = {
        "gpt-4": "cl100k_base",
        "gpt-3.5-turbo": "cl100k_base",
        "gpt-4o": "o200k_base",
        "gpt-4o-mini": "o200k_base",
        "text-embedding-ada-002": "cl100k_base",
    }
    
    encoding_name = encodings.get(model, "cl100k_base")
    encoding = tiktoken.get_encoding(encoding_name)
    
    # Count tokens
    tokens = encoding.encode(text)
    return len(tokens)

def format_number(num):
    """Format number with commas"""
    return f"{int(num):,}"

def main():
    parser = argparse.ArgumentParser(description="Count tokens in text files")
    parser.add_argument("file", help="Path to the file to analyze")
    parser.add_argument("--model", default="gpt-4", 
                        choices=["gpt-4", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"],
                        help="Model to use for token counting (default: gpt-4)")
    parser.add_argument("--method", default="all",
                        choices=["simple", "words", "tiktoken", "all"],
                        help="Counting method to use (default: all)")
    
    args = parser.parse_args()
    
    # Read the file
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        sys.exit(1)
    
    # File stats
    file_size = os.path.getsize(args.file)
    char_count = len(text)
    word_count = len(text.split())
    line_count = text.count('\n') + 1
    
    print(f"\n📄 File: {args.file}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"📏 Size: {format_number(file_size)} bytes")
    print(f"📝 Characters: {format_number(char_count)}")
    print(f"📖 Words: {format_number(word_count)}")
    print(f"📋 Lines: {format_number(line_count)}")
    
    print(f"\n🪙 Token Counts:")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    if args.method in ["simple", "all"]:
        simple_tokens = count_tokens_simple(text)
        print(f"📊 Simple estimate (÷4): {format_number(simple_tokens)} tokens")
    
    if args.method in ["words", "all"]:
        word_tokens = count_tokens_words(text)
        print(f"📊 Word-based (×1.3): {format_number(word_tokens)} tokens")
    
    if args.method in ["tiktoken", "all"]:
        tiktoken_count = count_tokens_tiktoken(text, args.model)
        if tiktoken_count is not None:
            print(f"🎯 Accurate ({args.model}): {format_number(tiktoken_count)} tokens")
            
            # Show context window usage
            context_windows = {
                "gpt-4": 128_000,
                "gpt-3.5-turbo": 16_385,
                "gpt-4o": 128_000,
                "gpt-4o-mini": 128_000,
            }
            
            window_size = context_windows.get(args.model, 128_000)
            usage_percent = (tiktoken_count / window_size) * 100
            print(f"📈 Context usage: {usage_percent:.1f}% of {format_number(window_size)} token limit")
    
    print()

if __name__ == "__main__":
    main() 