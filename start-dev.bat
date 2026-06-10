@echo off
chcp 65001 >nul
echo ========================================
echo   天天半首诗 - 一键启动脚本
echo ========================================
echo.
echo 正在启动后端 API 服务器...
echo.

cd /d "%~dp0backend"

if not exist "venv\Scripts\python.exe" (
    echo [错误] 虚拟环境不存在！
    echo 请先在 backend 目录下运行:
    echo   python -m venv venv
    echo   venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

if not exist "data" mkdir data

set DEV_MODE=true
set DEBUG=true

echo [1/2] 初始化数据库...
venv\Scripts\python.exe -c "import asyncio;from app.core.database import engine,Base;from app.models.user import User,UserProfile;async def _i():\n async with engine.begin() as c:\n  await c.run_sync(Base.metadata.create_all)\n print('  OK')\nasyncio.run(_i())" 2>nul

echo.
echo [2/2] 启动服务器 (端口 8000)...
echo.
echo   后端地址: http://localhost:8000
echo   API 文档: http://localhost:8000/docs
echo   健康检查: http://localhost:8000/health
echo.
echo   小程序 API 已指向: http://localhost:8000/api/v1
echo.
echo   按 Ctrl+C 停止
echo ========================================

venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
