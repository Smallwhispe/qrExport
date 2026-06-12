@echo off
REM ============================================================
REM  Windows 一键打包脚本 —— 在开发机执行，产出"绿色版" dist\
REM  效果: 将 Python 解释器、所有 pip 依赖、项目源码
REM         一起打包进 QrExport.exe，目标机器不需要装 Python。
REM  用法: 在本项目根目录双击 scripts\build_windows.bat
REM ============================================================
setlocal
cd /d "%~dp0\.."
set ROOT=%cd%

echo [1/5] 检查本机 Python ...
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 当前机器未找到 python.exe。请先安装 Python 3.10+，
    echo         安装后重启本脚本。下载: https://www.python.org/downloads/
    endlocal
    exit /b 1
)

for /f "delims=" %%i in ('python -c "import sys; print(sys.version.split()[0])"') do set PYVER=%%i
echo   Python 版本: %PYVER%

echo [2/5] 创建/更新本地 venv 并安装依赖 ...
if not exist "%ROOT%\.venv\" (
    python -m venv "%ROOT%\.venv"
)
call "%ROOT%\.venv\Scripts\activate.bat"

python -m pip install --upgrade pip
python -m pip install -r "%ROOT%\requirements.txt"

echo [3/5] 清理旧产物 ...
if exist "%ROOT%\build"  rmdir /s /q "%ROOT%\build"
if exist "%ROOT%\dist"   rmdir /s /q "%ROOT%\dist"
if exist "%ROOT%\QrExport.spec" del /q "%ROOT%\QrExport.spec"

echo [4/5] 开始 PyInstaller 打包（第一次会较慢，约 1-3 分钟） ...
python -m PyInstaller ^
    --onefile ^
    --noconsole ^
    --clean ^
    --noconfirm ^
    --name QrExport ^
    --collect-submodules config ^
    --collect-submodules routes ^
    --collect-submodules services ^
    --collect-submodules vo ^
    --collect-all oracledb ^
    "%ROOT%\app.py"

if errorlevel 1 (
    echo [ERROR] 打包失败, 请查看上方输出。
    call "%ROOT%\.venv\Scripts\deactivate.bat" 2>nul
    endlocal
    exit /b 1
)

echo [5/5] 复制运行时文件到 dist\ ...
if exist "%ROOT%\.env" (
    copy /y "%ROOT%\.env" "%ROOT%\dist\.env" >nul
    echo   已复制 .env -> dist\.env
) else (
    echo   警告: 未找到 %ROOT%\.env
    echo   请将 .env 手动复制到 dist\ 目录下, 与 QrExport.exe 同级。
)

echo.
echo ============================================================
echo [DONE] 打包成功
echo   产物目录       : %ROOT%\dist\
echo   主程序         : %ROOT%\dist\QrExport.exe
echo   配置文件       : %ROOT%\dist\.env
echo ============================================================
echo.
echo 下一步 - 将 dist\ 整个目录拷到目标机器（无需装 Python）：
echo   1) 双击  scripts\install_service.bat  （管理员）注册为服务
echo   2) 或    双击  dist\QrExport.exe      手动运行测试
echo.

call "%ROOT%\.venv\Scripts\deactivate.bat" 2>nul
endlocal
