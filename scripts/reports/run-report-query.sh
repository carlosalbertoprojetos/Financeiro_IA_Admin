#!/usr/bin/env bash
# Executive [AQUI] Report — curl
# Usage: ./scripts/reports/run-report-query.sh YOUR_BOARD_ID

set -euo pipefail

BOARD_ID="${1:?Usage: $0 BOARD_ID}"
API_URL="${API_URL:-http://127.0.0.1:8000}"
OUTPUT="${OUTPUT:-report-executive-aqui.json}"

curl -sS -X POST "${API_URL}/api/reports/query/" \
  -H "Content-Type: application/json" \
  -d "{
    \"board_id\": \"${BOARD_ID}\",
    \"query_dsl\": \"TYPE = EXECUTIVE\\nPERIOD = LAST_30_DAYS\\nLABELS = Financeiro AND Jurídico\\nMEMBERS = Carlos\\nTITLE_PREFIX = [AQUI]\\nSTATUS = (ATRASADO OR BLOQUEADO)\\nMETRICS = LEAD_TIME, CYCLE_TIME, RISK_SCORE, SLA\\nGROUP_BY = LABELS, MEMBERS\\nSORT = RISK_SCORE DESC\\nLIMIT = 100\"
  }" | tee "${OUTPUT}"

echo ""
echo "Saved to ${OUTPUT}"
