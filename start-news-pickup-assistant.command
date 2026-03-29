#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

APP_URL="http://127.0.0.1:8000/items/view"
LOG_FILE="$SCRIPT_DIR/data/news-pickup-assistant.log"

mkdir -p "$SCRIPT_DIR/data"

if [[ ! -x "$SCRIPT_DIR/.venv/bin/python" ]]; then
  echo ""
  echo ".venv/bin/python が見つかりません。"
  echo "先に仮想環境と依存関係をセットアップしてください。"
  echo ""
  read -r "?Enterキーで閉じます..."
  exit 1
fi

if ! lsof -iTCP:8000 -sTCP:LISTEN -n -P >/dev/null 2>&1; then
  nohup "$SCRIPT_DIR/.venv/bin/python" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 \
    >"$LOG_FILE" 2>&1 &

  for _ in {1..30}; do
    if curl -fsS "$APP_URL" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi

open "$APP_URL"

echo ""
echo "News Pickup Assistant を開きました。"
echo "URL: $APP_URL"
echo "ログ: $LOG_FILE"
echo ""
