from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.station import FireStation, EquipmentExpiry, ResponsiblePerson
from app.models.equipment import FireEquipment
from app.models.user import User, Permission
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import traceback

# 创建蓝图
analytics_bp = Blueprint('analytics', __name__)

# 通用的管理员检查装饰器
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('您没有访问此页面的权限', 'danger')
            return redirect(url_for('station.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@analytics_bp.route('/')
@login_required
@admin_required
def index():
    """分析概览页面"""
    try:
        # 获取统计数据
        # 1. 微型站物资数量
        station_count = FireStation.query.count()
        
        # 2. 消防器材数量
        equipment_count = FireEquipment.query.count()
        
        # 3. 区域数量
        area_count = db.session.query(func.count(func.distinct(ResponsiblePerson.area_code))).scalar()
        
        # 4. 负责人数量
        responsible_count = ResponsiblePerson.query.count()
        
        # 5. 即将到期物品数量
        current_date = datetime.now().date()
        
        # 获取所有规则
        expiry_rules = EquipmentExpiry.query.all()
        expiry_rule_dict = {}
        for rule in expiry_rules:
            if rule.normal_expiry != 0:  # 排除长期有效的物品
                expiry_rule_dict[rule.item_name] = rule.normal_expiry
        
        # 统计即将到期的项目数
        expiring_count = {
            'expired': 0,
            'within_30': 0,
            'within_90': 0,
            'within_180': 0
        }
        
        # 处理微型站物资
        station_items = FireStation.query.filter(FireStation.production_date.isnot(None)).all()
        for item in station_items:
            for rule_name, expiry_years in expiry_rule_dict.items():
                if item.item_name == rule_name or item.item_name in rule_name or rule_name in item.item_name:
                    expiry_date = item.production_date + timedelta(days=int(expiry_years*365))
                    days_remaining = (expiry_date - current_date).days
                    
                    if days_remaining < 0:
                        expiring_count['expired'] += 1
                    elif days_remaining <= 30:
                        expiring_count['within_30'] += 1
                    elif days_remaining <= 90:
                        expiring_count['within_90'] += 1
                    elif days_remaining <= 180:
                        expiring_count['within_180'] += 1
                    break
        
        # 处理消防器材
        equipment_items = FireEquipment.query.filter(FireEquipment.production_date.isnot(None)).all()
        for item in equipment_items:
            for rule_name, expiry_years in expiry_rule_dict.items():
                if item.equipment_type == rule_name or item.equipment_type in rule_name or rule_name in item.equipment_type:
                    expiry_date = item.production_date + timedelta(days=int(expiry_years*365))
                    days_remaining = (expiry_date - current_date).days
                    
                    if days_remaining < 0:
                        expiring_count['expired'] += 1
                    elif days_remaining <= 30:
                        expiring_count['within_30'] += 1
                    elif days_remaining <= 90:
                        expiring_count['within_90'] += 1
                    elif days_remaining <= 180:
                        expiring_count['within_180'] += 1
                    break
        
        # 获取前5个区域的物资数量
        top_areas = db.session.query(
            FireStation.area_name, 
            func.count(FireStation.id).label('count')
        ).group_by(FireStation.area_name).order_by(func.count(FireStation.id).desc()).limit(5).all()
        
        top_area_data = {
            'labels': [area[0] for area in top_areas],
            'counts': [area[1] for area in top_areas]
        }
        
        # 获取前5个负责人的物品数量
        top_responsibles = []
        for person in ResponsiblePerson.query.all():
            # 计算每个负责人的物品数量
            station_items_count = FireStation.query.filter_by(area_code=person.area_code).count()
            equipment_items_count = FireEquipment.query.filter_by(area_code=str(person.area_code)).count()
            total_count = station_items_count + equipment_items_count
            
            if total_count > 0:
                top_responsibles.append((person.person_name, total_count))
        
        # 排序并获取前5位
        top_responsibles.sort(key=lambda x: x[1], reverse=True)
        top_responsibles = top_responsibles[:5]
        
        top_resp_data = {
            'labels': [resp[0] for resp in top_responsibles],
            'counts': [resp[1] for resp in top_responsibles]
        }
        
        return render_template(
            'analytics/index.html',
            station_count=station_count,
            equipment_count=equipment_count,
            area_count=area_count,
            responsible_count=responsible_count,
            expiring_count=expiring_count,
            top_area_data=top_area_data,
            top_resp_data=top_resp_data
        )
    except Exception as e:
        traceback.print_exc()
        return render_template('analytics/index.html', error=str(e))

@analytics_bp.route('/expiry_analysis')
@login_required
@admin_required
def expiry_analysis():
    """到期时间分析页面"""
    try:
        # 获取筛选参数
        source_type = request.args.get('source_type', 'all')
        
        # 获取当前日期
        current_date = datetime.now().date()
        
        # 从有效期规则表获取所有规则
        expiry_rules = EquipmentExpiry.query.all()
        expiry_rule_dict = {}
        for rule in expiry_rules:
            if rule.normal_expiry != 0:  # 排除长期有效的物品
                expiry_rule_dict[rule.item_name] = rule.normal_expiry
        
        # 初始化统计数据
        expiry_stats = {
            'expired': 0,
            'within_30': 0,
            'within_60': 0,
            'within_90': 0,
            'within_180': 0,
            'within_365': 0,
            'more_than_365': 0,
            'total': 0
        }
        
        # 用于存储按物品类别分组的到期统计
        category_expiry_data = {}
        
        # 用于存储未来12个月的到期趋势
        monthly_expiry = {}
        for i in range(12):
            month_date = current_date.replace(day=1) + timedelta(days=32*i)
            month_key = month_date.strftime('%Y-%m')
            monthly_expiry[month_key] = 0
        
        # 处理微型站物资
        if source_type in ['all', 'station']:
            station_items = FireStation.query.filter(FireStation.production_date.isnot(None)).all()
            for item in station_items:
                for rule_name, expiry_years in expiry_rule_dict.items():
                    if item.item_name == rule_name or item.item_name in rule_name or rule_name in item.item_name:
                        # 计算到期日期和剩余天数
                        expiry_date = item.production_date + timedelta(days=int(expiry_years*365))
                        days_remaining = (expiry_date - current_date).days
                        
                        # 更新统计数据
                        expiry_stats['total'] += 1
                        
                        if days_remaining < 0:
                            expiry_stats['expired'] += 1
                        elif days_remaining <= 30:
                            expiry_stats['within_30'] += 1
                        elif days_remaining <= 60:
                            expiry_stats['within_60'] += 1
                        elif days_remaining <= 90:
                            expiry_stats['within_90'] += 1
                        elif days_remaining <= 180:
                            expiry_stats['within_180'] += 1
                        elif days_remaining <= 365:
                            expiry_stats['within_365'] += 1
                        else:
                            expiry_stats['more_than_365'] += 1
                        
                        # 更新物品类别统计
                        category = item.item_name
                        if category not in category_expiry_data:
                            category_expiry_data[category] = {
                                'total': 0,
                                'expired': 0,
                                'within_90': 0,
                                'within_365': 0,
                                'more_than_365': 0
                            }
                        
                        category_expiry_data[category]['total'] += 1
                        
                        if days_remaining < 0:
                            category_expiry_data[category]['expired'] += 1
                        elif days_remaining <= 90:
                            category_expiry_data[category]['within_90'] += 1
                        elif days_remaining <= 365:
                            category_expiry_data[category]['within_365'] += 1
                        else:
                            category_expiry_data[category]['more_than_365'] += 1
                        
                        # 更新月度趋势
                        if 0 <= days_remaining <= 365:
                            expiry_month = (current_date + timedelta(days=days_remaining)).replace(day=1).strftime('%Y-%m')
                            if expiry_month in monthly_expiry:
                                monthly_expiry[expiry_month] += 1
                        
                        break
        
        # 处理消防器材
        if source_type in ['all', 'equipment']:
            equipment_items = FireEquipment.query.filter(FireEquipment.production_date.isnot(None)).all()
            for item in equipment_items:
                for rule_name, expiry_years in expiry_rule_dict.items():
                    if item.equipment_type == rule_name or item.equipment_type in rule_name or rule_name in item.equipment_type:
                        # 计算到期日期和剩余天数
                        expiry_date = item.production_date + timedelta(days=int(expiry_years*365))
                        days_remaining = (expiry_date - current_date).days
                        
                        # 更新统计数据
                        expiry_stats['total'] += 1
                        
                        if days_remaining < 0:
                            expiry_stats['expired'] += 1
                        elif days_remaining <= 30:
                            expiry_stats['within_30'] += 1
                        elif days_remaining <= 60:
                            expiry_stats['within_60'] += 1
                        elif days_remaining <= 90:
                            expiry_stats['within_90'] += 1
                        elif days_remaining <= 180:
                            expiry_stats['within_180'] += 1
                        elif days_remaining <= 365:
                            expiry_stats['within_365'] += 1
                        else:
                            expiry_stats['more_than_365'] += 1
                        
                        # 更新物品类别统计
                        category = item.equipment_type
                        if category not in category_expiry_data:
                            category_expiry_data[category] = {
                                'total': 0,
                                'expired': 0,
                                'within_90': 0,
                                'within_365': 0,
                                'more_than_365': 0
                            }
                        
                        category_expiry_data[category]['total'] += 1
                        
                        if days_remaining < 0:
                            category_expiry_data[category]['expired'] += 1
                        elif days_remaining <= 90:
                            category_expiry_data[category]['within_90'] += 1
                        elif days_remaining <= 365:
                            category_expiry_data[category]['within_365'] += 1
                        else:
                            category_expiry_data[category]['more_than_365'] += 1
                        
                        # 更新月度趋势
                        if 0 <= days_remaining <= 365:
                            expiry_month = (current_date + timedelta(days=days_remaining)).replace(day=1).strftime('%Y-%m')
                            if expiry_month in monthly_expiry:
                                monthly_expiry[expiry_month] += 1
                        
                        break
        
        # 对物品类别统计按到期比例排序，选择前10个
        top_categories = sorted(
            category_expiry_data.items(),
            key=lambda x: (x[1]['expired'] + x[1]['within_90']) / x[1]['total'] if x[1]['total'] > 0 else 0,
            reverse=True
        )[:10]
        
        category_expiry_data = dict(top_categories)
        
        return render_template(
            'analytics/expiry_analysis.html',
            source_type=source_type,
            expiry_stats=expiry_stats,
            category_expiry_data=category_expiry_data,
            monthly_expiry=monthly_expiry
        )
    except Exception as e:
        traceback.print_exc()
        return render_template('analytics/expiry_analysis.html', error=str(e))

@analytics_bp.route('/responsible_analysis')
@login_required
@admin_required
def responsible_analysis():
    """负责人物资分析页面"""
    try:
        # 获取所有负责人
        responsibles = ResponsiblePerson.query.all()
        
        # 初始化负责人统计数据
        responsible_stats = []
        
        # 获取当前日期
        current_date = datetime.now().date()
        
        # 获取物资有效期规则
        expiry_rules = EquipmentExpiry.query.all()
        expiry_rule_dict = {}
        for rule in expiry_rules:
            if rule.normal_expiry != 0:
                expiry_rule_dict[rule.item_name] = rule.normal_expiry
        
        # 处理每个负责人的数据
        for responsible in responsibles:
            # 初始化该负责人的统计数据
            stats = {
                'id': responsible.id,
                'name': responsible.person_name,
                'area_name': responsible.area_name,
                'area_code': responsible.area_code,
                'contact': responsible.contact,
                'email': responsible.email,
                'station_count': 0,
                'equipment_count': 0,
                'total_count': 0,
                'expired_count': 0,
                'expiring_soon_count': 0  # 90天内到期
            }
            
            # 统计微型站物资
            station_items = FireStation.query.filter_by(area_code=responsible.area_code).all()
            stats['station_count'] = len(station_items)
            
            for item in station_items:
                if item.production_date:
                    for rule_name, expiry_years in expiry_rule_dict.items():
                        if item.item_name == rule_name or item.item_name in rule_name or rule_name in item.item_name:
                            # 计算到期日期和剩余天数
                            expiry_date = item.production_date + timedelta(days=int(expiry_years*365))
                            days_remaining = (expiry_date - current_date).days
                            
                            if days_remaining < 0:
                                stats['expired_count'] += 1
                            elif days_remaining <= 90:
                                stats['expiring_soon_count'] += 1
                            
                            break
            
            # 统计消防器材
            equipment_items = FireEquipment.query.filter_by(area_code=str(responsible.area_code)).all()
            stats['equipment_count'] = len(equipment_items)
            
            for item in equipment_items:
                if item.production_date:
                    for rule_name, expiry_years in expiry_rule_dict.items():
                        if item.equipment_type == rule_name or item.equipment_type in rule_name or rule_name in item.equipment_type:
                            # 计算到期日期和剩余天数
                            expiry_date = item.production_date + timedelta(days=int(expiry_years*365))
                            days_remaining = (expiry_date - current_date).days
                            
                            if days_remaining < 0:
                                stats['expired_count'] += 1
                            elif days_remaining <= 90:
                                stats['expiring_soon_count'] += 1
                            
                            break
            
            # 计算总数
            stats['total_count'] = stats['station_count'] + stats['equipment_count']
            
            # 只添加有物资的负责人
            if stats['total_count'] > 0:
                responsible_stats.append(stats)
        
        # 按物资总数排序
        responsible_stats.sort(key=lambda x: x['total_count'], reverse=True)
        
        # 准备图表数据
        total_chart_data = {
            'labels': [resp['name'] for resp in responsible_stats[:10]],  # 前10个负责人
            'datasets': [
                {
                    'label': '微型站物资',
                    'data': [resp['station_count'] for resp in responsible_stats[:10]]
                },
                {
                    'label': '消防器材',
                    'data': [resp['equipment_count'] for resp in responsible_stats[:10]]
                }
            ]
        }
        
        expiry_chart_data = {
            'labels': [resp['name'] for resp in responsible_stats[:10]],
            'datasets': [
                {
                    'label': '已到期',
                    'data': [resp['expired_count'] for resp in responsible_stats[:10]]
                },
                {
                    'label': '即将到期',
                    'data': [resp['expiring_soon_count'] for resp in responsible_stats[:10]]
                }
            ]
        }
        
        return render_template(
            'analytics/responsible_analysis.html',
            responsible_stats=responsible_stats,
            total_chart_data=total_chart_data,
            expiry_chart_data=expiry_chart_data
        )
    except Exception as e:
        traceback.print_exc()
        return render_template('analytics/responsible_analysis.html', error=str(e))

@analytics_bp.route('/area_analysis')
@login_required
@admin_required
def area_analysis():
    """区域物资分析页面"""
    try:
        # 获取所有区域
        areas = db.session.query(
            ResponsiblePerson.area_code,
            ResponsiblePerson.area_name,
            ResponsiblePerson.person_name
        ).all()
        
        # 初始化区域统计数据
        area_stats = []
        
        # 获取当前日期
        current_date = datetime.now().date()
        
        # 获取物资有效期规则
        expiry_rules = EquipmentExpiry.query.all()
        expiry_rule_dict = {}
        for rule in expiry_rules:
            if rule.normal_expiry != 0:
                expiry_rule_dict[rule.item_name] = rule.normal_expiry
        
        # 处理每个区域的数据
        for area in areas:
            # 初始化该区域的统计数据
            stats = {
                'area_code': area.area_code,
                'area_name': area.area_name,
                'responsible_person': area.person_name,
                'station_count': 0,
                'equipment_count': 0,
                'total_count': 0,
                'expired_count': 0,
                'expiring_soon_count': 0,  # 90天内到期
                'types_count': 0,  # 物品类型数量
                'types': set()     # 用于统计物品类型
            }
            
            # 统计微型站物资
            station_items = FireStation.query.filter_by(area_code=area.area_code).all()
            stats['station_count'] = len(station_items)
            
            for item in station_items:
                # 添加物品类型
                stats['types'].add(item.item_name)
                
                if item.production_date:
                    for rule_name, expiry_years in expiry_rule_dict.items():
                        if item.item_name == rule_name or item.item_name in rule_name or rule_name in item.item_name:
                            # 计算到期日期和剩余天数
                            expiry_date = item.production_date + timedelta(days=int(expiry_years*365))
                            days_remaining = (expiry_date - current_date).days
                            
                            if days_remaining < 0:
                                stats['expired_count'] += 1
                            elif days_remaining <= 90:
                                stats['expiring_soon_count'] += 1
                            
                            break
            
            # 统计消防器材
            equipment_items = FireEquipment.query.filter_by(area_code=str(area.area_code)).all()
            stats['equipment_count'] = len(equipment_items)
            
            for item in equipment_items:
                # 添加物品类型
                stats['types'].add(item.equipment_type)
                
                if item.production_date:
                    for rule_name, expiry_years in expiry_rule_dict.items():
                        if item.equipment_type == rule_name or item.equipment_type in rule_name or rule_name in item.equipment_type:
                            # 计算到期日期和剩余天数
                            expiry_date = item.production_date + timedelta(days=int(expiry_years*365))
                            days_remaining = (expiry_date - current_date).days
                            
                            if days_remaining < 0:
                                stats['expired_count'] += 1
                            elif days_remaining <= 90:
                                stats['expiring_soon_count'] += 1
                            
                            break
            
            # 计算总数和类型数
            stats['total_count'] = stats['station_count'] + stats['equipment_count']
            stats['types_count'] = len(stats['types'])
            stats['types'] = list(stats['types'])  # 转换为列表，方便JSON序列化
            
            # 只添加有物资的区域
            if stats['total_count'] > 0:
                area_stats.append(stats)
        
        # 按物资总数排序
        area_stats.sort(key=lambda x: x['total_count'], reverse=True)
        
        # 准备图表数据
        total_chart_data = {
            'labels': [area['area_name'] for area in area_stats[:10]],  # 前10个区域
            'datasets': [
                {
                    'label': '微型站物资',
                    'data': [area['station_count'] for area in area_stats[:10]]
                },
                {
                    'label': '消防器材',
                    'data': [area['equipment_count'] for area in area_stats[:10]]
                }
            ]
        }
        
        expiry_chart_data = {
            'labels': [area['area_name'] for area in area_stats[:10]],
            'datasets': [
                {
                    'label': '已到期',
                    'data': [area['expired_count'] for area in area_stats[:10]]
                },
                {
                    'label': '即将到期',
                    'data': [area['expiring_soon_count'] for area in area_stats[:10]]
                }
            ]
        }
        
        return render_template(
            'analytics/area_analysis.html',
            area_stats=area_stats,
            total_chart_data=total_chart_data,
            expiry_chart_data=expiry_chart_data
        )
    except Exception as e:
        traceback.print_exc()
        return render_template('analytics/area_analysis.html', error=str(e))
