import logging
from app import create_app
from app.scheduler import scheduler

# 设置APScheduler日志级别为DEBUG
logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

app = create_app()
print("已将APScheduler日志级别设置为DEBUG")
print("请重启应用查看详细日志")
