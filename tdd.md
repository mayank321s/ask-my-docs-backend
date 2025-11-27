# Technical Design Document (TDD): Ask My Docs

**Version:** 1.0 
**Project:** Ask My Docs - Intelligent Document Query System 

## 1. Executive Summary

### 1.1 Project Purpose

Ask My Docs is an intelligent document query system that leverages Large Language Models (LLMs) and vector search technology to enable users to upload documents and interact with their content through natural language conversations. The system transforms static documentation into an interactive knowledge base with semantic search capabilities.

### 1.2 Core Features

- **Document Processing Pipeline**: Upload and process PDF, Word documents, and code repositories with automatic text extraction and chunking
- **Vector-Based Semantic Search**: Qdrant vector database with 768-dimensional embeddings for contextually relevant retrieval
- **AI-Powered Conversational Interface**: Context-aware responses using HuggingFace (Qwen2.5-7B-Instruct) and Ollama (Llama3) models
- **Session-Based Memory**: LangChain-powered conversation history for multi-turn dialogues
- **Multi-Tenant Architecture**: JWT authentication with user and project-level isolation
- **GitHub Integration**: Sync and query code repositories directly from GitHub
- **Category Management**: Organize documents into logical namespaces for filtered searches

### 1.3 Target Use Cases

- Development teams querying technical specifications and API documentation
- Organizations managing large document repositories across multiple projects
- Engineering teams requiring intelligent code search and explanation capabilities
- Businesses needing conversational interfaces for internal knowledge bases

### 1.4 Key Technical Decisions

- **FastAPI** chosen for high-performance async operations and automatic OpenAPI documentation
- **Qdrant** selected for production-ready vector search with namespace-based filtering capabilities
- **Ollama** for local LLM inference providing privacy and cost control
- **Tortoise ORM** for async database operations with Django-like syntax
- **LangChain** for standardized text processing and memory management

---

## 2. System Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Client Layer │
│ (Web/Mobile Applications) │
└────────────────────────┬────────────────────────────────┘
 │
 │ HTTPS/REST API
 │
┌────────────────────────▼────────────────────────────────┐
│ FastAPI Backend │
│ ┌──────────────────────────────────────────────────┐ │
│ │ API Layer (v1, v2) │ │
│ │ • Authentication & Authorization │ │
│ │ • Project Management │ │
│ │ • Document Management │ │
│ │ • Chat & Search │ │
│ │ • GitHub Integration │ │
│ └────────────────────┬─────────────────────────────┘ │
│ │ │
│ ┌────────────────────▼─────────────────────────────┐ │
│ │ Service Layer │ │
│ │ • Business Logic Orchestration │ │
│ │ • Data Validation & Transformation │ │
│ │ • Cross-cutting Concerns │ │
│ └────────────────────┬─────────────────────────────┘ │
│ │ │
│ ┌────────────────────▼─────────────────────────────┐ │
│ │ Core Components │ │
│ │ • LLM Integration (HuggingFace, Ollama) │ │
│ │ • Vector Database Client (Qdrant) │ │
│ │ • Document Chunker (LangChain) │ │
│ │ • Memory Management │ │
│ └────────────────────┬─────────────────────────────┘ │
│ │ │
│ ┌────────────────────▼─────────────────────────────┐ │
│ │ Repository Layer │ │
│ │ • Data Access Abstraction │ │
│ │ • CRUD Operations │ │
│ └────────────────────┬─────────────────────────────┘ │
└───────────────────────┼─────────────────────────────────┘
 │
 ┌───────────────┴───────────────┐
 │ │
┌───────▼─────────┐ ┌────────▼──────────┐
│ PostgreSQL │ │ Qdrant │
│ (Tortoise ORM) │ │ (Vector Store) │
│ │ │ │
│ • Users │ │ • Collections │
│ • Projects │ │ • Vectors │
│ • Documents │ │ • Metadata │
│ • Chat History │ │ • Namespaces │
└─────────────────┘ └────────┬──────────┘
 │
 ┌───────▼──────────┐
 │ Ollama Server │
 │ │
 │ • LLM Models │
 │ • Embeddings │
 └──────────────────┘
```

### 2.2 Component Interactions

#### 2.2.1 Document Upload Flow
```
1. Client uploads document → API Controller (multipart/form-data)
2. Controller validates file and metadata → Document Service
3. Service extracts text → Document Parser (PyMuPDF/python-docx)
4. Parser returns raw text → Chunker Service
5. Chunker splits text → LangChain RecursiveCharacterTextSplitter
 (300 char chunks, 30 char overlap)
