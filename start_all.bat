@echo off
echo ========================================
echo   CONTENT ROBOT v3.1 - STARTUP
echo ========================================
echo.

cd /d "%~dp0"
call venv\Scripts\activate.bat

echo [1/3] Iniciando Content Robot...
start "Content Robot" cmd /k python content_robot.py

timeout /t 5 /nobreak

echo [2/3] Iniciando Dashboard...
start "Dashboard" cmd /k python dashboard.py

timeout /t 5 /nobreak

echo [3/3] Iniciando Sistema de Aprovação...
start "Approval System" cmd /k python approval_system.py

echo.
echo ========================================
echo   TODOS OS SISTEMAS INICIADOS!
echo ========================================
echo.
echo Dashboard: http://localhost:5000
echo Aprovacao: http://localhost:5001
echo.
echo Pressione qualquer tecla para sair...
pause > nul