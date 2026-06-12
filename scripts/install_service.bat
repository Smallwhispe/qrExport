@echo off
REM ============================================================
REM  安装并启动 "QR Export" 为 Windows 服务 (NSSM)
REM  说明:
REM    - 优先使用 dist\QrExport.exe（PyInstaller 打包产物，无需 Python）
REM    - 找不到 exe 时才回退到用 python.exe 跑源码
REM  注意: 必须以 管理员身份 运行本脚本
REM ============================================================
setlocal
chcp 65001 >nul

cd /d "%~dp0\.."
set ROOT=%cd%

REM === 服务配置 ===
set SERVICE_NAME=QR Export Service
set SERVICE_DISPLAY=QR Export Service
set SERVICE_DESC=定时从 Oracle 导出二维码并弹窗展示

REM === 1) 准备执行程序 ===
set EXE=%ROOT%\dist\QrExport.exe
if exist "%EXE%" (
    set RUNNER="%EXE%"
    set RUNNER_ARGS=
    echo [INFO] 使用打包好的 exe: %EXE%
    goto :check_nssm
)

REM exe 不存在时, 尝试用系统 python 跑源码
for /f "delims=" %%i in ('where python 2^>nul') do set PYTHON=%%i
if "%PYTHON%"=="" (
    echo [ERROR] 既未找到 dist\QrExport.exe, 也未找到 python.exe
    echo         请先执行 scripts\build_windows.bat 打包出 exe,
    echo         或将整个 dist\ 目录拷到此机器后再运行本脚本。
    endlocal
    exit /b 1
)
set RUNNER="%PYTHON%"
set RUNNER_ARGS="%ROOT%\app.py"
echo [INFO] 使用源码方式: %PYTHON% app.py

:check_nssm
for /f "delims=" %%i in ('where nssm 2^>nul') do set NSSM=%%i
if "%NSSM%"=="" (
    echo [ERROR] 未找到 nssm.exe
    echo 请从 https://nssm.cc/download 下载, 任选一种方式:
    echo   1) 把 nssm.exe 放到 C:\Windows\System32\
    echo   2) 或放到项目的 scripts\ 目录
    echo   3) 或解压后把它所在目录加入 PATH
    endlocal
    exit /b 1
)

echo [INFO] 服务名     : %SERVICE_NAME%
echo [INFO] 工作目录   : %ROOT%
echo [INFO] NSSM       : %NSSM%
if not exist "%ROOT%\.env" (
    echo [WARN] 未找到 %ROOT%\.env, 请确认配置文件存在。
)
echo.

REM === 若已存在, 先停 + 删 ===
sc query "%SERVICE_NAME%" >nul 2>&1
if %errorlevel%==0 (
    echo [1/5] 服务已存在, 先停止并删除 ...
    net stop "%SERVICE_NAME%" 2>nul
    %NSSM% stop "%SERVICE_NAME%" confirm >nul 2>&1
    %NSSM% remove "%SERVICE_NAME%" confirm >nul 2>&1
    timeout /t 2 /nobreak >nul
)

REM === 安装 ===
echo [2/5] 安装服务 ...
%NSSM% install "%SERVICE_NAME%" %RUNNER% %RUNNER_ARGS%
if errorlevel 1 (
    echo [ERROR] 安装失败, 请确保:
    echo         - 本脚本以 管理员身份 运行
    echo         - nssm.exe 与 QrExport.exe 同是 32/64 位
    endlocal
    exit /b 1
)

REM === 配置 ===
echo [3/5] 配置服务参数 ...
if not exist "%ROOT%\log" mkdir "%ROOT%\log"

%NSSM% set "%SERVICE_NAME%" AppDirectory "%ROOT%"
%NSSM% set "%SERVICE_NAME%" AppStdout "%ROOT%\log\service-stdout.log"
%NSSM% set "%SERVICE_NAME%" AppStderr "%ROOT%\log\service-stderr.log"
%NSSM% set "%SERVICE_NAME%" Start SERVICE_AUTO_START
%NSSM% set "%SERVICE_NAME%" Description "%SERVICE_DESC%"
%NSSM% set "%SERVICE_NAME%" DisplayName "%SERVICE_DISPLAY%"
%NSSM% set "%SERVICE_NAME%" AppExit Default Restart
%NSSM% set "%SERVICE_NAME%" AppRestartDelay 3000
%NSSM% set "%SERVICE_NAME%" AppThrottle 1500

REM === 启动 ===
echo [4/5] 启动服务 ...
net start "%SERVICE_NAME%"
if errorlevel 1 (
    echo [ERROR] 服务启动失败。常见原因:
    echo         - .env 配置缺失 / Oracle 账号密码错误
    echo         - 5001 端口被占用
    echo         - 查看日志: %ROOT%\log\service-stderr.log
    endlocal
    exit /b 1
)

echo [5/5] 完成。
echo.
echo 常用命令:
echo   启动    : net start "%SERVICE_NAME%"
echo   停止    : net stop  "%SERVICE_NAME%"
echo   重启    : net stop "%SERVICE_NAME%" ^&^& net start "%SERVICE_NAME%"
echo   图形配置: nssm edit "%SERVICE_NAME%"
echo   查看状态: services.msc  或  sc query "%SERVICE_NAME%"
echo   健康检查: 浏览器访问 http://127.0.0.1:5001/health
echo.
endlocal
