@echo off
echo Starting AI Second Brain Server...
cd c:\Apps\Contributions\AI-Second-Brain
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
pause
