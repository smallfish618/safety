@echo off
echo 正在后台启动服务器...
start /min cmd /c "cd /d %~dp0 && call venv\Scripts\activate && python run_with_waitress.py > logs\console_output.log 2>&1"
echo 服务器已在后台启动，日志保存在logs目录中
echo 要查看实时日志，请运行: type logs\server_YYYYMMDD.log
timeout /t 5
