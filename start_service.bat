@echo on
echo ======================================
echo 消防安全管理系统服务启动脚本
echo ======================================

REM 切换到项目目录
cd /d %~dp0

echo [%time%] 正在激活虚拟环境...
call venv\Scripts\activate || (
    echo 错误: 虚拟环境激活失败!
    echo 请确保您已创建虚拟环境: python -m venv venv
    pause
    exit /b 1
)

REM 检查Python和虚拟环境是否正常
python --version
if %errorlevel% neq 0 (
    echo 错误: Python未正确安装或虚拟环境有问题!
    pause
    exit /b 1
)

echo [%time%] 检查Waitress是否已安装...
python -c "import waitress" 2>nul || (
    echo [%time%] Waitress未安装，正在安装...
    pip install waitress
    if %errorlevel% neq 0 (
        echo 错误: 安装Waitress失败!
        pause
        exit /b 1
    )
)

echo [%time%] 确保日志目录存在...
if not exist logs mkdir logs

echo [%time%] 启动服务器...
echo 服务器日志将写入 logs\server_*.log 文件
echo 按CTRL+C可以停止服务器

REM 启动Waitress服务器
python run_with_waitress.py

echo [%time%] 服务器已停止
pause
