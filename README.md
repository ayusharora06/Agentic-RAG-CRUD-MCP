# AI Agent System with CrewAI and MCP

An intelligent multi-agent system that combines database operations, document retrieval, and social profile enrichment using CrewAI framework and Model Context Protocol (MCP) servers.

## 🚀 Features

- **Multi-Agent Orchestration**: Intelligent routing between specialized agents
- **Database CRUD Operations**: Person and Bank account management via MCP servers
- **Document Search (RAG)**: PDF document retrieval using Qdrant vector database
- **Social Profile Enrichment**: Automatic GitHub and LinkedIn profile discovery
- **AI-Powered Data Masking**: Intelligent Aadhar number masking in documents
- **Dynamic Query Routing**: Automatic detection and routing of queries to appropriate agents

## 📋 Prerequisites

- Python 3.11 or higher
- Qdrant vector database
- OpenAI API key
- Serper API key (for social profile search)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd hackathon
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install and Run Qdrant

Using Docker:
```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```

## 🔑 Environment Configuration

### 1. Create `.env` File

Copy the example file and add your API keys:

```bash
cp .env.example .env
```

### 2. Configure API Keys

Edit `.env` and add your keys:

```env
# Required API Keys
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxx
SERPER_API_KEY=xxxxxxxxxxxxxxxxxxxx

# Optional: Qdrant Configuration (defaults shown)
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### 3. Getting API Keys

- **OpenAI API Key**: Get from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Serper API Key**: Get from [https://serper.dev](https://serper.dev) (free tier available)

## 🏃‍♂️ Running the Application

### 1. Ensure Qdrant is Running

Check Qdrant status:
```bash
curl http://localhost:6333/health
```

### 2. Start the FastAPI Server

```bash
python main.py
```

The server will start on `http://localhost:8003`

### 3. Verify Setup

Check the health endpoint:
```bash
curl http://localhost:8003/health
```

## 📡 API Documentation

### Base URL
```
http://localhost:8003
```

### Endpoints

#### 1. Health Check
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "crew": "initialized",
  "rag_pipeline": "initialized",
  "qdrant": {
    "status": "connected",
    "vectors": 0
  }
}
```

#### 2. Process Query
```http
POST /query
Content-Type: application/json

{
  "query": "your natural language query here"
}
```

Response:
```json
{
  "success": true,
  "query": "your query",
  "result": "AI-generated response",
  "routing": {
    "handler": "crud|pdf|multi",
    "confidence": 0.95
  }
}
```

#### 3. Index PDFs
```http
POST /index-pdfs
```

Indexes all PDFs in the `resources/` directory.


## 🏗️ Architecture

### Agent System
- **Orchestrator Agent**: Routes queries to appropriate specialist agents
- **CRUD Agent**: Handles database operations with Person and Bank MCP servers
- **PDF Agent**: Performs document search using RAG pipeline

### MCP Servers
- **Person Server** (`mcp_servers/person_server.py`): Manages person records
- **Bank Server** (`mcp_servers/bank_server.py`): Manages bank accounts

### RAG Pipeline
- Uses Qdrant vector database for document storage
- Sentence transformers for embeddings
- Supports PDF document indexing and retrieval


## 🐛 Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY not set"**
   - Ensure `.env` file exists and contains valid API key
   - Or export directly: `export OPENAI_API_KEY='your-key'`

2. **"Cannot connect to Qdrant"**
   - Ensure Qdrant is running on port 6333
   - Check with: `curl http://localhost:6333/health`

3. **"Serper API 403 Forbidden"**
   - Verify SERPER_API_KEY is correct
   - Check API key status at https://serper.dev

4. **Database locked errors**
   - SQLite is being used by multiple processes
   - Restart the application


## 📁 Project Structure

```
hackathon/
├── main.py                 # FastAPI server entry point
├── crew_v2.py             # CrewAI agent orchestration
├── config.py              # Configuration settings
├── load_env.py            # Environment variable loader
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── config/
│   ├── agents.yaml       # Agent configurations
│   └── tasks.yaml        # Task definitions
├── mcp_servers/
│   ├── person_server.py  # Person CRUD MCP server
│   └── bank_server.py    # Bank account MCP server
├── tools/
│   ├── database.py       # Database connection manager
│   ├── mcp_tool_wrapper.py # MCP tool sync wrapper
│   ├── rag_tools.py      # RAG search tools
│   └── serper_tool.py    # Social profile search
├── rag/
│   └── rag_pipeline.py   # RAG pipeline implementation
├── resources/            # PDF documents directory
└── db/
    └── main.db          # SQLite database

```

