from app import db
from datetime import datetime

class SchedulerConfig(db.Model):
    """定时任务配置表"""
    __tablename__ = 'scheduler_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 任务名称
    enabled = db.Column(db.Boolean, default=True)  # 是否启用
    frequency_type = db.Column(db.String(20), nullable=False)  # 频率类型: daily, weekly, monthly
    execution_time = db.Column(db.String(10), nullable=False)  # 执行时间，格式: HH:MM
    day_of_week = db.Column(db.String(10))  # 周几执行，用于weekly: mon, tue, wed, thu, fri, sat, sun
    day_of_month = db.Column(db.Integer)  # 每月几号执行，用于monthly: 1-31
    warning_levels = db.Column(db.String(100))  # 预警级别，逗号分隔: expired,within_30,within_60,within_90
    recipient_filter = db.Column(db.String(200))  # 接收人筛选，逗号分隔的负责人名称或'all'
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.Integer)  # 创建者用户ID
    
    def __repr__(self):
        return f'<SchedulerConfig {self.name}>'
