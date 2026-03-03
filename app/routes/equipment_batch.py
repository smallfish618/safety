from flask import Blueprint, render_template, request, jsonify, current_app, send_file, redirect, url_for, flash, session
from app.models.equipment import FireEquipment
from app import db
from flask_login import login_required
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
import os
from datetime import datetime
import uuid
import xlsxwriter
from sqlalchemy import or_, func

# 创建蓝图
equipment_batch_bp = Blueprint('equipment_batch', __name__)

# 临时文件存储目录
UPLOAD_FOLDER = 'app/static/uploads/temp'
TEMPLATE_FOLDER = 'app/static/templates'

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMPLATE_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls'}

# 批量管理页面
@equipment_batch_bp.route('/batch-manage')
@login_required
def batch_manage():
    # 获取所有设备类型，用于筛选
    equipment_types = db.session.query(FireEquipment.equipment_type).distinct().all()
    categories = [et[0] for et in equipment_types if et[0]]
    
    # 获取所有区域名称，用于筛选
    areas = db.session.query(FireEquipment.area_name).distinct().all()
    area_names = [area[0] for area in areas if area[0]]
    
    # 检查模型属性
    has_production_date = hasattr(FireEquipment, 'production_date')
    has_expiry_date = hasattr(FireEquipment, 'expiry_date')
    
    return render_template('equipment/batch_manage.html', 
                          categories=categories, 
                          area_names=area_names,
                          has_production_date=has_production_date,
                          has_expiry_date=has_expiry_date)

# 获取设备数据（支持搜索和筛选）
@equipment_batch_bp.route('/api/equipment-data')
@login_required
def get_equipment_data():
    # 获取查询参数
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    area = request.args.get('area', '')
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 构建查询
    query = FireEquipment.query
    
    # 应用搜索条件
    if search:
        query = query.filter(or_(
            FireEquipment.equipment_type.contains(search),
            FireEquipment.model.contains(search),
            FireEquipment.area_name.contains(search)
        ))
    
    # 应用筛选条件
    if category:
        query = query.filter(FireEquipment.equipment_type == category)
    
    if area:
        query = query.filter(FireEquipment.area_name == area)
    
    # 获取总记录数
    total = query.count()
    
    # 应用分页
    equipments = query.order_by(FireEquipment.id).offset((page-1)*per_page).limit(per_page).all()
    
    # 查询设备数据 - 修改查询以包含installation_floor和remark字段
    query = db.session.query(
        FireEquipment.id,
        FireEquipment.equipment_type,
        FireEquipment.equipment_name,
        FireEquipment.model,
        FireEquipment.weight,
        FireEquipment.quantity,
        FireEquipment.area_name,
        FireEquipment.area_code,
        FireEquipment.installation_location,
        FireEquipment.production_date,
        FireEquipment.installation_floor,  # 添加楼层字段
        FireEquipment.remark  # 添加备注字段
    )

    # 格式化结果
    result = []
    for equipment in equipments:
        item = {
            'id': equipment.id,
            'equipment_type': equipment.equipment_type,
            'equipment_name': equipment.equipment_name,  # 确保包含此字段
            'model': equipment.model,
            'weight': equipment.weight,
            'quantity': equipment.quantity,
            'area_name': equipment.area_name,
            'installation_location': equipment.installation_location,
            'installation_floor': equipment.installation_floor,
            'remark': equipment.remark
        }
        
        # 安全地添加可能存在的属性
        if hasattr(equipment, 'production_date') and equipment.production_date:
            item['production_date'] = equipment.production_date.strftime('%Y-%m-%d')
        else:
            item['production_date'] = ''
            
        if hasattr(equipment, 'expiry_date') and equipment.expiry_date:
            item['expiry_date'] = equipment.expiry_date.strftime('%Y-%m-%d')
        else:
            item['expiry_date'] = ''
        
        result.append(item)
    
    # 返回分页信息和数据
    response = jsonify({
        'data': result,
        'pagination': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page  # 向上取整计算总页数
        }
    })
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# 批量更新设备
@equipment_batch_bp.route('/api/batch-update', methods=['POST'])
@login_required
def batch_update():
    data = request.json
    equipment_ids = data.get('ids', [])
    updates = data.get('updates', {})
    
    try:
        for equipment_id in equipment_ids:
            equipment = FireEquipment.query.get(equipment_id)
            if equipment:
                # 更新允许的字段
                if 'equipment_type' in updates:
                    equipment.equipment_type = updates['equipment_type']
                if 'model' in updates:
                    equipment.model = updates['model']
                if 'weight' in updates and updates['weight']:
                    equipment.weight = float(updates['weight'])
                if 'quantity' in updates and updates['quantity']:
                    equipment.quantity = int(updates['quantity'])
                
                # 如果模型有生产日期字段
                if hasattr(equipment, 'production_date') and 'production_date' in updates and updates['production_date']:
                    equipment.production_date = datetime.strptime(updates['production_date'], '%Y-%m-%d').date()
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'成功更新 {len(equipment_ids)} 条记录'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量更新出错: {str(e)}")
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500

