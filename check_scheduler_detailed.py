from app import create_app, db
from app.scheduler import scheduler
import datetime
import pytz
import time

app = create_app()

with app.app_context():
    print(f"\n=== 调度器详细状态检查 ===")
    
    # 1. 检查调度器基本状态
    print(f"调度器是否运行: {scheduler.running}")
    print(f"调度器时区: {scheduler.timezone}")
    print(f"系统时区: {datetime.datetime.now().astimezone().tzinfo}")
    
    # 2. 检查系统时间
    now = datetime.datetime.now()
    utc_now = datetime.datetime.utcnow()
    print(f"当前本地时间: {now}")
    print(f"当前UTC时间: {utc_now}")
    print(f"时差: {now - utc_now}")
    
    # 3. 检查所有任务
    jobs = scheduler.get_jobs()
    print(f"注册的任务数量: {len(jobs)}")
    
    if not jobs:
        print("警告: 没有找到任何已注册的任务!")
    
    # 4. 手动计算下次运行时间
    for job in jobs:
        print(f"\n任务ID: {job.id}")
        print(f"触发器类型: {job.trigger.__class__.__name__}")
        
        # 尝试获取任务设置
        if hasattr(job.trigger, 'fields'):
            print("触发器字段:")
            for field in job.trigger.fields:
                if hasattr(field, 'name') and hasattr(field, 'expressions'):
                    print(f"  {field.name}: {[str(e) for e in field.expressions]}")
        
        # 检查下次运行时间
        if hasattr(job, 'next_run_time'):
            next_run = job.next_run_time
            print(f"下次运行时间: {next_run}")
            
            # 计算与当前时间的差异
            now_with_tz = datetime.datetime.now(next_run.tzinfo)
            time_diff = next_run - now_with_tz
            print(f"距离下次运行: {time_diff}")
            seconds_diff = time_diff.total_seconds()
            print(f"  - 秒数: {seconds_diff}")
            print(f"  - 分钟: {seconds_diff/60:.2f}")
            print(f"  - 小时: {seconds_diff/3600:.2f}")
            
            # 检查是否应该在最近执行
            if -300 < seconds_diff < 300:  # 在5分钟内
                print("提示: 任务应该最近执行或即将执行!")
        else:
            print("警告: 任务没有设置下次运行时间")
    
    # 5. 检查来自数据库的任务配置
    from app.models.scheduler_config import SchedulerConfig
    configs = SchedulerConfig.query.filter_by(enabled=True).all()
    print(f"\n数据库中启用的任务配置: {len(configs)}")
    
    for config in configs:
        print(f"配置ID: {config.id}, 名称: {config.name}")
        print(f"  - 频率: {config.frequency_type}")
        print(f"  - 执行时间: {config.execution_time}")
        
        # 尝试解析时间
        try:
            hour, minute = map(int, config.execution_time.split(':'))
            print(f"  - 解析后的时间: {hour:02d}:{minute:02d}")
            
            # 手动计算下次执行时间
            now = datetime.datetime.now()
            if hour > now.hour or (hour == now.hour and minute > now.minute):
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            else:
                next_run = (now + datetime.timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            print(f"  - 预期下次执行时间: {next_run}")
            time_diff = next_run - now
            print(f"  - 距离下次执行: {time_diff}")
            
        except Exception as e:
            print(f"  - 时间解析错误: {str(e)}")
    
    print("\n=== 调度器监控开始 ===")
    print("将监控5分钟，每10秒检查一次任务执行情况...")
    
    # 记录初始任务执行次数
    from app.models.mail_log import MailLog
    initial_mail_count = MailLog.query.filter(
        MailLog.username == "系统自动发送",
        MailLog.send_time > datetime.datetime.now() - datetime.timedelta(hours=24)
    ).count()
    
    print(f"过去24小时内的自动邮件数量: {initial_mail_count}")
    
    # 监控5分钟
    end_time = time.time() + 300  # 5分钟后
    while time.time() < end_time:
        current_mail_count = MailLog.query.filter(
            MailLog.username == "系统自动发送",
            MailLog.send_time > datetime.datetime.now() - datetime.timedelta(hours=24)
        ).count()
        
        if current_mail_count > initial_mail_count:
            print(f"[{datetime.datetime.now()}] 检测到新的自动邮件! 总数: {current_mail_count}")
            initial_mail_count = current_mail_count
        
        # 获取当前所有任务的下次执行时间
        print(f"[{datetime.datetime.now()}] 任务状态检查:")
        for job in scheduler.get_jobs():
            if job.next_run_time:
                time_diff = job.next_run_time - datetime.datetime.now(job.next_run_time.tzinfo)
                print(f"  - {job.id}: 下次执行时间 {job.next_run_time}, 剩余 {time_diff}")
            else:
                print(f"  - {job.id}: 未设置下次执行时间")
        
        # 等待10秒
        time.sleep(10)
    
    print("\n=== 监控结束 ===")
