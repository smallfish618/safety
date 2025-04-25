from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, func, desc
from app import db
from app.models.equipment import FireEquipment
from app.models.user import Permission
from datetime import datetime, timedelta
import traceback

equipment_bp = Blueprint('equipment', __name__)

# 添加一个直接路由从根路径到index
@equipment_bp.route('')
@login_required
def root():
    """重定向到索引页面"""
    return redirect(url_for('equipment.index'))

@equipment_bp.route('/')
@equipment_bp.route('/index')
@login_required
def index():

    # 添加在index函数的开头部分
    # 输出所有权限（不仅限于"灭火器和呼吸器"）
    all_permissions = Permission.query.filter_by(user_id=current_user.id).all()
    print(f"用户所有权限数量: {len(all_permissions)}")
    for p in all_permissions:
        print(f"所有权限: {p.operation_type}, 区域ID: {p.area_id}, 权限详情: 查看={p.can_view}, 新增={p.can_add}, 编辑={p.can_edit}, 删除={p.can_delete}")
    
    try:
        # 添加调试日志
        print(f"当前用户: {current_user.username}, ID: {current_user.id}")
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = 15  # 每页显示的记录数
        
        # 获取搜索和筛选参数
        search = request.args.get('search', '')
        filter_type = request.args.get('filter_type', '')
        filter_area = request.args.get('filter_area', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # 基础查询 - 修改权限过滤逻辑
        if current_user.role == 'admin':
            # 管理员可以查看所有区域
            query = FireEquipment.query
            print("用户是管理员，可查看所有消防器材")
        else:
            # 修改这里：获取用户对应类型的所有权限（不只是可查看的）
            permissions = Permission.query.filter_by(
                user_id=current_user.id,
                operation_type='灭火器和呼吸器'
                # 移除can_view=True条件，允许有任何权限的区域都能被查看
            ).all()
            
            #print(f"用户权限数量: {len(permissions)}")
            #for p in permissions:
            #    print(f"权限: {p.operation_type}, 区域ID: {p.area_id}, 类型: {type(p.area_id)}")
            #    print(f"权限详情: 查看={p.can_view}, 新增={p.can_add}, 编辑={p.can_edit}, 删除={p.can_delete}")
            
            # 只要有任何权限（新增、编辑、删除），就应该允许查看
            area_ids = []
            for p in permissions:
                if p.can_view or p.can_add or p.can_edit or p.can_delete:  # 修改这里：只要有任何权限就允许查看
                    # 处理类型转换
                    try:
                        if isinstance(p.area_id, str) and p.area_id.isdigit():
                            area_id = int(p.area_id)
                        else:
                            area_id = p.area_id
                        area_ids.append(area_id)
                    except (ValueError, TypeError):
                        area_ids.append(p.area_id)
            
            print(f"过滤后的区域ID列表: {area_ids}")
            
            if area_ids:
                # 构建灵活的查询条件
                conditions = []
                for area_id in area_ids:
                    conditions.append(FireEquipment.area_code == area_id)
                
                query = FireEquipment.query.filter(or_(*conditions))
            else:
                query = FireEquipment.query.filter_by(id=-1)  # 无数据
        
        # 应用筛选条件
        if filter_type:
            query = query.filter(FireEquipment.equipment_type == filter_type)
        
        if filter_area:
            query = query.filter(FireEquipment.area_name == filter_area)
        
        # 添加生产日期范围筛选
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(FireEquipment.production_date >= from_date)
            except ValueError:
                flash('开始日期格式不正确', 'warning')
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(FireEquipment.production_date <= to_date)
            except ValueError:
                flash('结束日期格式不正确', 'warning')
        
        # 应用搜索条件
        if search:
            search_term = f"%{search}%"
            query = query.filter(or_(
                FireEquipment.equipment_name.ilike(search_term),
                FireEquipment.equipment_type.ilike(search_term),
                FireEquipment.model.ilike(search_term),
                FireEquipment.installation_floor.ilike(search_term),
                FireEquipment.installation_location.ilike(search_term),
                FireEquipment.remark.ilike(search_term)
            ))
        
        # 获取筛选选项
        equipment_types = db.session.query(FireEquipment.equipment_type).distinct().all()
        equipment_types = [t[0] for t in equipment_types if t[0]]
        
        # 获取区域列表
        areas = db.session.query(FireEquipment.area_name).distinct().all()
        areas = [a[0] for a in areas if a[0]]
        
        floors = db.session.query(FireEquipment.installation_floor).distinct().all()
        floors = [f[0] for f in floors if f[0]]
        
        locations = db.session.query(FireEquipment.installation_location).distinct().all()
        locations = [l[0] for l in locations if l[0]]
        
        # 获取总记录数
        total_count = query.count()
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        equipments = pagination.items
        
        # 获取用户权限并转换为更易用的格式
        user_permissions = {}
        if current_user.role != 'admin':
            permissions = Permission.query.filter_by(
                user_id=current_user.id,
                operation_type='灭火器和呼吸器'
            ).all()
            
            # 转换为以area_code为键的字典，便于在模板中快速查找
            # 注意：确保键是字符串类型，以便在模板中统一比较
            for perm in permissions:
                area_id_key = str(perm.area_id)  # 转换为字符串
                user_permissions[area_id_key] = {
                    'can_view': perm.can_view or perm.can_add or perm.can_edit or perm.can_delete,  # 如果有任何权限就允许查看
                    'can_add': perm.can_add,
                    'can_edit': perm.can_edit,
                    'can_delete': perm.can_delete,
                    'area_name': perm.area_name
                }
        
        # 判断用户是否有添加权限（针对任何区域）
        user_can_add = False
        if current_user.role == 'admin':
            user_can_add = True
        else:
            # 检查是否有任何区域的添加权限
            for perm_data in user_permissions.values():
                if perm_data.get('can_add'):
                    user_can_add = True
                    break
        
        # 计算当前日期，用于模板中显示
        current_date = datetime.now().date()
        
        return render_template(
            'equipment/index.html',
            equipments=equipments,
            pagination=pagination,
            equipment_types=equipment_types,
            areas=areas,
            floors=floors,
            locations=locations,
            total_count=total_count,
            search=search,
            filter_type=filter_type,
            filter_area=filter_area,
            date_from=date_from,
            date_to=date_to,
            has_advanced_filters=bool(filter_type or filter_area or date_from or date_to),
            today=current_date,
            user_permissions=user_permissions,
            user_can_add=user_can_add
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'加载消防器材数据时出错: {str(e)}', 'danger')
        return render_template('equipment/index.html', equipments=[], error=str(e))

# 修改添加消防器材的路由函数，添加用户权限传递
@equipment_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """添加消防器材"""
    # 添加权限检查
    user_can_add = False
    if current_user.role == 'admin':
        user_can_add = True
    else:
        # 检查是否有任何区域的添加权限
        permissions = Permission.query.filter_by(
            user_id=current_user.id,
            operation_type='灭火器和呼吸器',
            can_add=True
        ).all()
        user_can_add = len(permissions) > 0
    
    # 如果没有权限就重定向
    if not user_can_add:
        flash('您没有添加消防器材的权限', 'danger')
        return redirect(url_for('equipment.index'))
        
    if request.method == 'POST':
        try:
            # 获取表单数据
            area_code = request.form.get('area_code', type=int)
            area_name = request.form.get('area_name')
            installation_floor = request.form.get('installation_floor')
            installation_location = request.form.get('installation_location')
            equipment_name = request.form.get('equipment_name')
            equipment_type = request.form.get('equipment_type')
            model = request.form.get('model', '')
            weight = request.form.get('weight', '')
            quantity = request.form.get('quantity', type=int, default=1)
            production_date_str = request.form.get('production_date')
            service_life = request.form.get('service_life', '')
            expiration_date = request.form.get('expiration_date', '')
            remark = request.form.get('remark', '')
            
            # 验证必填字段
            required_fields = {
                '区域编码': area_code,
                '区域名称': area_name,
                '楼层': installation_floor,
                '安装位置': installation_location,
                '器材类型': equipment_type,
                '器材名称': equipment_name,
                '数量': quantity,
                '生产日期': production_date_str
            }
            
            missing_fields = []
            for field_name, field_value in required_fields.items():
                if not field_value:
                    missing_fields.append(field_name)
            
            if missing_fields:
                flash(f"以下必填字段不能为空: {', '.join(missing_fields)}", 'danger')
                return redirect(url_for('equipment.add'))
            
            # 处理日期字段
            production_date = None
            if production_date_str:
                try:
                    production_date = datetime.strptime(production_date_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('生产日期格式不正确', 'danger')
                    return redirect(url_for('equipment.add'))
            
            # 创建新器材记录
            equipment = FireEquipment(
                area_code=area_code,
                area_name=area_name,
                installation_floor=installation_floor,
                installation_location=installation_location,
                equipment_name=equipment_name,
                equipment_type=equipment_type,
                model=model,
                weight=weight,
                quantity=quantity,
                production_date=production_date,
                service_life=service_life,
                expiration_date=expiration_date,
                remark=remark
            )
            
            db.session.add(equipment)
            db.session.commit()
            flash('消防器材添加成功', 'success')
            return redirect(url_for('equipment.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加消防器材时出错: {str(e)}', 'danger')
            return redirect(url_for('equipment.add'))
    
    # 获取用户权限
    user_permissions = {}
    if current_user.role != 'admin':
        permissions = Permission.query.filter_by(
            user_id=current_user.id,
            operation_type='灭火器和呼吸器'
        ).all()
        
        # 确保转换为字符串类型的键，避免类型不匹配问题
        for perm in permissions:
            area_id_key = str(perm.area_id)
            user_permissions[area_id_key] = {
                'can_view': perm.can_view,
                'can_add': perm.can_add,
                'can_edit': perm.can_edit,
                'can_delete': perm.can_delete,
                'area_name': perm.area_name
            }
    
    # 从责任人表中获取区域数据 - 修改这部分代码以按区域编码排序
    from app.models.station import ResponsiblePerson
    responsible_areas = db.session.query(
        ResponsiblePerson.area_code,
        ResponsiblePerson.area_name
    ).distinct().order_by(ResponsiblePerson.area_code).all()  # 修改这行，将order_by从area_name改为area_code
    responsible_areas = [{'code': area[0], 'name': area[1]} for area in responsible_areas]
    
    # 获取现有的器材类型，用于下拉选择
    equipment_types = db.session.query(FireEquipment.equipment_type).distinct().all()
    equipment_types = [t[0] for t in equipment_types if t[0]]
    
    # 如果数据库中没有现有类型，提供默认选项
    if not equipment_types:
        equipment_types = ["灭火器", "消防栓", "消防水带", "应急灯", "烟感探测器", "警铃", "灭火毯"]
    
    return render_template(
        'equipment/add.html',
        equipment_types=equipment_types,
        responsible_areas=responsible_areas,
        user_permissions=user_permissions  # 添加这个参数传递用户权限
    )

@equipment_bp.route('/edit/<int:equipment_id>', methods=['GET', 'POST'])
@login_required
def edit(equipment_id):
    """编辑消防器材"""
    equipment = FireEquipment.query.get_or_404(equipment_id)
    
    # 添加权限检查
    if current_user.role != 'admin':
        # 检查用户是否有权限编辑该区域物资
        permission = Permission.query.filter_by(
            user_id=current_user.id,
            area_id=str(equipment.area_code),
            operation_type='灭火器和呼吸器',
            can_edit=True
        ).first()
        
        if not permission:
            flash('您没有权限编辑此消防器材信息', 'danger')
            return redirect(url_for('equipment.index'))
    
    if request.method == 'POST':
        try:
            # 获取表单数据
            equipment.area_code = request.form.get('area_code', type=int)
            equipment.area_name = request.form.get('area_name')
            equipment.installation_floor = request.form.get('installation_floor')
            equipment.installation_location = request.form.get('installation_location')
            equipment.equipment_name = request.form.get('equipment_name')
            equipment.equipment_type = request.form.get('equipment_type')
            equipment.model = request.form.get('model')
            equipment.weight = request.form.get('weight')
            equipment.quantity = request.form.get('quantity', type=int)
            
            # 处理日期字段
            production_date_str = request.form.get('production_date')
            if production_date_str:
                try:
                    equipment.production_date = datetime.strptime(production_date_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('生产日期格式不正确', 'danger')
                    return redirect(url_for('equipment.index'))
            
            equipment.service_life = request.form.get('service_life')
            
            # 修改这里：处理到期日期，确保不会设置为 NULL
            expiration_date_str = request.form.get('expiry_date')
            if expiration_date_str:
                try:
                    equipment.expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('到期日期格式不正确', 'danger')
                    return redirect(url_for('equipment.edit', equipment_id=equipment_id))
            else:
                # 如果没有提供到期日期，则根据生产日期和使用年限计算
                if equipment.production_date and equipment.service_life:
                    # 尝试从使用年限中提取年数
                    import re
                    year_match = re.search(r'(\d+)', equipment.service_life)
                    if year_match:
                        years = int(year_match.group(1))
                        # 计算到期日期 = 生产日期 + 使用年限(年)
                        from datetime import timedelta
                        equipment.expiration_date = equipment.production_date + timedelta(days=365*years)
                    else:
                        # 如果无法提取年数，则使用当前的到期日期
                        # 如果当前也没有设置，则使用生产日期加5年作为默认值
                        if not equipment.expiration_date:
                            equipment.expiration_date = equipment.production_date + timedelta(days=365*5)
                elif equipment.production_date:
                    # 如果只有生产日期没有使用年限，默认使用生产日期加5年
                    from datetime import timedelta
                    equipment.expiration_date = equipment.production_date + timedelta(days=365*5)
                else:
                    # 如果连生产日期都没有，使用当前日期作为到期日期
                    # 这种情况不应该发生，因为生产日期是必填的
                    equipment.expiration_date = datetime.now().date()
            
            equipment.remark = request.form.get('remark')
            
            # 更新时间戳
            equipment.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('消防器材更新成功', 'success')
            return redirect(url_for('equipment.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新消防器材时出错: {str(e)}', 'danger')
    
    # 获取现有的器材类型、楼层和位置，用于下拉选择
    equipment_types = db.session.query(FireEquipment.equipment_type).distinct().all()
    equipment_types = [t[0] for t in equipment_types if t[0]]
    
    floors = db.session.query(FireEquipment.installation_floor).distinct().all()
    floors = [f[0] for f in floors if f[0]]
    
    locations = db.session.query(FireEquipment.installation_location).distinct().all()
    locations = [l[0] for l in locations if l[0]]
    
    return render_template(
        'equipment/edit.html',
        equipment=equipment,
        equipment_types=equipment_types,
        floors=floors,
        locations=locations
    )

@equipment_bp.route('/delete/<int:equipment_id>', methods=['POST'])
@login_required
def delete(equipment_id):
    """删除消防器材"""
    try:
        equipment = FireEquipment.query.get_or_404(equipment_id)
        
        # 添加权限检查
        if current_user.role != 'admin':
            # 检查用户是否有权限删除该区域物资
            permission = Permission.query.filter_by(
                user_id=current_user.id,
                area_id=str(equipment.area_code),
                operation_type='灭火器和呼吸器',
                can_delete=True
            ).first()
            
            if not permission:
                flash('您没有权限删除此消防器材信息', 'danger')
                return redirect(url_for('equipment.index'))
        
        equipment_name = equipment.equipment_name
        
        db.session.delete(equipment)
        db.session.commit()
        flash(f'消防器材 "{equipment_name}" 已成功删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除消防器材时出错: {str(e)}', 'danger')
    
    return redirect(url_for('equipment.index'))

@equipment_bp.route('/detail/<int:equipment_id>')
@login_required
def detail(equipment_id):
    """查看消防器材详情"""
    try:
        # 获取指定ID的器材记录
        equipment = FireEquipment.query.get_or_404(equipment_id)
        
        # 添加权限检查
        if current_user.role != 'admin':
            # 检查用户是否有权限查看该区域物资
            permission = Permission.query.filter_by(
                user_id=current_user.id,
                area_id=str(equipment.area_code),
                operation_type='灭火器和呼吸器',
                can_view=True
            ).first()
            
            if not permission:
                flash('您没有权限查看此消防器材详情', 'danger')
                return redirect(url_for('equipment.index'))
        
        return render_template('equipment/detail.html', equipment=equipment)
    except Exception as e:
        flash(f'查看器材详情时出错: {str(e)}', 'danger')
        return redirect(url_for('equipment.index'))

@equipment_bp.route('/debug_all')
@login_required
def debug_all():
    """显示所有数据用于调试"""
    try:
        # 查询该用户的所有权限，不限制操作类型
        all_permissions = Permission.query.filter_by(user_id=current_user.id).all()
        
        # 按操作类型分组显示权限
        permissions_by_type = {}
        for perm in all_permissions:
            if perm.operation_type not in permissions_by_type:
                permissions_by_type[perm.operation_type] = []
            permissions_by_type[perm.operation_type].append({
                'area_id': perm.area_id,
                'area_name': perm.area_name,
                'can_view': perm.can_view,
                'can_add': perm.can_add,
                'can_edit': perm.can_edit,
                'can_delete': perm.can_delete
            })

        # 获取所有消防器材数据
        all_equipment = FireEquipment.query.all()
        
        # 获取数据库中的区域编码和名称
        areas = db.session.query(
            FireEquipment.area_code,
            FireEquipment.area_name
        ).distinct().all()
        
        area_info = [{'code': a[0], 'name': a[1], 'type': type(a[0]).__name__} for a in areas]
        
        return render_template(
            'equipment/debug.html',
            equipment_count=len(all_equipment),
            areas=area_info,
            all_equipment=all_equipment,
            all_permissions=all_permissions,
            permissions_by_type=permissions_by_type
        )
    except Exception as e:
        traceback.print_exc()
        return f"错误: {str(e)}", 500

@equipment_bp.route('/get_expiry_years')
@login_required
def get_expiry_years():
    """获取设备类型的有效期年数"""
    try:
        equipment_type = request.args.get('type', '')
        if not equipment_type:
            return jsonify({'success': False, 'error': '设备类型不能为空'})
        
        # 查询有效期规则表
        from app.models.station import EquipmentExpiry
        
        # 首先尝试精确匹配
        rule = EquipmentExpiry.query.filter(EquipmentExpiry.item_name == equipment_type).first()
        
        # 如果精确匹配失败，尝试模糊匹配
        if not rule:
            rules = EquipmentExpiry.query.all()
            for r in rules:
                if equipment_type in r.item_name or r.item_name in equipment_type:
                    rule = r
                    break
        
        if rule and rule.normal_expiry > 0:
            return jsonify({
                'success': True, 
                'expiry_years': rule.normal_expiry,
                'item_name': rule.item_name
            })
        else:
            return jsonify({
                'success': False, 
                'error': '未找到该设备类型的有效期规则或该设备长期有效'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