# 批量删除设备
@equipment_batch_bp.route('/api/batch-delete', methods=['POST'])
@login_required
def batch_delete():
    data = request.json
    equipment_ids = data.get('ids', [])
    
    try:
        deleted_count = 0
        for equipment_id in equipment_ids:
            equipment = FireEquipment.query.get(equipment_id)
            if equipment:
                db.session.delete(equipment)
                deleted_count += 1
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'成功删除 {deleted_count} 条记录'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量删除出错: {str(e)}")
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

# 下载Excel模板
@equipment_batch_bp.route('/download-template')
@login_required
def download_template():
    # 修正模板路径 - 使用os.path.join确保路径分隔符正确
    template_path = os.path.join(current_app.root_path, 'static', 'templates', '消防器材批量导入模板.xlsx')
    
    # 添加调试日志
    current_app.logger.info(f"尝试下载模板文件，路径: {template_path}")
    
    # 检查文件是否存在，如果不存在，创建一个新的模板文件
    if not os.path.exists(template_path):
        current_app.logger.info(f"模板文件不存在，创建新模板")
        return generate_template()
    
    return send_file(template_path, 
                     as_attachment=True,
                     download_name='消防器材批量导入模板.xlsx')

# 生成模板文件
@equipment_batch_bp.route('/generate-template')
@login_required
def generate_template():
    template_path = os.path.join(current_app.root_path, 'static', 'templates', '消防器材批量导入模板.xlsx')
    
    # 确保目录存在
    os.makedirs(os.path.dirname(template_path), exist_ok=True)
    
    try:
        # 创建工作簿
        workbook = xlsxwriter.Workbook(template_path)
        worksheet = workbook.add_worksheet('消防器材导入')
        
        # 添加表头和说明
        worksheet.merge_range('A1:L1', '消防器材批量导入模板 - 带(*)的为必填字段', workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter', 
            'bg_color': '#4472C4', 'font_color': 'white', 'font_size': 14
        }))
        
        # 添加表头 - 使用实际的表格所需字段
        headers = ['区域名称(*)', '楼层(*)', '安装位置(*)', '设备类型', '器材名称(*)', '品牌型号', '重量', '数量(*)', 
                  '生产日期(YYYY/MM/DD)(*)', '使用年限', '有效期时间', '备注']
        
        # 设置加粗格式用于表头
        bold_format = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#D9E1F2', 'border': 1})
        
        # 写入表头
        for col_num, header in enumerate(headers):
            worksheet.write(1, col_num, header, bold_format)
        
        # 设置列宽
        worksheet.set_column(0, len(headers)-1, 15)  # 统一设置列宽为15
        
        # 添加一行示例数据
        example_data = ['一层', 'A区', '走廊', '灭火器', '干粉灭火器', 'MF/ABC4', '4', '1', '2024-01-01', '5', '2029-01-01', '示例数据']
        for col_num, value in enumerate(example_data):
            worksheet.write(2, col_num, value)
        
        # 保存工作簿
        workbook.close()
        
        current_app.logger.info(f"成功创建模板文件: {template_path}")
        return send_file(template_path, 
                        as_attachment=True,
                        download_name='消防器材批量导入模板.xlsx')
    except Exception as e:
        current_app.logger.error(f"创建模板文件失败: {str(e)}")
        return jsonify({'error': f'创建模板文件失败: {str(e)}'}), 500

