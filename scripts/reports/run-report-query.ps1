# Executive [AQUI] Report — PowerShell
# Usage: .\scripts\reports\run-report-query.ps1 -BoardId "YOUR_BOARD_ID"

param(
    [Parameter(Mandatory = $true)]
    [string]$BoardId,

    [string]$ApiUrl = "http://127.0.0.1:8000",
    [string]$OutputFile = "report-executive-aqui.json"
)

$body = @{
    board_id = $BoardId
    query_dsl = @"
TYPE = EXECUTIVE
PERIOD = LAST_30_DAYS
LABELS = Financeiro AND Jurídico
MEMBERS = Carlos
TITLE_PREFIX = [AQUI]
STATUS = (ATRASADO OR BLOQUEADO)
METRICS = LEAD_TIME, CYCLE_TIME, RISK_SCORE, SLA
GROUP_BY = LABELS, MEMBERS
SORT = RISK_SCORE DESC
LIMIT = 100
"@
} | ConvertTo-Json

Write-Host "POST $ApiUrl/api/reports/query/"

$response = Invoke-RestMethod `
    -Uri "$ApiUrl/api/reports/query/" `
    -Method Post `
    -ContentType "application/json; charset=utf-8" `
    -Body $body

$response | ConvertTo-Json -Depth 20 | Out-File -Encoding utf8 $OutputFile

Write-Host "Matched: $($response.meta.matched_cards) cards"
Write-Host "Saved: $OutputFile"
