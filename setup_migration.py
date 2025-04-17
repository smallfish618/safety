"""
安装并设置Flask-Migrate数据库迁移扩展，并创建scheduler_configs表

这个脚本将：
1. 安装必要的依赖
2. 初始化数据库迁移环境
3. 创建包含scheduler_configs表的模型
4. 生成并应用迁移脚本
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

def install_dependencies():
    """安装必要的依赖"""
    print("正在安装必要的依赖...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask-migrate"])
        print("✅ Flask-Migrate 安装成功")
        return True
    except Exception as e:
        print(f"❌ 安装依赖时出错: {str(e)}")
        return False

def check_migration_setup():
    """检查应用中是否已经设置了Flask-Migrate"""
    init_file = Path("app/__init__.py")
    if not init_file.exists():
        print(f"❌ 找不到应用初始化文件: {init_file}")
        return False
    
    with open(init_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "flask_migrate" not in content:
        print("❓ 应用中似乎没有初始化Flask-Migrate，需要更新__init__.py文件")
        return False
    
    print("✅ 应用中已配置Flask-Migrate")
    return True

def update_app_init():
    """更新应用的__init__.py文件以添加Flask-Migrate支持"""
    init_file = Path("app/__init__.py")
    if not init_file.exists():
        print(f"❌ 找不到应用初始化文件: {init_file}")
        return False
    
    with open(init_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 检查是否已存在Flask-Migrate导入
    if "flask_migrate" not in content:
        # 添加导入语句
        import_line = "from flask_migrate import Migrate\n"
        if "from flask import Flask" in content:
            content = content.replace("from flask import Flask", "from flask import Flask\n" + import_line)
        else:
            content = import_line + content
        
        # 添加Migrate初始化
        migrate_init = "\n# 初始化数据库迁移扩展\nmigrate = Migrate(app, db)\n"
        if "db.init_app(app)" in content:
            content = content.replace("db.init_app(app)", "db.init_app(app)" + migrate_init)
        else:
            # 如果找不到db.init_app，则在文件末尾添加
            content += migrate_init
        
        # 保存更新后的文件
        with open(init_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        print("✅ 已更新应用初始化文件，添加了Flask-Migrate支持")
        return True
    else:
        print("✅ 应用初始化文件中已有Flask-Migrate支持")
        return True

def create_scheduler_model():
    """确保scheduler_configs模型已定义"""
    model_file = Path("app/models/scheduler_config.py")
    
    if not model_file.exists():
        print("📁 正在创建scheduler_config模型文件...")
        
        # 确保目录存在
        model_file.parent.mkdir(exist_ok=True)
        
        # 编写模型文件内容
        model_content = """# filepath: /e:/safety/app/models/scheduler_config.py
from app import db
from datetime import datetime

class SchedulerConfig(db.Model):
    \"\"\"定时任务配置表\"\"\"
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
"""
        with open(model_file, "w", encoding="utf-8") as f:
            f.write(model_content)
        
        print(f"✅ 已创建scheduler_config模型文件: {model_file}")
        
        # 更新models/__init__.py文件以导入新模型
        init_file = Path("app/models/__init__.py")
        if init_file.exists():
            with open(init_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 添加导入语句
            if "scheduler_config" not in content:
                if "# 此处可能有其他导入语句" in content:
                    content = content.replace("# 此处可能有其他导入语句", "from app.models.scheduler_config import SchedulerConfig\n# 此处可能有其他导入语句")
                else:
                    content += "\nfrom app.models.scheduler_config import SchedulerConfig\n"
                
                with open(init_file, "w", encoding="utf-8") as f:
                    f.write(content)
                print("✅ 已更新models/__init__.py，添加了SchedulerConfig导入")
        return True
    else:
        print(f"✅ scheduler_config模型文件已存在: {model_file}")
        return True

def initialize_migrations():
    """初始化数据库迁移环境"""
    print("\n正在初始化数据库迁移环境...")
    
    # 设置环境变量
    os.environ["FLASK_APP"] = "run.py"
    
    try:
        # 初始化迁移环境
        subprocess.check_call([sys.executable, "-m", "flask", "db", "init"])
        print("✅ 数据库迁移环境初始化成功")
        return True
    except subprocess.CalledProcessError as e:
        if "Directory migrations already exists" in str(e.output):
            print("✅ 数据库迁移环境已存在")
            return True
        print(f"❌ 初始化数据库迁移环境时出错: {str(e)}")
        return False

def create_and_apply_migration():
    """创建并应用数据库迁移"""
    print("\n正在创建数据库迁移...")
    os.environ["FLASK_APP"] = "run.py"
    
    # 确保data目录存在
    data_dir = Path("data")
    if not data_dir.exists():
        data_dir.mkdir()
        print(f"📁 创建了data目录: {data_dir}")
    
    try:
        # 创建迁移
        subprocess.check_call([
            sys.executable, 
            "-m", "flask", "db", "migrate", 
            "-m", f"添加scheduler_configs表"
        ])
        print("✅ 数据库迁移创建成功")
        
        # 应用迁移
        subprocess.check_call([sys.executable, "-m", "flask", "db", "upgrade"])
        print("✅ 数据库迁移应用成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 创建或应用数据库迁移时出错: {str(e)}")
        return False

def create_direct_table():
    """如果迁移失败，直接创建表"""
    print("\n尝试直接创建scheduler_configs表...")
    
    try:
        # 动态导入应用和数据库模型
        from app import db
        from app.models.scheduler_config import SchedulerConfig
        
        # 创建表
        with db.app.app_context():
            if not db.engine.dialect.has_table(db.engine, 'scheduler_configs'):
                db.create_all(tables=[SchedulerConfig.__table__])
                print("✅ 直接创建scheduler_configs表成功")
                return True
            else:
                print("✅ scheduler_configs表已存在")
                return True
    except Exception as e:
        print(f"❌ 直接创建表时出错: {str(e)}")
        return False

def main():
    """主函数"""
    print("=== 数据库迁移设置与初始化 ===")
    
    if not install_dependencies():
        print("❌ 无法安装必要的依赖，程序终止")
        return
    
    if not check_migration_setup():
        if not update_app_init():
            print("❌ 无法更新应用初始化文件，程序终止")
            return
    
    if not create_scheduler_model():
        print("❌ 无法创建scheduler_config模型，程序终止")
        return
    
    if not initialize_migrations():
        print("⚠️ 无法初始化数据库迁移环境，尝试直接创建表")
        if not create_direct_table():
            print("❌ 所有方法都失败，请手动解决数据库问题")
            return
    else:
        if not create_and_apply_migration():
            print("⚠️ 无法创建或应用迁移，尝试直接创建表")
            if not create_direct_table():
                print("❌ 所有方法都失败，请手动解决数据库问题")
                return
    
    print("\n🎉 数据库设置完成！定时任务功能应该可以正常工作了")
    print("现在可以重新启动应用: python run.py")

if __name__ == "__main__":
    main()
