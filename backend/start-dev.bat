@echo off
chcp 65001 >nul
echo ========================================
echo   天天半首诗 - 本地开发环境启动
echo ========================================
echo.

cd /d "%~dp0"

:: 检查虚拟环境
if not exist "venv\Scripts\python.exe" (
    echo [错误] 虚拟环境不存在，请先运行:
    echo   python -m venv venv
    echo   venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

:: 确保 data 目录存在
if not exist "data" mkdir data

:: 设置开发环境变量
set DEV_MODE=true
set DEBUG=true

:: 创建数据库表（首次运行）
echo [1/2] 初始化数据库...
venv\Scripts\python.exe -c "import asyncio; from app.core.database import engine, Base; from app.models.user import User, UserProfile; asyncio.run((lambda: None)()); asyncio.run((lambda: engine.dispose())())" 2>nul
venv\Scripts\python.exe -c "import asyncio; from app.core.database import engine, Base; from app.models.user import User, UserProfile; exec('async def _init():\n    async with engine.begin() as conn:\n        await conn.run_sync(Base.metadata.create_all)\n    print(\"  数据库表就绪\")\nasyncio.run(_init())')"

:: 启动服务器
echo.
echo [2/2] 启动 API 服务器...
echo.
echo   后端地址: http://localhost:8000
echo   API 文档: http://localhost:8000/docs
echo   健康检查: http://localhost:8000/health
echo.
echo   按 Ctrl+C 停止服务器
echo ========================================
echo.

venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
