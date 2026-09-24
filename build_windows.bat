@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo   图片随机测试 - Windows EXE 打包
echo ========================================
echo.

where py >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python Launcher (py)。
    echo 请先安装 Python 3.11+，并勾选“Add Python to PATH”。
    pause
    exit /b 1
)

echo [1/4] 安装/更新打包依赖...
py -m pip install --upgrade pip
py -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo [错误] Python 依赖安装失败。
    pause
    exit /b 1
)

echo.
echo [2/4] 清理旧构建...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "图片随机测试.spec" del /q "图片随机测试.spec"

echo.
echo [3/4] 构建 Windows 单文件 EXE...
py -m PyInstaller --noconfirm --clean --onefile --windowed --name "图片随机测试" "图片随机测试.py"
if errorlevel 1 (
    echo [错误] PyInstaller 打包失败。
    pause
    exit /b 1
)

echo.
echo [4/4] 完成。
echo EXE 已生成：
echo %CD%\dist\图片随机测试.exe

echo.
echo 双击 dist\图片随机测试.exe 即可运行。
pause
endlocal
