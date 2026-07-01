param(
    [switch]$SkipDocker,
    [switch]$SkipFrontendBuild
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
$FrontendDir = Join-Path $Root "frontend"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Name" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

function Test-HttpStatus {
    param(
        [string]$Url,
        [int]$ExpectedStatus = 200
    )

    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 20
    if ($response.StatusCode -ne $ExpectedStatus) {
        throw "$Url returned $($response.StatusCode), expected $ExpectedStatus"
    }
    Write-Host "$Url -> $($response.StatusCode)"
}

Set-Location -LiteralPath $Root

Invoke-Step "Workspace validation" {
    & $Python manage.py validate_eor_workspace --json
}

if (-not $SkipDocker) {
    Invoke-Step "Start PostgreSQL and Redis" {
        docker compose up -d
    }
}

Invoke-Step "Django check" {
    & $Python manage.py check
}

Invoke-Step "Django migrations" {
    & $Python manage.py migrate --noinput
}

Invoke-Step "Report quality gate fixture" {
    $previous = $env:EOR_TESTING
    try {
        $env:EOR_TESTING = "true"
        & $Python manage.py validate_report_quality --fixture --compare-baseline --json
    }
    finally {
        if ($null -eq $previous) {
            Remove-Item Env:\EOR_TESTING -ErrorAction SilentlyContinue
        }
        else {
            $env:EOR_TESTING = $previous
        }
    }
}

$backendOut = Join-Path $Root "tmp_local_demo_backend.out.log"
$backendErr = Join-Path $Root "tmp_local_demo_backend.err.log"
Remove-Item -LiteralPath $backendOut, $backendErr -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "==> Start temporary backend" -ForegroundColor Cyan
$backend = Start-Process `
    -FilePath $Python `
    -ArgumentList @("manage.py", "runserver", "127.0.0.1:8000", "--noreload") `
    -WorkingDirectory $Root `
    -WindowStyle Hidden `
    -RedirectStandardOutput $backendOut `
    -RedirectStandardError $backendErr `
    -PassThru

try {
    Start-Sleep -Seconds 8
    Test-HttpStatus "http://127.0.0.1:8000/health/"
    Test-HttpStatus "http://127.0.0.1:8000/api/v1/settings/"
    Test-HttpStatus "http://127.0.0.1:8000/api/v1/data-sources/trello/status/"
    Test-HttpStatus "http://127.0.0.1:8000/api/pilot/dashboard/"
}
finally {
    Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $backendOut, $backendErr -Force -ErrorAction SilentlyContinue
}

Invoke-Step "Frontend typecheck" {
    Push-Location $FrontendDir
    try {
        npx.cmd tsc --noEmit
    }
    finally {
        Pop-Location
    }
}

if (-not $SkipFrontendBuild) {
    Invoke-Step "Frontend build" {
        Push-Location $FrontendDir
        try {
            npm.cmd run build
        }
        finally {
            Pop-Location
        }
    }
}

Write-Host ""
Write-Host "LOCAL DEMO CHECK: PASS" -ForegroundColor Green
