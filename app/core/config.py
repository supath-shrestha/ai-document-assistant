from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration.

    Values are loaded from environment variables and the .env file.
    """

    APP_NAME: str = "AI Document Assistant"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # PostgreSQL
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # Qdrant
    QDRANT_URL: str
    QDRANT_COLLECTION: str = "documents_ollama"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_CHAT_MODEL: str = "qwen3:4b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    # Embedding configuration
    EMBEDDING_DIMENSIONS: int = 768
    EMBEDDING_BATCH_SIZE: int = 32

    # Chunking configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Upload configuration
    MAX_UPLOAD_SIZE_MB: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
