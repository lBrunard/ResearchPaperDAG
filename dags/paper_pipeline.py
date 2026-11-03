import datetime
from airflow.sdk import dag, task
from library import scanner, converter

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



    pdfs = scan_new_pdf()
    docs = convert_pdf_markdown.expand(pdf_path=pdfs)



paper_pipeline()
    