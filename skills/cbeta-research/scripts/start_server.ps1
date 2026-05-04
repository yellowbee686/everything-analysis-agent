param(
    [string]$Url = $(if ($env:CBETA_MCP_URL) { $env:CBETA_MCP_URL } else { "http://localhost:18765/mcp/" }),
    [string]$Port = $(if ($env:APP_PORT) { $env:APP_PORT } else { "18765" }),
    [string]$Python = $env:CBETA_MCP_PYTHON,
    [switch]$Foreground
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $PSCommandPath
$RootDir = Resolve-Path (Join-Path $ScriptDir "..\..\..")
$ServerDir = Join-Path $RootDir "mcp_servers\CbetaMCP"
$CheckScript = Join-Path $RootDir "skills\cbeta-research\scripts\check_server.py"
$LogFile = if ($env:CBETA_MCP_LOG) { $env:CBETA_MCP_LOG } else { Join-Path $env:TEMP "cbeta-mcp.log" }
$ErrorLogFile = "$LogFile.err"

function Resolve-Python {
    if ($Python) {
        return $Python
    }

    $VenvPython = Join-Path $ServerDir ".venv\Scripts\python.exe"
    if (Test-Path $VenvPython) {
        return $VenvPython
    }

    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($PythonCommand) {
        return $PythonCommand.Source
    }

    $PyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($PyCommand) {
        return $PyCommand.Source
    }

    throw "Python was not found. Install Python or set CBETA_MCP_PYTHON."
}

function Test-Server {
    param([string]$PythonBin)

    try {
        & $PythonBin $CheckScript --url $Url *> $null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

function Test-Dependencies {
    param([string]$PythonBin)

    $ImportScript = @"
import fastapi
import fastmcp
import httpx
import pydantic
import uvicorn
"@
    $TempFile = New-TemporaryFile
    try {
        Set-Content -Path $TempFile -Value $ImportScript -Encoding UTF8
        & $PythonBin $TempFile *> $null
        return $LASTEXITCODE -eq 0
    }
    finally {
        Remove-Item $TempFile -Force -ErrorAction SilentlyContinue
    }
}

$PythonBin = Resolve-Python

if (Test-Server -PythonBin $PythonBin) {
    Write-Output "CBETA MCP server is already reachable at $Url"
    exit 0
}

if (-not (Test-Path $ServerDir)) {
    Write-Error "CBETA MCP submodule is missing: $ServerDir. Run: git submodule update --init --recursive"
    exit 1
}

if (-not (Test-Dependencies -PythonBin $PythonBin)) {
    Write-Error @"
CBETA MCP dependencies are not installed for $PythonBin.
Run:
  cd $ServerDir
  py -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
"@
    exit 1
}

$env:APP_PORT = $Port

if ($Foreground -or $env:CBETA_MCP_FOREGROUND -eq "1") {
    Push-Location $ServerDir
    try {
        Write-Output "Starting CBETA MCP server in foreground at $Url"
        & $PythonBin main.py
        exit $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
}

$Process = Start-Process `
    -FilePath $PythonBin `
    -ArgumentList "main.py" `
    -WorkingDirectory $ServerDir `
    -RedirectStandardOutput $LogFile `
    -RedirectStandardError $ErrorLogFile `
    -WindowStyle Hidden `
    -PassThru

Set-Content -Path (Join-Path $env:TEMP "cbeta-mcp.pid") -Value $Process.Id -Encoding ASCII

foreach ($Attempt in 1..10) {
    Start-Sleep -Seconds 1
    if (Test-Server -PythonBin $PythonBin) {
        Write-Output "CBETA MCP server started at $Url"
        Write-Output "Log: $LogFile"
        Write-Output "Error log: $ErrorLogFile"
        exit 0
    }
}

Write-Error "CBETA MCP server did not become reachable at $Url. Log: $LogFile Error log: $ErrorLogFile"
exit 1
