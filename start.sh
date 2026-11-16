#!/usr/bin/env bash
# Start Airflow standalone with a project-local configuration.
set -euo pipefail
cd "$(dirname "$0")"

[ -d .venv ] || { echo "Start setup.sh before"; exit 1; }
source .venv/bin/activate

if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

export AIRFLOW_HOME="$(pwd)/airflow_home"
export AIRFLOW__CORE__DAGS_FOLDER="$(pwd)/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False

# Correctifs macOS (crashs de tâches liés à fork)
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
export NO_PROXY="*"

# Démarre Ollama s'il ne tourne pas déjà (app, service ou autre terminal)
if ! curl -s -o /dev/null http://localhost:11434; then
    command -v ollama >/dev/null || { echo "Ollama and model required"; exit 1; }
    echo "Ollama starting"
    ollama serve > /dev/null 2>&1 &
    for _ in {1..10}; do
        curl -s -o /dev/null http://localhost:11434 && break
        sleep 1
    done
fi

echo "Admin password : airflow_home/simple_auth_manager_passwords.json.generated"
airflow standalone
