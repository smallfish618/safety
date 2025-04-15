import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Flask应用配置类"""
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # 数据库配置 - 修改为使用固定的绝对路径指向现有数据库
    SQLALCHEMY_DATABASE_URI = 'sqlite:///E:/safety/data/database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CSRF保护配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or SECRET_KEY
    WTF_CSRF_TIME_LIMIT = 3600  # CSRF令牌有效期为1小时
    
    # 安全配置
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # 在生产环境中设置为True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = False  # 在生产环境中设置为True
    
    # Session配置
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)  # 设置会话过期时间为12小时
    
    # 缓存配置
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # 邮件配置 - 直接硬编码
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.qq.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 465)
    MAIL_USE_SSL = True  # QQ邮箱一般使用SSL而非TLS
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() in ['true', 'yes', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or '18184887@qq.com'  # 请替换为实际使用的QQ邮箱
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'xvohbtalnuazcbdi'  # 请替换为邮箱授权码
    MAIL_DEFAULT_SENDER = ('消防安全管理系统', os.environ.get('MAIL_SENDER') or '18184887@qq.com')  # 发件人显示名称和邮箱

    # 每页显示的记录数
    ITEMS_PER_PAGE = 15

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    # 确保开发环境也使用相同的数据库文件
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///E:/safety/data/database.db'

class ProductionConfig(Config):
    """生产环境配置"""
    # 确保生产环境也使用相同的数据库文件
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///E:/safety/data/database.db'
    
    # 生产环境安全设置
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    # 测试环境可以使用单独的数据库文件
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///E:/safety/data/test-database.db'
    WTF_CSRF_ENABLED = False  # 测试环境关闭CSRF保护以方便测试

# 配置映射字典，便于通过字符串选择不同配置
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    
    'default': DevelopmentConfig
}
