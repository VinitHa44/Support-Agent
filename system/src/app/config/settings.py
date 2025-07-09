from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Pinecone settings
    PINECONE_API_KEY: str
    PINECONE_CREATE_INDEX_URL: str = "https://api.pinecone.io/indexes"
    PINECONE_API_VERSION: str = "2025-01"
    PINECONE_EMBED_URL: str = "https://api.pinecone.io/embed"
    PINECONE_UPSERT_URL: str = "https://{}/vectors/upsert"
    PINECONE_RERANK_URL: str = "https://api.pinecone.io/rerank"
    PINECONE_QUERY_URL: str = "https://{}/query"
    PINECONE_LIST_INDEXES_URL: str = "https://api.pinecone.io/indexes"
    PINECONE_INDEX_NAME: str = "support-agent-dataset"

    # MongoDB settings
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "rocket-classification-system-v2"
    LLM_USAGE_COLLECTION_NAME: str = "llm_usage"
    ERROR_COLLECTION_NAME: str = "errors"

    class Config:
        env_file = ".env"


settings = Settings()
