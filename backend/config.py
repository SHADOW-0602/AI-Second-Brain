import os
from dotenv import load_dotenv

load_dotenv()

# R2 Storage Configuration
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL")

# Qdrant Configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "second_brain")
QDRANT_SCORE_THRESHOLD = float(os.getenv("QDRANT_SCORE_THRESHOLD", "0.6"))

# Server Configuration
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("PORT", os.getenv("SERVER_PORT", "10000")))

# Processing Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "64"))
MIN_CHUNK_SIZE = int(os.getenv("MIN_CHUNK_SIZE", "50"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))
VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", "384"))

# Database Configuration
DB_TIMEOUT = int(os.getenv("DB_TIMEOUT", "30"))
DB_RETRY_ATTEMPTS = int(os.getenv("DB_RETRY_ATTEMPTS", "3"))
DB_CONNECTION_POOL_SIZE = int(os.getenv("DB_CONNECTION_POOL_SIZE", "10"))

# Analytics Configuration
ANALYTICS_SEARCH_COLLECTION = os.getenv("ANALYTICS_SEARCH_COLLECTION", "analytics_search_history")
ANALYTICS_FILE_ACCESS_COLLECTION = os.getenv("ANALYTICS_FILE_ACCESS_COLLECTION", "analytics_file_access")
ANALYTICS_METRICS_COLLECTION = os.getenv("ANALYTICS_METRICS_COLLECTION", "analytics_usage_metrics")

# Cleanup Configuration
CLEANUP_DAYS_OLD = int(os.getenv("CLEANUP_DAYS_OLD", "30"))
CLEANUP_BATCH_SIZE = int(os.getenv("CLEANUP_BATCH_SIZE", "1000"))

# Workflow Configuration
WORKFLOW_WEBHOOK_URL = os.getenv("WORKFLOW_WEBHOOK_URL")
WORKFLOW_API_KEY = os.getenv("WORKFLOW_API_KEY")

# LangSmith Configuration
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "true")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "ai-second-brain")

if not QDRANT_URL:
    raise ValueError("QDRANT_URL is not set in .env")


