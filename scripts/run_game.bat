@echo off
chcp 65001 >nul
echo 포켓볼 게임 시작...

cd /d "%~dp0.."
call .venv\Scripts\activate.bat
cd client
python main.py
pause