# 上传Excel文件
@equipment_batch_bp.route('/upload-excel', methods=['POST'])
@login_required
def upload_excel():
    if 'file' not in request.files:
        flash('没有选择文件', 'danger')
        return redirect(url_for('equipment_batch.batch_manage'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('没有选择文件', 'danger')
        return redirect(url_for('equipment_batch.batch_manage'))
    
    if file and allowed_file(file.filename):
        # 生成唯一文件名
        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # 读取Excel数据并解析
        try:
            df = pd.read_excel(filepath)
            
            # 记录读取到的列，用于调试
            current_app.logger.info(f"Excel文件包含的列: {list(df.columns)}")
            
            # 创建列名映射表，支持多种常见的列名格式
            column_mappings = {
                # 标准格式 -> 多种可能的格式
                '器材名称(*)': ['器材名称(*)', '器材名称', '设备名称', '消防器材名称'],
                '数量(*)': ['数量(*)', '数量', '设备数量'],
                '区域名称(*)': ['区域名称(*)', '区域(*)', '区域', '区域名称', '所在区域'],
                '安装位置(*)': ['安装位置(*)', '设备放置地点(*)', '设备放置地点', '位置', '安装位置'],
                '楼层(*)': ['楼层(*)', '楼层', '所在楼层'],
                '设备类型(*)': ['设备类型(*)', '设备类型', '器材类型'],
                # 修复生产日期映射 - 扩展可能的格式
                '生产日期(*)': ['生产日期(*)', '生产日期(YYYY/MM/DD)(*)', '生产日期(YYYY-MM-DD)(*)', 
                            '生产日期', '生产日期(YYYY/MM/DD)', '生产日期(YYYY-MM-DD)', 
                            '制造日期', '出厂日期']
            }
            
            # 尝试重命名列，从而适应不同的输入格式
            renamed_columns = {}
            for std_col, possible_names in column_mappings.items():
                # 判断是否需要重命名
                for possible_name in possible_names:
                    if possible_name in df.columns and possible_name != std_col:
                        renamed_columns[possible_name] = std_col
                        current_app.logger.info(f"将列 '{possible_name}' 重命名为 '{std_col}'")
                        break
            
            if renamed_columns:
                df = df.rename(columns=renamed_columns)
                current_app.logger.info(f"重命名后的列: {list(df.columns)}")
            
            # 更新必填字段列表
            required_columns = ['区域名称(*)', '楼层(*)', '安装位置(*)', '设备类型(*)', '器材名称(*)', '数量(*)', '生产日期(*)']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                # 记录更详细的错误信息
                input_columns = list(df.columns)
                current_app.logger.error(f"Excel列名不匹配。期望: {required_columns}, 实际: {input_columns}")
                
                os.remove(filepath)  # 删除临时文件
                flash(f'Excel文件缺少必填列: {", ".join(missing_columns)}。请使用标准模板或确保列名正确。', 'danger')
                flash(f'请点击"下载Excel模板"获取标准格式模板。', 'info')
                return redirect(url_for('equipment_batch.batch_manage'))
            
            # 检查并清理数据
            df = df.replace(np.nan, '', regex=True)
            
            # 从负责人表获取区域代码映射
            try:
                # 假设有一个AreaManager表包含区域代码和区域名称
                from app.models.manager import AreaManager
                area_manager_map = {}
                area_managers = db.session.query(AreaManager.area_name, AreaManager.area_code).distinct().all()
                for manager in area_managers:
                    if manager[0] and manager[1]:
                        area_manager_map[manager[0]] = manager[1]
                current_app.logger.info(f"从负责人表获取到区域代码映射: {area_manager_map}")
            except ImportError:
                # 如果没有AreaManager模型，则使用设备表中已有的映射
                area_manager_map = {}
                current_app.logger.warning("找不到负责人表模型，将使用设备表获取区域代码映射")
            
            # 备用：从设备表获取区域代码映射
            area_equipment_map = {}
            area_equipments = db.session.query(FireEquipment.area_name, FireEquipment.area_code).distinct().all()
            for area in area_equipments:
                if area[0] and area[1]:
                    area_equipment_map[area[0]] = area[1]
                    
            # 合并两个映射，优先使用负责人表的映射
            area_code_map = {**area_equipment_map, **area_manager_map}
            current_app.logger.info(f"最终区域代码映射: {area_code_map}")
            
            # 为数据添加区域代码字段
            enhanced_data = []
            for record in df.to_dict('records'):
                # 获取区域名称
                area_name_key = next((key for key in record.keys() if '区域' in key and '名称' in key), None)
                if not area_name_key:
                    area_name_key = next((key for key in record.keys() if '区域' in key), None)
                
                if area_name_key and record[area_name_key]:
                    area_name = record[area_name_key]
                    # 获取区域代码，如果不存在则使用区域名前两个字符
                    area_code = area_code_map.get(area_name, area_name[:2] if area_name else 'UN')
                    record['区域代码'] = area_code
                else:
                    record['区域代码'] = 'UN'  # 未知区域标识
                
                enhanced_data.append(record)
            
            # 列名顺序调整，确保区域代码在前面
            all_columns = ['区域代码'] + list(df.columns)
            
            # 保存文件路径到session
            session['import_filepath'] = filepath
            
            return render_template('equipment/batch_preview.html', 
                                  data=enhanced_data,
                                  columns=all_columns,
                                  filepath=filepath)
            
        except Exception as e:
            current_app.logger.error(f"解析Excel出错: {str(e)}")
            flash(f'解析Excel文件失败: {str(e)}', 'danger')
            return redirect(url_for('equipment_batch.batch_manage'))
    else:
        flash('仅支持上传Excel文件(.xlsx, .xls)', 'danger')
        return redirect(url_for('equipment_batch.batch_manage'))

# 确认导入Excel数据
@equipment_batch_bp.route('/confirm-import', methods=['POST'])
@login_required
def confirm_import():
    filepath = request.form.get('filepath')
    
    if not filepath or not os.path.exists(filepath):
        flash('文件不存在或已过期', 'danger')
        return redirect(url_for('equipment_batch.batch_manage'))
    
    try:
        # 读取Excel数据
        df = pd.read_excel(filepath)
        df = df.replace(np.nan, '', regex=True)
        
        # 应用列映射
        column_mappings = {
            '器材名称(*)': ['器材名称(*)', '器材名称', '设备名称', '消防器材名称'],
            '数量(*)': ['数量(*)', '数量', '设备数量'],
            '区域名称(*)': ['区域名称(*)', '区域(*)', '区域', '区域名称', '所在区域'],
            '安装位置(*)': ['安装位置(*)', '设备放置地点(*)', '设备放置地点', '位置', '安装位置']
        }
        
        # 尝试重命名列
        renamed_columns = {}
        for std_col, possible_names in column_mappings.items():
            for possible_name in possible_names:
                if possible_name in df.columns and possible_name != std_col:
                    renamed_columns[possible_name] = std_col
                    break
        
        if renamed_columns:
            df = df.rename(columns=renamed_columns)
        
        # 导入数据
        success_count = 0
        error_count = 0
        errors = []
        
        # 获取区域代码映射
        area_code_map = {}
        areas = db.session.query(FireEquipment.area_name, FireEquipment.area_code).distinct().all()
        for area in areas:
            if area[0] and area[1]:
                area_code_map[area[0]] = area[1]
        
        # 调试信息
        current_app.logger.info(f"可用区域代码映射: {area_code_map}")
        
        for index, row in df.iterrows():
            try:
                # 必填字段检查
                area_name_key = next((key for key in row.keys() if key in ['区域名称(*)', '区域(*)', '区域', '区域名称', '所在区域']), None)
                if not area_name_key or not row[area_name_key]:
                    errors.append(f"行 {index+2}: 缺少区域名称")
                    error_count += 1
                    continue
                
                area_name = row[area_name_key]
                
                # 获取区域代码 - 如果映射表没有，则使用区域名称的前两个字符作为代码
                area_code = area_code_map.get(area_name)
                if not area_code:
                    area_code = area_name[:2] if area_name else 'UN'  # UN代表未知区域
                    current_app.logger.info(f"为区域'{area_name}'创建新代码: {area_code}")
                
                # 获取其他必填字段
                # 在获取其他必填字段部分添加设备类型查找
                equipment_name_key = next((key for key in row.keys() if key in ['器材名称(*)', '器材名称', '设备名称', '消防器材名称']), None)
                equipment_type_key = next((key for key in row.keys() if key in ['设备类型(*)', '设备类型', '器材类型']), None)  # 添加设备类型字段查找
                quantity_key = next((key for key in row.keys() if key in ['数量(*)', '数量', '设备数量']), None)
                location_key = next((key for key in row.keys() if key in ['安装位置(*)', '设备放置地点(*)', '设备放置地点', '位置', '安装位置']), None)
                
                # 检查所有必填字段，包括设备类型
                if (not equipment_name_key or not row[equipment_name_key] or 
                    not equipment_type_key or not row[equipment_type_key] or 
                    not quantity_key or not row[quantity_key] or 
                    not location_key or not row[location_key]):
                    errors.append(f"行 {index+2}: 缺少必填字段")
                    error_count += 1
                    continue
                
                # 创建设备记录 - 确保设置area_code字段
                equipment = FireEquipment(
                    area_code=area_code,
                    area_name=area_name,
                    equipment_type=row[equipment_type_key],
                    equipment_name=row[equipment_name_key],  
                    installation_location=row[location_key],
                    quantity=int(row[quantity_key])
                )
                
                # 设置可选字段
                for col_name, value in row.items():
                    if '型号' in col_name and value:
                        equipment.model = str(value)
                    elif '重量' in col_name and value:
                        try:
                            equipment.weight = float(value)
                        except (ValueError, TypeError):
                            pass
                    elif '楼层' in col_name and value:
                        equipment.installation_floor = str(value)
                    elif ('使用年限' in col_name or '年限' in col_name) and value:
                        try:
                            equipment.service_life = int(value)
                        except (ValueError, TypeError):
                            # 如果转换失败，设置默认值
                            equipment.service_life = 5  # 默认使用年限5年
                            current_app.logger.warning(f"无法解析使用年限'{value}'，设置默认值5")
                
                # 处理生产日期
                production_date_fields = [col for col in row.keys() if '生产日期' in col or '制造日期' in col or '出厂日期' in col]
                for field in production_date_fields:
                    if row[field]:
                        try:
                            date_value = row[field]
                            if isinstance(date_value, pd.Timestamp):
                                equipment.production_date = date_value.date()
                            else:
                                # 尝试多种日期格式
                                try:
                                    equipment.production_date = datetime.strptime(str(date_value), '%Y-%m-%d').date()
                                except ValueError:
                                    try:
                                        equipment.production_date = datetime.strptime(str(date_value), '%Y/%m/%d').date()
                                    except ValueError:
                                        equipment.production_date = datetime.strptime(str(date_value), '%d/%m/%Y').date()
                            break
                        except Exception as date_error:
                            current_app.logger.warning(f"解析生产日期'{date_value}'失败: {str(date_error)}")
                            pass
                
                # 处理有效期
                expiry_date_fields = [col for col in row.keys() if '有效期' in col or '到期' in col]
                for field in expiry_date_fields:
                    if row[field]:
                        try:
                            date_value = row[field]
                            if isinstance(date_value, pd.Timestamp):
                                equipment.expiration_date = date_value.date()
                            else:
                                equipment.expiration_date = datetime.strptime(str(date_value), '%Y-%m-%d').date()
                            break
                        except:
                            pass
                
                # 确保设置service_life字段
                if not hasattr(equipment, 'service_life') or equipment.service_life is None:
                    # 如果有生产日期和有效期，尝试计算使用年限
                    if hasattr(equipment, 'production_date') and equipment.production_date and \
                    hasattr(equipment, 'expiration_date') and equipment.expiration_date:
                        try:
                            delta = equipment.expiration_date - equipment.production_date
                            years = delta.days // 365
                            if years > 0:
                                equipment.service_life = years
                            else:
                                equipment.service_life = 5  # 默认5年
                        except Exception as e:
                            equipment.service_life = 5  # 无法计算时使用默认值
                    else:
                        equipment.service_life = 5  # 默认5年

                db.session.add(equipment)
                success_count += 1
                
            except Exception as e:
                errors.append(f"行 {index+2}: {str(e)}")
                current_app.logger.error(f"导入第{index+2}行错误: {str(e)}")
                error_count += 1
        
        # 提交事务
        db.session.commit()
        
        # 删除临时文件
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # 显示结果
        if error_count > 0:
            flash(f'导入完成，成功: {success_count}条，失败: {error_count}条。错误详情: {"; ".join(errors[:5])}{"..." if len(errors) > 5 else ""}', 'warning')
        else:
            flash(f'成功导入 {success_count} 条记录', 'success')
        
        return redirect(url_for('equipment_batch.batch_manage'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"导入数据出错: {str(e)}")
        flash(f'导入失败: {str(e)}', 'danger')
        return redirect(url_for('equipment_batch.batch_manage'))
    
#多记录批量更新接口
@equipment_batch_bp.route('/api/batch-update-multiple', methods=['POST'])
@login_required
def batch_update_multiple():
    # 添加调试输出
    current_app.logger.info("====== 批量更新API被调用 ======")
    current_app.logger.info(f"请求头: {dict(request.headers)}")
    current_app.logger.info(f"请求方法: {request.method}")
    current_app.logger.info(f"内容类型: {request.content_type}")
    
    try:
        # 检查请求数据
        data = request.get_json()
        if not data:
            current_app.logger.error("无法解析JSON数据")
            return jsonify({'success': False, 'message': '请求数据格式错误，无法解析JSON'}), 400
            
        current_app.logger.info(f"请求数据: {data}")
        
        updates_list = data.get('updates', [])
        current_app.logger.info(f"更新列表: {updates_list}")
        
        success_count = 0
        
        for update_item in updates_list:
            equipment_id = update_item.get('id')
            changes = update_item.get('changes', {})
            
            current_app.logger.info(f"处理设备ID: {equipment_id}, 变更: {changes}")
            
            equipment = FireEquipment.query.get(equipment_id)
            if equipment and changes:
                # 更新允许的字段
                for field, value in changes.items():
                    if field == 'equipment_name':
                        equipment.equipment_name = value
                        current_app.logger.info(f"更新equipment_name为: {value}")
                    elif field == 'model':
                        equipment.model = value
                        current_app.logger.info(f"更新model为: {value}")
                    elif field == 'weight' and value:
                        try:
                            equipment.weight = float(value)
                            current_app.logger.info(f"更新weight为: {value}")
                        except ValueError:
                            current_app.logger.error(f"weight值转换失败: {value}")
                    elif field == 'quantity' and value:
                        try:
                            equipment.quantity = int(value)
                            current_app.logger.info(f"更新quantity为: {value}")
                        except ValueError:
                            current_app.logger.error(f"quantity值转换失败: {value}")
                    elif field == 'area_name':
                        equipment.area_name = value
                        current_app.logger.info(f"更新area_name为: {value}")
                    elif field == 'installation_location':
                        equipment.installation_location = value
                        current_app.logger.info(f"更新installation_location为: {value}")
                    elif field == 'production_date' and value and hasattr(equipment, 'production_date'):
                        try:
                            equipment.production_date = datetime.strptime(value, '%Y-%m-%d').date()
                            current_app.logger.info(f"更新production_date为: {value}")
                        except ValueError as e:
                            current_app.logger.error(f"日期格式转换错误: {value}, 错误: {str(e)}")
                    elif field == 'remark':
                        equipment.remark = value
                        current_app.logger.info(f"更新remark为: {value}")
                        success_count += 1
        
        current_app.logger.info(f"提交事务, 成功更新: {success_count}条")
        db.session.commit()
        
        response_data = {'success': True, 'message': f'成功更新 {success_count} 条记录'}
        current_app.logger.info(f"准备返回响应: {response_data}")
        
        return jsonify(response_data)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量更新失败: {str(e)}", exc_info=True)  # 添加完整异常堆栈
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500