from app import db
from datetime import datetime

class MailLog(db.Model):
    """邮件发送日志表"""
    __tablename__ = 'mail_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    send_time = db.Column(db.DateTime, default=datetime.now, nullable=False)  # 发送时间
    sender = db.Column(db.String(100), nullable=False)  # 发件人邮箱
    recipient = db.Column(db.String(100), nullable=False)  # 收件人邮箱
    recipient_name = db.Column(db.String(50))  # 收件人姓名
    subject = db.Column(db.String(200))  # 邮件主题
    content_summary = db.Column(db.Text)  # 邮件内容摘要
    status = db.Column(db.String(20), nullable=False)  # 发送状态：success, failed
    error_message = db.Column(db.Text)  # 错误信息
    items_count = db.Column(db.Integer, default=0)  # 预警物品数量
    ip_address = db.Column(db.String(50))  # 发送IP地址
    user_id = db.Column(db.Integer)  # 操作用户ID
    username = db.Column(db.String(50))  # 操作用户名
    
    def __repr__(self):
        return f'<MailLog {self.id} to {self.recipient} at {self.send_time}>'
