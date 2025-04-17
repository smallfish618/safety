from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.scheduler_config import SchedulerConfig
from app.models.station import ResponsiblePerson
from app.scheduler import refresh_tasks
import traceback
from datetime import datetime
import re

scheduler_bp = Blueprint('scheduler', __name__)

# 管理员权限检查装饰器
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('您没有访问此页面的权限', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@scheduler_bp.route('/')
@login_required
@admin_required
def index():
    """定时任务管理页面"""
    try:
        # 获取所有定时任务配置
        configs = SchedulerConfig.query.order_by(SchedulerConfig.id.desc()).all()
        
        # 获取所有负责人信息，用于负责人选择器
        responsible_persons = ResponsiblePerson.query.order_by(ResponsiblePerson.person_name).all()
        
        return render_template(
            'scheduler/index.html',
            configs=configs,
            responsible_persons=responsible_persons
        )
    except Exception as e:
        traceback.print_exc()
        flash(f'加载定时任务配置出错: {str(e)}', 'danger')
        return render_template('scheduler/index.html', configs=[], error=str(e))

@scheduler_bp.route('/add', methods=['POST'])
@login_required
@admin_required
def add_config():
    """添加定时任务配置"""
    try:
        # 获取表单数据
        name = request.form.get('name')
        frequency_type = request.form.get('frequency_type')
        execution_time = request.form.get('execution_time')
        day_of_week = request.form.get('day_of_week')
        day_of_month = request.form.get('day_of_month', type=int)
        warning_levels = ','.join(request.form.getlist('warning_levels'))
        recipient_filter = request.form.get('recipient_filter', '')
        
        # 如果选择了"all"，则使用"all"
        # 否则，如果选择了特定收件人，则获取所有选中的收件人并用逗号连接
        if recipient_filter != 'all':
            selected_recipients = request.form.getlist('selected_recipients')
            if selected_recipients:
                recipient_filter = ','.join(selected_recipients)
        
        # 验证必填字段
        if not all([name, frequency_type, execution_time]):
            flash('名称、频率类型和执行时间不能为空', 'danger')
            return redirect(url_for('scheduler.index'))
        
        # 更多验证逻辑...
        
        # 创建新配置
        config = SchedulerConfig(
            name=name,
            enabled=True,
            frequency_type=frequency_type,
            execution_time=execution_time,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            warning_levels=warning_levels,
            recipient_filter=recipient_filter,
            created_by=current_user.id
        )
        
        db.session.add(config)
        db.session.commit()
        
        # 刷新任务调度
        from flask import current_app
        refresh_tasks(current_app._get_current_object())
        
        flash('定时任务配置已添加', 'success')
        return redirect(url_for('scheduler.index'))
    
    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        flash(f'添加定时任务配置失败: {str(e)}', 'danger')
        return redirect(url_for('scheduler.index'))

@scheduler_bp.route('/toggle/<int:config_id>', methods=['POST'])
@login_required
@admin_required
def toggle_config(config_id):
    """启用/禁用定时任务配置"""
    try:
        # 查找配置
        config = SchedulerConfig.query.get_or_404(config_id)
        
        # 保存当前状态到本地变量
        current_status = config.enabled  
        
        # 切换启用状态
        config.enabled = not current_status
        db.session.commit()
        
        # 刷新任务调度
        from flask import current_app
        refresh_tasks(current_app._get_current_object())
        
        # 使用之前存储的状态值来生成消息
        status = "启用" if not current_status else "禁用"
        flash(f'定时任务配置已{status}', 'success')
        return redirect(url_for('scheduler.index'))
    
    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        flash(f'更改定时任务状态失败: {str(e)}', 'danger')
        return redirect(url_for('scheduler.index'))

@scheduler_bp.route('/run-now/<int:config_id>', methods=['POST'])
@login_required
@admin_required
def run_now(config_id):
    """立即执行指定的任务"""
    try:
        from flask import current_app
        from app.scheduler import send_scheduled_expiry_alerts
        
        # 检查配置是否存在
        config = SchedulerConfig.query.get_or_404(config_id)
        
        # 获取配置名称用于显示
        config_name = config.name
        
        # 立即执行任务
        send_scheduled_expiry_alerts(current_app._get_current_object(), config_id)
        
        flash(f'任务 "{config_name}" 已手动执行', 'success')
        return redirect(url_for('scheduler.index'))
    
    except Exception as e:
        traceback.print_exc()
        flash(f'手动执行任务失败: {str(e)}', 'danger')
        return redirect(url_for('scheduler.index'))

@scheduler_bp.route('/delete/<int:config_id>', methods=['POST'])
@login_required
@admin_required
def delete_config(config_id):
    """删除定时任务配置"""
    try:
        # 查找配置
        config = SchedulerConfig.query.get_or_404(config_id)
        
        # 从数据库删除
        db.session.delete(config)
        db.session.commit()
        
        # 刷新任务调度
        from flask import current_app
        refresh_tasks(current_app._get_current_object())
        
        flash('定时任务配置已删除', 'success')
        return redirect(url_for('scheduler.index'))
    
    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        flash(f'删除定时任务配置失败: {str(e)}', 'danger')
        return redirect(url_for('scheduler.index'))

@scheduler_bp.route('/edit/<int:config_id>', methods=['POST'])
@login_required
@admin_required
def edit_config(config_id):
    """编辑定时任务配置"""
    try:
        # 查找配置
        config = SchedulerConfig.query.get_or_404(config_id)
        
        # 获取表单数据
        config.name = request.form.get('name')
        config.frequency_type = request.form.get('frequency_type')
        config.execution_time = request.form.get('execution_time')
        config.day_of_week = request.form.get('day_of_week')
        config.day_of_month = request.form.get('day_of_month', type=int)
        config.warning_levels = ','.join(request.form.getlist('warning_levels'))
        recipient_filter = request.form.get('recipient_filter', '')
        
        # 处理收件人选项
        if recipient_filter != 'all':
            selected_recipients = request.form.getlist('selected_recipients')
            if selected_recipients:
                recipient_filter = ','.join(selected_recipients)
        else:
            recipient_filter = 'all'
        
        config.recipient_filter = recipient_filter
        
        # 保存更改
        db.session.commit()
        
        # 刷新任务调度
        from flask import current_app
        refresh_tasks(current_app._get_current_object())
        
        flash('定时任务配置已更新', 'success')
        return redirect(url_for('scheduler.index'))
    
    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        flash(f'更新定时任务配置失败: {str(e)}', 'danger')
        return redirect(url_for('scheduler.index'))

@scheduler_bp.route('/status')
@login_required
@admin_required
def scheduler_status():
    """查看调度器状态"""
    from app.scheduler import scheduler
    import datetime
    
    jobs = scheduler.get_jobs()
    job_list = []
    
    for job in jobs:
        next_run = getattr(job, 'next_run_time', None)
        job_info = {
            'id': job.id,
            'function': job.func.__name__ if hasattr(job.func, '__name__') else str(job.func),
            'trigger': job.trigger.__class__.__name__,
            'next_run': next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else '未调度',
            'scheduled': bool(next_run)
        }
        job_list.append(job_info)
    
    now = datetime.datetime.now()
    timezone_info = now.astimezone().tzinfo
    
    status_info = {
        'running': scheduler.running,
        'scheduler_timezone': str(scheduler.timezone),
        'system_time': now.strftime('%Y-%m-%d %H:%M:%S'),
        'system_timezone': str(timezone_info),
        'jobs_count': len(jobs),
        'jobs': job_list
    }
    
    return render_template('scheduler/status.html', status=status_info)

@scheduler_bp.route('/refresh', methods=['POST'])
@login_required
@admin_required
def refresh_all_tasks():
    """手动刷新所有任务"""
    try:
        from flask import current_app
        from app.scheduler import refresh_tasks
        
        # 刷新所有任务
        refresh_tasks(current_app._get_current_object())
        flash('所有调度任务已刷新', 'success')
    except Exception as e:
        flash(f'刷新任务时出错: {str(e)}', 'danger')
    return redirect(url_for('scheduler.status'))
