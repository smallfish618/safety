from flask import Flask, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect, generate_csrf
import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

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
    
    # 确保WTF CSRF保护已启用
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_SECRET_KEY'] = app.config['SECRET_KEY']
    
    # 配置邮箱
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

    # 在create_app函数内修改会话配置
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)  # 延长会话时间

    # 注册扩展
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
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

    # 添加调度器
    print("\n开始初始化定时任务调度器...")
    from app.scheduler import scheduler, init_scheduler
    init_scheduler(app)

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
    
    # 注册通用蓝图
    from app.routes.common import common_bp
    app.register_blueprint(common_bp, url_prefix='/common')
    
    # 注册分析蓝图
    from app.routes.analytics import analytics_bp
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    
    # 在注册蓝图部分添加以下代码
    from app.routes.scheduler import scheduler_bp
    app.register_blueprint(scheduler_bp, url_prefix='/scheduler')
    
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
    
    return app

# 导入模型
from app.models import user, station