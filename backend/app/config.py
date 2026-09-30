import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Postgres
    POSTGRES_HOST: str = os.environ.get("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.environ.get("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.environ.get("POSTGRES_DB", "ats_db")
    POSTGRES_USER: str = os.environ.get("POSTGRES_USER", "ats_user")
    POSTGRES_PASSWORD: str = os.environ.get("POSTGRES_PASSWORD", "ats_pass")

    # OpenAI
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_LLM_MODEL: str = os.environ.get("OPENAI_LLM_MODEL", "gpt-4o-mini")
    OPENAI_EMBEDDING_MODEL: str = os.environ.get(
        "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
    )
    EMBEDDING_DIM: int = int(os.environ.get("EMBEDDING_DIM", "1536"))

    # Chunking del CV para el RAG
    CHUNK_SIZE: int = int(os.environ.get("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(os.environ.get("CHUNK_OVERLAP", "150"))

    # Cuantos chunks trae la busqueda por similitud, por skill, por CV
    RAG_TOP_K: int = int(os.environ.get("RAG_TOP_K", "5"))

    # CORS (para que el frontend en Vite pueda pegarle al backend)
    CORS_ORIGINS: list[str] = os.environ.get(
        "CORS_ORIGINS", "http://localhost:5173"
    ).split(",")


settings = Settings()
