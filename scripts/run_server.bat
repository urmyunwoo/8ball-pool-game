@echo off
chcp 65001 >nul
echo 포켓볼 서버 시작...

cd /d "%~dp0.."
call .venv\Scripts\activate.bat
cd server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
