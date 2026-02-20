@echo off
REM LLM Router Start Script for Windows

cd /d "%~dp0..\service"

REM Load environment (optional)
if exist .env (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do set "%%a=%%b"
)

REM Start
python -m uvicorn main:app --host 0.0.0.0 --port 3456
