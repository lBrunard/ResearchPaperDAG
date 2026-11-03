# 1. Obtenir le numéro de la dernière version d'Airflow via l'API PyPI
AIRFLOW_VERSION=$(curl -s https://pypi.org/pypi/apache-airflow/json | grep -o '"version":"[^"]*"' | head -n 1 | cut -d'"' -f4)

# 2. Obtenir la version majeure/mineure de Python (ex: 3.11)
PYTHON_VERSION="$(python --version | cut -d " " -f 2 | cut -d "." -f 1-2)"

# 3. Construire l'URL des contraintes officielle correspondante
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

# 4. Installer la dernière version via uv
uv pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
