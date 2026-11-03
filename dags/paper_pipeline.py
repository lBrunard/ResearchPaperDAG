import datetime
from airflow.sdk import dag, task
from library import scanner, converter, llm, database

@dag(start_date=datetime.datetime(2026,11,1), 
     schedule="@hourly", 
     tags=["paper"], 
     max_active_runs=1)
def paper_pipeline():
    @task
    def scan_new_pdf() -> list[str]:
        return scanner.find_new_pdf()

    @task
    def convert_pdf_markdown(pdf_path: str) -> dict:
        return converter.convert_pdf_markdown(pdf_path)

    @task
    def extract_metadata(doc: dict) -> dict:
        return llm.extract_metadata(doc)

    @task
    def save_to_sqlite(meta: dict):
        database.save_paper(
            filename=meta["filename"],
            summary=meta["summary"],
            title=meta["title"],
            keywords=meta["keywords"],
            category=meta["category"],
        )


    pdfs = scan_new_pdf()
    docs = convert_pdf_markdown.expand(pdf_path=pdfs)
    metas = extract_metadata.expand(doc=docs)
    save_to_sqlite.expand(meta=metas)



paper_pipeline()
    