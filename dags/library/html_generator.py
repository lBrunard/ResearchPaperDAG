"""Generate a self-contained, searchable HTML research-paper catalog."""

from datetime import datetime, timezone
from html import escape
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import quote

from library.config import OUTPUT_DIR
from library.database import get_all_papers


def _paper_card(paper: dict) -> str:
    """Render one paper safely, escaping untrusted metadata from the LLM."""
    filename = str(paper["filename"])
    title = str(paper["title"])
    summary = str(paper["summary"])
    category = str(paper["category"])
    keywords = [str(keyword) for keyword in paper["keywords"]]
    processed_at = str(paper.get("processed_at") or "")

    # index.html lives in ResearchLibrary/output/, beside ResearchLibrary/papers/.
    # Percent-encoding makes links work for filenames containing spaces or accents.
    pdf_url = "../papers/" + quote(filename, safe="")
    searchable = " ".join([filename, title, summary, category, *keywords])
    tags = "".join(f'<span class="tag">{escape(word)}</span>' for word in keywords)

    return f"""
    <article class="paper-card" data-search="{escape(searchable, quote=True)}"
             data-category="{escape(category, quote=True)}">
      <div class="paper-topline">
        <span class="category">{escape(category)}</span>
        <span class="date">{escape(processed_at)}</span>
      </div>
      <h2>{escape(title)}</h2>
      <p class="summary">{escape(summary)}</p>
      <div class="tags">{tags}</div>
      <div class="paper-footer">
        <span class="filename" title="{escape(filename, quote=True)}">{escape(filename)}</span>
        <a href="{escape(pdf_url, quote=True)}" target="_blank" rel="noopener noreferrer"
           aria-label="Open PDF: {escape(title, quote=True)}">Open PDF ↗</a>
      </div>
    </article>"""


