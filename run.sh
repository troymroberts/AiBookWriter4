#!/bin/bash
# AiBookWriter4 - Run Script
# Starts the Streamlit app with configured port

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Read port from config.yaml (default to 8501)
PORT=$(python3 -c "import yaml; print(yaml.safe_load(open('config.yaml'))['ui'].get('port', 8501))" 2>/dev/null || echo 8501)

echo "Starting AI Book Writer on port $PORT..."
echo "Access the app at: http://localhost:$PORT"
echo ""

# Kill any existing process on the port
fuser -k $PORT/tcp 2>/dev/null || true

# Start Streamlit
streamlit run app.py \
    --server.port $PORT \
    --server.headless true \
    --browser.gatherUsageStats false
