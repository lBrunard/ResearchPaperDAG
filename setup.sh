#!/usr/bin/env bash
# One-time setup: venv, Airflow, dependencies, folders, LLM model.
set -euo pipefail
cd "$(dirname "$0")"

AIRFLOW_VERSION="3.3.2"   # même version pour tout le groupe
PYTHON_VERSION="3.13"

command -v uv >/dev/null || { echo "❌ uv est requis : brew install uv"; exit 1; }

# 1. Environnement Python (uv télécharge Python si besoin)
[ -d .venv ] || uv venv .venv --python "$PYTHON_VERSION"
source .venv/bin/activate

# 2. Airflow avec son fichier de contraintes officiel
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
uv pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "$CONSTRAINT_URL"

# 3. Autres dépendances
uv pip install -r requirements.txt

# 4. Dossiers et fichier de config local
mkdir -p ResearchLibrary/papers ResearchLibrary/output data/markdown
[ -f .env ] || cp .env.example .env

# 5. Modèle LLM local
set -a; source .env; set +a
if command -v ollama >/dev/null; then
    ollama pull "${OLLAMA_MODEL:-llama3.2}"
else
    echo "⚠️  Ollama n'est pas installé : https://ollama.com (puis : ollama pull ${OLLAMA_MODEL:-llama3.2})"
fi

echo "✅ Setup terminé. Complète .env si besoin, puis lance ./start.sh"
