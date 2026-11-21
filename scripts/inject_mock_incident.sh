#!/usr/bin/env bash
# inject_mock_incident.sh — air-gapped demo trigger.
# POSTs a crafted incident to the local PocketSRE API; the real Discord
# card → approval → SSH runbook → report loop runs from there.
#
# Usage:
#   ./scripts/inject_mock_incident.sh --scenario crash --service yuki-core-api
#   ./scripts/inject_mock_incident.sh --scenario bug --service yuki-core-api
#   ./scripts/inject_mock_incident.sh --scenario socket-lock --service yuki-core-api
#
# Env: POCKETSRE_API_URL (default http://127.0.0.1:8000)
set -euo pipefail

API_URL="${POCKETSRE_API_URL:-http://127.0.0.1:8000}"
SCENARIO=""
SERVICE="yuki-core-api"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scenario) SCENARIO="$2"; shift 2 ;;
    --service)  SERVICE="$2";  shift 2 ;;
    --api-url)  API_URL="$2";  shift 2 ;;
    -h|--help)
      sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$SCENARIO" ]]; then
  echo "missing --scenario (crash|bug|socket-lock)" >&2; exit 2
fi

case "$SCENARIO" in
  crash)
    SEVERITY="P1"
    SUMMARY="[DEMO] Container ${SERVICE} exited unexpectedly — restart loop detected; last logs show OOM kill (exit 137)."
    ;;
  bug)
    SEVERITY="P2"
    SUMMARY="[DEMO] ${SERVICE} returning HTTP 500 on /health; traceback points to a bad response handler introduced in the last deploy."
    ;;
  socket-lock)
    SEVERITY="P2"
    SUMMARY="[DEMO] ${SERVICE} wedged — redis connection pool exhausted; sockets held open; no new requests served."
    ;;
  *) echo "unknown scenario: $SCENARIO (crash|bug|socket-lock)" >&2; exit 2 ;;
esac

BODY=$(printf '{"source":"mock_injector","service":"%s","severity":"%s","summary":"%s"}' \
  "$SERVICE" "$SEVERITY" "$SUMMARY")

echo "Injecting ${SCENARIO} incident for ${SERVICE} → ${API_URL}/api/incidents"
curl -fsS -X POST "${API_URL}/api/incidents" \
  -H "Content-Type: application/json" \
  -d "$BODY"
echo
echo "Done — watch the Discord alert channel for the approval card."
