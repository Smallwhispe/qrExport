@echo off
REM ============================================================
REM  整理绿色部署包 —— 把 scripts\*.bat 和 .env 复制到 dist\
REM  整理后 dist\ 就是一个完整绿色包, 拷到任何 Windows 机器上无需安装 Python
REM  用法: 在开发机执行 scripts\build_windows.bat 后再跑本脚本
REM ============================================================
setlocal
cd /d "%~dp0\.."
set ROOT=%cd%

if not exist "%ROOT%\dist\QrExport.exe (
    echo [ERROR] 未找到 dist\QrExport.exe
    echo        请先运行 scripts\build_windows.bat
    endlocal
    exit /b 1
)

echo [1/3] 复制脚本到 dist\scripts\
if not exist "%ROOT%\dist\scripts" mkdir "%ROOT%\dist\scripts
copy /y "%ROOT%\scripts\install_service.bat "%ROOT%\dist\scripts\install_service.bat >nul
copy /y "%ROOT%\scripts\uninstall_service.bat "%ROOT%\dist\scripts\uninstall_service.bat >nul
echo   已复制 install_service.bat, uninstall_service.bat

echo [2/3] 复制 .env 到 dist\
if exist "%ROOT%\.env" (
    copy /y "%ROOT%\.env" "%ROOT%\dist\.env" >nul
    echo   已复制 .env
) else (
    echo   [警告: 未找到 %ROOT%\.env, 请手动放置到 dist\ 目录
)

echo [3/3] 复制 README
(
echo QR Export - Windows 部署说明
echo ==========================
echo.
echo 目标机器: Windows 7 / 不再需要安装 Python。
echo.
echo 1. 把本 dist\ 整个目录拷贝到目标机器, 例如 D:\apps\QrExport\
echo 2. 以 右键 dist\scripts\install_service.bat 以管理员身份运行
echo    - 会自动注册为 Windows 服务, 开机自启, 崩溃自动重启
echo.
echo 常用命令:
echo   启动: net start "QR Export Service"
echo   停止: net stop  "QR Export Service"
echo   卸载: 右键 dist\scripts\uninstall_service.bat (管理员)
echo.
echo 验证:
echo   在目标机器浏览器打开 http://127.0.0.1:5001/health
echo.
echo 配置:
echo   编辑 dist\.env 中的 Oracle 账号 / 调度周期 等
) > "%ROOT%\dist\README.txt
echo   已生成 README.txt

echo.
echo [DONE] 绿色部署包已准备好:
echo   目录: %ROOT%\dist\
echo   内容:
dir /b "%ROOT%\dist\"
echo.
echo 将 dist\ 整个目录拷到目标机器后, 以管理员身份运行:
echo   dist\scripts\install_service.bat
echo.
endlocal
