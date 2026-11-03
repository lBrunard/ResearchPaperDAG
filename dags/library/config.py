import os
from pathlib import Path

PROJECT_DIR     = Path(__file__).resolve().parents[2]
LIBRARY_DIR     = Path(os.getenv("LIBRARY_DIR") or PROJECT_DIR / "ResearchLibrary")

PAPERS_DIR      = LIBRARY_DIR / "papers"
OUTPUT_DIR      = LIBRARY_DIR / "output"
DB_PATH         = PROJECT_DIR / "data" / "papers.db"
MARKDOWN_DIR    = PROJECT_DIR / "data" / "markdown"

OLLAMA_MODEL        = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL     = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
