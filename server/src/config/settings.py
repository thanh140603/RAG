"""
Application settings with environment-based configuration
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional
from functools import lru_cache
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from parent directory (same level as server folder)
env_path = Path(__file__).parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "dev")
    debug: bool = os.getenv("ENVIRONMENT", "dev") == "dev"
    
    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_reload: bool = os.getenv("API_RELOAD", "true").lower() == "true"
    api_workers: int = int(os.getenv("API_WORKERS", "1"))
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from JSON array or comma-separated string"""
        import json
        if isinstance(v, str):
            # Try to parse as JSON array first
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                # If not JSON, treat as comma-separated string
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    # Database
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "rag_db")
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    
    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    # Vector Store
    vector_store_type: str = os.getenv("VECTOR_STORE_TYPE", "pgvector")
    pgvector_dimension: int = int(os.getenv("PGVECTOR_DIMENSION", "1536"))
    faiss_index_path: str = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
    chroma_persist_directory: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db")
    chroma_host: str = os.getenv("CHROMA_HOST", "localhost")
    chroma_port: int = int(os.getenv("CHROMA_PORT", "8001"))
    
    # Object Storage
    storage_provider: str = os.getenv("STORAGE_PROVIDER", "minio")
    # In Docker, use service name 'minio', otherwise use 'localhost'
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "ragadmin")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "ragadmin123")
    minio_bucket: str = os.getenv("MINIO_BUCKET", "rag-documents")
    minio_secure: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    # Optional external endpoint for presigned URLs (e.g., http://localhost:9000)
    minio_external_endpoint: Optional[str] = os.getenv("MINIO_EXTERNAL_ENDPOINT")
    
    # LLM - Groq (OpenAI-compatible) as default provider for chat
    llm_provider: str = os.getenv("LLM_PROVIDER", "groq")
    groq_api_key: Optional[str] = os.getenv("GROQ_API_KEY")
    # Chat model
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    groq_base_url: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    # Groq embedding model (legacy, no longer used now that we embed locally)
    groq_embedding_model: str = os.getenv("GROQ_EMBEDDING_MODEL", "nomic-embed-text")

    # Local embedding model name for sentence-transformers
    hf_embedding_model: str = os.getenv("HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    # Optional vLLM settings (not used yet)
    vllm_base_url: str = os.getenv("VLLM_BASE_URL", "http://localhost:8002")
    vllm_model_name: str = os.getenv("VLLM_MODEL_NAME", "mistral-7b-instruct")
    vllm_api_key: Optional[str] = os.getenv("VLLM_API_KEY")

    embedding_model: str = os.getenv("EMBEDDING_MODEL", "openai")
    embedding_dimension: int = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
    
    # RAG Configuration
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    use_semantic_chunking: bool = os.getenv("USE_SEMANTIC_CHUNKING", "true").lower() == "true"
    top_k: int = int(os.getenv("TOP_K", "10"))
    retrieval_method: str = os.getenv("RETRIEVAL_METHOD", "hybrid")
    
    use_multi_query: bool = os.getenv("USE_MULTI_QUERY", "true").lower() == "true"
    multi_query_count: int = int(os.getenv("MULTI_QUERY_COUNT", "3"))
    use_step_back_prompting: bool = os.getenv("USE_STEP_BACK_PROMPTING", "false").lower() == "true"
    
    use_reranking: bool = os.getenv("USE_RERANKING", "true").lower() == "true"
    reranking_method: str = os.getenv("RERANKING_METHOD", "rrf")
    
    max_tokens: int = int(os.getenv("MAX_TOKENS", "1000"))
    temperature: float = float(os.getenv("TEMPERATURE", "0.7"))
    
    # Web Search / External Knowledge
    enable_web_search: bool = os.getenv("ENABLE_WEB_SEARCH", "false").lower() == "true"
    web_search_provider: str = os.getenv("WEB_SEARCH_PROVIDER", "tavily")  # tavily or serper
    tavily_api_key: Optional[str] = os.getenv("TAVILY_API_KEY")
    serper_api_key: Optional[str] = os.getenv("SERPER_API_KEY")
    web_search_max_results: int = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "3"))
    web_search_fallback_threshold: float = float(os.getenv("WEB_SEARCH_FALLBACK_THRESHOLD", "0.5"))  # Use web search if internal score < threshold
    
    # Authentication
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    jwt_refresh_token_expire_days: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # File Upload
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    allowed_file_types: List[str] = os.getenv("ALLOWED_FILE_TYPES", "pdf,docx,txt,md").split(",")
    upload_directory: str = os.getenv("UPLOAD_DIRECTORY", "./uploads")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO" if not debug else "DEBUG")
    log_file: str = os.getenv("LOG_FILE", "./logs/app.log")
    
    # Redis (Optional)
    redis_host: Optional[str] = os.getenv("REDIS_HOST")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    
    class Config:
        # Look for .env file in parent directory (same level as server folder)
        env_file = str(Path(__file__).parent.parent.parent.parent / ".env")
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

