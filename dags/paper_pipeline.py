import datetime

from airflow.sdk import TriggerRule, dag, task
from library import scanner, converter, llm, database, html_generator, discord_notification


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
    def save_to_sqlite(meta: dict) -> dict:
        database.save_paper(
            filename=meta["filename"],
            summary=meta["summary"],
            title=meta["title"],
            keywords=meta["keywords"],
            category=meta["category"],
        )
        # Pass only this newly processed paper to the notification task.
        return meta

    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def generate_html():
        return html_generator.generate_library_html()

    @task
    def notify_discord(meta: dict) -> None:
        discord_notification.send_paper_notification(meta)

    pdfs = scan_new_pdf()
    docs = convert_pdf_markdown.expand(pdf_path=pdfs)
    metas = extract_metadata.expand(doc=docs)
    saved_papers = save_to_sqlite.expand(meta=metas)

    # Only one task regenerates the full HTML page, after ALL mapped inserts.
    # NONE_FAILED also lets it run when the scan found no new PDFs (empty map).
    html_result = generate_html()
    saved_papers >> html_result

    # A notification is mapped for each saved paper, but must wait for the
    # single HTML regeneration task to succeed.
    notifications = notify_discord.expand(meta=saved_papers)
    html_result >> notifications


paper_pipeline()
