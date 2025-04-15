from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from sqlalchemy import or_, func
from app import db
from app.models.station import FireStation
from app.models.user import Permission

station_bp = Blueprint('station', __name__)

# 修改index函数，将权限检查移到最前面

@station_bp.route('/index')
@login_required
def index():
    try:
        # 权限检查先行，没有权限直接重定向到无权限页面
        if current_user.role != 'admin':
            permissions = Permission.query.filter_by(
                user_id=current_user.id,
                operation_type='微型消防站',
                can_view=True
            ).all()
            
            # 如果没有微型站的权限，立即重定向至无权限页面
            if not permissions:
                return redirect(url_for('common.no_permission', module='微型消防站物资表'))
        
        # 有权限才继续执行后续代码
        page = request.args.get('page', 1, type=int)
        per_page = 15  # 每页显示15条记录
        
        # 获取搜索和筛选参数
        search = request.args.get('search', '')
        filter_area = request.args.get('filter_area', '')  # 使用filter_area作为参数名
        filter_item = request.args.get('filter_item', '')  # 使用filter_item作为参数名
        filter_manufacturer = request.args.get('filter_manufacturer', '')  # 使用filter_manufacturer作为参数名
        
        # 基础查询
        if current_user.role == 'admin':
            # 管理员可以查看所有区域
            query = FireStation.query
        else:
            # 普通用户只能查看有权限的区域
            permissions = Permission.query.filter_by(
                user_id=current_user.id,
                operation_type='微型消防站',
                can_view=True
            ).all()
            area_ids = [p.area_id for p in permissions]
            if area_ids:
                query = FireStation.query.filter(FireStation.area_code.in_(area_ids))
            else:
                query = FireStation.query.filter_by(id=-1)  # 无数据
        
        # 应用筛选条件
        if filter_area:
            query = query.filter(FireStation.area_name == filter_area)
        if filter_item:
            query = query.filter(FireStation.item_name == filter_item)
        if filter_manufacturer:
            query = query.filter(FireStation.manufacturer == filter_manufacturer)
        
        # 应用搜索条件
        if search:
            search_term = f"%{search}%"
            query = query.filter(or_(
                FireStation.area_name.ilike(search_term),
                FireStation.item_name.ilike(search_term),
                FireStation.manufacturer.ilike(search_term),
                FireStation.model.ilike(search_term),
                FireStation.certificate.ilike(search_term),
                FireStation.certificate_no.ilike(search_term),
                FireStation.remark.ilike(search_term)
            ))
        
        # 获取唯一值列表用于筛选下拉菜单
        area_list = db.session.query(FireStation.area_name).distinct().order_by(FireStation.area_name).all()
        area_list = [area[0] for area in area_list if area[0]]
        
        item_list = db.session.query(FireStation.item_name).distinct().order_by(FireStation.item_name).all()
        item_list = [item[0] for item in item_list if item[0]]
        
        manufacturer_list = db.session.query(FireStation.manufacturer).distinct().order_by(FireStation.manufacturer).all()
        manufacturer_list = [m[0] for m in manufacturer_list if m[0]]
        
        # 获取总记录数
        total_count = query.count()
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 修改这里：将stations重命名为equipments以匹配模板中的变量名
        equipments = pagination.items
        
        # 判断是否有高级筛选条件
        has_advanced_filters = bool(filter_area or filter_item or filter_manufacturer)
        
        # 获取用户权限并转换为更易用的格式
        user_permissions = {}
        if current_user.role != 'admin':
            permissions = Permission.query.filter_by(
                user_id=current_user.id,
                operation_type='微型消防站'
            ).all()
            
            # 转换为以area_code为键的字典，便于在模板中快速查找
            for perm in permissions:
                user_permissions[perm.area_id] = {
                    'can_view': perm.can_view,
                    'can_add': perm.can_add,
                    'can_edit': perm.can_edit,
                    'can_delete': perm.can_delete,
                    'area_name': perm.area_name
                }
        
        # 确保我们只返回用户有权查看的记录
        if current_user.role != 'admin':
            viewable_areas = [area_id for area_id, perms in user_permissions.items() if perms.get('can_view')]
            if not viewable_areas:
                equipments = []
                pagination = None
                total_count = 0
            else:
                query = query.filter(FireStation.area_code.in_(viewable_areas))
        
        # 从ResponsiblePerson表中获取所有区域编码和区域名称（用于添加物资时选择）
        from app.models.station import ResponsiblePerson
        responsible_areas = db.session.query(
            ResponsiblePerson.area_code, 
            ResponsiblePerson.area_name
        ).distinct().order_by(ResponsiblePerson.area_code).all()
        
        # 将区域数据转换为列表，包含代码和名称
        responsible_area_list = [{'code': area[0], 'name': area[1]} for area in responsible_areas if area[0] and area[1]]
        
        # 判断用户是否有添加权限（针对任何区域）
        user_can_add = False
        if current_user.role != 'admin':
            # 检查是否有任何区域的添加权限
            for perm_data in user_permissions.values():
                if perm_data.get('can_add'):
                    user_can_add = True
                    break

        # 在user_permissions构建部分后添加
        print(f"构建的用户权限数据: {user_permissions}")
        print(f"responsible_area_list中的区域: {[(area['code'], area['name']) for area in responsible_area_list]}")

        # 确保将权限字典的键统一为字符串类型
        user_permissions_str = {}
        for key, value in user_permissions.items():
            user_permissions_str[str(key)] = value
        user_permissions = user_permissions_str

        print(f"转换后的用户权限数据: {user_permissions}")

        # 获取有效期表中的所有物资名称，用于添加物资下拉菜单
        from app.models.station import EquipmentExpiry
        item_names_list = db.session.query(EquipmentExpiry.item_name).distinct().order_by(EquipmentExpiry.item_name).all()
        item_names_list = [item[0] for item in item_names_list if item[0]]
        
        return render_template(
            'station/inventory.html', 
            equipments=equipments,  # 修改这里：变量名从stations改为equipments
            pagination=pagination,
            area_list=area_list,
            item_list=item_list,
            manufacturer_list=manufacturer_list,
            total_count=total_count,
            total_items=total_count,  # 添加这个变量以兼容模板中的另一个变量名
            search=search,
            area=filter_area,
            item=filter_item,
            manufacturer=filter_manufacturer,
            # 添加这些变量以确保模板能正确获取筛选条件
            filter_area=filter_area,
            filter_item=filter_item,
            filter_manufacturer=filter_manufacturer,
            areas=area_list,
            items=item_list,
            manufacturers=manufacturer_list,
            has_advanced_filters=has_advanced_filters,
            user_permissions=user_permissions,  # 添加这个参数
            responsible_area_list=responsible_area_list,  # 添加负责人区域列表
            user_can_add=user_can_add,  # 添加此参数用于控制添加按钮
            item_names_list=item_names_list  # 添加这个新参数，用于物资下拉菜单
        )
    except Exception as e:
        import traceback
        traceback.print_exc()  # 添加错误追踪以便调试
        flash(f'发生错误: {str(e)}')
        return render_template('station/inventory.html', equipments=[], error=str(e))

