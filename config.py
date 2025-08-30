"""
Configuration for the AI Agent System
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DB_DIR = BASE_DIR / "db"
RESOURCES_DIR = BASE_DIR / "resources"

# Database
DB_PATH = DB_DIR / "main.db"

# MCP Server Configuration
PERSON_SERVER_HOST = "localhost"
PERSON_SERVER_PORT = 8001

BANK_SERVER_HOST = "localhost"
BANK_SERVER_PORT = 8002

# API Keys (from environment)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

# Qdrant Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_COLLECTION = "insurance_docs"

# Embedding Configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# FastAPI Configuration
API_HOST = "0.0.0.0"
API_PORT = 8003

# Masking patterns
SENSITIVE_PATTERNS = {
    "aadhar": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
    "phone": r"\b\d{10}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"
}