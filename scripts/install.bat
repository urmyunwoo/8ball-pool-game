@echo off
chcp 65001 >nul
echo ========================================
echo   포켓볼 게임 패키지 설치
echo ========================================

cd /d "%~dp0.."

if not exist ".venv" (
    echo 가상환경 생성 중...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo 클라이언트 패키지 설치 중...
pip install -r client\requirements.txt

echo 서버 패키지 설치 중...
pip install -r server\requirements.txt

echo.
echo ========================================
echo   설치 완료!
echo   scripts\run_game.bat  → 게임 실행
echo   scripts\run_server.bat → 서버 실행
echo ========================================
pause
