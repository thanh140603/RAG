# RAG System - Retrieval-Augmented Generation

A RAG (Retrieval-Augmented Generation) system built with Clean Architecture + SOLID + DDD principles, enabling document upload and natural language querying with document context.

## ✨ Key Features

- **Document Management**: Upload and manage documents (PDF, DOCX, TXT, MD, HTML)
- **Document Grouping**: Organize documents into groups with color coding
- **RAG Query**: Query documents with natural language, supports conversation history
- **Chat Sessions**: Manage chat sessions with auto-generated titles
- **Multi-Query & Step-Back**: Improve retrieval with query variations
- **Hybrid Retrieval**: Combine vector search and BM25 keyword search
- **Token Tracking**: Monitor API token usage (Groq, Tavily) - Admin only
- **Web Search Fallback**: Automatically search web when no internal documents found
- **Authentication**: JWT-based authentication with role-based access control

## 🏗️ Project Structure

```
RAG/
├── client/                    # Frontend (React + TypeScript)
│   └── src/
│       ├── presentation/      # UI Components & Pages
│       ├── application/      # Use Cases & Services
│       ├── domain/           # Domain Entities & Repositories
│       └── infrastructure/   # API Clients & Repositories
│
├── server/                    # Backend (Python FastAPI)
│   └── src/
│       ├── domain/           # Domain Layer
│       │   ├── entities/     # Domain entities
│       │   └── repositories/ # Repository interfaces
│       ├── application/      # Application Layer
│       │   ├── usecases/     # Business use cases
│       │   └── services/    # Application services
│       └── infrastructure/   # Infrastructure Layer
│           ├── http/        # HTTP controllers & routes
│           ├── database/    # PostgreSQL + pgvector
│           ├── vector_store/# PgVector store abstraction
│           ├── rag/         # RAG pipeline components
│           ├── llm/         # LLM clients (Groq)
│           ├── storage/     # MinIO object storage
│           └── repositories/# Repository implementations
│
├── docker-compose.dev.yml    # Development environment
├── docker-compose.prod.yml   # Production environment
└── README.md
```

## 🔄 RAG Pipeline Flow

```
User Query
    ↓
Query Translation (Multi-Query) ──→ Generate query variations
    ↓
Step-Back Prompting (Optional) ──→ Abstract reasoning
    ↓
Retrieval ──→ Vector Search + BM25 (Hybrid)
    ↓
RAG Fusion (RRF) ──→ Merge & rank results
    ↓
Context Formatting ──→ Prepare for LLM
    ↓
LLM Generation ──→ Groq API
    ↓
Final Answer
```

## 🛠️ Tech Stack

### Frontend
- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Zustand** - State management
- **Tailwind CSS** - Styling
- **React Router** - Routing

### Backend
- **Python 3.11+** - Programming language
- **FastAPI** - Web framework
- **PostgreSQL + pgvector** - Database with vector search
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations
- **Groq** - LLM provider (OpenAI-compatible)
- **Sentence-Transformers** - Local embeddings
- **MinIO** - Object storage
- **JWT** - Authentication

## 📋 Prerequisites

- **Node.js 20+**
- **Python 3.11+**
- **Docker & Docker Compose**
- **API Keys**:
  - Groq API key (for LLM)
  - Tavily API key (optional, for web search)
  - Serper API key (optional, alternative web search)

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd RAG
```

### 2. Environment Setup

Create `.env` file from template and configure:

```bash
# Database
POSTGRES_DB=rag_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Groq (LLM)
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
GROQ_BASE_URL=https://api.groq.com/openai/v1

# Web Search (Optional)
TAVILY_API_KEY=your_tavily_key
SERPER_API_KEY=your_serper_key
ENABLE_WEB_SEARCH=true

# JWT
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=ragadmin
MINIO_SECRET_KEY=ragadmin123
MINIO_BUCKET=rag-documents
```

### 3. Development Mode

#### Option 1: Docker Compose (Recommended)

```bash
# Windows PowerShell
.\scripts\dev.ps1

# Linux/Mac
chmod +x scripts/dev.sh
./scripts/dev.sh

# Or manually
docker-compose -f docker-compose.dev.yml up --build
```

Services will run at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5433
- **MinIO**: http://localhost:9001

#### Option 2: Local Development

**Frontend:**
```bash
cd client
npm install
npm run dev
```

**Backend:**
```bash
cd server
python -m venv env
source env/bin/activate  
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --reload
```

### 4. Production Mode

```bash
# Windows PowerShell
.\scripts\prod.ps1

