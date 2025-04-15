from flask import Blueprint, render_template, redirect, url_for, current_app
import os
import sys
from importlib import reload

debug_bp = Blueprint('debug', __name__)

@debug_bp.route('/flush_cache')
def flush_cache():
    """强制清理Flask模板缓存并重建应用上下文"""
    # 清理Jinja2模板缓存
    current_app.jinja_env.cache.clear()
    # 设置自动重载模板
    current_app.jinja_env.auto_reload = True
    current_app.jinja_env.cache_size = 0
    # 强制刷新配置
    current_app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # 返回重定向到主页，附加时间戳参数强制刷新
    from datetime import datetime
    timestamp = datetime.now().timestamp()
    return redirect(url_for('index') + f'?_ts={timestamp}')

@debug_bp.route('/emergency')
def emergency_view():
    """使用应急布局显示页面"""
    from app.models.equipment import FireEquipment
    equipments = FireEquipment.query.limit(10).all()  # 获取最新10条记录
    return render_template('emergency_view.html', equipments=equipments)
