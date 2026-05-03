#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SERVER_DIR="${ROOT_DIR}/mcp_servers/CbetaMCP"
CHECK_SCRIPT="${ROOT_DIR}/skills/cbeta-research/scripts/check_server.py"
URL="${CBETA_MCP_URL:-http://localhost:18765/mcp/}"
PORT="${APP_PORT:-18765}"
LOG_FILE="${CBETA_MCP_LOG:-/tmp/cbeta-mcp.log}"

if python3 "${CHECK_SCRIPT}" --url "${URL}" >/dev/null 2>&1; then
  echo "CBETA MCP server is already reachable at ${URL}"
  exit 0
fi

if [[ ! -d "${SERVER_DIR}" ]]; then
  echo "CBETA MCP submodule is missing: ${SERVER_DIR}" >&2
  echo "Run: git submodule update --init --recursive" >&2
  exit 1
fi

PYTHON_BIN="${CBETA_MCP_PYTHON:-python3}"
if [[ -z "${CBETA_MCP_PYTHON:-}" && -x "${SERVER_DIR}/.venv/bin/python" ]]; then
  PYTHON_BIN="${SERVER_DIR}/.venv/bin/python"
fi

if ! "${PYTHON_BIN}" - <<'PY' >/dev/null 2>&1
import fastapi
import fastmcp
import httpx
import pydantic
import uvicorn
PY
then
  echo "CBETA MCP dependencies are not installed for ${PYTHON_BIN}." >&2
  echo "Run:" >&2
  echo "  cd ${SERVER_DIR}" >&2
  echo "  python3 -m venv .venv" >&2
  echo "  . .venv/bin/activate" >&2
  echo "  pip install -r requirements.txt" >&2
  exit 1
fi

if [[ "${CBETA_MCP_FOREGROUND:-0}" == "1" ]]; then
  cd "${SERVER_DIR}"
  echo "Starting CBETA MCP server in foreground at ${URL}"
  exec env APP_PORT="${PORT}" "${PYTHON_BIN}" main.py
fi

(
  cd "${SERVER_DIR}"
  APP_PORT="${PORT}" nohup "${PYTHON_BIN}" main.py >"${LOG_FILE}" 2>&1 &
  echo "$!" > /tmp/cbeta-mcp.pid
)

for _ in 1 2 3 4 5 6 7 8 9 10; do
  if python3 "${CHECK_SCRIPT}" --url "${URL}" >/dev/null 2>&1; then
    echo "CBETA MCP server started at ${URL}"
    echo "Log: ${LOG_FILE}"
    exit 0
  fi
  sleep 1
done

echo "CBETA MCP server did not become reachable at ${URL}" >&2
echo "Log: ${LOG_FILE}" >&2
exit 1
