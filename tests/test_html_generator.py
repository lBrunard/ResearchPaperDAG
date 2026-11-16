"""Run with: python -m unittest discover -s tests -v"""
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dags"))

from library import database, html_generator


class HtmlGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.db_path = database.DB_PATH
        self.output_dir = html_generator.OUTPUT_DIR
        database.DB_PATH = Path(self.tmp.name) / "data" / "papers.db"
        html_generator.OUTPUT_DIR = Path(self.tmp.name) / "ResearchLibrary" / "output"

    def tearDown(self):
        database.DB_PATH = self.db_path
        html_generator.OUTPUT_DIR = self.output_dir
        self.tmp.cleanup()

    def test_empty_library(self):
        html = Path(html_generator.generate_library_html()).read_text()
        self.assertIn("No papers yet", html)
        self.assertIn("0 paper(s)", html)

    def test_searchable_catalog_escapes_untrusted_content(self):
        database.save_paper(
            filename="AI & Ethics.pdf",
            title="Paper <script>alert(1)</script>",
            summary="Research on privacy.",
            keywords=["privacy", "trust"],
            category="Data Engineering",
        )
        html = Path(html_generator.generate_library_html()).read_text()
        self.assertIn("Paper &lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn("Paper <script>alert(1)</script>", html)
        self.assertIn("../papers/AI%20%26%20Ethics.pdf", html)
        self.assertIn('value="Data Engineering"', html)
        self.assertIn('id="search"', html)
        self.assertIn('id="category-filter"', html)


if __name__ == "__main__":
    unittest.main()
