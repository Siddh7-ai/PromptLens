@echo off
.\.venv\Scripts\uvicorn.exe src.proxy.server:app --reload --port 8000
