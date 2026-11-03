from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
DB_PATH     = PROJECT_DIR / "data" / "papers.db"
PAPERS_DIR  = PROJECT_DIR / "ResearchLibrary" / "papers" 