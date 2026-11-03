# Assignment 3 – Guideline étape par étape

**Deadline : lundi 9 novembre 2026** (rapport PDF sur l'UV)
**Groupe : 3 personnes**, différent des assignments précédents

Pipeline final :
```
scan_new_pdfs → convert_to_markdown → extract_metadata (LLM) → save_to_sqlite → build_html → notify_discord
```

---

## Phase 0 – Organisation (jour 1)

- [ ] S'inscrire dans un groupe via « Groups for Assignment 3 » sur l'UV
- [ ] Créer un repo GitHub (ex. `research-library-airflow`) et inviter les 2 autres membres
- [ ] Se répartir le travail, par exemple :
  - Personne A : installation Airflow + DAG + scan des PDF
  - Personne B : conversion PDF→Markdown + LLM (Ollama) + parsing JSON
  - Personne C : SQLite + page HTML + Discord + rapport
- [ ] Se mettre d'accord sur le format des données échangées entre tâches (voir Phase 5)

---

## Phase 1 – Mettre en place l'environnement (jour 1)

### 1.1 Structure du projet local
```
research-library-airflow/
├── dags/
│   └── paper_pipeline.py
├── data/                  ← NON synchronisé (dans .gitignore)
│   ├── papers.db
│   └── markdown/
├── templates/             (optionnel, template HTML)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### 1.2 Dossier Google Drive
- [ ] Installer Google Drive for Desktop si ce n'est pas déjà fait
- [ ] Créer dans le Drive :
  ```
  ResearchLibrary/
  ├── papers/
  └── output/
  ```
- [ ] Repérer le chemin local (sur macOS en général :
  `~/Library/CloudStorage/GoogleDrive-<email>/My Drive/ResearchLibrary`)
- [ ] ⚠️ `papers.db` doit rester dans `data/` du projet local, **jamais** dans le Drive

### 1.3 Environnement Python
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 1.4 Installer Airflow (avec le fichier de contraintes officiel)
```bash
AIRFLOW_VERSION=3.1.0   # vérifier la dernière version sur airflow.apache.org
PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
pip install "apache-airflow==${AIRFLOW_VERSION}" \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
pip install pymupdf4llm openai requests
```

### 1.5 Lancer Airflow
```bash
export AIRFLOW_HOME="$(pwd)/airflow_home"
export AIRFLOW__CORE__DAGS_FOLDER="$(pwd)/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
airflow standalone
```
- [ ] Ouvrir http://localhost:8080 et se connecter avec le mot de passe affiché dans le terminal
  (aussi dans `airflow_home/simple_auth_manager_passwords.json.generated`)
- [ ] Ajouter `airflow_home/` au `.gitignore`

> 💡 Problème fréquent sur macOS (tâches qui crashent sans raison) :
> `export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` et `export NO_PROXY="*"` avant `airflow standalone`.

### 1.6 Installer le LLM local (Ollama)
```bash
brew install ollama          # ou télécharger sur ollama.com
ollama serve                 # dans un terminal séparé (ou lancer l'app)
ollama pull llama3.2         # petit modèle (3B), rapide ; alternative : qwen2.5:7b
```
- [ ] Tester l'API compatible OpenAI :
  ```bash
  curl http://localhost:11434/v1/models
  ```

### 1.7 Webhook Discord
- [ ] Créer un serveur Discord (ou utiliser un existant) → un salon → *Paramètres du salon > Intégrations > Webhooks > Nouveau webhook* → copier l'URL
- [ ] ⚠️ Ne **jamais** commit l'URL : la mettre dans une Variable Airflow ou une variable d'environnement
  ```bash
  airflow variables set DISCORD_WEBHOOK_URL "https://discord.com/api/webhooks/..."
  ```

---

## Phase 2 – Tester chaque brique séparément, hors Airflow (jours 2–3)

Avant d'écrire le DAG, vérifier que chaque morceau marche dans un petit script Python.

### 2.1 PDF → Markdown
```python
import pymupdf4llm
md = pymupdf4llm.to_markdown("paper.pdf")
```
- [ ] Sauvegarder le résultat dans `data/markdown/<nom>.md`

### 2.2 Appel au LLM (JSON)
```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

resp = client.chat.completions.create(
    model="llama3.2",
    temperature=0,                               # sortie plus stable
    response_format={"type": "json_object"},     # JSON mode
    messages=[
        {"role": "system", "content": "You extract metadata from research papers. "
         "Answer ONLY with JSON: {\"title\": str, \"summary\": str, "
         "\"keywords\": [str], \"category\": str}"},
        {"role": "user", "content": md[:12000]},  # tronquer : contexte limité
    ],
)
raw = resp.choices[0].message.content
```
- [ ] Imposer une **liste fixe de catégories** dans le prompt (ex. Data Engineering, Machine Learning, NLP, Process Mining, Databases, Other), sinon le filtre par catégorie sera inutilisable

### 2.3 Parsing + validation (exigé par l'énoncé)
- [ ] `json.loads(raw)`
- [ ] **Si le parsing échoue → réessayer une fois** (nouvel appel au LLM)
- [ ] Vérifier que les champs existent et ont le bon type :
  - `title` : str, `summary` : str, `keywords` : list de str, `category` : str
- [ ] Si ça échoue encore → lever une exception (la tâche Airflow passera en rouge)

### 2.4 SQLite
```sql
CREATE TABLE IF NOT EXISTS papers (
    filename     TEXT PRIMARY KEY,   -- unique
    title        TEXT NOT NULL,
    summary      TEXT NOT NULL,
    keywords     TEXT NOT NULL,      -- json.dumps(list)
    category     TEXT NOT NULL,
    processed_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```
- [ ] Utiliser `INSERT OR REPLACE` (ou `ON CONFLICT`) → la tâche est **idempotente** (slide 38 du chap. 5)

### 2.5 Page HTML statique
- [ ] Lire **toute** la table et régénérer `output/index.html` dans le Drive
- [ ] Une carte par paper : titre, catégorie, mots-clés, résumé, lien vers le PDF (`../papers/<filename>`)
- [ ] Un champ de **recherche** (JavaScript qui filtre les cartes sur le texte) **et/ou** un **menu déroulant de catégories**
- [ ] Échapper le texte avec `html.escape()` (le LLM peut générer des `<` ou des `&`)

### 2.6 Discord
```python
import requests
requests.post(webhook_url, json={"content": f"📄 Nouveau paper : **{title}** ({category})"}, timeout=10).raise_for_status()
```

---

## Phase 3 – Écrire le DAG Airflow (jours 3–4) — 3 points

### 3.1 Paramètres du DAG
- [ ] `schedule="*/5 * * * *"` (toutes les 5 min, ou `@hourly`)
- [ ] `catchup=False` (ne pas rattraper les runs passés)
- [ ] `max_active_runs=1` (pas deux runs en même temps sur les mêmes fichiers)
- [ ] `default_args={"retries": 1, "retry_delay": timedelta(minutes=1)}`
- [ ] Des `tags` et une `doc_md` (visibles dans l'UI, bonus pour la documentation)

### 3.2 Les tâches (TaskFlow API : `@dag` / `@task`)
| Tâche | Entrée | Sortie (XCom) |
|---|---|---|
| `scan_new_pdfs` | dossier `papers/` + base SQLite | liste des PDF **pas encore en base** |
| `convert_to_markdown` | chemin d'un PDF | chemin du `.md` |
| `extract_metadata` | chemin du `.md` | dict JSON validé |
| `save_to_sqlite` | dict | filename |
| `build_html` | (toute la base) | chemin de `index.html` |
| `notify_discord` | liste des papers traités | — |

### 3.3 Bonnes pratiques à respecter (et à mentionner dans le rapport)
- [ ] **Faire passer des chemins de fichiers dans les XCom, pas le contenu du Markdown** (les XCom sont stockés dans la base d'Airflow, ils doivent rester légers)
- [ ] **Dynamic task mapping** : `convert_to_markdown.expand(pdf_path=new_pdfs)` → une instance de tâche par PDF, visible séparément dans l'UI, et un PDF qui plante ne bloque pas les autres
- [ ] **Short-circuit** quand il n'y a aucun nouveau PDF (`@task.short_circuit`, ou une liste vide qui fait sauter les tâches mappées) → pas de HTML régénéré ni de notification inutile
- [ ] Dépendances explicites (ordre clair dans la vue *Graph*)
- [ ] Les chemins (Drive, DB, modèle) en **constantes en haut du fichier** ou en Variables Airflow, rien de codé en dur au milieu du code

### 3.4 Squelette
```python
from datetime import datetime, timedelta
from airflow.sdk import dag, task

@dag(schedule="*/5 * * * *", start_date=datetime(2026, 11, 1),
     catchup=False, max_active_runs=1, tags=["papers"],
     default_args={"retries": 1, "retry_delay": timedelta(minutes=1)})
def paper_pipeline():

    @task
    def scan_new_pdfs() -> list[str]: ...

    @task
    def convert_to_markdown(pdf_path: str) -> str: ...

    @task
    def extract_metadata(md_path: str) -> dict: ...

    @task
    def save_to_sqlite(meta: dict) -> str: ...

    @task
    def build_html(saved: list[str]) -> str: ...

    @task
    def notify_discord(saved: list[str]) -> None: ...

    pdfs  = scan_new_pdfs()
    mds   = convert_to_markdown.expand(pdf_path=pdfs)
    metas = extract_metadata.expand(md_path=mds)
    saved = save_to_sqlite.expand(meta=metas)
    build_html(saved) >> notify_discord(saved)

paper_pipeline()
```
> Le `filename` doit être conservé dans le dict renvoyé par `extract_metadata` (il est nécessaire pour SQLite).

---

## Phase 4 – Tester de bout en bout (jour 4–5)

- [ ] Le DAG apparaît dans l'UI sans erreur d'import (sinon : `airflow dags list-import-errors`)
- [ ] Test rapide en ligne de commande : `airflow dags test paper_pipeline`
- [ ] **Scénario 1** : déposer 3–5 PDF dans `papers/` → tout passe au vert → `index.html` à jour → message(s) Discord
- [ ] **Scénario 2** : relancer sans nouveau PDF → rien n'est retraité (idempotence)
- [ ] **Scénario 3** : ajouter 1 nouveau PDF → seul celui-ci est traité
- [ ] (Bonus) **Scénario 4** : couper Ollama → la tâche LLM échoue, retry visible dans les logs, aucune donnée corrompue
- [ ] Vérifier le contenu de la base : `sqlite3 data/papers.db "SELECT filename, category FROM papers;"`

### 📸 Captures d'écran à prendre pour le rapport
- [ ] Vue **Graph** du DAG
- [ ] Vue **Grid** avec plusieurs runs verts (et éventuellement un retry)
- [ ] Logs d'une tâche `extract_metadata` (montrant le JSON reçu)
- [ ] Contenu de la table SQLite
- [ ] La page `index.html` (avec la recherche / le filtre en action)
- [ ] Le message dans Discord
- [ ] Le dossier Drive (`papers/` + `output/`)

---

## Phase 5 – Documentation GitHub (jour 5) — fait partie des 2 points

### README.md
- [ ] Description du projet en 3–4 lignes + schéma du pipeline
- [ ] Prérequis (Python 3.12, Ollama, Google Drive for Desktop, un webhook Discord)
- [ ] Installation pas à pas (venv, pip, `ollama pull`)
- [ ] Configuration : chemins Drive, `DISCORD_WEBHOOK_URL`, nom du modèle
- [ ] Commandes de lancement (`airflow standalone`, ajout de PDF)
- [ ] Structure du repo
- [ ] Choix techniques et limites connues

### Autres fichiers
- [ ] `requirements.txt`
- [ ] `.gitignore` : `.venv/`, `airflow_home/`, `data/`, `.env`, `__pycache__/`
- [ ] `.env.example` (variables à remplir, **sans** les vraies valeurs)
- [ ] Vérifier qu'**aucun secret** (URL du webhook) n'est dans l'historique Git
- [ ] Le repo doit être accessible au prof (public, ou prof ajouté)

---

## Phase 6 – Rapport PDF (jours 5–6) — court (≈ 4–6 pages)

1. **Introduction** : objectif + membres du groupe + **lien GitHub**
2. **Architecture** : schéma du pipeline, où vit chaque donnée (Drive vs local, et pourquoi la DB n'est pas dans le Drive)
3. **Le DAG** : tâches, dépendances, scheduling, dynamic task mapping, retries, idempotence → relier au cours (chap. 5, slides 9–10, 33, 36–38 : task-artifact graph, orchestrateur, tâches idempotentes)
4. **Intégration du LLM** : modèle choisi et pourquoi, prompt, JSON mode, `temperature=0` (chap. 6, slides 48–51), retry en cas d'échec de parsing, validation des champs
5. **Stockage, HTML, Discord** : schéma de la table, fonctionnement de la recherche/du filtre
6. **Démonstration** : les captures d'écran de la Phase 4
7. **Limites et améliorations** : PDF scannés (pas de texte), troncature du texte pour le contexte du LLM, hallucinations possibles du LLM, sensor de fichiers au lieu d'un polling, etc.

- [ ] Exporter en PDF et l'uploader dans « Assignment 3 » sur l'UV **avant le 9 novembre**

---

## Planning conseillé

| Jour | Date | Tâches |
|---|---|---|
| 1 | mar. 3/11 | Phase 0 + Phase 1 (tout installé, Airflow et Ollama tournent) |
| 2 | mer. 4/11 | Phase 2 (chaque brique marche seule) |
| 3 | jeu. 5/11 | Phase 3 (DAG) |
| 4 | ven. 6/11 | Phase 4 (tests + captures) |
| 5 | sam. 7/11 | Phase 5 (README) + début du rapport |
| 6 | dim. 8/11 | Finir le rapport, relecture, upload |
| — | lun. 9/11 | **Deadline** (marge de sécurité) |

## Barème (rappel)
| Critère | Points | Où ça se joue |
|---|---|---|
| DAG Airflow et dépendances | 3 | Phase 3 |
| Conversion PDF + LLM local | 3 | Phases 2.1–2.3 |
| SQLite + HTML + Discord | 2 | Phases 2.4–2.6 |
| Rapport + documentation | 2 | Phases 5–6 |
