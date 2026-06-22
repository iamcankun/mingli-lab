$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Start-Process -FilePath "python" `
  -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000" `
  -WorkingDirectory (Join-Path $Root "backend") `
  -WindowStyle Hidden

Set-Location (Join-Path $Root "frontend")
npm run dev

