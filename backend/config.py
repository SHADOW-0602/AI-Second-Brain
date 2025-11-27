import os
from dotenv import load_dotenv

load_dotenv()

R2_ENDPOINT = os.getenv("R2_ENDPOINT", "https://617c07ad9ac38cde394c399b3f7eb0a6.r2.cloudflarestorage.com")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "second-brain")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "https://pub-c8d242a9e7194c5eb8291af9db008248.r2.dev")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not QDRANT_URL:
    raise ValueError("QDRANT_URL is not set in .env")


