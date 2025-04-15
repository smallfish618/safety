import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.equipment import FireEquipment

def create_tables():
    """创建数据库表"""
    app = create_app()
    with app.app_context():
        print("正在检查并创建消防器材表...")
        # 检查表是否存在
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/database.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fire_equipment'")
        if not cursor.fetchone():
            print("消防器材表不存在，正在创建...")
            # 创建表
            db.create_all()
            print("消防器材表创建成功!")
        else:
            print("消防器材表已存在，无需创建")
        
        conn.close()

if __name__ == "__main__":
    create_tables()
