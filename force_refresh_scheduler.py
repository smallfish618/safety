from app import create_app
from app.scheduler import scheduler, register_scheduled_tasks
import time

app = create_app()

with app.app_context():
    print("强制重新注册所有调度任务...")
    
    # 先停止调度器
    if scheduler.running:
        print("停止现有调度器...")
        scheduler.shutdown()
        time.sleep(2)
    
    # 重新启动调度器
    print("重新启动调度器...")
    scheduler.start()
    time.sleep(2)
    
    if scheduler.running:
        print(f"调度器已启动，状态: {scheduler.running}")
        
        # 清空现有任务
        jobs = scheduler.get_jobs()
        print(f"清除现有任务 ({len(jobs)}个)...")
        for job in jobs:
            scheduler.remove_job(job.id)
        
        # 重新注册任务
        print("重新注册调度任务...")
        register_scheduled_tasks(app)
        
        # 检查注册结果
        jobs = scheduler.get_jobs()
        print(f"重新注册后的任务数量: {len(jobs)}")
        
        for job in jobs:
            next_run = getattr(job, 'next_run_time', None)
            print(f"任务ID: {job.id}, 下次执行时间: {next_run}")
    else:
        print("错误: 调度器无法启动")
