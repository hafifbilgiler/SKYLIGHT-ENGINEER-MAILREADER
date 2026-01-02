import os

DATABASE_URL = os.getenv("DATABASE_URL", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://skylight-engineer-mailreader-llm:8080")
MASTER_KEY = os.getenv("MAILREADER_MASTER_KEY", "")
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "3"))
