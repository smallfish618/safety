from flask import Flask, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect, generate_csrf, CSRFError, CSRFError  # 添加 CSRFError 导入
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config, ProductionConfig, DevelopmentConfig

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'info'
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(config_class)
    
    # 配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 确保WTF CSRF保护已启用，并添加调试信息
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_SECRET_KEY'] = app.config['SECRET_KEY']
    app.logger.info("CSRF保护已启用")
    
    # 注册扩展
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # 使用标准的 Flask 错误处理器代替 csrf.error_handler
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        app.logger.error(f"CSRF错误: {e.description}")
        return jsonify({"error": f"CSRF验证失败: {e.description}"}), 400
    
    @app.after_request
    def add_csrf_cookie(response):
        """确保CSRF令牌在cookie中也可用"""
        if 'text/html' in response.content_type:
            csrf_token = generate_csrf()
            response.set_cookie('csrf_token', csrf_token, httponly=False)
        return response
    
    @app.after_request
    def add_header(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        if 'text/html' in response.content_type:
            response.headers['Cache-Control'] = 'public, max-age=0'
        elif '.css' in request.path or '.js' in request.path:
            response.headers['Cache-Control'] = 'public, max-age=86400'
        return response
    
    # 添加缓存破坏函数
    @app.context_processor
    def inject_cache_buster():
        return {'cache_buster': datetime.now().timestamp()}

    # 添加CSRF令牌生成方法
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf)

    # 向Jinja2环境添加min函数
    @app.context_processor
    def inject_min():
        return dict(min=min)

    # 用户加载函数
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
        
    # 添加用户权限上下文处理器
    @app.context_processor
    def inject_user_permissions():
        from app.models.user import Permission
        import flask_login
        
        # 默认值
        user_permissions_by_type = {
            'micro_station': False,  # 微型消防站权限
            'fire_equipment': False  # 灭火器和呼吸器权限
        }
        
        # 仅处理已登录用户
        if flask_login.current_user.is_authenticated:
            # 管理员默认拥有所有权限
            if current_user.role == 'admin':
                user_permissions_by_type = {
                    'micro_station': True,
                    'fire_equipment': True
                }
            else:
                # 获取用户权限
                permissions = Permission.query.filter_by(user_id=current_user.id).all()
                
                # 检查是否有"微型消防站"权限
                for perm in permissions:
                    if perm.operation_type == '微型消防站' and perm.can_view:
                        user_permissions_by_type['micro_station'] = True
                        
                    if perm.operation_type == '灭火器和呼吸器' and perm.can_view:
                        user_permissions_by_type['fire_equipment'] = True
        
        return {'user_permissions_by_type': user_permissions_by_type}

    # 在 app.context_processor 中添加检查预警权限的函数
    @app.context_processor
    def inject_expiry_permissions():
        """注入用户是否有查看预警权限的变量"""
        from app.models.user import Permission  # 添加此导入语句
        
        can_view_expiry_alert = False
        
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                can_view_expiry_alert = True
            else:
                # 检查微型消防站权限
                station_permission = Permission.query.filter_by(
                    user_id=current_user.id,
                    operation_type='微型消防站',
                    can_view=True
                ).first()
                
                # 检查灭火器和呼吸器权限
                equipment_permission = Permission.query.filter_by(
                    user_id=current_user.id,
                    operation_type='灭火器和呼吸器',
                    can_view=True
                ).first()
                
                # 只要有任一权限，就可以查看预警
                can_view_expiry_alert = (station_permission is not None) or (equipment_permission is not None)
        
        return {'can_view_expiry_alert': can_view_expiry_alert}

    # 注册URL转换器
    try:
        from app.urls import register_converters
        register_converters(app)
    except ImportError:
        pass
        
    # 注册蓝图
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.routes.station import station_bp
    app.register_blueprint(station_bp, url_prefix='/station')
    
    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.routes.equipment import equipment_bp
    app.register_blueprint(equipment_bp, url_prefix='/equipment')
    
    # 注册分析蓝图
    from app.routes.analytics import analytics_bp
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    
    # 注册通用蓝图
    from app.routes.common import common_bp
    app.register_blueprint(common_bp, url_prefix='/common')
    
    # 注册错误处理器
    from app.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # 添加测试路由
    @app.route('/test')
    def test():
        return '测试页面 - 应用正常运行'
    
    # 修改根路由处理函数，添加无权限处理
    @app.route('/')
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # 检查用户是否有任何访问权限
        if current_user.role != 'admin':
            from app.models.user import Permission
            station_permission = Permission.query.filter_by(
                user_id=current_user.id,
                operation_type='微型消防站',
                can_view=True
            ).first()
            
            equipment_permission = Permission.query.filter_by(
                user_id=current_user.id,
                operation_type='灭火器和呼吸器',
                can_view=True
            ).first()
            
            # 如果用户没有任何权限，则显示无权限页面
            if not station_permission and not equipment_permission:
                return redirect(url_for('common.index_no_permission'))
        
        return redirect(url_for('station.index'))
    
    # index重定向
    @app.route('/index')
    def redirect_index():
        return redirect(url_for('index'))
    
    # 添加日志记录功能
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        
        # 确保日志目录存在
        if not os.path.exists('logs'):
            os.mkdir('logs')
            
        # 创建日志处理器
        file_handler = RotatingFileHandler('logs/safety.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        
        # 将处理器添加到应用
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('安全管理系统启动')
    
    # 使用配置类中的设置
    app.logger.info('======= 邮箱配置 =======')
    app.logger.info(f'MAIL_SERVER: {app.config.get("MAIL_SERVER")}')
    app.logger.info(f'MAIL_PORT: {app.config.get("MAIL_PORT")}')
    app.logger.info(f'MAIL_USE_TLS: {app.config.get("MAIL_USE_TLS")}')
    app.logger.info(f'MAIL_USE_SSL: {app.config.get("MAIL_USE_SSL")}')
    app.logger.info(f'MAIL_USERNAME: {app.config.get("MAIL_USERNAME")}')
    app.logger.info(f'MAIL_DEFAULT_SENDER: {app.config.get("MAIL_DEFAULT_SENDER")}')
    app.logger.info('=======================')
    
    return app

# 导入模型
from app.models import user, station