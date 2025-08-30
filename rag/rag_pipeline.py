"""
RAG Pipeline for PDF document processing and retrieval
"""
from typing import List, Dict, Any
import os
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from sentence_transformers import SentenceTransformer
import numpy as np
from config import (
    QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION,
    EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP,
    RESOURCES_DIR
)

class RAGPipeline:
    """Handles PDF indexing and retrieval using Qdrant"""
    
    def __init__(self):
        # Initialize Qdrant client
        self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        
        # Initialize embedding model
        self.encoder = SentenceTransformer(EMBEDDING_MODEL)
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Create collection if it doesn't exist
        self._initialize_collection()
    
    def _initialize_collection(self):
        """Initialize Qdrant collection"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            if QDRANT_COLLECTION not in [c.name for c in collections.collections]:
                # Create collection
                self.client.create_collection(
                    collection_name=QDRANT_COLLECTION,
                    vectors_config=models.VectorParams(
                        size=384,  # Size for all-MiniLM-L6-v2
                        distance=models.Distance.COSINE
                    )
                )
                print(f"✅ Created Qdrant collection: {QDRANT_COLLECTION}")
            else:
                print(f"✅ Using existing Qdrant collection: {QDRANT_COLLECTION}")
        except Exception as e:
            print(f"❌ Error initializing Qdrant collection: {e}")
    
    def index_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Index a single PDF file"""
        try:
            # Load PDF
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            
            # Split into chunks
            chunks = []
            for page_num, page in enumerate(pages):
                page_chunks = self.text_splitter.split_text(page.page_content)
                for chunk in page_chunks:
                    chunks.append({
                        "content": chunk,
                        "metadata": {
                            "source": os.path.basename(pdf_path),
                            "page": page_num + 1,
                            "path": pdf_path
                        }
                    })
            
            # Generate embeddings
            texts = [chunk["content"] for chunk in chunks]
            embeddings = self.encoder.encode(texts)
            
            # Prepare points for Qdrant
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                points.append(
                    models.PointStruct(
                        id=i,
                        vector=embedding.tolist(),
                        payload={
                            "content": chunk["content"],
                            "source": chunk["metadata"]["source"],
                            "page": chunk["metadata"]["page"],
                            "path": chunk["metadata"]["path"]
                        }
                    )
                )
            
            # Upload to Qdrant
            self.client.upload_points(
                collection_name=QDRANT_COLLECTION,
                points=points
            )
            
            print(f"✅ Indexed {os.path.basename(pdf_path)}: {len(chunks)} chunks from {len(pages)} pages")
            
            return {
                "success": True,
                "file": os.path.basename(pdf_path),
                "chunks": len(chunks),
                "pages": len(pages)
            }
        
        except Exception as e:
            print(f"❌ Error indexing {pdf_path}: {e}")
            return {
                "success": False,
                "file": os.path.basename(pdf_path),
                "error": str(e)
            }
    
    def index_all_pdfs(self) -> List[Dict[str, Any]]:
        """Index all PDFs in the resources directory"""
        results = []
        
        # Create resources directory if it doesn't exist
        RESOURCES_DIR.mkdir(exist_ok=True)
        
        # Find all PDF files
        pdf_files = list(RESOURCES_DIR.glob("*.pdf"))
        
        if not pdf_files:
            print(f"⚠️ No PDF files found in {RESOURCES_DIR}")
            return results
        
        print(f"📚 Found {len(pdf_files)} PDF files to index")
        
        # Clear existing collection
        try:
            self.client.delete_collection(collection_name=QDRANT_COLLECTION)
            self._initialize_collection()
            print("🗑️ Cleared existing collection")
        except:
            pass
        
        # Index each PDF
        for pdf_file in pdf_files:
            result = self.index_pdf(str(pdf_file))
            results.append(result)
        
        # Print summary
        successful = sum(1 for r in results if r["success"])
        total_chunks = sum(r.get("chunks", 0) for r in results if r["success"])
        print(f"\n📊 Indexing Summary:")
        print(f"   - Successfully indexed: {successful}/{len(pdf_files)} files")
        print(f"   - Total chunks: {total_chunks}")
        
        return results
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        try:
            # Generate query embedding
            query_embedding = self.encoder.encode(query)
            
            # Search in Qdrant
            search_result = self.client.search(
                collection_name=QDRANT_COLLECTION,
                query_vector=query_embedding.tolist(),
                limit=top_k
            )
            
            # Format results
            results = []
            for hit in search_result:
                results.append({
                    "content": hit.payload.get("content", ""),
                    "metadata": {
                        "source": hit.payload.get("source", ""),
                        "page": hit.payload.get("page", 0),
                        "path": hit.payload.get("path", "")
                    },
                    "score": hit.score
                })
            
            return results
        
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            info = self.client.get_collection(collection_name=QDRANT_COLLECTION)
            return {
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "indexed_payload_count": info.indexed_vectors_count
            }
        except Exception as e:
            return {"error": str(e)}