6. Chunks sent to Ollama → Generate embeddings (nomic-embed-text, 768-dim)
7. Embeddings + metadata → Qdrant Client
8. Qdrant upserts vectors (batch size: 50)
9. Document metadata → PostgreSQL (Tortoise ORM)
10. Success response → Client with document ID and chunk count
```

#### 2.2.2 Query & Answer Flow
```
1. User submits question → Chat Controller (with projectId, categoryId, sessionId)
2. Controller validates → Chat Service
3. Service embeds question → Ollama Embedding API
4. Query vector → Qdrant Client
5. Qdrant performs vector search (limit: 8, filtered by namespace)
6. Top-K chunks retrieved → Context Builder
7. Context + Question + Chat History → LLM Service
8. LLM generates answer → HuggingFace/Ollama
9. Answer + Chat History → PostgreSQL (Chat Repository)
10. Response → Client (answer, sessionId, contextChunksCount)
```

### 2.3 Design Principles

The system follows these architectural principles:

1. **Separation of Concerns**: Clear boundaries between presentation, business logic, data access, and infrastructure layers
2. **Dependency Injection**: Loose coupling through FastAPI's dependency injection system
3. **Async/Await Pattern**: Non-blocking I/O operations for better concurrency and throughput
4. **Type Safety**: Pydantic models for request/response validation and serialization
5. **Repository Pattern**: Data access abstraction for testability and maintainability
6. **Single Responsibility**: Each module focuses on one well-defined purpose

---

## 3. Architecture Design

### 3.1 Layered Architecture

The system implements a strict four-layer architecture:

#### Layer 1: Presentation Layer (API)
- **Location**: `app/api/v1/`, `app/api/v2/`
- **Responsibility**: HTTP request handling, response formatting, route definitions
- **Components**: Controllers, request/response DTOs, middleware
- **Key Files**: 
 - `auth_controller.py` - Authentication endpoints
 - `project_controller.py` - Project management
 - `documents_controller.py` - Document operations
 - `chat_controller.py` - Chat and search endpoints

#### Layer 2: Business Logic Layer (Services)
- **Location**: `app/api/v{version}/{domain}/*_service.py`
- **Responsibility**: Business rules, workflow orchestration, data transformation
- **Components**: Service classes that coordinate between repositories and core components
- **Key Files**:
 - `chat_service.py` - Chat logic, context building, LLM interaction
 - `document_service.py` - Document processing orchestration
 - `project_service.py` - Project and category management

#### Layer 3: Data Access Layer (Repositories)
- **Location**: `app/core/repository/`
- **Responsibility**: Database operations, query building, data persistence
- **Components**: Repository classes extending base repository
- **Key Files**:
 - `base_repository.py` - Generic CRUD operations
 - `vector_index_repository.py` - Vector index operations
 - `chat_repository.py` - Chat history persistence
 - `document_repository.py` - Document metadata operations

#### Layer 4: Infrastructure Layer
- **Responsibility**: External service integration, database connections, vector storage
- **Components**:
 - **Core Modules**: `app/core/llm/`, `app/core/qdrant/`, `app/core/chunker/`
 - **Configuration**: `app/config/cfg.py`, `app/config/db.py`
 - **Models**: `app/core/models/tortoise/`

### 3.3 Data Flow Architecture

#### 3.3.1 Request Processing Flow
```
HTTP Request
 ↓
Middleware (CORS, Logging)
 ↓
Route Handler (Controller)
 ↓
Request Validation (Pydantic)
 ↓
Dependency Injection (Authentication)
 ↓
Service Layer (Business Logic)
 ↓
Repository Layer (Data Access)
 ↓
Database/Vector Store
 ↓
Response Transformation (DTO)
 ↓
HTTP Response
```

#### 3.3.2 Error Propagation Flow
```
Exception Raised (Any Layer)
 ↓
Service Layer catches and logs
 ↓
Transform to HTTPException
 ↓
FastAPI Exception Handler
 ↓
JSON Error Response
 {
 "detail": "Error message"
 }
```

---

## 4. Technology Stack

### 4.1 Backend Framework

#### FastAPI 0.111.0+
**Selection Rationale**:
- High performance comparable to NodeJS and Go
- Automatic OpenAPI/Swagger documentation generation
- Built-in request/response validation with Pydantic
- Native async/await support for concurrent operations
- Modern Python type hints for better IDE support

### 4.2 Database Layer

#### 4.2.1 PostgreSQL (Relational Database)
**Purpose**: Primary data store for structured data

**Tables**:
- Users, Projects, VectorIndexes, VectorNamespaces
- Documents, VectorChunks, Chats
- GitHub-related tables (GithubRepo, GithubBranch, GithubToken, GithubPullRequest)

#### 4.2.2 Tortoise ORM 0.21.3
**Selection Rationale**:
- Async ORM with Django-like API
- Migration support via Aerich
- Type hints and IDE support
- Performance optimized for async operations

#### 4.2.3 Qdrant v1.13.4 (Vector Database)
**Selection Rationale**:
- High-performance vector similarity search
- Namespace-based filtering for multi-tenancy
- Cosine similarity distance metric
- REST and gRPC APIs
- Payload indexing for metadata filtering

**Key Features**:
- **Vector Dimension**: 768 (nomic-embed-text)
- **Distance Metric**: Cosine similarity
- **Indexing**: HNSW (Hierarchical Navigable Small World)
- **Batch Operations**: Batch size 50 for upserts

### 4.3 AI/ML Components

#### 4.3.1 LLM Providers

**HuggingFace Inference API**
- **Model**: Qwen/Qwen2.5-7B-Instruct
- **Provider**: Together AI
- **Parameters**:
 - Max tokens: 512
 - Temperature: 0.7
 - Top-p: 0.95
- **Use Case**: Production inference with high quality responses

**Ollama (Local Inference)**
- **Models**: llama3.2:1b, llama3.1
- **Endpoint**: `http://127.0.0.1:11434`
- **Timeout**: 300 seconds
- **Use Case**: Privacy-focused local inference, development environment

#### 4.3.2 Embedding Generation

**nomic-embed-text**
- **Dimensions**: 768
- **Provider**: Ollama
- **Endpoint**: `POST /api/embed`
- **Batch Processing**: Supports batch embedding generation

**Performance Characteristics**:
- Average embedding time: ~100-150ms per chunk
- Batch size: 50 chunks per request
- Context window: 8192 tokens

#### 4.3.3 Text Processing

**LangChain Framework**
- **RecursiveCharacterTextSplitter**:
 - Chunk size: 300 characters
 - Chunk overlap: 30 characters (10%)
 - Separators: `["\n\n", "\n", " ", ""]`
 
- **ChatMessageHistory**: In-memory conversation storage
- **RunnableWithMessageHistory**: Session-based memory integration
- **ChatPromptTemplate**: Structured prompt engineering

### 4.4 Document Processing

**PyMuPDF (fitz)**
- **Purpose**: PDF text extraction
- **Features**: High-performance, layout preservation, metadata extraction

**python-docx**
- **Purpose**: Word document (.docx) processing
- **Features**: Paragraph extraction, formatting preservation

**python-multipart**
- **Purpose**: File upload handling
- **Features**: Multipart form-data parsing, streaming uploads


### 6.1 API Versioning Strategy

The system maintains two API versions:

- **v1** (`/api/v1/`): Legacy endpoints without authentication
- **v2** (`/api/v2/`): Current version with JWT authentication (recommended)



### 6.5 Chat & Search Endpoints (v2)

#### 6.5.1 Search and Answer
```http
POST /api/v2/chat/search-and-answer
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
 "projectId": 1,
 "categoryId": 1,
 "query": "How does the authentication system work?",
 "sessionId": "550e8400-e29b-41d4-a716-446655440000" // Optional
}

Response (200 OK):
{
 "answer": "The authentication system uses JWT tokens with bcrypt password hashing. When a user logs in, the server validates credentials against the PostgreSQL database, generates a JWT token with userId and emailAddress claims, and returns it to the client. The token must be included in the Authorization header for subsequent requests.",
 "sessionId": "550e8400-e29b-41d4-a716-446655440000",
 "memoryEnabled": true,
 "contextChunksCount": 5
}

Processing Flow:
1. Validate project and category access
2. Embed query using Ollama (nomic-embed-text)
3. Search Qdrant (top-8 chunks, filtered by namespace)
4. Load conversation history (if sessionId provided)
5. Build context from retrieved chunks
6. Generate answer using LLM (HuggingFace/Ollama)
7. Save conversation to chat history
8. Return response with sessionId

Performance:
- Average response time: 2-3 seconds
- Embedding generation: ~150ms
- Vector search: ~50-100ms
- LLM inference: 1.5-2.5 seconds
```


**Common HTTP Status Codes**:
- `200 OK` - Successful GET/DELETE
- `201 Created` - Successful POST
- `400 Bad Request` - Invalid input/validation error
- `401 Unauthorized` - Missing or invalid authentication token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Duplicate resource (e.g., email, project name)
- `422 Unprocessable Entity` - Pydantic validation failed
- `500 Internal Server Error` - Server-side error

#### 7.2.1 Connection Management

```python
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

# Initialize client
qdrant = QdrantClient(
 url="http://152.67.163.210:6333", # Production Qdrant server
 timeout=60
)
```

**Chunking Strategy**:

The recursive character text splitter attempts to split on these separators in order:
1. Double newlines (`\n\n`) - paragraph boundaries
2. Single newlines (`\n`) - line boundaries
3. Spaces (` `) - word boundaries
4. Characters (`""`) - character boundaries

**Chunk Overlap Rationale**:
- 30 characters (10% of chunk size) ensures context continuity
- Prevents information loss at chunk boundaries
- Improves retrieval quality for queries spanning chunks

**Current System Performance** (based on implementation):

| Operation | Avg Time | Optimizations |
|-----------|----------|---------------|
| Document Upload (10 pages) | 8-12s | Batch embedding generation, async I/O |
| Vector Search | 50-100ms | HNSW indexing, namespace filtering |
| Embedding Generation | 100-150ms/chunk | Ollama local inference |
| LLM Response (HuggingFace) | 1.5-2.5s | Streaming disabled, max 512 tokens |
| LLM Response (Ollama) | 3-5s | Local inference, smaller models |
| End-to-End Query | 2-3s | Combined vector search + LLM |
