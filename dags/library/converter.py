import pymupdf4llm


def convert_pdf_markdown(paths: list[str]) -> list[str]:
    res = []
    for path in paths:
        md = pymupdf4llm.to_markdown(path)
        

