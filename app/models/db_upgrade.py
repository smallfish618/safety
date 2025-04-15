from app import db
import sqlite3
import logging
import os

logger = logging.getLogger(__name__)

def check_and_upgrade_database(app):
    """检查已有数据库结构中是否缺少必要的列，只添加缺失的列而不创建新表"""
    logger.info("检查数据库结构...")
    
    # 获取数据库路径 - 使用固定路径
    db_path = 'E:/safety/data/database.db'
    
    # 确保数据库文件存在
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        logger.error("请确保数据库文件存在，本脚本不会创建新的数据库文件")
        return
    
    # 连接到数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查fire_equipment表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fire_equipment'")
        if not cursor.fetchone():
            logger.info("fire_equipment表不存在，正在创建...")
            # 创建表结构
            cursor.execute('''
                CREATE TABLE fire_equipment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    area_code INTEGER NOT NULL,
                    area_name VARCHAR(50),
                    installation_floor VARCHAR(50) NOT NULL,
                    installation_location VARCHAR(200) NOT NULL,
                    equipment_type VARCHAR(50) NOT NULL,
                    equipment_name VARCHAR(100) NOT NULL,
                    model VARCHAR(100) NOT NULL,
                    weight VARCHAR(30) NOT NULL,
                    quantity INTEGER,
                    production_date DATE,
                    service_life VARCHAR(30) NOT NULL,
                    expiration_date VARCHAR(50) NOT NULL,
                    remark TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            logger.info("成功创建fire_equipment表")
        
        # 检查user表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        if cursor.fetchone():
            # 检查user表中是否有is_active列
            cursor.execute("PRAGMA table_info(user)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'is_active' not in columns:
                logger.info("正在向user表添加is_active列...")
                cursor.execute("ALTER TABLE user ADD COLUMN is_active BOOLEAN DEFAULT 1")
                conn.commit()
                logger.info("成功添加is_active列")
                
            # 检查user表中是否有email列
            if 'email' not in columns:
                logger.info("正在向user表添加email列...")
                cursor.execute("ALTER TABLE user ADD COLUMN email VARCHAR(120)")
                conn.commit()
                logger.info("成功添加email列")
        
        # 检查permission表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='permission'")
        if cursor.fetchone():
            # 检查permission表中是否有area_name列
            cursor.execute("PRAGMA table_info(permission)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'area_name' not in columns:
                logger.info("正在向permission表添加area_name列...")
                cursor.execute("ALTER TABLE permission ADD COLUMN area_name VARCHAR(100)")
                conn.commit()
                logger.info("成功添加area_name列")
    except Exception as e:
        logger.error(f"检查数据库结构时出错: {str(e)}")
    finally:
        cursor.close()
        conn.close()
        
    logger.info("数据库结构检查完成")
