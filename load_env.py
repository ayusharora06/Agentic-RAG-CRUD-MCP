#!/usr/bin/env python3
"""
Load environment variables from .env file
"""
import os
from pathlib import Path
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent / '.env'
    
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ Loaded environment variables from .env")
        
        # Check for required keys
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  OPENAI_API_KEY not found in .env")
        
        if not os.getenv("SERPER_API_KEY"):
            print("⚠️  SERPER_API_KEY not found in .env")
    else:
        print("⚠️  No .env file found. Using system environment variables.")
        print("   Create a .env file from .env.example:")
        print("   cp .env.example .env")

if __name__ == "__main__":
    load_environment()