# 添加新的路由处理函数来处理物资添加功能

@station_bp.route('/add_station', methods=['POST'])
@login_required
def add_station():
    """添加微型消防站物资信息"""
    try:
        # 获取表单数据
        area_code = request.form.get('area_code')
        area_name = request.form.get('area_name')
        item_name = request.form.get('item_name')
        manufacturer = request.form.get('manufacturer')
        model = request.form.get('model')
        quantity = request.form.get('quantity')
        production_date_str = request.form.get('production_date')
        remark = request.form.get('remark')
        
        # 验证必要字段
        if not all([area_code, area_name, item_name, quantity]):
            flash('必填字段不能为空', 'danger')
            return redirect(url_for('station.index'))
            
        # 处理日期字段
        production_date = None
        if production_date_str:
            try:
                from datetime import datetime
                production_date = datetime.strptime(production_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('生产日期格式不正确', 'danger')
                return redirect(url_for('station.index'))
        
        # 强化权限检查逻辑
        if current_user.role != 'admin':
            # 检查用户是否有权限在该区域添加物资
            permission = Permission.query.filter_by(
                user_id=current_user.id,
                area_id=area_code,
                operation_type='微型消防站',
                can_add=True
            ).first()
            
            if not permission:
                flash(f'您没有权限在区域 "{area_name}" 添加物资', 'danger')
                return redirect(url_for('station.index'))
        
        # 创建新物资记录
        new_station = FireStation(
            area_code=area_code,
            area_name=area_name,
            item_name=item_name,
            manufacturer=manufacturer,
            model=model,
            quantity=quantity,
            production_date=production_date,
            remark=remark
        )
        
        # 保存到数据库
        db.session.add(new_station)
        db.session.commit()
        
        flash(f'在区域 "{area_name}" 成功添加物资 "{item_name}"', 'success')
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"添加物资时出错: {str(e)}")
        traceback.print_exc()
        flash(f'添加物资时出错: {str(e)}', 'danger')
        
    return redirect(url_for('station.index'))

