#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Installed. Next:"
echo "  1) cp .env.example .env"
echo "  2) edit .env with your spreadsheet path + AI_BASE_URL"
echo "  3) source .venv/bin/activate"
echo "  4) streamlit run app.py --server.port 8501 --server.address 0.0.0.0"
