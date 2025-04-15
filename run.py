import os
import sys
from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash
import logging
from config import ProductionConfig  # 直接导入配置类

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入数据库升级脚本
from app.models.db_upgrade import check_and_upgrade_database

# 使用配置类而非字符串
app = create_app(ProductionConfig)

# 在应用上下文中执行数据库操作
with app.app_context():
    # 注释掉这一行，防止创建新的表结构
    # db.create_all()
    
    # 仅检查并添加缺失的列
    check_and_upgrade_database(app)
    
    # 创建管理员账号（如果不存在）
    admin = User.query.filter_by(username='admin').first()
    if admin is None:
        logger.info("创建默认管理员账号")
        admin = User(username='admin', 
                    password_hash=generate_password_hash('admin123'),
                    role='admin',
                    is_active=True)
        db.session.add(admin)
        db.session.commit()
        logger.info("管理员账号创建成功")

if __name__ == '__main__':
    # 获取运行配置
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    
    # 启动应用
    app.run(host="0.0.0.0", port=port, debug=debug)