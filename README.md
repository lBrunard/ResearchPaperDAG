# ResearchPaperDAG — Airflow research-paper library

Local Airflow pipeline for a searchable research-paper library (INFO-H420, Assignment 3).

## What works

1. `scan_new_pdf` finds PDF filenames missing from the SQLite database.
2. `convert_pdf_markdown` converts each new PDF using PyMuPDF4LLM.
3. `extract_metadata` asks a locally served Ollama model for JSON metadata.
4. `save_to_sqlite` inserts the metadata into `data/papers.db`.
5. `generate_html` **regenerates `ResearchLibrary/output/index.html`** from every record in the database.

The HTML includes a title, summary, keywords, category, links to original PDFs, text search, and category filtering. Discord notifications are not implemented in this version.

## Folder layout

```text
ResearchPaperDAG/
├── dags/
│   ├── paper_pipeline.py
│   └── library/
│       ├── config.py
│       ├── converter.py
│       ├── database.py
│       ├── html_generator.py
│       ├── llm.py
│       └── scanner.py
├── ResearchLibrary/
│   ├── papers/            # Local test PDF files; can point to Drive sync
│   └── output/
│       └── index.html     # Generated; do not edit manually
├── data/
│   ├── papers.db          # SQLite local only; not for Google Drive
│   └── markdown/
├── requirements.txt
├── setup.sh
└── start.sh
```

## First-time setup (macOS/Linux)

Install `uv` and Ollama before starting. From the root of the project:

```bash
bash setup.sh
```

This script creates `.venv` using Python 3.13 and installs Airflow 3.3.2 and the packages listed in `requirements.txt`.

Start Ollama separately if needed, and ensure the configured model exists:

```bash
ollama pull qwen2.5:7b
# If it is not already running as a service:
ollama serve
```

Then in another terminal:

```bash
bash start.sh
```

Open <http://localhost:8080> and find `paper_pipeline` on the **DAGs** tab. The generated Airflow login password is stored locally under `airflow_home/` (do not share it).

## Test the HTML generator

- Put a PDF in `ResearchLibrary/papers/` and trigger `paper_pipeline`.
- Wait for all tasks, including `generate_html`, to succeed.
- Open `ResearchLibrary/output/index.html` in a local browser.
- Search for a keyword or filter by category; open a paper's PDF link.

To regenerate the HTML without calling Airflow or the LLM, run:

```bash
PYTHONPATH=dags .venv/bin/python -m library.html_generator
```

**Empty page?** The `papers` SQLite table in the originally shared ZIP was empty. The page will display an empty-library message until a PDF has been processed successfully. Check task logs if `extract_metadata` or `save_to_sqlite` failed.

## Google Drive-synced library

Your project currently defaults to the local `ResearchLibrary/` folder. To point it to a folder synced by Google Drive instead, set the `LIBRARY_DIR` environment variable when starting Airflow:

```bash
LIBRARY_DIR="/absolute/path/to/Google Drive/ResearchLibrary" bash start.sh
```

Keep its `papers/` and `output/` subfolders together. `output/index.html` links to each PDF using the relative URL `../papers/<filename>`.

**Do not sync the SQLite database**: `data/papers.db` remains inside the local project directory.

Google Drive's online preview may block JavaScript; open the locally synced HTML file in a browser for search/filter interaction.

## Notes for team collaboration

The original project uses `setup.sh`, `requirements.txt`, and `uv pip`, **not** a checked-in `pyproject.toml` / `uv.lock`. For consistent environments, keep the Airflow version specified in `setup.sh` the same among teammates. You can migrate to uv project mode later if desired.

Keep `.venv/`, `.env`, `airflow_home/`, `data/` and the local `ResearchLibrary/` out of Git. In particular, `airflow_home/` contains generated local credentials. Review the existing `.gitignore` before pushing.

The scheduled DAG runs hourly. Because it dynamically maps over newly detected PDFs, the new single `generate_html` task uses `TriggerRule.NONE_FAILED`: it runs after all successful database saves and also when there are no new PDFs; if any upstream mapped save fails, it does not regenerate the page.
