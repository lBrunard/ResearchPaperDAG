#!/usr/bin/env bash
# Start Airflow standalone with a project-local configuration.
set -euo pipefail
cd "$(dirname "$0")"

[ -d .venv ] || { echo "❌ Lance d'abord ./setup.sh"; exit 1; }
source .venv/bin/activate

# Variables du projet (.env) transmises à toutes les tâches Airflow
set -a; source .env; set +a

export AIRFLOW_HOME="$(pwd)/airflow_home"
export AIRFLOW__CORE__DAGS_FOLDER="$(pwd)/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False

# Correctifs macOS (crashs de tâches liés à fork)
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
export NO_PROXY="*"

curl -s -m 2 "${OLLAMA_BASE_URL:-http://localhost:11434/v1}/models" >/dev/null \
    || echo "⚠️  Ollama ne répond pas : lance 'ollama serve' ou l'app Ollama"

echo "🔑 Mot de passe admin : airflow_home/simple_auth_manager_passwords.json.generated"
airflow standalone
