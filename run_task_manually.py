from app import create_app, db
from app.scheduler import send_scheduled_expiry_alerts
import datetime

app = create_app()

# 获取要测试的任务ID
config_id = input("请输入要测试的任务配置ID: ")
try:
    config_id = int(config_id)
except ValueError:
    print("错误: 请输入有效的任务ID（整数）")
    exit(1)

print(f"开始手动执行任务ID: {config_id}")
print(f"当前时间: {datetime.datetime.now()}")

with app.app_context():
    from app.models.scheduler_config import SchedulerConfig
    
    # 确认任务存在
    config = SchedulerConfig.query.get(config_id)
    if not config:
        print(f"错误: 找不到ID为 {config_id} 的任务配置")
        exit(1)
    
    print(f"找到任务: {config.name}")
    print(f"预定执行时间: {config.execution_time}")
    print(f"任务状态: {'启用' if config.enabled else '禁用'}")
    
    # 手动执行任务
    print("开始执行任务...")
    send_scheduled_expiry_alerts(app, config_id)
    print("任务执行完成")
    
    # 检查是否发送了邮件
    from app.models.mail_log import MailLog
    recent_logs = MailLog.query.filter(
        MailLog.send_time > datetime.datetime.now() - datetime.timedelta(minutes=5)
    ).all()
    
    print(f"过去5分钟内的邮件日志数量: {len(recent_logs)}")
    for log in recent_logs:
        print(f"ID: {log.id}, 时间: {log.send_time}, 状态: {log.status}, 收件人: {log.recipient_name}")
