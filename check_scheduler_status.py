from app import create_app, db
from app.scheduler import scheduler
import datetime

app = create_app()

with app.app_context():
    print(f"\n=== 调度器状态检查 ===")
    
    # 检查调度器运行状态
    print(f"调度器是否运行: {scheduler.running}")
    
    # 获取所有调度任务
    jobs = scheduler.get_jobs()
    print(f"注册的任务数量: {len(jobs)}")
    
    # 输出每个任务的详细信息
    for job in jobs:
        print(f"\n任务ID: {job.id}")
        print(f"执行函数: {job.func.__name__ if hasattr(job.func, '__name__') else str(job.func)}")
        print(f"触发器类型: {job.trigger.__class__.__name__}")
        
        # 尝试获取下次运行时间
        if hasattr(job, 'next_run_time'):
            next_run = job.next_run_time
            print(f"下次运行时间: {next_run}")
            
            # 计算距离下次运行的时间
            now = datetime.datetime.now(next_run.tzinfo)
            time_diff = next_run - now
            print(f"距离下次运行: {time_diff}")
        else:
            print("警告: 任务没有设置下次运行时间")
        
        # 检查触发器的具体设置
        if hasattr(job.trigger, 'fields'):
            print("触发器字段:")
            for field in job.trigger.fields:
                if hasattr(field, 'name') and hasattr(field, 'expressions'):
                    print(f"  {field.name}: {[str(e) for e in field.expressions]}")
    
    print("\n当前时间:", datetime.datetime.now())
    print("系统时区:", datetime.datetime.now().astimezone().tzinfo)
    print("===========================\n")
