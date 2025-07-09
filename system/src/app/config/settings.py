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
    PINECONE_INDEX_NAME: str = "rocket-support-agent-dataset"
    ROCKET_DOCS_PINECONE_INDEX_NAME: str = "rocket-docs-support-agent"

    # Indexing settings
    INDEXING_SIMILARITY_METRIC: str = "dotproduct"

    # Codebase indexing settings
    EMBEDDINGS_BATCH_SIZE: int = 80
    EMBEDDINGS_DIMENSION: int = 1024

    # MongoDB settings
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "rocket-support-agent"
    LLM_USAGE_COLLECTION_NAME: str = "llm_usage"
    ERROR_COLLECTION_NAME: str = "errors"

    # OpenAI settings
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_COMPLETION_ENDPOINT: str = "/chat/completions"
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_API_KEY: str

    # Gemini Settings
    GEMINI_API_KEY: str
    GEMINI_BASE_URL: str = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
    )
    GEMINI_COMPLETION_ENDPOINT: str = "generateContent"
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Voyage Settings
    VOYAGEAI_API_KEY: str
    VOYAGEAI_BASE_URL: str = "https://api.voyageai.com/v1"
    VOYAGEAI_RERANKING_MODEL: str = "rerank-2"

    class Config:
        env_file = ".env"


settings = Settings()
