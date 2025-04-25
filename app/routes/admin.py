from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.models.station import FireStation, EquipmentExpiry, ResponsiblePerson  # 移除 Equipment 导入
from app.models.user import User, Permission
from app.forms.equipment import EquipmentForm
from app.forms.expiry import ExpiryRuleForm  # 导入新表单
import traceback
from datetime import datetime, timedelta  # 添加 timedelta 导入


admin_bp = Blueprint('admin', __name__)

# 检查是否是管理员的装饰器
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('您没有访问此页面的权限')
            return redirect(url_for('station.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """用户管理页面"""
    try:
        users = User.query.all()
        return render_template('admin/users.html', users=users)
    except Exception as e:
        import traceback
        traceback.print_exc()  # 打印完整堆栈到控制台
        flash(f'加载用户数据出错: {str(e)}', 'danger')
        return redirect(url_for('index'))

# 修改expiry视图函数以确保筛选条件正确处理

@admin_bp.route('/expiry')
@login_required
@admin_required
def expiry():
    """有效期管理页面"""
    try:
        # 将查询和模板渲染放在try块中，以便捕获任何错误
        page = request.args.get('page', 1, type=int)
        per_page = 15  # 每页显示15条记录
        
        # 获取搜索和筛选参数
        search = request.args.get('search', '')
        filter_category = request.args.get('filter_category', '')
        filter_item = request.args.get('filter_item', '')
        
        # 基础查询
        query = EquipmentExpiry.query
        
        # 应用筛选条件
        if filter_category:
            query = query.filter(EquipmentExpiry.item_category == filter_category)
            print(f"应用类别筛选: {filter_category}")
        
        if filter_item:
            query = query.filter(EquipmentExpiry.item_name == filter_item)
            print(f"应用物品名称筛选: {filter_item}")
        
        # 应用搜索条件
        if search:
            search_term = f"%{search}%"
            query = query.filter(or_(
                EquipmentExpiry.item_category.ilike(search_term),
                EquipmentExpiry.item_name.ilike(search_term),
                EquipmentExpiry.description.ilike(search_term) if EquipmentExpiry.description is not None else False
            ))
            print(f"应用搜索条件: {search}")
        
        # 获取唯一值列表用于筛选下拉菜单
        category_list = db.session.query(EquipmentExpiry.item_category).distinct().order_by(EquipmentExpiry.item_category).all()
        category_list = [cat[0] for cat in category_list if cat[0]]
        
        item_list = db.session.query(EquipmentExpiry.item_name).distinct().order_by(EquipmentExpiry.item_name).all()
        item_list = [item[0] for item in item_list if item[0]]
        
        # 获取总记录数
        total_count = query.count()
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        expiry_items = pagination.items
        
        # 创建表单对象
        form = ExpiryRuleForm()
        
        # 明确传递筛选参数以确保模板能够访问
        return render_template(
            'admin/expiry.html', 
            expiry_items=expiry_items, 
            pagination=pagination,
            category_list=category_list,
            item_list=item_list,
            total_count=total_count,
            form=form,
            filter_category=filter_category,
            filter_item=filter_item
        )
    except Exception as e:
        print(f"发生错误: {str(e)}")
        traceback.print_exc()
        flash(f'发生错误: {str(e)}')
        return render_template('admin/expiry.html', expiry_items=[], error=str(e))

@admin_bp.route('/responsible')
@login_required
@admin_required
def responsible():
    """负责人管理页面"""
    try:
        print("开始处理物资负责人信息请求")
        page = request.args.get('page', 1, type=int)
        per_page = 15
        
        # 直接获取所有数据进行调试
        all_data = ResponsiblePerson.query.all()
        print(f"数据库中总共有 {len(all_data)} 条负责人记录")
        
        # 获取搜索和筛选参数
        search = request.args.get('search', '')
        filter_area = request.args.get('filter_area', '')
        
        # 专门标记是否有高级筛选 (与 station.index 保持一致)
        has_advanced_filters = bool(filter_area)
        
        # 基础查询
        query = ResponsiblePerson.query
        
        # 应用筛选条件
        if filter_area:
            query = query.filter(ResponsiblePerson.area_name == filter_area)
            print(f"应用区域筛选: {filter_area}")
        
        # 应用搜索条件
        if search:
            search_term = f"%{search}%"
            query = query.filter(or_(
                ResponsiblePerson.person_name.ilike(search_term),
                ResponsiblePerson.contact.ilike(search_term),
                ResponsiblePerson.area_name.ilike(search_term),
                ResponsiblePerson.email.ilike(search_term)
            ))
            print(f"应用搜索条件: {search}")
        
        # 获取唯一值列表用于筛选
        area_list = [area[0] for area in db.session.query(ResponsiblePerson.area_name).distinct().all() if area[0]]
        print(f"可选区域列表: {area_list}")
        
        # 获取总记录数和分页筛选
        total_count = query.count()
        print(f"筛选后的记录总数: {total_count}")
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        responsible_persons = pagination.items
        print(f"当前页面记录数: {len(responsible_persons)}")
        
        return render_template(
            'admin/responsible.html', 
            responsible_persons=responsible_persons, 
            pagination=pagination,
            area_list=area_list,
            total_count=total_count,
            current_search=search,
            current_area=filter_area,
            has_advanced_filters=has_advanced_filters  # 传递筛选标志
        )
    except Exception as e:
        import traceback
        print(f"物资负责人信息页面出错: {str(e)}")
        print(traceback.format_exc())
        flash(f'获取负责人数据时出错: {str(e)}')
        return render_template('admin/responsible.html', responsible_persons=[], error=str(e))

@admin_bp.route('/equipment/add', methods=['POST'])
@login_required
@admin_required
def add_equipment():
    """添加物资信息"""
    form = EquipmentForm()
    if form.validate_on_submit():
        try:
            equipment = FireStation(
                area_code=form.area_code.data,
                area_name=form.area_name.data,
                item_name=form.name.data,
                model=form.model.data,
                quantity=form.quantity.data,
                remark=form.description.data,
                manufacturer=form.manufacturer.data
            )
            db.session.add(equipment)
            db.session.commit()
            flash('物资信息添加成功', 'success')
            return redirect(url_for('admin.equipment'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加失败: {str(e)}', 'error')
            return redirect(url_for('admin.equipment'))
    # 如果表单验证失败,返回错误信息
    for field, errors in form.errors.items():
        flash(f'{getattr(form, field).label.text}: {", ".join(errors)}', 'error')
    return redirect(url_for('admin.equipment'))
    
@admin_bp.route('/equipment')
@login_required
@admin_required
def equipment():
    try:
        # 获取搜索和筛选参数
        search = request.args.get('search', '')
        filter_item = request.args.get('filter_item', '')
        
        # 基础查询
        query = FireStation.query
        
        # 应用筛选条件
        if search:
            search_term = f"%{search}%"
            query = query.filter(or_(
                FireStation.item_name.ilike(search_term),
                FireStation.model.ilike(search_term),
                FireStation.manufacturer.ilike(search_term),
                FireStation.remark.ilike(search_term)
            ))
        
        if filter_item:
            query = query.filter(FireStation.item_name.ilike(f"%{filter_item}%"))
        
        # 获取记录数和分页
        page = request.args.get('page', 1, type=int)
        per_page = 15
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        equipments = pagination.items
        
        return render_template(
            'admin/equipment.html',
            equipments=equipments,
            pagination=pagination,
            total_count=query.count(),
            form=EquipmentForm()
        )
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
        flash(f'获取设备数据时出错: {str(e)}')
        return render_template('admin/equipment.html', equipments=[], error=str(e))

@admin_bp.route('/add_expiry_rule', methods=['POST'])
@login_required
@admin_required
def add_expiry_rule():
    """添加设备有效期规则"""
    form = ExpiryRuleForm()
    if form.validate_on_submit():
        try:
            # 创建新的有效期规则
            expiry_rule = EquipmentExpiry(
                item_category=form.item_category.data,
                item_name=form.item_name.data,
                normal_expiry=form.normal_expiry.data,
                mandatory_expiry=form.mandatory_expiry.data if form.mandatory_expiry.data else form.normal_expiry.data,
                description=form.description.data
            )
            # 保存到数据库
            db.session.add(expiry_rule)
            db.session.commit()
            flash('有效期规则添加成功', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'添加有效期规则失败: {str(e)}', 'danger')
            print(f"Error adding expiry rule: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        # 表单验证失败，显示错误信息
        for field, errors in form.errors.items():
            flash(f'{getattr(form, field).label.text}: {", ".join(errors)}', 'danger')
    return redirect(url_for('admin.expiry'))

@admin_bp.route('/edit_expiry_rule/<int:rule_id>', methods=['POST'])
@login_required
@admin_required
def edit_expiry_rule(rule_id):
    """编辑设备有效期规则"""
    # 创建表单实例并接收用户提交的数据
    form = ExpiryRuleForm()
    try:
        # 使用validate_on_submit方法包含CSRF验证
        if form.validate_on_submit():
            # 查找要编辑的规则
            expiry_rule = EquipmentExpiry.query.get_or_404(rule_id)
            
            # 更新规则信息
            expiry_rule.item_category = form.item_category.data
            expiry_rule.item_name = form.item_name.data
            expiry_rule.normal_expiry = form.normal_expiry.data
            expiry_rule.mandatory_expiry = form.mandatory_expiry.data if form.mandatory_expiry.data else form.normal_expiry.data
            expiry_rule.description = form.description.data
            
            # 保存到数据库
            db.session.commit()
            flash(f'有效期规则【{expiry_rule.item_name}】更新成功', 'success')
            return redirect(url_for('admin.expiry'))
        else:
            # 打印详细错误信息，用于调试
            print(f"表单验证失败: {form.errors}")
            error_messages = []
            for field, errors in form.errors.items():
                field_name = getattr(form, field).label.text if hasattr(form, field) and hasattr(getattr(form, field), "label") else field
                error_messages.append(f'{field_name}: {", ".join(errors)}')
            flash(f'表单验证失败: {"; ".join(error_messages)}', 'danger')
    except Exception as e:
        db.session.rollback()
        print(f"编辑有效期规则时出错: {str(e)}")
        traceback.print_exc()
        flash(f'更新有效期规则失败: {str(e)}', 'danger')
    # 无论是否成功，都重定向回页面的路由
    return redirect(url_for('admin.expiry'))

# 修复语法错误，正确定义删除有效期规则的路由
@admin_bp.route('/delete_expiry_rule/<int:rule_id>', methods=['POST'])
@login_required
@admin_required
def delete_expiry_rule(rule_id):
    """删除设备有效期规则"""
    try:
        # 获取要删除的规则
        expiry_rule = EquipmentExpiry.query.get_or_404(rule_id)
        # 记录规则信息，用于显示
        rule_name = expiry_rule.item_name
        rule_category = expiry_rule.item_category
        # 从数据库删除
        db.session.delete(expiry_rule)
        db.session.commit()
        flash(f'成功删除有效期规则 [{rule_category} - {rule_name}]', 'success')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'删除有效期规则失败: {str(e)}', 'danger')
    return redirect(url_for('admin.expiry'))

# 添加负责人编辑路由
@admin_bp.route('/edit_responsible/<int:person_id>', methods=['POST'])
@login_required
@admin_required
def edit_responsible(person_id):
    """编辑负责人信息"""
    try:
        # 获取要编辑的负责人记录
        person = ResponsiblePerson.query.get_or_404(person_id)
        # 获取表单数据
        area_code = request.form.get('area_code')
        area_name = request.form.get('area_name')
        person_name = request.form.get('person_name')
        contact = request.form.get('contact')
        email = request.form.get('email')
        
        # 验证必填字段
        if not all([area_code, area_name, person_name, contact]):
            flash('必填字段不能为空', 'danger')
            return redirect(url_for('admin.responsible'))
        
        # 更新信息字段
        person.area_code = area_code
        person.area_name = area_name
        person.person_name = person_name
        person.contact = contact
        person.email = email
        
        # 保存到数据库
        db.session.commit()
        flash('负责人信息更新成功', 'success')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'更新负责人信息失败: {str(e)}', 'danger')
    return redirect(url_for('admin.responsible'))

# 添加负责人管理的删除和添加路由函数
@admin_bp.route('/add_responsible', methods=['POST'])
@login_required
@admin_required
def add_responsible():
    """添加负责人信息"""
    try:
        # 获取表单数据
        area_code = request.form.get('area_code', type=int)
        area_name = request.form.get('area_name')
        person_name = request.form.get('person_name')
        contact = request.form.get('contact')
        email = request.form.get('email')
        
        # 验证区域编码
        if not area_code or area_code < 1 or area_code > 100:
            flash('区域编码必须是1-100之间的整数', 'danger')
            return redirect(url_for('admin.responsible'))
            
        # 检查区域编码是否已存在
        existing_area = ResponsiblePerson.query.filter_by(area_code=area_code).first()
        if existing_area:
            flash(f'区域编码 {area_code} 已有负责人，不能重复添加', 'danger')
            return redirect(url_for('admin.responsible'))
        
        # 验证必填字段
        if not all([area_code, area_name, person_name, contact]):
            flash('必填字段不能为空', 'danger')
            return redirect(url_for('admin.responsible'))
        
        # 创建新的负责人记录
        person = ResponsiblePerson(
            area_code=area_code,
            area_name=area_name,
            person_name=person_name,
            contact=contact,
            email=email
        )
        
        # 保存到数据库
        db.session.add(person)
        db.session.commit()
        flash('负责人添加成功', 'success')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'添加负责人失败: {str(e)}', 'danger')
    return redirect(url_for('admin.responsible'))

@admin_bp.route('/delete_responsible/<int:person_id>', methods=['POST'])
@login_required
@admin_required
def delete_responsible(person_id):
    """删除负责人信息"""
    try:
        # 获取要删除的负责人
        person = ResponsiblePerson.query.get_or_404(person_id)
        # 从数据库中删除
        db.session.delete(person)
        db.session.commit()
        flash(f'负责人 {person.person_name} 已成功删除', 'success')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'删除负责人失败: {str(e)}', 'danger')
    return redirect(url_for('admin.responsible'))

# 添加用户管理相关路由
@admin_bp.route('/add_user', methods=['POST'])
@login_required
@admin_required
def add_user():
    """添加新用户"""
    try:
        # 获取表单数据
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'user')  # 默认为普通用户
        email = request.form.get('email', '')
        
        # 验证必填字段
        if not all([username, password]):
            flash('用户名和密码不能为空', 'danger')
            return redirect(url_for('admin.users'))
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return redirect(url_for('admin.users'))
        
        # 创建新用户
        new_user = User(username=username, role=role, email=email)
        new_user.set_password(password)
        
        # 保存到数据库
        db.session.add(new_user)
        db.session.commit()
        flash('用户创建成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'创建用户时出错: {str(e)}', 'danger')
        traceback.print_exc()
        
    return redirect(url_for('admin.users'))

@admin_bp.route('/toggle_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    """启用/禁用用户"""
    try:
        # 记录接收到的请求
        print(f"收到切换用户状态请求，用户ID: {user_id}")
        
        user = User.query.get_or_404(user_id)
        
        # 防止管理员禁用自己
        if user.id == current_user.id:
            flash('您不能禁用自己的账户', 'danger')
            return redirect(url_for('admin.users'))
        
        # 切换用户状态
        user.is_active = not user.is_active
        db.session.commit()
        status = "启用" if user.is_active else "禁用"
        flash(f'用户 {user.username} 已被{status}', 'success')
    except Exception as e:
        db.session.rollback()
        # 添加更详细的错误记录
        import traceback
        traceback.print_exc()
        print(f"切换用户状态时发生错误：{str(e)}")
        flash(f'操作用户时出错: {str(e)}', 'danger')
    return redirect(url_for('admin.users'))

@admin_bp.route('/edit_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    """编辑用户信息"""
    try:
        user = User.query.get_or_404(user_id)
        
        # 获取表单数据
        role = request.form.get('role')
        email = request.form.get('email', '')
        new_password = request.form.get('password', '').strip()
        
        # 更新角色和邮箱
        user.role = role
        user.email = email
        
        # 如果提供了新密码，则更新密码
        if new_password:
            user.set_password(new_password)
        
        db.session.commit()
        flash(f'用户 {user.username} 信息更新成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'更新用户信息时出错: {str(e)}', 'danger')
    return redirect(url_for('admin.users'))

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """删除用户"""
    try:
        user = User.query.get_or_404(user_id)
        
        # 防止管理员删除自己
        if user.id == current_user.id:
            flash('您不能删除自己的账户', 'danger')
            return redirect(url_for('admin.users'))
        
        # 记录用户名以在删除后显示
        username = user.username
        
        # 删除用户
        db.session.delete(user)
        db.session.commit()
        flash(f'用户 {username} 已成功删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除用户时出错: {str(e)}', 'danger')
    return redirect(url_for('admin.users'))

# 添加权限管理相关的路由
@admin_bp.route('/add_permission', methods=['POST'])
@login_required
@admin_required
def add_permission():
    """添加用户权限"""
    try:
        # 获取表单数据
        user_id = request.form.get('user_id', type=int)
        operation_type = request.form.get('operation_type')
        area_id = request.form.get('area_id')
        area_name = request.form.get('area_name')
        can_view = 'can_view' in request.form
        can_add = 'can_add' in request.form
        can_edit = 'can_edit' in request.form
        can_delete = 'can_delete' in request.form
        
        # 验证必填字段
        if not all([user_id, operation_type, area_id]):
            flash('用户ID、操作类型和区域ID不能为空', 'danger')
            return redirect(url_for('admin.users'))
        
        # 强制应用"如果有新增、编辑或删除权限，则必须有查看权限"的规则
        if can_add or can_edit or can_delete:
            can_view = True
            print(f"自动启用查看权限，因为用户拥有其他权限: 新增={can_add}, 编辑={can_edit}, 删除={can_delete}")
        
        # 检查是否已存在该用户对该区域的权限
        existing_permission = Permission.query.filter_by(
            user_id=user_id,
            operation_type=operation_type,
            area_id=area_id
        ).first()
        
        if existing_permission:
            # 更新现有权限
            existing_permission.area_name = area_name
            existing_permission.can_view = can_view  # 应用更新后的查看权限
            existing_permission.can_add = can_add
            existing_permission.can_edit = can_edit
            existing_permission.can_delete = can_delete
            db.session.commit()
            flash('用户权限已更新', 'success')
        else:
            # 创建新权限
            new_permission = Permission(
                user_id=user_id,
                operation_type=operation_type,
                area_id=area_id,
                area_name=area_name,
                can_view=can_view,  # 应用更新后的查看权限
                can_add=can_add,
                can_edit=can_edit,
                can_delete=can_delete
            )
            db.session.add(new_permission)
            db.session.commit()
            flash('用户权限已添加', 'success')
            
        return redirect(url_for('admin.users'))
    except Exception as e:
        db.session.rollback()
        flash(f'添加权限时出错: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('admin.users'))

@admin_bp.route('/delete_permission/<int:permission_id>', methods=['POST'])
@login_required
@admin_required
def delete_permission(permission_id):
    """删除用户权限"""
    try:
        permission = Permission.query.get_or_404(permission_id)
        
        # 删除权限
        db.session.delete(permission)
        db.session.commit()
        flash('权限已成功删除', 'success')
        return redirect(url_for('admin.users'))
    except Exception as e:
        db.session.rollback()
        flash(f'删除权限时出错: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('admin.users'))

@admin_bp.route('/get_areas/<operation_type>')
@login_required
@admin_required
def get_areas(operation_type):
    """根据操作类型获取区域列表"""
    try:
        areas = []
        if operation_type == '微型消防站':
            # 从ResponsiblePerson获取区域列表
            areas_data = db.session.query(ResponsiblePerson.area_code, ResponsiblePerson.area_name).distinct().all()
            areas = [{'id': area[0], 'name': area[1]} for area in areas_data]
        elif operation_type == '灭火器和呼吸器':
            # 从FireEquipment获取区域列表
            from app.models.equipment import FireEquipment
            areas_data = db.session.query(FireEquipment.area_code, FireEquipment.area_name).distinct().all()
            areas = [{'id': str(area[0]), 'name': area[1]} for area in areas_data]
        elif operation_type == '应急灯具':
            # 应急灯具暂时不可用，返回空列表
            areas = []
        
        # 是否可用的标记
        available = operation_type != '应急灯具'
        
        return jsonify({
            'success': True, 
            'areas': areas,
            'available': available,
            'message': None if available else '应急灯具模块暂未开放，敬请期待'
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
        
# 确保reset_password路由接收参数的方式正确
@admin_bp.route('/reset_password', methods=['POST'])
@login_required
@admin_required
def reset_password():
    """重置用户密码"""
    try:
        # 通过表单获取user_id，而不是URL参数
        user_id = request.form.get('user_id', type=int)
        new_password = request.form.get('new_password')
        
        # 验证必填字段
        if not all([user_id, new_password]):
            flash('用户ID和新密码不能为空', 'danger')
            return redirect(url_for('admin.users'))
        
        # 获取用户对象
        user = User.query.get_or_404(user_id)
        
        # 更新密码
        user.set_password(new_password)
        db.session.commit()
        
        flash(f'用户 {user.username} 的密码已成功重置', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'重置密码时出错: {str(e)}', 'danger')
        traceback.print_exc()
    
    return redirect(url_for('admin.users'))

# 添加用户权限API端点
@admin_bp.route('/api/users/<int:user_id>/permissions')
@login_required
@admin_required
def get_user_permissions(user_id):
    """获取用户的权限列表 - API端点"""
    try:
        # 查找用户
        user = User.query.get_or_404(user_id)
        
        # 获取该用户的所有权限
        permissions = Permission.query.filter_by(user_id=user_id).all()
        
        # 将权限对象转换为字典列表
        permissions_data = []
        for perm in permissions:
            permissions_data.append({
                'id': perm.id,
                'operation_type': perm.operation_type,
                'area_id': perm.area_id,
                'area_name': perm.area_name or '未命名区域',
                'can_view': perm.can_view,
                'can_add': perm.can_add,
                'can_edit': perm.can_edit,
                'can_delete': perm.can_delete
            })
        
        # 返回JSON响应
        return jsonify({
            'success': True,
            'permissions': permissions_data
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 添加编辑权限路由
@admin_bp.route('/edit_permission/<int:permission_id>', methods=['POST'])
@login_required
@admin_required
def edit_permission(permission_id):
    """编辑用户权限"""
    try:
        # 获取要编辑的权限
        permission = Permission.query.get_or_404(permission_id)
        user_id = permission.user_id  # 保存用户ID用于重定向后显示正确的用户
        
        # 调试信息 - 输出收到的表单数据
        print(f"编辑权限 ID {permission_id} 的表单数据:")
        for key, value in request.form.items():
            print(f"{key}: {value}")
            
        # 获取表单数据
        operation_type = request.form.get('operation_type')
        area_id = request.form.get('area_id')
        area_name = request.form.get('area_name')
        can_view = 'can_view' in request.form
        can_add = 'can_add' in request.form
        can_edit = 'can_edit' in request.form
        can_delete = 'can_delete' in request.form
        
        # 修正这一行 - 将中文的"或"改为英文的"or"
        if not operation_type or not area_id or not area_name:
            # 如果前端未传递这些值，则保留原始值
            if not operation_type:
                operation_type = permission.operation_type
                print(f"使用原始操作类型: {operation_type}")
            if not area_id:
                area_id = permission.area_id
                print(f"使用原始区域ID: {area_id}")
            if not area_name:
                area_name = permission.area_name
                print(f"使用原始区域名称: {area_name}")
        
        # 强制应用"如果有新增、编辑或删除权限，则必须有查看权限"的规则
        if can_add or can_edit or can_delete:
            can_view = True
            print(f"自动启用查看权限，因为用户拥有其他权限: 新增={can_add}, 编辑={can_edit}, 删除={can_delete}")
        
        # 更新权限
        permission.operation_type = operation_type
        permission.area_id = area_id
        permission.area_name = area_name
        permission.can_view = can_view
        permission.can_add = can_add
        permission.can_edit = can_edit
        permission.can_delete = can_delete
        
        # 打印更新后的字段值
        print(f"更新后的权限字段: 操作类型={permission.operation_type}, 区域ID={permission.area_id}, 区域名称={permission.area_name}")
        
        db.session.commit()
        flash('权限更新成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'更新权限时出错: {str(e)}', 'danger')
        traceback.print_exc()
    
    # 添加查询参数user_id以便页面加载后可以聚焦到该用户
    return redirect(url_for('admin.users', user_id=user_id if 'user_id' in locals() else None))

@admin_bp.route('/check_area_code')
@login_required
@admin_required
def check_area_code():
    """检查区域编码是否已存在"""
    try:
        area_code = request.args.get('area_code', type=int)
        
        # 验证区域编码 - 修复语法错误："或" -> "or"
        if not area_code or area_code < 1 or area_code > 100:
            return jsonify({'exists': False, 'error': '区域编码无效'})
        
        # 检查数据库中是否存在该区域编码
        exists = ResponsiblePerson.query.filter_by(area_code=area_code).first() is not None
        
        return jsonify({'exists': exists})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'exists': False, 'error': str(e)})

# 在文件中添加新的路由函数

@admin_bp.route('/expiry_alert')
@login_required
def expiry_alert():
    """有效期预警页面 - 综合扫描微型站物资表和消防器材表"""
    try:
        # 权限检查 - 判断用户是否有任何区域权限
        has_permission = False
        allowed_areas = {'微型消防站': [], '灭火器和呼吸器': []}
        
        if current_user.role == 'admin':
            has_permission = True  # 管理员有全部权限
        else:
            # 获取用户对应两个操作类型的权限
            station_permissions = Permission.query.filter_by(
                user_id=current_user.id,
                operation_type='微型消防站',
                can_view=True
            ).all()
            
            equipment_permissions = Permission.query.filter_by(
                user_id=current_user.id,
                operation_type='灭火器和呼吸器',
                can_view=True
            ).all()
            
            # 收集用户有权限的区域
            for perm in station_permissions:
                allowed_areas['微型消防站'].append(perm.area_id)
                has_permission = True
                
            for perm in equipment_permissions:
                allowed_areas['灭火器和呼吸器'].append(perm.area_id)
                has_permission = True
        
        # 如果没有任何权限，提示用户并重定向
        if not has_permission:
            flash('您没有查看有效期预警的权限。请联系管理员获取相应权限。', 'danger')
            return redirect(url_for('common.no_permission', module='有效期预警'))
        
        # 获取当前日期
        from datetime import datetime, timedelta
        current_date = datetime.now().date()
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = 15  # 每页显示15条记录
        filter_type = request.args.get('filter_type', 'all')  # 新增: 过滤类型参数
        
        # 获取筛选条件参数
        filter_source = request.args.get('filter_source', '')  # 新增: 来源类型筛选
        filter_level = request.args.get('filter_level', '')
        filter_name = request.args.get('filter_name', '')
        filter_responsible = request.args.get('filter_responsible', '')
        
        # 检查是否应用了任何筛选
        has_filters = bool(filter_source or filter_level or filter_name or filter_responsible)
        
        # 修改：将预警天数扩展到90天
        warning_days = 90  # 预警天数从30天改为90天
        
        # 初始化预警物品列表 - 修复：在使用前初始化
        expiring_items = []
        
        # 1. 从有效期规则表中获取所有规则
        # ...现有代码...
        expiry_rules = EquipmentExpiry.query.all()
        expiry_rule_dict = {}
        
        # 输出所有规则的详细信息，帮助诊断问题
        print(f"加载有效期规则总数: {len(expiry_rules)}")
        for rule in expiry_rules:
            print(f"规则: 类别={rule.item_category}, 名称={rule.item_name}, 有效期(年)={rule.normal_expiry}")
            # 只有当规则的有效期不为0时才添加到字典中，0表示长期有效不需要预警
            if rule.normal_expiry != 0:
                expiry_rule_dict[rule.item_name] = rule.normal_expiry
            else:
                print(f"物品 '{rule.item_name}' 标记为长期有效，不进行预警")
        
        # 2. 获取所有区域的负责人信息 - 修复：在使用前初始化responsible_dict
        from app.models.station import ResponsiblePerson
        responsible_persons = ResponsiblePerson.query.all()
        responsible_dict = {}
        for person in responsible_persons:
            responsible_dict[person.area_code] = person.person_name
        
        print(f"加载负责人数据: {len(responsible_dict)}条")
        
        # 3. 扫描微型站物资表 - 根据权限过滤
        print("正在扫描微型站物资表...")
        from app.models.station import FireStation
        
        # 根据用户角色和权限过滤微型站物资
        if current_user.role == 'admin':
            # 管理员可以查看所有区域
            station_items = FireStation.query.all()
        else:
            # 非管理员只能查看有权限的区域
            if allowed_areas['微型消防站']:
                # 确保区域ID是正确的类型（整数或字符串）
                area_ids = []
                for area_id in allowed_areas['微型消防站']:
                    if isinstance(area_id, str) and area_id.isdigit():
                        area_ids.append(int(area_id))
                    else:
                        area_ids.append(area_id)
                        
                station_items = FireStation.query.filter(FireStation.area_code.in_(area_ids)).all()
                print(f"用户权限微型站区域: {area_ids}, 查询到物资数量: {len(station_items)}")
            else:
                # 没有微型站权限
                station_items = []
                print("用户无微型站权限，不查询物资")
                
        print(f"微型站物资总数: {len(station_items)}")
        station_with_date = 0
        station_with_rule = 0
        station_in_warning = 0
        
        for item in station_items:
            # ...现有代码（处理微型站物资的逻辑）...
            # 跳过生产日期为空的物品
            if not item.production_date:
                #print(f"跳过无生产日期的物资: {item.item_name}")
                continue
            
            station_with_date += 1
            #print(f"处理微型站物资: {item.item_name}, 生产日期: {item.production_date}")
            
            # 检查微型站物资的item_name是否在规则字典中
            item_name = item.item_name
            
            # 添加模糊匹配逻辑，可能是命名不完全一致
            matching_rule = None
            for rule_name in expiry_rule_dict.keys():
                if item_name == rule_name or item_name in rule_name or rule_name in item_name:
                    matching_rule = rule_name
                    break
            
            if matching_rule:
                station_with_rule += 1
                # 有效期规则 (年)
                expiry_years = expiry_rule_dict[matching_rule]
                
                # 计算到期日期与剩余天数
                expiry_date = item.production_date + timedelta(days=int(expiry_years*365))
                days_remaining = (expiry_date - current_date).days
                
                # 获取区域负责人
                responsible_person = responsible_dict.get(item.area_code, "未指定负责人")
                
                # 修改条件：只要小于等于预警天数的都添加（包括已过期的负数天数）
                if days_remaining <= warning_days:  # 修改这一行，去掉0 <=
                    station_in_warning += 1
                    print(f"找到到期预警物资: {item.item_name}, 剩余天数: {days_remaining}")
                    expiring_items.append({
                        'id': item.id,
                        'type': '微型站物资',
                        'area_name': item.area_name,
                        'area_code': item.area_code,
                        'location': '未指定',
                        'name': item.item_name,
                        'model': item.model or '未指定',
                        'production_date': item.production_date,
                        'expiry_date': expiry_date,
                        'days_remaining': days_remaining,
                        'expiry_years': expiry_years,
                        'responsible_person': responsible_person,
                        'source_table': 'station',
                        'source_id': item.id,
                        'operation_type': '微型消防站'  # 添加操作类型字段
                    })
            else:
                print(f"警告: 物资 '{item.item_name}' 在有效期规则表中找不到匹配项或标记为长期有效")
        
        # 输出微型站物资处理统计
        print(f"微型站物资统计: 总数={len(station_items)}, 有生产日期={station_with_date}, 找到规则={station_with_rule}, 在预警期内={station_in_warning}")
        
        # 4. 扫描消防器材表 - 根据权限过滤
        print("正在扫描消防器材表...")
        from app.models.equipment import FireEquipment
        
        # 根据用户角色和权限过滤消防器材
        if current_user.role == 'admin':
            # 管理员可以查看所有消防器材
            equipment_items = FireEquipment.query.all()
        else:
            # 非管理员只能查看有权限的区域
            if allowed_areas['灭火器和呼吸器']:
                # 确保区域ID是正确的类型（整数或字符串）
                area_ids = []
                for area_id in allowed_areas['灭火器和呼吸器']:
                    area_ids.append(str(area_id))  # 消防器材区域ID存储为字符串
                        
                equipment_items = FireEquipment.query.filter(FireEquipment.area_code.in_(area_ids)).all()
                print(f"用户权限消防器材区域: {area_ids}, 查询到器材数量: {len(equipment_items)}")
            else:
                # 没有消防器材权限
                equipment_items = []
                print("用户无消防器材权限，不查询器材")
        
        equipment_with_date = 0
        equipment_with_rule = 0
        equipment_in_warning = 0
        
        for item in equipment_items:
            # ...现有代码（处理消防器材的逻辑）...
            # 跳过生产日期为空的物品
            if not item.production_date:
                #print(f"跳过无生产日期的设备: {item.equipment_name}")
                continue
            
            equipment_with_date += 1
            #print(f"处理消防器材: {item.equipment_name}, 类型: {item.equipment_type}, 生产日期: {item.production_date}")
            
            # 注意：这里使用equipment_type查找规则，而微型站使用item_name
            equipment_type = item.equipment_type
            
            # 同样添加模糊匹配逻辑
            matching_rule = None
            for rule_name in expiry_rule_dict.keys():
                if equipment_type == rule_name or equipment_type in rule_name or rule_name in equipment_type:
                    matching_rule = rule_name
                    break
            
            if matching_rule:
                equipment_with_rule += 1
                # 有效期规则 (年)
                expiry_years = expiry_rule_dict[matching_rule]
                
                # 计算到期日期与剩余天数
                expiry_date = item.production_date + timedelta(days=int(expiry_years*365))
                days_remaining = (expiry_date - current_date).days
                
                # 获取区域负责人
                responsible_person = responsible_dict.get(item.area_code, "未指定负责人")
                
                # 修改条件：只要小于等于预警天数的都添加（包括已过期的负数天数）
                if days_remaining <= warning_days:  # 修改这一行，去掉0 <=
                    equipment_in_warning += 1
                    print(f"找到到期预警器材: {item.equipment_name}, 剩余天数: {days_remaining}")
                    # 修改这里：使用equipment_type作为name字段，而不是equipment_name
                    expiring_items.append({
                        'id': item.id,
                        'type': '消防器材',
                        'area_name': item.area_name,
                        'area_code': item.area_code,
                        'location': f"{item.installation_floor} - {item.installation_location}",
                        'name': item.equipment_type,  # 修改这一行，从equipment_name改为equipment_type
                        'model': item.model or '未指定',
                        'production_date': item.production_date,
                        'expiry_date': expiry_date,
                        'days_remaining': days_remaining,
                        'expiry_years': expiry_years,
                        'responsible_person': responsible_person,
                        'source_table': 'equipment',
                        'source_id': item.id,
                        'operation_type': '灭火器和呼吸器'  # 添加操作类型字段
                    })
            else:
                print(f"警告: 器材类型 '{equipment_type}' 在有效期规则表中找不到匹配项或标记为长期有效")
        
        # 后续的排序、分页、数据处理等代码保持不变
        # ...现有代码...
        # 输出消防器材处理统计
        print(f"消防器材统计: 总数={len(equipment_items)}, 有生产日期={equipment_with_date}, 找到规则={equipment_with_rule}, 在预警期内={equipment_in_warning}")
        
        # 5. 排序 - 首先按已到期与否排序，然后按剩余天数，最后按区域名称
        # 已到期的物品(剩余天数<0)会排在最前面
        expiring_items.sort(key=lambda x: (x['days_remaining'] >= 0, x['days_remaining'], x['area_name']))
        
        # 输出总预警数据统计
        print(f"总预警数量: {len(expiring_items)}")
        print(f"其中: 微型站物资={station_in_warning}, 消防器材={equipment_in_warning}")
        
        # 在应用类型筛选之前应用自定义筛选条件
        filtered_items = expiring_items
        
        # 应用来源类型筛选
        if filter_source:
            filtered_items = [item for item in filtered_items if item['source_table'] == filter_source]
        
        # 应用预警级别筛选
        if filter_level:
            if filter_level == 'expired':
                filtered_items = [item for item in filtered_items if item['days_remaining'] < 0]
            elif filter_level == 'warning30':
                filtered_items = [item for item in filtered_items if 0 <= item['days_remaining'] <= 30]
            elif filter_level == 'warning60':
                filtered_items = [item for item in filtered_items if 30 < item['days_remaining'] <= 60]
            elif filter_level == 'warning90':
                filtered_items = [item for item in filtered_items if 60 < item['days_remaining'] <= 90]
        
        # 应用物品/器材名称筛选
        if filter_name:
            filtered_items = [item for item in filtered_items if item['name'] == filter_name]
        
        # 应用负责人筛选
        if filter_responsible:
            filtered_items = [item for item in filtered_items if item['responsible_person'] == filter_responsible]
        
        # 应用类型筛选（微型站/消防器材）
        if filter_type == 'station':
            filtered_items = [item for item in filtered_items if item['source_table'] == 'station']
        elif filter_type == 'equipment':
            filtered_items = [item for item in filtered_items if item['source_table'] == 'equipment']
        
        # 收集所有唯一的物品名称和负责人，用于筛选下拉菜单
        item_names = sorted(set(item['name'] for item in expiring_items))
        responsible_persons = sorted(set(item['responsible_person'] for item in expiring_items))
        
        # 7. 分页处理
        total_items = len(filtered_items)
        total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 1
        
        # 确保页码在有效范围内
        page = max(1, min(page, total_pages))
        
        # 计算当前页的数据
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total_items)
        current_items = filtered_items[start_idx:end_idx]
        
        # 8. 按剩余天数分组 (仅统计全部数据，不考虑分页)
        expiring_by_days = {}
        for item in expiring_items:
            days = item['days_remaining']
            if days not in expiring_by_days:
                expiring_by_days[days] = []
            expiring_by_days[days].append(item)
        
        # 添加额外的调试输出，查看是否有数据
        print(f"所有预警项目数量: {len(expiring_items)}")
        print(f"已到期项目数: {sum(1 for item in expiring_items if item['days_remaining'] < 0)}")
        print(f"30天内到期项目数: {sum(1 for item in expiring_items if 0 <= item['days_remaining'] <= 30)}")
        print(f"60天内到期项目数: {sum(1 for item in expiring_items if 30 < item['days_remaining'] <= 60)}")
        print(f"90天内到期项目数: {sum(1 for item in expiring_items if 60 < item['days_remaining'] <= 90)}")
        
        # 检查一下expiring_by_days是否正确构建
        print(f"expiring_by_days包含的天数键: {list(expiring_by_days.keys())}")
        
        # 添加详细的权限变量，用于传递给模板
        has_station_permission = False
        has_equipment_permission = False
        
        if current_user.role == 'admin':
            has_station_permission = True
            has_equipment_permission = True
        else:
            # 检查微型站权限
            if any(allowed_areas['微型消防站']):
                has_station_permission = True
            
            # 检查设备权限
            if any(allowed_areas['灭火器和呼吸器']):
                has_equipment_permission = True

        return render_template(
            'admin/expiry_alert.html',
            expiring_items=current_items,  # 当前页的预警项目
            all_expiring_items=expiring_items,  # 所有预警项目(用于统计)
            expiring_by_days=expiring_by_days,
            current_date=current_date,
            warning_days=warning_days,
            page=page,  # 当前页码
            per_page=per_page,  # 每页条数
            total_items=total_items,  # 总条数
            total_pages=total_pages,  # 总页数
            filter_type=filter_type,  # 当前筛选类型
            is_admin=current_user.role == 'admin',  # 添加标识是否为管理员
            has_station_permission=has_station_permission,
            has_equipment_permission=has_equipment_permission,
            filter_level=filter_level,
            filter_name=filter_name,
            filter_responsible=filter_responsible,
            has_filters=has_filters,
            item_names=item_names,
            responsible_persons=responsible_persons,
            filter_source=filter_source  # 新增变量
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'加载有效期预警数据出错: {str(e)}', 'danger')
        
        # 错误时返回空数据并传递必要变量
        return render_template(
            'admin/expiry_alert.html', 
            expiring_items=[],
            all_expiring_items=[],
            expiring_by_days={},
            current_date=datetime.now().date(),
            warning_days=90,
            page=1,
            per_page=15,
            total_items=0,
            total_pages=1,
            filter_type='all',
            is_admin=current_user.role == 'admin',  # 添加标识是否为管理员
            has_station_permission=False,
            has_equipment_permission=False,
            filter_level='',
            filter_name='',
            filter_responsible='',
            has_filters=False,
            item_names=[],
            responsible_persons=[],
            filter_source=''  # 错误时也添加这个变量
        )

# 导入邮件发送相关模块
from flask import jsonify, request
from app.models.station import ResponsiblePerson
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from flask import current_app  # 导入current_app代理对象以获取配置
from app.models.mail_log import MailLog
# 添加发送预警邮件的路由
# 添加更详细的调试日志到邮件发送路由
@admin_bp.route('/send_expiry_alert_emails', methods=['POST'])
@login_required
@admin_required
def send_expiry_alert_emails():
    """发送有效期预警邮件"""
    try:
        print("接收到发送预警邮件请求")
        # 获取请求数据
        data = request.get_json()
        print(f"请求数据: {data}")
        
        email_content = data.get('email_content', '')
        email_subject = data.get('email_subject', '【重要】物资有效期预警通知')
        options = data.get('options', {})
        original_items = data.get('items', [])  # 获取原始物品数据，用于重新生成针对性内容
        
        print(f"邮件主题: {email_subject}")
        print(f"选项: {options}")
        
        selected_responsibles = data.get('selected_responsibles', [])
        print(f"选中的负责人: {selected_responsibles}")
        
        # 从数据库获取所有负责人的邮箱地址
        responsible_persons = ResponsiblePerson.query.all()
        print(f"查询到 {len(responsible_persons)} 位负责人记录")
        
        email_mapping = {}
        for person in responsible_persons:
            # 检查该负责人是否在选中列表中
            if selected_responsibles and person.person_name not in selected_responsibles:
                print(f"负责人 {person.person_name} 未被选中，跳过")
                continue
                
            if person.email and '@' in person.email:  # 简单验证邮箱格式
                email_mapping[person.person_name] = person.email
                print(f"负责人 {person.person_name} 有效邮箱: {person.email}")
            else:
                print(f"负责人 {person.person_name} 邮箱无效或为空: {person.email}")
        
        # 如果没有有效的邮箱地址
        if not email_mapping:
            print("没有找到有效的邮箱地址，无法发送邮件")
            return jsonify({
                'success': True,
                'recipients_count': 0,
                'message': '没有找到有效的邮箱地址'
            })
        
        # 导入formataddr函数用于RFC标准格式化发件人
        from email.utils import formataddr
        
        # 从应用配置中获取邮件配置
        mail_server = current_app.config.get('MAIL_SERVER')
        mail_port = current_app.config.get('MAIL_PORT')
        mail_use_ssl = current_app.config.get('MAIL_USE_SSL', False)
        mail_use_tls = current_app.config.get('MAIL_USE_TLS', False)
        mail_username = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')
        mail_sender = current_app.config.get('MAIL_DEFAULT_SENDER', mail_username)
        
        # 处理元组格式的发件人，使用formataddr确保符合RFC标准
        if isinstance(mail_sender, tuple):
            sender_name, sender_email = mail_sender
            formatted_sender = formataddr((sender_name, sender_email))  # 使用formataddr格式化
            mail_sender_email = sender_email  # 用于SMTP身份验证和发件人地址
        else:
            # 如果不是元组，也使用formataddr处理可能的编码问题
            formatted_sender = formataddr(('', mail_sender)) if '@' in mail_sender else mail_sender
            mail_sender_email = mail_sender
        
        print(f"邮件服务器配置: 服务器={mail_server}, 端口={mail_port}, SSL={mail_use_ssl}, TLS={mail_use_tls}")
        print(f"发件人格式化后: {formatted_sender}, 发件地址: {mail_sender_email}")
        
        # 检查邮箱密码是否存在
        if not mail_password:
            print("警告: 未设置邮箱密码，尝试获取环境变量MAIL_PASSWORD")
            import os
            mail_password = os.environ.get('MAIL_PASSWORD', '')
            if not mail_password:
                print("错误: 无法获取邮箱密码，请在配置文件或环境变量中设置")
                return jsonify({
                    'success': False,
                    'error': '邮件服务器配置错误：未设置邮箱密码'
                })
        
        # 获取客户端IP地址
        ip_address = request.remote_addr
        
        # 向所有有效的邮箱地址发送邮件 - 为每个收件人重新建立连接
        recipients_count = 0
        failed_recipients = []
        
        for person_name, email_address in email_mapping.items():
            try:
                # 为当前负责人生成专属的邮件内容
                personalized_content = generate_personalized_email_content(
                    person_name, 
                    email_content, 
                    original_items if original_items else None
                )
                
                if not personalized_content:
                    print(f"警告: 无法为 {person_name} 生成个性化内容，可能没有相关预警项目，跳过发送")
                    continue
                
                # 计算此人的预警物品数量
                person_items_count = sum(1 for item in original_items if item.get('responsible_person') == person_name)
                
                # 为每位收件人创建新的SMTP连接
                try:
                    # 使用正确的SMTP类，基于SSL/TLS配置
                    if mail_use_ssl:
                        print(f"为 {person_name} 使用SSL连接到SMTP服务器: {mail_server}:{mail_port}")
                        server = smtplib.SMTP_SSL(mail_server, mail_port, timeout=10)
                    else:
                        print(f"为 {person_name} 使用普通连接到SMTP服务器: {mail_server}:{mail_port}")
                        server = smtplib.SMTP(mail_server, mail_port, timeout=10)
                        
                        # 如果启用了TLS，初始化TLS连接
                        if mail_use_tls:
                            print("启用TLS连接")
                            server.starttls()
                    
                    # 登录SMTP服务器
                    if mail_username and mail_password:
                        print(f"使用用户名 {mail_username} 登录SMTP服务器")
                        server.login(mail_username, mail_password)
                    
                    # 创建每个收件人的邮件副本
                    recipient_msg = MIMEMultipart('alternative')
                    recipient_msg['Subject'] = Header(email_subject, 'utf-8')
                    recipient_msg['From'] = formatted_sender  # 使用RFC标准格式化的发件人
                    recipient_msg['To'] = email_address
                    
                    # 设置邮件内容 - 使用个性化内容
                    personalized_html_part = MIMEText(personalized_content, 'html', 'utf-8')
                    recipient_msg.attach(personalized_html_part)
                    
                    # 发送邮件 - 使用纯邮箱地址
                    print(f"发送邮件给 {person_name} ({email_address})")
                    server.sendmail(mail_sender_email, [email_address], recipient_msg.as_string())
                    
                    # 记录成功发送的邮件日志 - 使用格式化的发件人字符串
                    mail_log = MailLog(
                        send_time=datetime.now(),
                        sender=formatted_sender,  # 使用RFC标准格式化后的发件人
                        recipient=email_address,
                        recipient_name=person_name,
                        subject=email_subject,
                        content_summary=f"有效期预警邮件 - 包含{person_items_count}个物品",
                        status="success",
                        error_message=None,
                        items_count=person_items_count,
                        ip_address=ip_address,
                        user_id=current_user.id,
                        username=current_user.username
                    )
                    db.session.add(mail_log)
                    db.session.commit()
                    
                    recipients_count += 1
                    print(f"已向 {person_name} ({email_address}) 发送预警邮件")
                    
                    # 关闭连接
                    server.quit()
                    print(f"SMTP服务器连接已关闭 (收件人: {person_name})")
                    
                    # 添加一点延迟，避免发送过快
                    import time
                    time.sleep(1)
                    
                except smtplib.SMTPAuthenticationError as e:
                    error_msg = "SMTP身份验证失败：用户名或密码错误"
                    print(f"向 {person_name} 发送邮件时错误: {error_msg}")
                    failed_recipients.append(f"{person_name} ({error_msg})")
                    
                    # 记录发送失败的邮件日志
                    mail_log = MailLog(
                        send_time=datetime.now(),
                        sender=formatted_sender,  # 使用RFC标准格式化后的发件人
                        recipient=email_address,
                        recipient_name=person_name,
                        subject=email_subject,
                        content_summary=f"有效期预警邮件 - 包含{person_items_count}个物品",
                        status="failed",
                        error_message=f"认证错误: {str(e)}",
                        items_count=person_items_count,
                        ip_address=ip_address,
                        user_id=current_user.id,
                        username=current_user.username
                    )
                    db.session.add(mail_log)
                    db.session.commit()
                    
                except smtplib.SMTPException as e:
                    error_msg = f"SMTP错误: {str(e)}"
                    print(f"向 {person_name} 发送邮件时错误: {error_msg}")
                    failed_recipients.append(f"{person_name} ({error_msg})")
                    
                    # 记录发送失败的邮件日志
                    mail_log = MailLog(
                        send_time=datetime.now(),
                        sender=formatted_sender,  # 使用RFC标准格式化后的发件人
                        recipient=email_address,
                        recipient_name=person_name,
                        subject=email_subject,
                        content_summary=f"有效期预警邮件 - 包含{person_items_count}个物品",
                        status="failed",
                        error_message=f"SMTP错误: {str(e)}",
                        items_count=person_items_count,
                        ip_address=ip_address,
                        user_id=current_user.id,
                        username=current_user.username
                    )
                    db.session.add(mail_log)
                    db.session.commit()
                    
                except Exception as e:
                    error_msg = f"发送邮件过程中出错: {str(e)}"
                    print(f"向 {person_name} 发送邮件时错误: {error_msg}")
                    failed_recipients.append(f"{person_name} ({error_msg})")
                    
                    # 记录发送失败的邮件日志
                    mail_log = MailLog(
                        send_time=datetime.now(),
                        sender=formatted_sender,  # 使用RFC标准格式化后的发件人
                        recipient=email_address,
                        recipient_name=person_name,
                        subject=email_subject,
                        content_summary=f"有效期预警邮件 - 包含{person_items_count}个物品",
                        status="failed",
                        error_message=f"未知错误: {str(e)}",
                        items_count=person_items_count,
                        ip_address=ip_address,
                        user_id=current_user.id,
                        username=current_user.username
                    )
                    db.session.add(mail_log)
                    db.session.commit()
                    
            except Exception as e:
                print(f"为 {person_name} 处理邮件内容时出错: {str(e)}")
                failed_recipients.append(person_name)
                
                # 记录处理失败的邮件日志
                try:
                    mail_log = MailLog(
                        send_time=datetime.now(),
                        sender=formatted_sender,  # 使用RFC标准格式化后的发件人
                        recipient=email_address,
                        recipient_name=person_name,
                        subject=email_subject,
                        content_summary="有效期预警邮件 - 内容处理失败",
                        status="failed",
                        error_message=f"邮件内容处理错误: {str(e)}",
                        items_count=0,
                        ip_address=ip_address,
                        user_id=current_user.id,
                        username=current_user.username
                    )
                    db.session.add(mail_log)
                    db.session.commit()
                except Exception as log_error:
                    print(f"记录邮件日志时出错: {str(log_error)}")
                    db.session.rollback()  # 添加回滚操作
        
        # 构建返回消息
        message = f'成功发送邮件给 {recipients_count} 位接收者'
        if failed_recipients:
            message += f'，但 {len(failed_recipients)} 位接收者发送失败: {", ".join(failed_recipients)}'
            
        print(message)
        return jsonify({
            'success': True,
            'recipients_count': recipients_count,
            'message': message
        })
    
    except Exception as e:
        import traceback
        print("发送预警邮件时出错:")
        traceback.print_exc()
        
        # 记录整体失败日志 - 使用字符串格式的发件人
        try:
            # 确保发件人是字符串格式
            if 'mail_sender' in locals():
                if isinstance(mail_sender, tuple):
                    from email.utils import formataddr
                    sender_str = formataddr(mail_sender)  # 使用formataddr替代字符串拼接
                else:
                    sender_str = mail_sender
            else:
                sender_str = current_app.config.get('MAIL_USERNAME', '')
                
            mail_log = MailLog(
                send_time=datetime.now(),
                sender=sender_str,  # 使用RFC标准格式的发件人
                recipient="多人发送",
                recipient_name="批量发送",
                subject=data.get('email_subject', '【重要】物资有效期预警通知') if 'data' in locals() else "未知",
                content_summary="有效期预警邮件 - 发送过程失败",
                status="failed",
                error_message=f"整体发送过程错误: {str(e)}",
                items_count=len(original_items) if 'original_items' in locals() else 0,
                ip_address=request.remote_addr,
                user_id=current_user.id,
                username=current_user.username
            )
            db.session.add(mail_log)
            db.session.commit()
        except Exception as log_error:
            print(f"记录整体失败日志时出错: {str(log_error)}")
            db.session.rollback()  # 添加回滚操作
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def generate_personalized_email_content(responsible_person, full_content, original_items=None):
    """生成针对特定负责人的个性化邮件内容"""
    try:
        print(f"为负责人 {responsible_person} 生成个性化邮件内容")
        
        # 方法1：优先使用传入的原始数据生成个性化内容
        if original_items and isinstance(original_items, list) and len(original_items) > 0:
            print(f"使用原始物品数据生成内容，共 {len(original_items)} 项")
            
            # 筛选该负责人的物品
            responsible_items = [item for item in original_items 
                               if item.get('responsible_person') == responsible_person]
            
            print(f"该负责人有 {len(responsible_items)} 个预警项目")
            
            # 如果没有该负责人的物品，返回None
            if not responsible_items:
                print(f"负责人 {responsible_person} 没有预警物品，跳过")
                return None
                
            # 生成该负责人的邮件内容
            html = f'''
            <div style="font-family: Arial, sans-serif;">
                <h2 style="color: #dc3545;">消防安全管理系统 - 物资有效期预警通知</h2>
                <p>尊敬的 {responsible_person}：</p>
                <p>您负责的以下物资即将到期或已经到期，请及时处理：</p>
                <div style="margin-top: 20px;">
                    <h3 style="margin-bottom: 10px; border-bottom: 1px solid #dee2e6; padding-bottom: 5px;">
                        负责人：{responsible_person}
                    </h3>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                        <thead>
                            <tr style="background-color: #f8f9fa;">
                                <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">物品名称</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">型号</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">区域</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">位置</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">到期日期</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">状态</th>
                            </tr>
                        </thead>
                        <tbody>
            '''
            
            # 为每个物品生成表格行
            for item in responsible_items:
                # 获取物品状态信息
                days_remaining = item.get('days_remaining', 0)
                
                statusText = ""
                statusColor = ""
                
                if days_remaining < 0:
                    statusText = "已到期"
                    statusColor = "#dc3545"  # 红色
                elif days_remaining <= 30:
                    statusText = "30天内到期"
                    statusColor = "#ffc107"  # 黄色
                elif days_remaining <= 60:
                    statusText = "60天内到期"
                    statusColor = "#17a2b8"  # 青色
                else:
                    statusText = "90天内到期"
                    statusColor = "#007bff"  # 蓝色
                
                # 添加一行表格数据
                html += f'''
                <tr>
                    <td style="border: 1px solid #dee2e6; padding: 8px;">{item.get('name', '')}</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px;">{item.get('model', '')}</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px;">{item.get('area_name', '')}</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px;">{item.get('location', '')}</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px;">{item.get('expiry_date', '')}</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px; color: {statusColor}; font-weight: bold;">
                        {statusText}
                    </td>
                </tr>
                '''
            
            # 完成HTML内容
            html += '''
                        </tbody>
                    </table>
                </div>
                <p>请及时对已到期和即将到期的物资进行更换或维护，确保消防安全。</p>
                <p>谢谢您的配合！</p>
                <p style="margin-top: 20px; color: #6c757d; font-size: 0.9em;">
                    消防安全管理系统<br>
                    发送时间：''' + f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}' + '''
                </p>
            </div>
            '''
            
            return html
        
        # 方法2：如果没有原始数据，从完整HTML中提取该负责人的部分
        else:
            print(f"尝试从完整HTML中提取该负责人的内容")
            import re
            
            # 先检查邮件内容中是否包含此负责人的表格
            if responsible_person not in full_content:
                print(f"完整HTML中不包含负责人 {responsible_person} 的内容")
                return None
            
            # 提取邮件标题和开头部分
            header_pattern = r'<div style="font-family: Arial, sans-serif;">.*?<p>您负责的以下物资即将到期或已经到期，请及时处理：</p>'
            header_match = re.search(header_pattern, full_content, re.DOTALL)
            header = header_match.group(0) if header_match else ""
            
            # 修改收件人称呼
            header = header.replace("尊敬的负责人：", f"尊敬的 {responsible_person}：")
            
            # 提取该负责人的表格部分
            responsible_pattern = rf'<div style="margin-top: 20px;">\s*<h3[^>]*>[\s\n]*负责人：{re.escape(responsible_person)}[\s\n]*</h3>(.*?)(?:<div style="margin-top: 20px;">|<p>请及时对已到期和即将到期的物资进行更换或维护)'
            
            responsible_match = re.search(responsible_pattern, full_content, re.DOTALL)
            
            if not responsible_match:
                print(f"无法匹配到负责人 {responsible_person} 的内容块")
                return None
                
            responsible_content = responsible_match.group(0)
            
            # 如果内容末尾不完整，可能需要手动修复
            if not responsible_content.endswith('</div>'):
                responsible_content += '</div>'
            
            # 提取结尾部分
            footer_pattern = r'<p>请及时对已到期和即将到期的物资进行更换或维护.*?</div>'
            footer_match = re.search(footer_pattern, full_content, re.DOTALL)
            footer = footer_match.group(0) if footer_match else ""
            
            # 组合内容
            personalized_content = f'{header}{responsible_content}{footer}'
            
            print(f"使用正则提取成功，内容长度: {len(personalized_content)}")
            return personalized_content
            
    except Exception as e:
        print(f"生成个性化邮件内容出错: {str(e)}")
        traceback.print_exc()
        # 出错时，返回一个基本的邮件模板
        return f'''
        <div style="font-family: Arial, sans-serif;">
            <h2 style="color: #dc3545;">消防安全管理系统 - 物资有效期预警通知</h2>
            <p>尊敬的 {responsible_person}：</p>
            <p>您有物资即将到期或已经到期，请登录系统查看详情。</p>
            <p>请及时对已到期和即将到期的物资进行更换或维护，确保消防安全。</p>
            <p>谢谢您的配合！</p>
            <p style="margin-top: 20px; color: #6c757d; font-size: 0.9em;">
                消防安全管理系统<br>
                发送时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </p>
        </div>
        '''

# 添加邮件日志页面路由
@admin_bp.route('/mail_logs')
@login_required
@admin_required
def mail_logs():
    """邮件发送日志页面"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 15  # 修改为每页显示15条记录
        
        # 获取搜索和筛选参数
        search = request.args.get('search', '')
        filter_status = request.args.get('status', '')
        
        # 将单一日期筛选改为日期范围筛选
        filter_start_date = request.args.get('start_date', '')
        filter_end_date = request.args.get('end_date', '')
        
        # 基础查询
        query = MailLog.query.order_by(MailLog.send_time.desc())
        
        # 应用筛选条件
        if filter_status:
            query = query.filter(MailLog.status == filter_status)
            
        # 修改日期筛选逻辑，支持日期范围
        if filter_start_date and filter_end_date:
            try:
                start_date_obj = datetime.strptime(filter_start_date, '%Y-%m-%d').date()
                end_date_obj = datetime.strptime(filter_end_date, '%Y-%m-%d').date()
                # 包含结束日期的数据，所以末尾加一天再比较
                end_date_obj_next = end_date_obj + timedelta(days=1)
                
                query = query.filter(
                    db.func.date(MailLog.send_time) >= start_date_obj,
                    db.func.date(MailLog.send_time) < end_date_obj_next
                )
            except ValueError:
                flash('日期格式无效，应为 YYYY-MM-DD', 'warning')
        elif filter_start_date:
            try:
                start_date_obj = datetime.strptime(filter_start_date, '%Y-%m-%d').date()
                query = query.filter(db.func.date(MailLog.send_time) >= start_date_obj)
            except ValueError:
                flash('开始日期格式无效，应为 YYYY-MM-DD', 'warning')
        elif filter_end_date:
            try:
                end_date_obj = datetime.strptime(filter_end_date, '%Y-%m-%d').date()
                end_date_obj_next = end_date_obj + timedelta(days=1)
                query = query.filter(db.func.date(MailLog.send_time) < end_date_obj_next)
            except ValueError:
                flash('结束日期格式无效，应为 YYYY-MM-DD', 'warning')
        
        # 应用搜索条件
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    MailLog.recipient.ilike(search_term),
                    MailLog.recipient_name.ilike(search_term),
                    MailLog.subject.ilike(search_term),
                    MailLog.username.ilike(search_term)
                )
            )
        
        # 获取统计信息 - 添加这部分代码
        total_count = query.count()
        success_count = query.filter(MailLog.status == 'success').count()
        failed_count = query.filter(MailLog.status == 'failed').count()
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        logs = pagination.items
        
        # 获取最近7天的发送统计 - 修复日期类型错误
        from sqlalchemy import func
        from sqlalchemy.sql.expression import text
        today = datetime.now().date()
        seven_days_ago = today - timedelta(days=6)
        
        # 使用正确的SQL表达式语法
        daily_stats = db.session.query(
            func.date(MailLog.send_time).label('date'),
            func.count(MailLog.id).label('count'),
            func.sum(text("CASE WHEN status = 'success' THEN 1 ELSE 0 END")).label('success'),
            func.sum(text("CASE WHEN status = 'failed' THEN 1 ELSE 0 END")).label('failed')
        ).filter(
            func.date(MailLog.send_time) >= seven_days_ago
        ).group_by(
            func.date(MailLog.send_time)
        ).order_by(
            func.date(MailLog.send_time)
        ).all()
        
        # 转换为可用于图表的数据
        dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
        daily_counts = [0] * 7
        daily_success = [0] * 7
        daily_failed = [0] * 7
        
        for stat in daily_stats:
            # 将字符串日期转换为datetime.date对象
            try:
                stat_date = datetime.strptime(str(stat.date), '%Y-%m-%d').date()
                day_diff = (today - stat_date).days
                if 0 <= day_diff <= 6:
                    idx = 6 - day_diff
                    daily_counts[idx] = stat.count
                    daily_success[idx] = stat.success
                    daily_failed[idx] = stat.failed
            except (ValueError, TypeError) as e:
                print(f"日期转换错误: {e}, 原始日期: {stat.date}, 类型: {type(stat.date)}")
                continue
        
        return render_template(
            'admin/mail_logs.html',
            logs=logs,
            pagination=pagination,
            total_count=total_count,
            success_count=success_count,
            failed_count=failed_count,
            filter_status=filter_status,
            filter_start_date=filter_start_date,
            filter_end_date=filter_end_date,
            search=search,
            dates=dates,
            daily_counts=daily_counts,
            daily_success=daily_success,
            daily_failed=daily_failed
        )
    except Exception as e:
        traceback.print_exc()
        flash(f'获取邮件日志时出错: {str(e)}', 'danger')
        
        # 错误时提供默认值给模板
        today = datetime.now().date()
        dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
        
        return render_template(
            'admin/mail_logs.html', 
            logs=[], 
            error=str(e),
            pagination=None,
            total_count=0,
            success_count=0,
            failed_count=0,
            dates=dates,
            daily_counts=[0]*7,
            daily_success=[0]*7,
            daily_failed=[0]*7,
            filter_status='',
            filter_start_date='',  # 更新为开始日期
            filter_end_date='',    # 添加结束日期
            search=''
        )

# 添加一个用于调试的API端点，检查预警数据
@admin_bp.route('/api/check_expiry_data')
@login_required
@admin_required
def check_expiry_data():
    """调试API - 检查有效期预警数据"""
    try:
        # 获取当前日期
        from datetime import datetime, timedelta
        current_date = datetime.now().date()
        
        # 从有效期规则表中获取所有规则
        expiry_rules = EquipmentExpiry.query.all()
        rules_count = len(expiry_rules)
        
        # 从ResponsiblePerson表获取负责人
        from app.models.station import ResponsiblePerson
        responsible_persons = ResponsiblePerson.query.all()
        persons_count = len(responsible_persons)
        
        # 获取微型站物资
        from app.models.station import FireStation
        station_items = FireStation.query.all()
        station_count = len(station_items)
        
        # 获取消防器材
        from app.models.equipment import FireEquipment
        equipment_items = FireEquipment.query.all()
        equipment_count = len(equipment_items)
        
        # 只处理有生产日期的物品并计算剩余天数
        expiring_items = []
        
        # 微型站物资
        for item in station_items:
            if item.production_date:
                for rule in expiry_rules:
                    if item.item_name in rule.item_name or rule.item_name in item.item_name:
                        expiry_date = item.production_date + timedelta(days=int(rule.normal_expiry*365))
                        days_remaining = (expiry_date - current_date).days
                        
                        # 只添加90天内到期的
                        if days_remaining <= 90:
                            expiring_items.append({
                                'name': item.item_name,
                                'days_remaining': days_remaining,
                                'type': '微型站物资'
                            })
                        break
        
        # 消防器材
        for item in equipment_items:
            if item.production_date:
                for rule in expiry_rules:
                    if item.equipment_type in rule.item_name or rule.item_name in item.equipment_type:
                        expiry_date = item.production_date + timedelta(days=int(rule.normal_expiry*365))
                        days_remaining = (expiry_date - current_date).days
                        
                        # 只添加90天内到期的
                        if days_remaining <= 90:
                            expiring_items.append({
                                'name': item.equipment_type,
                                'days_remaining': days_remaining,
                                'type': '消防器材'
                            })
                        break
        
        # 按剩余天数分类统计
        expired_count = sum(1 for item in expiring_items if item['days_remaining'] < 0)
        days30_count = sum(1 for item in expiring_items if 0 <= item['days_remaining'] <= 30)
        days60_count = sum(1 for item in expiring_items if 30 < item['days_remaining'] <= 60)
        days90_count = sum(1 for item in expiring_items if 60 < item['days_remaining'] <= 90)
        
        return jsonify({
            'success': True,
            'data': {
                'rules_count': rules_count,
                'persons_count': persons_count,
                'station_count': station_count,
                'equipment_count': equipment_count,
                'expiring_items_count': len(expiring_items),
                'stats': {
                    'expired': expired_count,
                    'days30': days30_count,
                    'days60': days60_count,
                    'days90': days90_count
                }
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 添加到文件末尾，不修改现有代码
@admin_bp.route('/api/check_item_name')
@login_required
@admin_required
def check_item_name():
    """检查物品名称是否已存在于有效期规则表中"""
    try:
        item_name = request.args.get('item_name', '')
        rule_id = request.args.get('rule_id', type=int)
        
        if not item_name:
            return jsonify({'exists': False, 'error': '物品名称不能为空'})
        
        # 查询条件：如果提供了rule_id，则排除此ID的记录(编辑模式)
        query = EquipmentExpiry.query.filter(EquipmentExpiry.item_name == item_name)
        if rule_id:
            query = query.filter(EquipmentExpiry.id != rule_id)
            
        exists = query.first() is not None
        
        return jsonify({'exists': exists})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'exists': False, 'error': str(e)})