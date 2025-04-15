from flask import Blueprint, render_template, request, session, redirect, url_for
from flask_login import login_required, current_user

common_bp = Blueprint('common', __name__)

# 增强无权限页面功能

@common_bp.route('/no-permission/<module>')
@login_required
def no_permission(module):
    """显示无权限提示页面，带有更详细的权限情况说明"""
    # 记录用户尝试访问的模块
    session['attempted_module'] = module
    
    # 检查用户的角色和权限
    is_admin = current_user.role == 'admin'
    
    # 获取用户各模块的权限情况用于显示
    from app.models.user import Permission
    
    # 微型站权限
    station_permissions = Permission.query.filter_by(
        user_id=current_user.id,
        operation_type='微型消防站'
    ).all()
    
    # 消防器材权限
    equipment_permissions = Permission.query.filter_by(
        user_id=current_user.id,
        operation_type='灭火器和呼吸器'
    ).all()
    
    # 根据不同的模块提供不同的指导建议
    suggestion = ""
    if module == '微型消防站物资表':
        suggestion = "请联系管理员为您添加'微型消防站'相关区域的查看权限。"
    elif module == '消防器材管理':
        suggestion = "请联系管理员为您添加'灭火器和呼吸器'相关区域的查看权限。"
    elif module == '有效期预警':
        suggestion = "要查看预警信息，您需要拥有'微型消防站'或'灭火器和呼吸器'的区域查看权限。"
    else:
        suggestion = "请联系管理员为您添加相应的权限。"
    
    # 为index页面添加特殊处理
    is_index = (module == 'index')
    
    # 返回提示页面
    return render_template(
        'common/no_permission.html',
        module=module,
        username=current_user.username,
        is_admin=is_admin,
        is_index=is_index,
        suggestion=suggestion,
        station_count=len(station_permissions),
        equipment_count=len(equipment_permissions)
    )

@common_bp.route('/index-no-permission')
@login_required
def index_no_permission():
    """首页无权限提示 - 这是新增的路由"""
    # 计算用户拥有的权限数量
    from app.models.user import Permission
    
    station_permissions = Permission.query.filter_by(
        user_id=current_user.id,
        operation_type='微型消防站',
        can_view=True
    ).count()
    
    equipment_permissions = Permission.query.filter_by(
        user_id=current_user.id,
        operation_type='灭火器和呼吸器',
        can_view=True
    ).count()
    
    return render_template(
        'common/index_no_permission.html',
        username=current_user.username,
        station_permissions=station_permissions,
        equipment_permissions=equipment_permissions
    )
