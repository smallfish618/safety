from app import create_app
from app.scheduler import scheduler, force_start_scheduler
import time

app = create_app()

print("强制启动调度器脚本")
with app.app_context():
    if scheduler.running:
        print(f"调度器已在运行中，状态: {scheduler.running}")
    else:
        print("调度器未运行，尝试强制启动")
        success = force_start_scheduler(app)
        
        if success:
            print("成功强制启动调度器")
            
            # 验证任务
            jobs = scheduler.get_jobs()
            print(f"注册的任务数量: {len(jobs)}")
            for job in jobs:
                next_run = getattr(job, 'next_run_time', None)
                print(f"任务: {job.id}, 下次执行: {next_run if next_run else '未调度'}")
        else:
            print("强制启动失败，请尝试以下措施:")
            print("1. 检查Flask-APScheduler版本")
            print("2. 尝试使用gunicorn或uwsgi启动")
            print("3. 验证调度器配置")

print("\n调度器状态监控运行5分钟...")
end_time = time.time() + 300
while time.time() < end_time:
    with app.app_context():
        status = "运行中" if scheduler.running else "未运行"
        job_count = len(scheduler.get_jobs())
        print(f"[{time.strftime('%H:%M:%S')}] 调度器状态: {status}, 任务数: {job_count}")
    time.sleep(10)