# 添加编辑物资的路由处理函数

@station_bp.route('/edit/<int:equipment_id>', methods=['POST'])
@login_required
def edit_station(equipment_id):
    """编辑物资信息"""
    try:
        # 获取要编辑的物资
        equipment = FireStation.query.get_or_404(equipment_id)
        
        # 检查权限
        if current_user.role != 'admin':
            # 检查用户是否有权限编辑该区域物资
            permission = Permission.query.filter_by(
                user_id=current_user.id,
                area_id=equipment.area_code,
                operation_type='微型消防站',
                can_edit=True
            ).first()
            
            if not permission:
                flash('您没有权限编辑此物资信息', 'danger')
                return redirect(url_for('station.index'))
        
        # 获取表单数据
        area_code = request.form.get('area_code')
        area_name = request.form.get('area_name')
        item_name = request.form.get('item_name')
        manufacturer = request.form.get('manufacturer')
        model = request.form.get('model')
        quantity = request.form.get('quantity')
        production_date_str = request.form.get('production_date')
        remark = request.form.get('remark')
        
        # 验证必要字段
        if not all([area_code, area_name, item_name, quantity]):
            flash('必填字段不能为空', 'danger')
            return redirect(url_for('station.index'))
        
        # 处理日期字段
        production_date = None
        if production_date_str:
            try:
                from datetime import datetime
                production_date = datetime.strptime(production_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('生产日期格式不正确', 'danger')
                return redirect(url_for('station.index'))
        
        # 更新物资信息
        equipment.area_code = area_code
        equipment.area_name = area_name
        equipment.item_name = item_name
        equipment.manufacturer = manufacturer
        equipment.model = model
        equipment.quantity = quantity
        equipment.production_date = production_date
        equipment.remark = remark
        
        # 保存到数据库
        db.session.commit()
        
        flash('物资信息更新成功', 'success')
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"编辑物资时出错: {str(e)}")
        traceback.print_exc()
        flash(f'编辑物资时出错: {str(e)}', 'danger')
        
    return redirect(url_for('station.index'))

# 添加删除物资的路由处理函数

@station_bp.route('/delete/<int:equipment_id>', methods=['POST'])
@login_required
def delete_station(equipment_id):
    """删除物资信息"""
    try:
        # 获取要删除的物资记录
        equipment = FireStation.query.get_or_404(equipment_id)
        
        # 检查权限
        if current_user.role != 'admin':
            # 检查用户是否有权限删除该区域物资
            permission = Permission.query.filter_by(
                user_id=current_user.id,
                area_id=equipment.area_code,
                operation_type='微型消防站',
                can_delete=True
            ).first()
            
            if not permission:
                flash('您没有权限删除此物资信息', 'danger')
                return redirect(url_for('station.index'))
        
        # 记录要删除的物资信息，用于显示确认消息
        item_name = equipment.item_name
        area_name = equipment.area_name
        
        # 从数据库删除
        db.session.delete(equipment)
        db.session.commit()
        
        # 显示成功消息
        flash(f'物资【{item_name}】已从【{area_name}】成功删除', 'success')
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"删除物资时出错: {str(e)}")
        traceback.print_exc()
        flash(f'删除物资时出错: {str(e)}', 'danger')
    
    # 删除后重定向回物资列表页
    return redirect(url_for('station.index'))

# 添加物资详情查看路由

@station_bp.route('/detail/<int:equipment_id>')
@login_required
def detail(equipment_id):
    """查看物资详情"""
    try:
        # 获取指定ID的物资
        equipment = FireStation.query.get_or_404(equipment_id)
        
        # 添加权限检查
        if current_user.role != 'admin':
            # 检查用户是否有权限查看该区域物资
            permission = Permission.query.filter_by(
                user_id=current_user.id,
                area_id=equipment.area_code,
                operation_type='微型消防站',
                can_view=True
            ).first()
            
            if not permission:
                flash('您没有权限查看此物资详情', 'danger')
                return redirect(url_for('station.index'))
        
        return render_template('station/detail.html', equipment=equipment)
    except Exception as e:
        flash(f'查看物资详情时出错: {str(e)}', 'danger')
        return redirect(url_for('station.index'))