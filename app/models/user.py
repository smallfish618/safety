from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    """用户表"""
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin 或 user
    is_active = db.Column(db.Boolean, default=True)  # 账号是否启用
    email = db.Column(db.String(120))  # 添加邮箱字段

    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    # 重写is_active属性，确保即使数据库字段不存在也能工作
    @property
    def is_active_safe(self):
        """安全获取活动状态，即使数据库列不存在"""
        try:
            return self.is_active
        except:
            # 如果数据库列不存在，默认为活动状态
            return True
    
    def is_authenticated(self):
        """是否已认证（覆盖UserMixin的方法）"""
        return True
    
    def is_anonymous(self):
        """是否匿名用户（覆盖UserMixin的方法）"""
        return False
    
    def get_id(self):
        """获取用户ID（覆盖UserMixin的方法）"""
        return str(self.id)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Permission(db.Model):
    """权限表"""
    __tablename__ = 'permission'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    operation_type = db.Column(db.String(50), nullable=False)  # 操作类型：微型消防站、灭火器和呼吸器、应急灯具
    area_id = db.Column(db.String(50), nullable=False)  # 区域ID
    area_name = db.Column(db.String(100))  # 区域名称（冗余字段，方便显示）
    can_view = db.Column(db.Boolean, default=True)  # 是否可查看
    can_add = db.Column(db.Boolean, default=False)  # 是否可添加
    can_edit = db.Column(db.Boolean, default=False)  # 是否可编辑
    can_delete = db.Column(db.Boolean, default=False)  # 是否可删除

    def __repr__(self):
        return f'<Permission {self.user_id}-{self.operation_type}-{self.area_id}>'

class VerificationCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True)
    code = db.Column(db.String(6))
    created_at = db.Column(db.DateTime)