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

## Discord webhook integration — ResearchPaperDAG

This update assumes the earlier HTML version of the DAG is working. It adds a
notification for **each new PDF that has been successfully saved and included
in the regenerated HTML library**.

# 1. Create the Discord webhook

In a Discord server where you have permission to manage webhooks, choose the
channel, then open **Edit Channel → Integrations → Webhooks → New Webhook**.
Copy its webhook URL. Treat this URL like a password.

# 2. Configure the local environment

In the root of the repository, add a line to your **local, git-ignored** `.env`:

```dotenv
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN
```

Your `start.sh` must load the `.env` **before** it starts Airflow. Immediately
after its existing `cd "$(dirname "$0")"` line, add:

```bash
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi
```

Keep the existing Airflow exports below these lines. In case the `library`
package import issue returns, also ensure `start.sh` has:

```bash
export PYTHONPATH="$PWD/dags${PYTHONPATH:+:$PYTHONPATH}"
```

`start.sh` sources a trusted local file, so `.env` must contain valid shell-style
`KEY=value` assignments (quotes around any values with spaces).

# 3. Verify locally

From `~/ResearchPaperDAG`:

```bash
PYTHONPATH="$PWD/dags" .venv/bin/python -m unittest discover -s tests -p 'test_discord_notification.py' -v
```

Stop any existing Airflow instance and restart:

```bash
bash start.sh
```

Use a second terminal to inspect any DAG import errors:

```bash
export AIRFLOW_HOME="$PWD/airflow_home"
export AIRFLOW__CORE__DAGS_FOLDER="$PWD/dags"
export PYTHONPATH="$PWD/dags${PYTHONPATH:+:$PYTHONPATH}"
.venv/bin/airflow dags list-import-errors --local
```

Add a **new PDF with a new filename** to `ResearchLibrary/papers/`, then trigger
`paper_pipeline` in Airflow. It should save metadata, regenerate `index.html`,
and send a Discord message. Then trigger the DAG again without adding any PDF:
`notify_discord` should be skipped, so there is no duplicate message.


