import pymupdf4llm
from pathlib import Path
from library.config import MARKDOWN_DIR

def convert_pdf_markdown(pdf_path: str) -> list[str]:
    pdf = Path(pdf_path)
    MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)
    md_path = MARKDOWN_DIR / f"{pdf.stem}.md"
    md_path.write_text(pymupdf4llm.to_markdown(pdf_path), encoding="utf-8")  
    return       

