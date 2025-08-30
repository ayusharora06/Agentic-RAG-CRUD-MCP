"""
Main Application - AI Agent System with MCP Servers
"""
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
from load_env import load_environment

# Load environment variables
load_environment()

from config import (
    API_HOST, API_PORT,
    QDRANT_HOST, QDRANT_PORT
)
from crew_supervisor import AIAgentCrew  # Use the supervisor multi-agent pattern
from rag.rag_pipeline import RAGPipeline

# Initialize FastAPI
app = FastAPI(title="AI Agent System", version="2.0.0")

# Add CORS middleware for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
ai_crew = None
rag_pipeline = None

class QueryRequest(BaseModel):
    """Request model for queries"""
    query: str

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global ai_crew, rag_pipeline
    
    print("🎯 Starting AI Agent System v2.0...")
    print("=" * 50)
    
    try:
        # Initialize the AI Agent Crew
        print("🤖 Initializing AI Agent Crew...")
        ai_crew = AIAgentCrew()
        
        # Initialize and index PDFs
        print("📚 Initializing RAG pipeline...")
        rag_pipeline = ai_crew.rag_pipeline
        
        # Index PDFs if resources exist
        print("📄 Indexing PDF documents...")
        rag_pipeline.index_all_pdfs()
        
        print("=" * 50)
        print("✅ System ready! Access the API at http://localhost:8003")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Shutting down AI Agent System...")
    print("✅ Shutdown complete")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Agent System",
        "version": "2.0.0",
        "status": "running",
        "architecture": "CrewAI with MCP Servers",
        "endpoints": {
            "query": "/query - Main endpoint for all natural language queries",
            "health": "/health - System health check",
            "index_pdfs": "/index-pdfs - Re-index PDF documents"
        },
        "usage": "Send natural language queries to /query endpoint",
        "examples": [
            "Create a person named John aged 30 with email john@example.com",
            "List all persons",
            "Show bank accounts for person 1",
            "What does the insurance policy say about coverage?",
            "Get person 3 with their bank accounts (JOIN operation)"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health = {
        "status": "healthy",
        "crew": "initialized" if ai_crew else "not initialized",
        "rag_pipeline": "initialized" if rag_pipeline else "not initialized"
    }
    
    # Get RAG status
    if rag_pipeline:
        try:
            collection_info = rag_pipeline.get_collection_info()
            health["qdrant"] = {
                "status": "connected",
                "vectors": collection_info.get("vectors_count", 0)
            }
        except:
            health["qdrant"] = {"status": "error or not running"}
    
    return health

@app.post("/query")
async def process_query(request: QueryRequest):
    """
    Process user query through the AI Agent Crew
    
    The orchestrator agent will:
    1. Analyze the query to determine its type
    2. Route to appropriate agent (CRUD or PDF)
    3. Execute the necessary operations
    4. Return the result
    """
    if not ai_crew:
        raise HTTPException(status_code=503, detail="AI Crew not initialized")
    
    try:
        print(f"📨 Received query: {request.query}")
        
        # Process query through the crew
        result = ai_crew.process_query(query=request.query)
        
        print(f"✅ Response sent for query: {request.query[:50]}...")
        return JSONResponse(content=result)
    
    except Exception as e:
        print(f"❌ Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index-pdfs")
async def index_pdfs():
    """Re-index all PDFs in resources directory"""
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    
    try:
        results = rag_pipeline.index_all_pdfs()
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """Main entry point"""
    print("""
    ╔══════════════════════════════════════════════╗
    ║     AI Agent System v2.0 with CrewAI        ║
    ║     MCP Servers and RAG Pipeline            ║
    ╚══════════════════════════════════════════════╝
    
    🔑 Make sure OPENAI_API_KEY is set in environment
    """)
    
    # Check for OpenAI API key
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  WARNING: OPENAI_API_KEY not found in environment")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        print()
    
    # Run FastAPI server
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=False
    )

if __name__ == "__main__":
    main()