def _html_document(papers: list[dict]) -> str:
    categories = sorted(
        {str(paper["category"]) for paper in papers}, key=str.casefold
    )
    options = "".join(
        f'<option value="{escape(category, quote=True)}">{escape(category)}</option>'
        for category in categories
    )
    cards = "\n".join(_paper_card(paper) for paper in papers)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = len(papers)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Research Library</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f8fc; --ink: #18253c; --muted: #68768d;
      --accent: #176f79; --line: #e0e6ef; --surface: #fff;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font: 16px/1.6 system-ui, -apple-system, sans-serif;
            color: var(--ink); background: var(--bg); }}
    .wrap {{ max-width: 1040px; margin: auto; padding: 0 24px; }}
    header {{ background: linear-gradient(120deg, #10283d, #175965);
              color: #fff; padding: 58px 0 72px; }}
    .eyebrow {{ font-size: .78rem; letter-spacing: .13em; text-transform: uppercase;
                opacity: .82; font-weight: 700; }}
    h1 {{ font-size: clamp(2rem, 5vw, 3.2rem); line-height: 1.1;
          letter-spacing: -.035em; margin: 10px 0; }}
    header p {{ max-width: 620px; margin: 0; opacity: .85; }}
    main {{ margin-top: -26px; padding-bottom: 70px; }}
    .filters {{ display: grid; grid-template-columns: minmax(0, 2fr) minmax(190px, 1fr);
                gap: 14px; padding: 20px; border: 1px solid var(--line);
                border-radius: 16px; background: var(--surface);
                box-shadow: 0 14px 45px #142a4010; }}
    label {{ display: block; font-weight: 700; font-size: .82rem; margin-bottom: 5px; }}
    input, select {{ width: 100%; font: inherit; border: 1px solid #cdd6e1;
                     padding: 12px 14px; border-radius: 9px; background: #fff;
                     color: var(--ink); }}
    input:focus-visible, select:focus-visible, a:focus-visible {{
        outline: 3px solid #77ccd1; outline-offset: 2px; }}
    .meta {{ display: flex; justify-content: space-between; gap: 16px;
             flex-wrap: wrap; color: var(--muted); margin: 25px 2px 14px;
             font-size: .9rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 390px), 1fr));
             gap: 18px; }}
    .paper-card {{ background: var(--surface); border: 1px solid var(--line);
                   border-radius: 15px; padding: 25px; min-width: 0;
                   box-shadow: 0 6px 20px #16253a06; }}
    .paper-card[hidden] {{ display: none; }}
    .paper-topline {{ display: flex; align-items: center; justify-content: space-between;
                      flex-wrap: wrap; gap: 10px; }}
    .category {{ background: #e5f3f1; color: #11646b; font-size: .75rem;
                 font-weight: 750; border-radius: 99px; padding: 4px 10px; }}
    .date {{ color: var(--muted); font-size: .75rem; }}
    h2 {{ font-size: 1.27rem; line-height: 1.3; margin: 16px 0 10px;
          letter-spacing: -.015em; }}
    .summary {{ color: #4b5c72; font-size: .92rem; margin: 0 0 16px;
                white-space: pre-wrap; overflow-wrap: anywhere; }}
    .tags {{ display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 18px; }}
    .tag {{ color: #43556f; border: 1px solid #dce3ed; background: #f8fafc;
            border-radius: 7px; padding: 2px 8px; font-size: .78rem; }}
    .paper-footer {{ border-top: 1px solid var(--line); padding-top: 15px;
                     display: flex; align-items: center; justify-content: space-between;
                     gap: 14px; }}
    .filename {{ color: var(--muted); font-size: .78rem;
                 overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    a {{ color: var(--accent); font-size: .88rem; font-weight: 750;
         white-space: nowrap; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .empty {{ text-align: center; border: 1px dashed #cbd5e1;
              padding: 52px 20px; border-radius: 14px;
              background: #fff; color: var(--muted); }}
    .empty h2 {{ color: var(--ink); }}
    footer {{ margin-top: 28px; text-align: center; font-size: .79rem; color: var(--muted); }}
    @media (max-width: 600px) {{
      .filters {{ grid-template-columns: 1fr; }}
      header {{ padding: 40px 0 62px; }}
    }}
  </style>
</head>
<body>
  <header><div class="wrap">
    <div class="eyebrow">Personal study collection</div>
    <h1>Research Library</h1>
    <p>Explore your research papers, read their summaries and discover related topics.</p>
  </div></header>
  <main class="wrap">
    <section class="filters" aria-label="Filter research papers">
      <div>
        <label for="search">Search papers</label>
        <input id="search" type="search" placeholder="Title, summary, keyword..." autocomplete="off">
      </div>
      <div>
        <label for="category-filter">Category</label>
        <select id="category-filter">
          <option value="">All categories</option>{options}
        </select>
      </div>
    </section>
    <div class="meta">
      <span id="result-count" aria-live="polite">{total} paper(s)</span>
      <span>Last updated: {generated_at}</span>
    </div>
    <section id="paper-list" class="grid" aria-label="Research papers">
      {cards}
    </section>
    <div id="no-papers" class="empty" {'hidden' if total else ''}>
      <h2>No papers yet</h2><p>Add a PDF to the papers folder and run the Airflow DAG.</p>
    </div>
    <div id="no-matches" class="empty" hidden>
      <h2>No matching papers</h2><p>Try a different search or select another category.</p>
    </div>
    <footer>Generated locally by your Airflow pipeline · {total} paper(s) in the library</footer>
  </main>
  <script>
    const input = document.getElementById('search');
    const category = document.getElementById('category-filter');
    const cards = Array.from(document.querySelectorAll('.paper-card'));
    const noMatches = document.getElementById('no-matches');
    const count = document.getElementById('result-count');
    function normalize(value) {{
      return value.normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLocaleLowerCase();
    }}
    function filterPapers() {{
      const term = normalize(input.value.trim());
      const selected = category.value;
      let visible = 0;
      for (const card of cards) {{
        const matches = normalize(card.dataset.search).includes(term)
          && (!selected || card.dataset.category === selected);
        card.hidden = !matches;
        if (matches) visible += 1;
      }}
      count.textContent = visible + ' of ' + cards.length + ' paper(s)';
      noMatches.hidden = visible !== 0 || cards.length === 0;
    }}
    input.addEventListener('input', filterPapers);
    category.addEventListener('change', filterPapers);
  </script>
</body>
</html>
"""


def generate_library_html() -> str:
    """Read SQLite, then atomically regenerate ResearchLibrary/output/index.html."""
    papers = get_all_papers()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    destination = OUTPUT_DIR / "index.html"
    html = _html_document(papers)

    # Write in the same directory and replace in one operation; this avoids
    # leaving a partially written page in a Google Drive-synced directory.
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".tmp",
            prefix=".index-", dir=OUTPUT_DIR, delete=False,
        ) as temporary:
            temporary.write(html)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, destination)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    print(f"Generated {destination} with {len(papers)} paper(s)")
    return str(destination)


if __name__ == "__main__":
    print(generate_library_html())
