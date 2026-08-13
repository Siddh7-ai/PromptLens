@echo off
echo Freeing port 8000 if occupied...
powershell -Command "Get-Process -Id (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue" >nul 2>&1
.\.venv\Scripts\uvicorn.exe src.proxy.server:app --reload --port 8000
