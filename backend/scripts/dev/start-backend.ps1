$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=========================================="
Write-Host " A4A Learn - Backend Development Startup"
Write-Host "=========================================="
Write-Host ""

# -------------------------------------------------------
# 1. Resolve current WSL2 IP
# -------------------------------------------------------

$wslIp = (wsl hostname -I).Trim().Split(' ')[0]

if ([string]::IsNullOrWhiteSpace($wslIp)) {
    Write-Error "Unable to determine WSL IP address."
    exit 1
}

$env:OLLAMA_BASE_URL = "http://${wslIp}:11434"

Write-Host "WSL IP          : $wslIp"
Write-Host "OLLAMA_BASE_URL : $env:OLLAMA_BASE_URL"

# -------------------------------------------------------
# 2. Verify Ollama connectivity
# -------------------------------------------------------

Write-Host ""
Write-Host "Checking Ollama..."

try {
    $response = Invoke-WebRequest `
        -Uri "$env:OLLAMA_BASE_URL/api/tags" `
        -Method Get `
        -TimeoutSec 5 `
        -UseBasicParsing

    if ($response.StatusCode -ne 200) {
        throw "Unexpected HTTP status: $($response.StatusCode)"
    }
}
catch {
    Write-Error "Ollama is not reachable at $env:OLLAMA_BASE_URL"
    exit 1
}

Write-Host "Ollama           : GREEN (HTTP 200)"

# -------------------------------------------------------
# 3. Verify Python virtual environment
# -------------------------------------------------------

if (-not $env:VIRTUAL_ENV) {
    Write-Error "Python virtual environment is not active."
    Write-Host "Activate it first using:"
    Write-Host ".\.venv\Scripts\Activate.ps1"
    exit 1
}

Write-Host "Python venv      : $env:VIRTUAL_ENV"

# -------------------------------------------------------
# 4. Show effective A4A configuration
# -------------------------------------------------------

Write-Host ""
Write-Host "Effective A4A configuration:"

python -c "from app.core.config import settings; print('  Ollama URL    :', settings.OLLAMA_BASE_URL); print('  Ollama Model  :', settings.OLLAMA_MODEL); print('  RAG Top K     :', settings.RAG_TOP_K); print('  Max Distance  :', settings.RAG_MAX_DISTANCE)"

if ($LASTEXITCODE -ne 0) {
    Write-Error "A4A configuration validation failed."
    exit 1
}

# -------------------------------------------------------
# 5. Start FastAPI
# -------------------------------------------------------

Write-Host ""
Write-Host "Starting A4A Learn backend..."
Write-Host "API: http://127.0.0.1:8000"
Write-Host ""

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload