from app import create_app
from app.scheduler import scheduler
import time
from datetime import datetime

app = create_app()

with app.app_context():
    print(f"\n=== 调度器状态监控 ===")
    print(f"当前时间: {datetime.now()}")
    print(f"调度器是否运行: {scheduler.running}")
    
    jobs = scheduler.get_jobs()
    print(f"注册的任务数量: {len(jobs)}")
    
    for job in jobs:
        print(f"\n任务ID: {job.id}")
        print(f"触发器类型: {job.trigger.__class__.__name__}")
        
        if hasattr(job, 'next_run_time') and job.next_run_time:
            print(f"下次运行时间: {job.next_run_time}")
        else:
            print("下次运行时间: 未调度")
