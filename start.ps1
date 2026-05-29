$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Check Python
try {
    $ver = python --version
    Write-Host "Python: $ver"
} catch {
    Write-Host "[ERROR] Python not found. Please install Python 3.8+"
    Write-Host "        https://www.python.org/downloads/"
    Read-Host "Press Enter to exit"
    exit 1
}

# Check / install PySide6
try {
    python -c "import PySide6" | Out-Null
} catch {
    Write-Host "[INFO] Installing dependencies (first run only)..."
    pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
    if ($LASTEXITCODE -ne 0) {
        pip install -r requirements.txt
    }
}

Write-Host "Starting..."
python main.py

Write-Host "App closed."
Read-Host "Press Enter to exit"
