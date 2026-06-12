@echo off
REM ============================================================
REM  停止并卸载 QR Export Windows 服务 (NSSM)
REM  注意: 必须以 管理员身份 运行
REM ============================================================
setlocal

set SERVICE_NAME=QR Export Service

for /f "delims=" %%i in ('where nssm 2^>nul') do set NSSM=%%i
if "%NSSM%"=="" (
    echo [ERROR] 未找到 nssm.exe
    endlocal
    exit /b 1
)

sc query "%SERVICE_NAME%" >nul 2>&1
if errorlevel 1 (
    echo [INFO] 服务 "%SERVICE_NAME%" 不存在, 无需卸载
    endlocal
    exit /b 0
)

echo [1/2] 停止服务 ...
net stop "%SERVICE_NAME%" 2>nul
%NSSM% stop "%SERVICE_NAME%" confirm >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/2] 删除服务 ...
%NSSM% remove "%SERVICE_NAME%" confirm
if errorlevel 1 (
    echo [ERROR] 删除失败, 请确保以管理员身份运行
    endlocal
    exit /b 1
)

echo [DONE] 服务已卸载。
endlocal