# Linux/Mac
chmod +x scripts/prod.sh
./scripts/prod.sh

# Or manually
docker-compose -f docker-compose.prod.yml up -d --build
```

## 📚 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user info

### Documents
- `GET /api/documents` - List documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents/{id}` - Get document details
- `DELETE /api/documents/{id}` - Delete document
- `POST /api/documents/{id}/reindex` - Re-index document

### Document Groups
- `GET /api/groups` - List groups
- `POST /api/groups` - Create group
- `PATCH /api/groups/{id}` - Update group
- `DELETE /api/groups/{id}` - Delete group

### Chat
- `GET /api/chats` - List chat sessions
- `POST /api/chats` - Create new chat
- `GET /api/chats/{id}` - Get chat with messages
- `POST /api/chats/{id}/messages` - Send message
- `PATCH /api/chats/{id}` - Update chat title
- `DELETE /api/chats/{id}` - Delete chat

### Tokens (Admin only)
- `GET /api/tokens/summary` - Token usage summary
- `GET /api/tokens/history` - Token usage history
- `PATCH /api/tokens/limits` - Update token limits

See details at: http://localhost:8000/docs

## 🔑 Key Features

### 1. Document Indexing
- **Chunking**: Semantic chunking with overlap
- **Embedding**: Local sentence-transformers (all-MiniLM-L6-v2)
- **Storage**: PostgreSQL with pgvector extension
- **Metadata**: Track chunk order, offsets, document info

### 2. Query Processing
- **Multi-Query**: Generate query variations to improve retrieval
- **Step-Back**: Abstract reasoning for complex queries
- **Hybrid Search**: Vector similarity + BM25 keyword search
- **RRF Fusion**: Reciprocal Rank Fusion to merge results

### 3. Context Management
- **Conversation History**: Maintain context across messages
- **Group Filtering**: Query documents in specific groups
- **Source Prioritization**: Internal documents > Web search
- **Context Formatting**: Clean document content for LLM

### 4. Chat Features
- **Auto-Title Generation**: Automatically generate title from first Q&A
- **Session Management**: Rename, delete chat sessions
- **Message History**: Full conversation history
- **Metadata Tracking**: Track sources, query variations, scores

### 5. Token Management
- **Usage Tracking**: Track Groq and Tavily token usage
- **Daily/Monthly Limits**: Set limits per provider
- **Admin Dashboard**: Monitor and manage token usage

## 🗄️ Database Schema

### Core Tables
- `users` - User accounts with roles
- `documents` - Document metadata
- `document_groups` - Document organization
- `chunks` - Document chunks
- `embeddings` - Vector embeddings (pgvector)
- `chat_sessions` - Chat sessions
- `chat_messages` - Chat messages
- `rag_queries` - RAG query logs
- `rag_retrieved_chunks` - Retrieved chunks log
- `api_token_usage` - Token usage tracking

## 🔧 Configuration

### RAG Settings
```python
CHUNK_SIZE=1000              
CHUNK_OVERLAP=200            
USE_SEMANTIC_CHUNKING=true   
TOP_K=10                    
USE_MULTI_QUERY=true         
USE_STEP_BACK=false      
USE_RERANKING=true           
ENABLE_WEB_SEARCH=true      
```

### LLM Settings
```python
GROQ_MODEL=llama-3.1-8b-instant
TEMPERATURE=0.7
MAX_TOKENS=2000
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=1536
```

## 🧪 Testing

```bash
cd server
pytest

cd client
npm test
```

## 📝 Development Notes

### Architecture Principles
- **Clean Architecture**: Separation of concerns
- **SOLID**: Single Responsibility, Dependency Inversion
- **DDD**: Domain-Driven Design
- **Repository Pattern**: Abstract data access
- **Use Case Pattern**: Business logic isolation

### Code Organization
- **Domain Layer**: Business entities and interfaces
- **Application Layer**: Use cases and business logic
- **Infrastructure Layer**: External dependencies (DB, APIs, etc.)

### Vector Store
- Uses `PgVectorStore` abstraction layer
- PostgreSQL with pgvector extension
- Cosine similarity search
- Support filtering by user_id and group_id

## 🐛 Troubleshooting

### Database Connection Issues
- Check PostgreSQL is running
- Verify credentials in `.env`
- Check port conflicts (default: 5433)

### Embedding Issues
- Verify sentence-transformers model is downloaded
- Check embedding dimension matches (1536)

### Token Limits
- Check Groq API key and limits
- Monitor usage in Tokens page (admin)
