from app import create_app, db
from config import DevelopmentConfig

# 创建应用实例
app = create_app(DevelopmentConfig)

# 在应用上下文中创建所有表
with app.app_context():
    # 使用create_all()方法创建所有表，包括新的mail_logs表
    db.create_all()
    print("所有数据库表已创建，包括mail_logs表")
