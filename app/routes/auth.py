from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User, Permission
from app.utils.email import send_verification_email, verify_code
from werkzeug.urls import url_parse
from werkzeug.security import check_password_hash, generate_password_hash
from flask_wtf.csrf import ValidationError
from datetime import datetime
import traceback

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # 如果是GET请求，则渲染登录页面
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    # 如果是POST请求，处理登录逻辑
    try:
        # 获取表单数据
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        # 验证CSRF令牌
        csrf_token = request.form.get('csrf_token')
        if not csrf_token:
            flash('CSRF令牌缺失，请重新提交表单', 'danger')
            return render_template('auth/login.html')
        
        # 获取用户
        user = User.query.filter_by(username=username).first()
        
        # 检查用户是否存在及密码是否正确
        if not user or not user.check_password(password):  # 改用check_password方法
            flash('用户名或密码错误', 'danger')
            return render_template('auth/login.html')
        
        # 检查用户状态
        if not user.is_active:
            flash('您的账户已被禁用，请联系管理员', 'danger')
            return render_template('auth/login.html')
        
        # 登录用户
        login_user(user, remember=remember)
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # 重定向到首页或用户请求的页面
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('station.index')  # 默认重定向到站点首页
        
        return redirect(next_page)
        
    except ValidationError:
        flash('CSRF验证失败，请重新提交表单', 'danger')
        return render_template('auth/login.html')
    except Exception as e:
        print(f"登录错误: {str(e)}")
        traceback.print_exc()
        flash('登录过程中发生错误，请稍后重试', 'danger')
        return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('station.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        
        if User.query.filter_by(email=email).first():
            flash('该邮箱已被注册')
            return redirect(url_for('auth.register'))
            
        send_verification_email(email)
        flash('验证码已发送到您的邮箱')
        return redirect(url_for('auth.verify_email', email=email))
        
    return render_template('auth/register.html')

@auth_bp.route('/verify/<email>', methods=['GET', 'POST'])
def verify_email(email):
    if current_user.is_authenticated:
        return redirect(url_for('station.index'))
        
    if request.method == 'POST':
        code = request.form.get('code')
        
        if verify_code(email, code):
            return redirect(url_for('auth.complete_registration', email=email))
        else:
            flash('验证码无效或已过期')
            
    return render_template('auth/verify_email.html', email=email)

@auth_bp.route('/complete/<email>', methods=['GET', 'POST'])
def complete_registration(email):
    if current_user.is_authenticated:
        return redirect(url_for('station.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('auth.complete_registration', email=email))
            
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/complete_registration.html', email=email)

@auth_bp.route('/logout')
@login_required
def logout():
    """退出登录"""
    logout_user()
    flash('您已成功退出登录', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/my-account')
@login_required
def my_account():
    """用户个人中心页面"""
    # 获取用户所有权限
    permissions = Permission.query.filter_by(user_id=current_user.id).all()
    
    # 管理员显示特殊提示
    is_admin = current_user.role == 'admin'
    
    return render_template('auth/my_account.html', permissions=permissions, is_admin=is_admin)

@auth_bp.route('/update-email', methods=['POST'])
@login_required
def update_email():
    """更新用户邮箱"""
    try:
        email = request.form.get('email')
        
        # 简单验证邮箱格式
        if email and '@' not in email:
            flash('请输入有效的邮箱地址', 'danger')
            return redirect(url_for('auth.my_account', tab='update'))
        
        # 更新邮箱
        current_user.email = email
        db.session.commit()
        
        flash('邮箱更新成功', 'success')
        return redirect(url_for('auth.my_account'))
    except Exception as e:
        db.session.rollback()
        flash(f'更新邮箱失败: {str(e)}', 'danger')
        return redirect(url_for('auth.my_account', tab='update'))

@auth_bp.route('/update-password', methods=['POST'])
@login_required
def update_password():
    """更新用户密码"""
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证当前密码
        if not current_user.check_password(current_password):
            flash('当前密码不正确', 'danger')
            return redirect(url_for('auth.my_account', tab='update'))
        
        # 验证新密码
        if new_password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('auth.my_account', tab='update'))
        
        # 更新密码
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash('密码更新成功', 'success')
        return redirect(url_for('auth.my_account'))
    except Exception as e:
        db.session.rollback()
        flash(f'更新密码失败: {str(e)}', 'danger')
        return redirect(url_for('auth.my_account', tab='update'))

@auth_bp.route('/debug-permissions')
@login_required
def debug_permissions():
    """权限调试页面"""
    try:
        # 获取用户所有权限 - 确保不限制操作类型
        all_permissions = Permission.query.filter_by(user_id=current_user.id).all()
        
        # 添加调试信息
        print(f"调试页面 - 用户: {current_user.username}, ID: {current_user.id}")
        print(f"找到权限数量: {len(all_permissions)}")
        for p in all_permissions:
            print(f"权限 {p.id}: {p.operation_type}, 区域: {p.area_id}, 查看={p.can_view}, 添加={p.can_add}, 编辑={p.can_edit}, 删除={p.can_delete}")
        
        # 按操作类型分类权限
        permissions_by_type = {}
        for perm in all_permissions:
            if perm.operation_type not in permissions_by_type:
                permissions_by_type[perm.operation_type] = []
            permissions_by_type[perm.operation_type].append({
                'id': perm.id,
                'area_id': perm.area_id,
                'area_name': perm.area_name,
                'can_view': perm.can_view,
                'can_add': perm.can_add,
                'can_edit': perm.can_edit,
                'can_delete': perm.can_delete
            })
        
        # 获取消防器材区域
        from app.models.equipment import FireEquipment
        equipment_areas = db.session.query(FireEquipment.area_code, FireEquipment.area_name).distinct().all()
        equipment_areas = [{'id': str(area[0]), 'name': area[1]} for area in equipment_areas]
        
        return render_template(
            'auth/debug_permissions.html', 
            permissions_by_type=permissions_by_type,
            equipment_areas=equipment_areas,
            all_permissions=all_permissions  # 添加这个变量
        )
    except Exception as e:
        import traceback
        traceback.print_exc()  # 添加完整的错误跟踪
        flash(f'获取权限调试信息失败: {str(e)}', 'danger')
        return redirect(url_for('auth.my_account'))