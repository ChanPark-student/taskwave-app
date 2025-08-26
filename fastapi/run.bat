@echo off
REM 1) 포트 8000 쓰는 프로세스 모두 강제 종료
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8000') do (
    echo Killing PID %%p on port 8000...
    taskkill /F /PID %%p >nul 2>&1
)

