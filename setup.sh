#!/usr/bin/env bash
set -uo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

FUSEKI_URL="http://localhost:3030"
DATA_DIR="./fuseki/data"
READY_TIMEOUT=90

log()  { printf '\033[1;34m==>\033[0m %s\n' "$1"; }
fail() { printf '\033[1;31mERROR:\033[0m %s\n' "$1" >&2; exit 1; }

for cmd in docker curl python3; do
  command -v "$cmd" >/dev/null 2>&1 || fail "'$cmd' is required but not found on PATH."
done
docker info >/dev/null 2>&1 || fail "Docker doesn't seem to be running."

if [[ "${1:-}" == "--reset" ]]; then
  log "Resetting"
  docker compose down >/dev/null 2>&1 || true
  sudo rm -rf "$DATA_DIR"
fi

if [[ ! -f .env ]]; then
  log "Creating .env"
  cat > .env <<EOF
FUSEKI_ADMIN_PASSWORD=devpassword123
FUSEKI_USER=admin
EOF
fi
set -a; source .env; set +a

mkdir -p "$DATA_DIR"
chmod -R 777 "$DATA_DIR"

log "Starting Fuseki"
docker compose up -d fuseki || fail "docker compose up failed."

log "Waiting for Fuseki (up to ${READY_TIMEOUT}s)"
ready=0
for ((i = 1; i <= READY_TIMEOUT; i++)); do
  curl -sf "$FUSEKI_URL/\$/ping" >/dev/null 2>&1 && { ready=1; break; }
  sleep 1
done
[[ "$ready" == "1" ]] || fail "Fuseki never became ready. Logs:
$(docker logs --tail 40 blastradius-fuseki 2>&1)"
log "Fuseki is up"

dataset_exists() {
  curl -sf -u "admin:$FUSEKI_ADMIN_PASSWORD" "$FUSEKI_URL/\$/datasets" 2>/dev/null \
    | python3 -c "
import sys, json
try:
    names = [d.get('ds.name','').lstrip('/') for d in json.load(sys.stdin).get('datasets', [])]
    sys.exit(0 if 'blastradius' in names else 1)
except Exception:
    sys.exit(1)
"
}

if dataset_exists; then
  log "Dataset 'blastradius' exists"
else
  log "Creating dataset 'blastradius'"
  resp=$(curl -s -w '\n%{http_code}' -X POST "$FUSEKI_URL/\$/datasets" \
    -u "admin:$FUSEKI_ADMIN_PASSWORD" --data 'dbName=blastradius&dbType=tdb2')
  code=$(echo "$resp" | tail -1)
  body=$(echo "$resp" | sed '$d')
  if [[ "$code" != "200" && "$code" != "409" ]] && ! dataset_exists; then
    fail "Dataset creation failed (HTTP $code): $body"
  fi
  dataset_exists || fail "Dataset still not listed — check '$FUSEKI_URL/\$/datasets'."
fi

log "Verifying SPARQL endpoint"
curl -sf "$FUSEKI_URL/blastradius/sparql?query=ASK%7B%7D" >/dev/null 2>&1 \
  || fail "Dataset listed but /blastradius/sparql isn't responding."

if [[ -f requirements.txt ]]; then
  log "Installing Python dependencies"
  pip install -r requirements.txt --break-system-packages || fail "pip install failed."
fi

log "Setup complete. Try:  python cli.py import-all ."
