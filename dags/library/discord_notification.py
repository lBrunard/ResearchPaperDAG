"""Send a Discord webhook message after a paper is saved and HTML is generated."""

import requests

from library.config import DISCORD_WEBHOOK_URL


def send_paper_notification(meta: dict) -> None:
    """Notify Discord about one successfully processed paper.

    Raises on a missing webhook or HTTP failure so Airflow marks the task failed.
    Never logs the webhook URL, which contains an authentication token.
    """
    if not DISCORD_WEBHOOK_URL:
        raise RuntimeError(
            "DISCORD_WEBHOOK_URL is missing. Add it to your local .env "
            "and ensure start.sh loads that file before Airflow starts."
        )

    # Bound each field to keep the Discord message below 2,000 characters.
    # Metadata comes from the LLM and may be unexpectedly long.
    title = str(meta["title"])[:250]
    category = str(meta["category"])[:100]
    keywords = ", ".join(str(word) for word in meta["keywords"])[:250]
    summary = str(meta["summary"])[:650]
    filename = str(meta["filename"])[:200]

    content = (
        "📄 **New research paper processed!**\n"
        f"**Title:** {title}\n"
        f"**Category:** {category}\n"
        f"**Keywords:** {keywords}\n"
        f"**Summary:** {summary}\n"
        f"**PDF:** {filename}"
    )

    # Disable automatic @everyone/@role/user mention parsing from LLM text.
    try:
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json={"content": content[:2000], "allowed_mentions": {"parse": []}},
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        # Requests errors may include the webhook URL (and its secret token).
        # Avoid propagating that exception into Airflow task logs.
        raise RuntimeError(
            f"Discord notification failed ({type(exc).__name__}). "
            "Check the webhook configuration and network connectivity."
        ) from None
    print(f"Discord notification sent for {filename}")
