import json

from openai import OpenAI

from library.config import OLLAMA_BASE_URL, OLLAMA_MODEL

CATEGORIES = [
    "Machine Learning", "Reinforcement Learning", "Game Theory", "NLP",
    "Data Engineering", "Databases", "Process Mining", "Other",
]

MAX_CHARS = 10_000

MAX_TRIES = 2

SYSTEM_PROMPT = f"""You extract metadata from research papers.
Return ONLY a JSON object with exactly these keys:
- "title": the title of the paper (string)
- "summary": a short summary of 3 to 4 sentences (string)
- "keywords": 3 to 6 keywords (list of strings)
- "category": exactly one of {", ".join(CATEGORIES)} (string)

Paper:
"""


def extract_metadata(doc: dict) -> dict:
    client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")

    with open(doc["md_path"], encoding="utf-8") as f:
        text = f.read()[:MAX_CHARS]

    for attempt in range(MAX_TRIES):
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": SYSTEM_PROMPT + text}],
        )
        try:
            data = json.loads(response.choices[0].message.content)
            if isinstance(data["title"], str) and \
                isinstance(data["summary"], str) and \
                isinstance(data["keywords"], list) and \
                isinstance(data["category"], str):

                data["filename"] = doc["filename"]
                return data

        except(json.JSONDecodeError, KeyError):
            pass
        print(f"Attempt {attempt + 1} failed, retrying...")

    raise ValueError(f"LLM failed {MAX_TRIES} times for {doc['filename']}")
