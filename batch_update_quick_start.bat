@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM 消防器材数据库批量更新 - 快速开始脚本

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║       消防器材数据库批量更新 - 快速开始向导                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ 错误: 未找到Python环境
    echo.
    echo 请确保已安装Python 3.7及以上版本
    echo 可从 https://www.python.org/ 下载安装
    pause
    exit /b 1
)

echo ✓ Python环境检测成功
echo.
echo 请选择要执行的操作:
echo.
echo 1. 【第一次使用】生成Excel数据模板
echo 2. 【准备数据】打开数据模板文件进行填写
echo 3. 【开始导入】执行数据库批量更新
echo 4. 【查看日志】查看最近的操作日志
echo 5. 【查看指南】打开操作指南文档
echo 6. 【退出程序】
echo.

set /p choice=请输入选项 (1-6):

if "%choice%"=="1" (
    call :generate_template
) else if "%choice%"=="2" (
    call :open_template
) else if "%choice%"=="3" (
    call :run_import
) else if "%choice%"=="4" (
    call :view_logs
) else if "%choice%"=="5" (
    call :view_guide
) else if "%choice%"=="6" (
    echo 再见！
    exit /b 0
) else (
    echo ✗ 无效的选项
    timeout /t 2 /nobreak > nul
    exit /b 1
)

goto end

REM ============================================================
REM 函数定义
REM ============================================================

:generate_template
echo.
echo 【第一步】生成Excel数据模板...
echo.
python create_excel_template.py
if errorlevel 1 (
    echo ✗ 生成模板失败
    pause
    exit /b 1
)
echo.
echo ✓ 模板生成成功!
echo.
echo 文件位置: e:\safety\data\batch_update_template.xlsx
echo.
pause
goto end

:open_template
echo.
echo 【第二步】打开数据模板...
echo.
if not exist "e:\safety\data\batch_update_template.xlsx" (
    echo ✗ 模板文件不存在
    echo.
    echo 请先执行选项 1 生成模板
    pause
    exit /b 1
)
echo 正在打开Excel文件...
start "" "e:\safety\data\batch_update_template.xlsx"
echo.
echo ✓ Excel文件已打开
echo.
echo 请填写以下内容:
echo 1. 在"消防器材"页签中填写消防器材数据
echo 2. 在"微型消防站"页签中填写微型消防站数据
echo 3. 完成填写后保存文件(Ctrl+S)
echo.
pause
goto end

:run_import
echo.
echo 【第三步】执行数据库批量更新...
echo.
if not exist "e:\safety\data\batch_update_template.xlsx" (
    echo ✗ 错误: 找不到数据文件
    echo.
    echo 请先执行以下步骤:
    echo 1. 执行选项 1 生成模板
    echo 2. 执行选项 2 打开模板并填写数据
    echo.
    pause
    exit /b 1
)
echo ⚠ 警告: 此操作将:
echo  - 备份当前数据库
echo  - 清空两个表的数据
echo  - 导入新数据
echo.
set /p confirm=确定要继续吗？(y/n):
if not "%confirm%"=="y" (
    echo 已取消操作
    pause
    exit /b 0
)
echo.
python batch_update_database.py
if errorlevel 1 (
    echo ✗ 导入失败，请查看日志信息
    pause
    exit /b 1
)
echo.
echo ✓ 导入完成！
pause
goto end

:view_logs
echo.
echo 【查看日志】
echo.
if not exist "e:\safety\logs" (
    echo 暂无日志记录
    pause
    exit /b 0
)
echo 最近的操作日志:
echo.
for /f "tokens=*" %%A in (
    'dir /b /o-d "e:\safety\logs\batch_update_*.log" 2^>nul'
) do (
    set latest_log=%%A
    goto found_log
)
echo 暂无日志记录
pause
exit /b 0

:found_log
echo 文件: e:\safety\logs\%latest_log%
echo.
echo 日志内容:
echo ────────────────────────────────────────────────────────────
type "e:\safety\logs\%latest_log%" | findstr /R ".*"
echo ────────────────────────────────────────────────────────────
echo.
pause
goto end

:view_guide
echo.
echo 【操作指南】
echo.
if not exist "BATCH_UPDATE_GUIDE.md" (
    echo ✗ 指南文件不存在
    pause
    exit /b 1
)
echo 正在打开操作指南...
start "" "BATCH_UPDATE_GUIDE.md"
pause
goto end

:end
cls
goto :eof
