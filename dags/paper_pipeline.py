import datetime

from airflow.sdk import TriggerRule, dag, task
from library import scanner, converter, llm, database, html_generator


@dag(
    start_date=datetime.datetime(2026, 11, 1),
    schedule="@hourly",
    catchup=False,
    tags=["paper"],
    max_active_runs=1,
)
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

    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def generate_html():
        return html_generator.generate_library_html()

    pdfs = scan_new_pdf()
    docs = convert_pdf_markdown.expand(pdf_path=pdfs)
    metas = extract_metadata.expand(doc=docs)
    saved_papers = save_to_sqlite.expand(meta=metas)

    # Only one task regenerates the full HTML page, after ALL mapped inserts.
    # NONE_FAILED also lets it run when the scan found no new PDFs (empty map).
    saved_papers >> generate_html()


paper_pipeline()
