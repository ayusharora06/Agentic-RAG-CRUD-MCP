"""
RAG Tools for document search using Qdrant
"""
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.rag_pipeline import RAGPipeline


class SearchDocumentsInput(BaseModel):
    """Input schema for SearchDocumentsTool"""
    query: str = Field(..., description="The search query to find relevant documents")


class SearchDocumentsTool(BaseTool):
    """Tool for searching documents in the RAG pipeline"""
    
    name: str = "Search Documents"
    description: str = (
        "Search for relevant documents in the knowledge base. "
        "This tool searches through indexed PDF documents using semantic search "
        "and returns relevant passages with source citations."
    )
    args_schema: Type[BaseModel] = SearchDocumentsInput
    
    # Class variable to hold the RAG pipeline instance
    _rag_pipeline: Optional[RAGPipeline] = None
    
    @classmethod
    def set_rag_pipeline(cls, rag_pipeline: RAGPipeline):
        """Set the RAG pipeline instance to be used by tools"""
        cls._rag_pipeline = rag_pipeline
    
    def _run(self, query: str) -> str:
        """Execute the document search"""
        # Access the class-level RAG pipeline
        if self._rag_pipeline is None:
            return "Error: RAG pipeline not initialized. Please ensure the system is properly started."
        
        try:
            # Perform the search
            results = self._rag_pipeline.search(query, top_k=5)
            
            if not results:
                return "No relevant documents found for your query."
            
            # Format the results
            formatted_results = []
            for i, result in enumerate(results, 1):
                source = result['metadata'].get('source', 'Unknown')
                page = result['metadata'].get('page', 'N/A')
                content = result['content'][:500]  # Limit content length
                score = result.get('score', 0.0)
                
                formatted_results.append(
                    f"Result {i}:\n"
                    f"Source: {source}, Page: {page}\n"
                    f"Relevance Score: {score:.2f}\n"
                    f"Content: {content}...\n"
                    f"-" * 50
                )
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            return f"Error searching documents: {str(e)}"