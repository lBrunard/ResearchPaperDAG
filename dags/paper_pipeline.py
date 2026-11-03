import datetime
from airflow.sdk import dag, task
from library import scanner

@dag(start_date=datetime.datetime(2026,11,1), 
     schedule="@hourly", 
     tags=["paper"], 
     max_active_runs=1)
def paper_pipeline():
    @task
    def scan_new_pdf() -> list[str]:
        return scanner.find_new_pdf()

    @task
    def convert_pdf_markdown():
        return ...



    pdfs = scan_new_pdf()


paper_pipeline()
    