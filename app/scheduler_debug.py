import logging
import sys
import traceback
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask import current_app
import time
import os

# 设置更详细的调度器日志
logging.basicConfig(level=logging.DEBUG)
scheduler_logger = logging.getLogger('apscheduler')
scheduler_logger.setLevel(logging.DEBUG)

# 将apscheduler的日志同时输出到控制台
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
scheduler_logger.addHandler(handler)

# 尝试导入psutil，但如果不可用则不会中断程序
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    print("[调试] psutil库未安装，某些系统资源监控功能将不可用")
    HAS_PSUTIL = False

def debug_init_scheduler(app):
    """增强的调度器初始化函数，带有详细的调试输出"""
    print("\n==================================================")
    print("==         调度器初始化调试模式开始         ==")
    print("==================================================")
    
    try:
        # 记录Python版本和环境信息
        print(f"[调试] Python版本: {sys.version}")
        print(f"[调试] 平台信息: {sys.platform}")
        
        # 检查apscheduler版本
        import apscheduler
        print(f"[调试] APScheduler版本: {apscheduler.__version__}")
        
        # 记录当前线程信息
        import threading
        print(f"[调试] 当前线程ID: {threading.get_ident()}")
        print(f"[调试] 活动线程数: {threading.active_count()}")
        
        # 记录进程信息 - 只在psutil可用时执行
        print(f"[调试] 进程ID: {os.getpid()}")
        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            print(f"[调试] 进程内存使用: {process.memory_info().rss / 1024 / 1024:.2f} MB")
        else:
            print("[调试] psutil不可用，跳过详细的进程资源监控")
        
        # 记录初始化前的调度器状态
        print("[调试] 检查是否有现有的调度器实例...")
        
        # 尝试获取应用程序上下文中的调度器
        scheduler = None
        if hasattr(app, 'scheduler'):
            scheduler = app.scheduler
            print(f"[调试] 发现现有调度器: {scheduler}")
            print(f"[调试] 调度器状态: {'运行中' if scheduler.running else '已停止'}")
        else:
            print("[调试] 未找到现有调度器实例")
        
        # 创建调度器配置对象 - 详细输出每一步配置
        print("[调试] 准备创建调度器配置...")
        
        # 检查应用配置
        print("[调试] 检查应用配置:")
        config_keys = [
            'SCHEDULER_JOBSTORES', 'SCHEDULER_EXECUTORS', 'SCHEDULER_JOB_DEFAULTS',
            'SCHEDULER_API_ENABLED', 'SCHEDULER_TIMEZONE'
        ]
        for key in config_keys:
            if key in app.config:
                print(f"[调试] 发现配置 {key}: {app.config[key]}")
            else:
                print(f"[调试] 未找到配置 {key}")
        
        # 检查数据库连接
        if 'SQLALCHEMY_DATABASE_URI' in app.config:
            from sqlalchemy import create_engine
            from sqlalchemy.exc import SQLAlchemyError
            try:
                print("[调试] 检查数据库连接...")
                engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
                with engine.connect() as conn:
                    print("[调试] 数据库连接成功")
            except SQLAlchemyError as e:
                print(f"[调试] 数据库连接错误: {e}")
        
        # 准备启动参数
        print("[调试] 准备调度器启动参数...")
        
        # 这里我们使用详细的方式构建配置
        jobstores = {
            'default': SQLAlchemyJobStore(url=app.config.get('SQLALCHEMY_DATABASE_URI'))
        }
        print(f"[调试] 配置 jobstores: {jobstores}")
        
        executors = {
            'default': ThreadPoolExecutor(20),
            'processpool': ProcessPoolExecutor(5)
        }
        print(f"[调试] 配置 executors: {executors}")
        
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        print(f"[调试] 配置 job_defaults: {job_defaults}")
        
        # 详细记录调度器创建过程 - 分步创建
        print("[调试] 步骤1: 创建调度器实例...")
        scheduler = BackgroundScheduler()
        print(f"[调试] 调度器实例创建成功: {scheduler}")
        
        print("[调试] 步骤2: 配置jobstores...")
        for name, jobstore in jobstores.items():
            try:
                scheduler.add_jobstore(jobstore, name)
                print(f"[调试] 成功添加jobstore '{name}'")
            except Exception as e:
                print(f"[调试] 添加jobstore '{name}'失败: {e}")
                traceback.print_exc()
        
        print("[调试] 步骤3: 配置executors...")
        for name, executor in executors.items():
            try:
                scheduler.add_executor(executor, name)
                print(f"[调试] 成功添加executor '{name}'")
            except Exception as e:
                print(f"[调试] 添加executor '{name}'失败: {e}")
                traceback.print_exc()
        
        print("[调试] 步骤4: 应用job_defaults...")
        if hasattr(scheduler, 'configure'):
            scheduler.configure(job_defaults=job_defaults)
            print("[调试] 成功应用job_defaults")
        else:
            print("[调试] 警告: 调度器没有configure方法，无法应用job_defaults")
        
        # 设置时区
        if 'SCHEDULER_TIMEZONE' in app.config:
            print(f"[调试] 设置时区为: {app.config['SCHEDULER_TIMEZONE']}")
            scheduler.timezone = app.config['SCHEDULER_TIMEZONE']
        
        # 现在尝试启动调度器
        print("[调试] 步骤5: 启动调度器 - 主方法...")
        try:
            scheduler.start()
            time.sleep(0.5)  # 给调度器一点时间启动
            print(f"[调试] 调度器启动状态: {'运行中' if scheduler.running else '未运行'}")
            
            if scheduler.running:
                print("[调试] 调度器主方法启动成功")
                app.scheduler = scheduler
            else:
                print("[调试] 调度器启动失败，检查原因...")
                
                # 检查常见的错误原因
                print("[调试] 检查进程锁文件...")
                # 根据平台选择临时目录
                temp_dir = '/tmp' if sys.platform != 'win32' else os.environ.get('TEMP', 'C:\\Windows\\Temp')
                try:
                    lock_files = [f for f in os.listdir(temp_dir) if f.startswith('apscheduler_') and f.endswith('.lock')]
                    if lock_files:
                        print(f"[调试] 发现锁文件: {lock_files}")
                        print("[调试] 可能是由于上一个进程未正常退出，锁文件未释放")
                    else:
                        print("[调试] 未发现锁文件")
                except Exception as e:
                    print(f"[调试] 检查锁文件时出错: {e}")
                
                print("[调试] 尝试备用方法...")
                # 备用方法：直接使用原生API创建
                new_scheduler = BackgroundScheduler(
                    jobstores=jobstores,
                    executors=executors,
                    job_defaults=job_defaults
                )
                new_scheduler.start()
                time.sleep(0.5)
                
                if new_scheduler.running:
                    print("[调试] 备用方法启动成功")
                    app.scheduler = new_scheduler
                else:
                    print("[调试] 备用方法也失败了，检查系统资源...")
                    
                    # 检查系统资源 - 只在psutil可用时执行
                    if HAS_PSUTIL:
                        print(f"[调试] CPU使用率: {psutil.cpu_percent()}%")
                        print(f"[调试] 内存使用率: {psutil.virtual_memory().percent}%")
                        print(f"[调试] 可用内存: {psutil.virtual_memory().available / 1024 / 1024:.2f} MB")
                        process = psutil.Process(os.getpid())
                        print(f"[调试] 当前进程打开的文件数: {len(process.open_files())}")
                        print(f"[调试] 当前进程线程数: {len(process.threads())}")
                    else:
                        print("[调试] psutil不可用，无法检查详细系统资源")
        except Exception as e:
            print(f"[调试] 调度器启动时捕获异常: {e}")
            traceback.print_exc()
            print("[调试] 尝试使用最简单的配置重新启动...")
            
            # 尝试最简单的配置
            try:
                simple_scheduler = BackgroundScheduler()
                simple_scheduler.start()
                time.sleep(0.5)
                
                if simple_scheduler.running:
                    print("[调试] 简单配置启动成功，问题可能在复杂配置中")
                    app.scheduler = simple_scheduler
                else:
                    print("[调试] 即使最简单的配置也无法启动，可能是环境问题")
            except Exception as e2:
                print(f"[调试] 简单配置也失败了: {e2}")
                traceback.print_exc()
        
        # 最终检查调度器状态
        if hasattr(app, 'scheduler') and app.scheduler.running:
            print("[调试] 调度器配置完成，状态正常")
            return app.scheduler
        else:
            print("[调试] 调度器配置失败，请检查日志并解决问题")
            return None
            
    except Exception as e:
        print(f"[调试] 调度器初始化过程中发生未捕获的异常: {e}")
        traceback.print_exc()
        return None
    finally:
        print("==================================================")
        print("==         调度器初始化调试模式结束         ==")
        print("==================================================")

# 扩展调度器启动函数，用于替换现有的初始化函数
def init_scheduler(app):
    """增强的调度器初始化函数，包含详细的调试输出"""
    return debug_init_scheduler(app)
