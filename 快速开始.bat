@echo off
chcp 65001 >nul
echo ========================================
echo   MoodAngels-LangGraph-DeepSeek
echo   多Agent精神疾病辅助筛查系统
echo ========================================
echo.

echo [1/4] 检查 Python 环境...
python --version
if %errorlevel% neq 0 (
    echo 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)
echo.

echo [2/4] 检查虚拟环境...
if not exist ".venv" (
    echo 创建虚拟环境...
    python -m venv .venv
)
echo.

echo [3/4] 激活虚拟环境并安装依赖...
call .venv\Scripts\activate.bat
pip install -r requirements.txt
echo.

echo [4/4] 运行系统测试...
echo.
echo 正在测试多 Agent 系统...
python test_full_workflow.py
echo.

echo ========================================
echo   系统准备完成！
echo ========================================
echo.
echo 请选择下一步操作:
echo.
echo   1. 启动 Web 服务 (推荐)
echo   2. 运行命令行 Demo
echo   3. 配置 DeepSeek API Key
echo   4. 退出
echo.
set /p choice=请输入选项 (1-4): 

if "%choice%"=="1" (
    echo.
    echo 启动 Web 服务...
    echo 浏览器将自动打开: http://127.0.0.1:8000
    echo 按 Ctrl+C 停止服务
    echo.
    start http://127.0.0.1:8000
    uvicorn app.main:app --reload --port 8000
) else if "%choice%"=="2" (
    echo.
    echo 运行命令行 Demo...
    echo.
    python run_demo.py
    echo.
    pause
) else if "%choice%"=="3" (
    echo.
    echo 正在打开 .env 配置文件...
    echo 请填写 DEEPSEEK_API_KEY= 你的 API Key
    echo 获取地址: https://platform.deepseek.com/
    echo.
    notepad .env
    pause
) else (
    echo.
    echo 退出。
    echo.
    echo 提示:
    echo   - 后续可直接运行: .venv\Scripts\activate ^&^& uvicorn app.main:app --port 8000
    echo   - 配置 DeepSeek: 编辑 .env 文件填写 API Key
    echo   - 详细文档: 查看 DEEPSEEK配置指南.md
    echo.
    pause
)
