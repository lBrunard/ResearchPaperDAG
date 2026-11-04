"""Run with: PYTHONPATH=dags .venv/bin/python -m unittest discover -s tests -p 'test_discord_notification.py' -v"""
import unittest
from unittest.mock import patch, Mock

from library.discord_notification import send_paper_notification

SAMPLE_META = {
    "filename": "new_paper.pdf",
    "title": "Example paper",
    "summary": "An example summary.",
    "keywords": ["Data", "Pipelines"],
    "category": "Data Engineering",
}


class DiscordNotificationTests(unittest.TestCase):
    @patch("library.discord_notification.DISCORD_WEBHOOK_URL", "")
    @patch("library.discord_notification.requests.post")
    def test_missing_webhook_fails_without_request(self, post):
        with self.assertRaisesRegex(RuntimeError, "DISCORD_WEBHOOK_URL"):
            send_paper_notification(SAMPLE_META)
        post.assert_not_called()

    @patch("library.discord_notification.DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/example/token")
    @patch("library.discord_notification.requests.post")
    def test_sends_paper_metadata_without_mentions(self, post):
        post.return_value = Mock(status_code=204)
        send_paper_notification(SAMPLE_META)
        post.assert_called_once()
        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://discord.com/api/webhooks/example/token")
        self.assertEqual(kwargs["json"]["allowed_mentions"], {"parse": []})
        self.assertIn("Example paper", kwargs["json"]["content"])
        self.assertIn("new_paper.pdf", kwargs["json"]["content"])
        self.assertLessEqual(len(kwargs["json"]["content"]), 2000)
        self.assertEqual(kwargs["timeout"], 15)
        post.return_value.raise_for_status.assert_called_once()

    @patch("library.discord_notification.DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/example/token")
    @patch("library.discord_notification.requests.post")
    def test_http_errors_propagate_to_airflow(self, post):
        from requests import HTTPError
        post.return_value.raise_for_status.side_effect = HTTPError("403 Forbidden")
        with self.assertRaisesRegex(RuntimeError, "Discord notification failed") as context:
            send_paper_notification(SAMPLE_META)
        self.assertNotIn("example/token", str(context.exception))

    @patch("library.discord_notification.DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/example/token")
    @patch("library.discord_notification.requests.post")
    def test_long_metadata_is_truncated(self, post):
        post.return_value = Mock(status_code=204)
        meta = {**SAMPLE_META, "title": "X" * 5000, "summary": "Y" * 5000}
        send_paper_notification(meta)
        self.assertLessEqual(len(post.call_args.kwargs["json"]["content"]), 2000)


if __name__ == "__main__":
    unittest.main()
