@echo off
cd /d "%~dp0"

REM 检查 .env 文件是否存在
if not exist ".env" (
    echo [提示] 未找到 .env 文件，使用系统环境变量
    echo [提示] 如需通过文件管理 Key，请复制 .env.example 为 .env 并填入 API Key
    echo.
)

echo 正在启动 Adaptive CRAG...
streamlit run app/main.py --server.port 8501
pause