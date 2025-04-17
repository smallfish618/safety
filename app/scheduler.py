from flask_apscheduler import APScheduler
from datetime import datetime, timedelta
from sqlalchemy import or_, func
from app import db
from app.models.station import FireStation, EquipmentExpiry, ResponsiblePerson
from app.models.equipment import FireEquipment
from app.models.mail_log import MailLog
from app.models.scheduler_config import SchedulerConfig
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import traceback
import time
import pytz

# 创建调度器实例
scheduler = APScheduler()

def init_scheduler(app):
    """初始化调度器"""
    try:
        print("\n" + "=" * 50)
        print("==         定时任务调度器初始化开始         ==")
        print("=" * 50)
        
        # 确保在配置调度器之前设置Flask应用上下文
        with app.app_context():
            # 配置调度器之前设置
            app.config['SCHEDULER_API_ENABLED'] = True
            app.config['SCHEDULER_TIMEZONE'] = 'Asia/Shanghai'
            
            # 设置作业存储和其他重要配置
            app.config['SCHEDULER_EXECUTORS'] = {'default': {'type': 'threadpool', 'max_workers': 10}}
            app.config['SCHEDULER_JOB_DEFAULTS'] = {'coalesce': False, 'max_instances': 3}
            
            # 确保调度器唯一性
            global scheduler
            if scheduler.running:
                print("[调度器] 调度器已在运行中，将重新启动")
                app.logger.info('调度器已在运行中，将重新启动')
                scheduler.shutdown()
            
            # 设置时区
            scheduler.timezone = pytz.timezone('Asia/Shanghai')
            print(f"[调度器] 时区已设置为: {scheduler.timezone}")
            app.logger.info(f'调度器时区已设置为: {scheduler.timezone}')
            
            # 使用明确的Flask应用对象初始化调度器
            scheduler.api_enabled = True
            scheduler.init_app(app)
            
            # 启动前循环等待，确保应用上下文就绪
            print("[调度器] 正在启动调度器...")
            app.logger.info('正在启动调度器...')
            
            # 直接在app上下文中启动
            scheduler.start()
            
            # 检查启动状态
            if scheduler.running:
                print(f"[调度器] 状态: \033[1;32m成功启动\033[0m")
                print(f"[调度器] 运行状态: {scheduler.running}")
                app.logger.info(f'调度器成功启动，状态: {scheduler.running}')
                
                # 添加测试任务
                scheduler.add_job(
                    id='test_scheduler',
                    func=test_scheduler_function,
                    trigger='interval',
                    minutes=1,
                    args=[app],
                    replace_existing=True
                )
                print("[调度器] 已添加测试任务，每分钟执行一次")
                app.logger.info('已添加测试任务，每分钟执行一次')
                
                # 注册实际任务
                register_scheduled_tasks(app)
                
                # 验证任务是否已正确调度
                jobs = scheduler.get_jobs()
                print(f"[调度器] 当前已注册的任务: {len(jobs)}个")
                app.logger.info(f'当前已注册的任务: {len(jobs)}个')
                for job in jobs:
                    next_run = getattr(job, 'next_run_time', None)
                    print(f"[调度器] 任务ID: {job.id}, 下次执行时间: {next_run if next_run else '未调度'}")
                    app.logger.info(f'任务ID: {job.id}, 下次执行时间: {next_run if next_run else "未调度"}')
            else:
                print(f"[调度器] 状态: \033[1;31m启动失败\033[0m")
                print("[调度器] 未能正确启动，启用备用方法")
                app.logger.error('调度器未能正确启动，启用备用方法')
                
                # 备用启动方法
                try:
                    scheduler._scheduler.start()
                    print(f"[调度器] 备用方法启动状态: {scheduler.running}")
                    app.logger.info(f'备用方法启动状态: {scheduler.running}')
                    if scheduler.running:
                        print("[调度器] 备用方法成功启动调度器")
                        app.logger.info('备用方法成功启动调度器')
                        register_scheduled_tasks(app)
                    else:
                        print("[调度器] 备用方法启动失败，请检查配置")
                        app.logger.error('备用方法启动失败，请检查配置')
                except Exception as start_error:
                    print(f"[调度器] 备用启动方法失败: {str(start_error)}")
                    app.logger.error(f'备用启动方法失败: {str(start_error)}')
        
        print("=" * 50)
        print(f"==  调度器状态: {'已启动' if scheduler.running else '启动失败'}  ==")
        print("=" * 50 + "\n")
    except Exception as e:
        print("\n" + "=" * 50)
        print(f"[调度器] \033[1;31m初始化时出错: {str(e)}\033[0m")
        print("=" * 50 + "\n")
        app.logger.error(f'初始化调度器时出错: {str(e)}')
        traceback.print_exc()

# 添加重新调度任务的辅助函数
def reschedule_task(app, config):
    """尝试重新调度单个任务"""
    try:
        job_id = f'expiry_alert_{config.id}'
        
        # 移除现有任务
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            app.logger.info(f'已移除现有任务 {job_id} 以重新调度')
        
        # 解析时间
        time_parts = config.execution_time.split(':')
        if len(time_parts) != 2:
            app.logger.error(f'时间格式错误: {config.execution_time}，应为HH:MM格式')
            return
            
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        # 直接使用API添加任务，避免队列
        if config.frequency_type == 'daily':
            # 每天执行
            job = scheduler.add_job(
                id=job_id,
                func=send_scheduled_expiry_alerts, 
                trigger='cron', 
                hour=hour,
                minute=minute, 
                args=[app, config.id],
                replace_existing=True  # 强制替换现有任务
            )
        elif config.frequency_type == 'weekly':
            # 每周执行
            job = scheduler.add_job(
                id=job_id,
                func=send_scheduled_expiry_alerts,
                trigger='cron',
                day_of_week=config.day_of_week,
                hour=hour,
                minute=minute,
                args=[app, config.id],
                replace_existing=True
            )
        elif config.frequency_type == 'monthly':
            # 每月执行
            job = scheduler.add_job(
                id=job_id,
                func=send_scheduled_expiry_alerts,
                trigger='cron',
                day=config.day_of_month,
                hour=hour,
                minute=minute,
                args=[app, config.id],
                replace_existing=True
            )
        
        app.logger.info(f'已重新调度任务 {job_id}，下次执行时间: {job.next_run_time if hasattr(job, "next_run_time") else "未知"}')
        
    except Exception as e:
        app.logger.error(f'重新调度任务 {config.id} 时出错: {str(e)}')
        traceback.print_exc()

# 添加测试函数，用于验证调度器是否正常工作
def test_scheduler_function(app):
    """调度器测试函数，每分钟执行一次"""
    with app.app_context():
        current_time = datetime.now()
        app.logger.info(f'调度器测试任务执行: {current_time}')

def register_scheduled_tasks(app):
    """根据数据库中的配置注册所有调度任务"""
    try:
        # 获取所有启用的调度任务配置
        configs = SchedulerConfig.query.filter_by(enabled=True).all()
        app.logger.info(f'找到 {len(configs)} 个启用的调度任务配置')
        
        # 输出当前系统时间，以便与任务时间比较
        app.logger.info(f'当前系统时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        app.logger.info(f'当前时区: {datetime.now().astimezone().tzinfo}')
        
        for config in configs:
            # 为每个配置创建一个定时任务
            job_id = f'expiry_alert_{config.id}'
            
            # 检查任务是否已存在，若存在则移除
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)
                app.logger.info(f'已移除现有任务 {job_id}')
            
            try:
                # 解析时间格式
                time_parts = config.execution_time.split(':')
                if len(time_parts) != 2:
                    app.logger.error(f'时间格式错误: {config.execution_time}，应为HH:MM格式')
                    continue
                    
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                
                app.logger.info(f'任务 {job_id} 设置为在每天 {hour:02d}:{minute:02d} 执行')
                
                # 根据频率类型设置触发器
                if config.frequency_type == 'daily':
                    # 每天执行
                    scheduler.add_job(
                        id=job_id,
                        func=send_scheduled_expiry_alerts, 
                        trigger='cron', 
                        hour=hour,
                        minute=minute, 
                        args=[app, config.id]
                    )
                    app.logger.info(f'已注册每日任务 {job_id}，执行时间: {hour:02d}:{minute:02d}')
                    
                elif config.frequency_type == 'weekly':
                    # 每周执行
                    day_of_week = config.day_of_week
                    scheduler.add_job(
                        id=job_id,
                        func=send_scheduled_expiry_alerts,
                        trigger='cron',
                        day_of_week=day_of_week,
                        hour=hour,
                        minute=minute,
                        args=[app, config.id]
                    )
                    app.logger.info(f'已注册每周任务 {job_id}，执行时间: 每周{day_of_week} {hour:02d}:{minute:02d}')
                    
                elif config.frequency_type == 'monthly':
                    # 每月执行
                    day = config.day_of_month
                    scheduler.add_job(
                        id=job_id,
                        func=send_scheduled_expiry_alerts,
                        trigger='cron',
                        day=day,
                        hour=hour,
                        minute=minute,
                        args=[app, config.id]
                    )
                    app.logger.info(f'已注册每月任务 {job_id}，执行时间: 每月{day}日 {hour:02d}:{minute:02d}')
                
                # 获取并打印下次运行时间
                job = scheduler.get_job(job_id)
                if job:
                    next_run = getattr(job, 'next_run_time', None)
                    if next_run:
                        app.logger.info(f'任务 {job_id} 下次执行时间: {next_run}')
                    else:
                        app.logger.info(f'任务 {job_id} 已添加，但尚未调度（调度器可能未完全启动）')
                else:
                    app.logger.warning(f'无法获取任务 {job_id}')
                    
            except ValueError as e:
                app.logger.error(f'任务 {job_id} 时间解析错误: {str(e)}')
                continue
                
    except Exception as e:
        app.logger.error(f'注册调度任务时出错: {str(e)}')
        traceback.print_exc()

def send_scheduled_expiry_alerts(app, config_id):
    """执行定时预警邮件发送任务"""
    with app.app_context():
        try:
            app.logger.info(f'开始执行定时预警邮件任务 (配置ID: {config_id})')
            
            # 获取任务配置
            config = SchedulerConfig.query.get(config_id)
            if not config or not config.enabled:
                app.logger.warning(f'任务配置 {config_id} 不存在或已禁用，跳过执行')
                return
            
            # 解析预警级别设置
            warning_levels = config.warning_levels.split(',') if config.warning_levels else ['expired', 'within_90']
            
            # 获取收件人筛选设置
            recipient_filter = config.recipient_filter
            
            # 获取当前日期
            current_date = datetime.now().date()
            
            # 获取所有物品有效期规则
            expiry_rules = EquipmentExpiry.query.all()
            expiry_rule_dict = {}
            for rule in expiry_rules:
                if rule.normal_expiry != 0:  # 排除长期有效物品
                    expiry_rule_dict[rule.item_name] = rule.normal_expiry
            
            # 获取所有负责人信息
            responsible_persons = ResponsiblePerson.query.all()
            person_dict = {}
            for person in responsible_persons:
                person_dict[person.area_code] = {
                    'name': person.person_name,
                    'email': person.email,
                    'items': []  # 用于存储该负责人的预警物品
                }
            
            # 处理微型站物资
            process_expiring_items(
                FireStation.query.filter(FireStation.production_date.isnot(None)).all(),
                expiry_rule_dict,
                person_dict,
                current_date,
                warning_levels,
                'station',
                app
            )
            
            # 处理消防器材
            process_expiring_items(
                FireEquipment.query.filter(FireEquipment.production_date.isnot(None)).all(),
                expiry_rule_dict,
                person_dict,
                current_date,
                warning_levels,
                'equipment',
                app
            )
            
            # 发送邮件给各个负责人
            mail_count = send_emails_to_responsibles(person_dict, app, config, recipient_filter)
            
            app.logger.info(f'定时预警任务完成，成功发送 {mail_count} 封邮件')
            
        except Exception as e:
            app.logger.error(f'执行定时预警任务时出错: {str(e)}')
            traceback.print_exc()

def process_expiring_items(items, expiry_rule_dict, person_dict, current_date, warning_levels, item_type, app):
    """处理即将到期的物品"""
    for item in items:
        # 跳过没有生产日期的物品
        if not item.production_date:
            continue
            
        # 对于微型站物资，使用item_name查找规则
        # 对于消防器材，使用equipment_type查找规则
        item_name = item.item_name if item_type == 'station' else item.equipment_type
        
        # 优先精确匹配，其次尝试模糊匹配
        matching_rule = None
        
        # 1. 精确匹配
        if item_name in expiry_rule_dict:
            matching_rule = item_name
        else:
            # 2. 模糊匹配 - 从最长的规则名开始匹配，避免短规则名误匹配
            sorted_rules = sorted(expiry_rule_dict.keys(), key=len, reverse=True)
            for rule_name in sorted_rules:
                if rule_name in item_name or item_name in rule_name:
                    matching_rule = rule_name
                    app.logger.debug(f"模糊匹配: {item_name} -> {rule_name}")
                    break
        
        if matching_rule:
            # 计算到期日期和剩余天数
            expiry_years = expiry_rule_dict[matching_rule]
            expiry_date = item.production_date + timedelta(days=int(expiry_years * 365))
            days_remaining = (expiry_date - current_date).days
            
            # 检查是否符合预警级别
            warning_flag = False
            
            if 'expired' in warning_levels and days_remaining < 0:
                warning_flag = True
            elif 'within_30' in warning_levels and 0 <= days_remaining <= 30:
                warning_flag = True
            elif 'within_60' in warning_levels and 30 < days_remaining <= 60:
                warning_flag = True
            elif 'within_90' in warning_levels and 60 < days_remaining <= 90:
                warning_flag = True
            
            if warning_flag:
                # 找到负责该区域的负责人
                area_code = item.area_code
                if area_code in person_dict:
                    # 将物品添加到负责人的预警列表中
                    person_dict[area_code]['items'].append({
                        'name': item_name,
                        'model': item.model if hasattr(item, 'model') else '未指定',
                        'area_name': item.area_name,
                        'location': getattr(item, 'installation_location', '未指定'),
                        'production_date': item.production_date,
                        'expiry_date': expiry_date,
                        'days_remaining': days_remaining,
                        'type': '微型站物资' if item_type == 'station' else '消防器材',
                        'id': item.id
                    })
                else:
                    app.logger.warning(f'区域编码 {area_code} 没有指定负责人')

def send_emails_to_responsibles(person_dict, app, config, recipient_filter=None):
    """向各个负责人发送预警邮件"""
    mail_count = 0
    
    # 获取邮件配置
    mail_server = app.config.get('MAIL_SERVER')
    mail_port = app.config.get('MAIL_PORT')
    mail_username = app.config.get('MAIL_USERNAME')
    mail_password = app.config.get('MAIL_PASSWORD')
    mail_use_ssl = app.config.get('MAIL_USE_SSL', True)
    mail_use_tls = app.config.get('MAIL_USE_TLS', False)
    
    # 添加重试机制
    max_retries = 3
    
    # 解析选中的负责人列表（修复问题的关键部分）
    selected_recipients = []
    if recipient_filter and recipient_filter != 'all':
        # 将字符串转换为列表
        selected_recipients = [name.strip() for name in recipient_filter.split(',')]
        app.logger.info(f"筛选的负责人列表: {selected_recipients}")
    
    # 输出调试信息
    app.logger.info(f"总负责人数: {len(person_dict)}")
    
    for area_code, person_data in person_dict.items():
        # 检查是否有预警物品和有效的邮箱
        if not person_data['items'] or not person_data['email'] or '@' not in person_data['email']:
            app.logger.info(f"跳过负责人 {person_data.get('name', '未知')}: 无有效邮箱或无预警物品")
            continue
        
        # 应用收件人筛选逻辑 - 修复这部分代码
        if selected_recipients:
            # 检查当前负责人是否在选中列表中
            if person_data['name'] not in selected_recipients:
                app.logger.info(f"跳过未选中的负责人: {person_data['name']}")
                continue
            else:
                app.logger.info(f"已选中负责人: {person_data['name']}")
        
        # 以下是正常的邮件发送流程...
        retries = 0
        while retries < max_retries:
            try:
                # 生成邮件内容
                person_name = person_data['name']
                email_content = generate_email_content(person_name, person_data['items'])
                
                # 设置邮件主题
                email_subject = f'【重要】消防安全管理系统 - 物资有效期自动预警通知'
                
                # 发送邮件
                if mail_use_ssl:
                    server = smtplib.SMTP_SSL(mail_server, mail_port)
                else:
                    server = smtplib.SMTP(mail_server, mail_port)
                    if mail_use_tls:
                        server.starttls()
                
                server.login(mail_username, mail_password)
                
                msg = MIMEMultipart('alternative')
                msg['Subject'] = Header(email_subject, 'utf-8')
                msg['From'] = mail_username
                msg['To'] = person_data['email']
                
                html_part = MIMEText(email_content, 'html', 'utf-8')
                msg.attach(html_part)
                
                server.sendmail(mail_username, [person_data['email']], msg.as_string())
                server.quit()
                
                # 记录邮件日志
                mail_log = MailLog(
                    send_time=datetime.now(),
                    sender=mail_username,
                    recipient=person_data['email'],
                    recipient_name=person_name,
                    subject=email_subject,
                    content_summary=f"自动有效期预警邮件 - 包含{len(person_data['items'])}个物品",
                    status="success",
                    items_count=len(person_data['items']),
                    username="系统自动发送",
                    user_id=None  # 自动发送没有用户ID
                )
                db.session.add(mail_log)
                db.session.commit()
                
                mail_count += 1
                app.logger.info(f"成功向 {person_name} ({person_data['email']}) 发送预警邮件")
                
                # 成功发送，跳出重试循环
                break
                
            except smtplib.SMTPException as e:
                retries += 1
                if retries >= max_retries:
                    # 记录失败日志
                    app.logger.error(f"向 {person_data['name']} 发送邮件时出错: {str(e)}")
                    
                    mail_log = MailLog(
                        send_time=datetime.now(),
                        sender=mail_username,
                        recipient=person_data['email'],
                        recipient_name=person_data['name'],
                        subject=email_subject if 'email_subject' in locals() else "物资有效期自动预警通知",
                        content_summary=f"自动有效期预警邮件 - 发送失败",
                        status="failed",
                        error_message=str(e),
                        items_count=len(person_data['items']),
                        username="系统自动发送",
                        user_id=None
                    )
                    db.session.add(mail_log)
                    db.session.commit()
                else:
                    app.logger.warning(f"邮件发送失败，尝试第{retries}次重试...")
                    time.sleep(2)  # 重试前等待
            
            except Exception as e:
                app.logger.error(f"向 {person_data['name']} 发送邮件时出错: {str(e)}")
                
                # 记录失败日志
                mail_log = MailLog(
                    send_time=datetime.now(),
                    sender=mail_username,
                    recipient=person_data['email'],
                    recipient_name=person_data['name'],
                    subject=email_subject if 'email_subject' in locals() else "物资有效期自动预警通知",
                    content_summary=f"自动有效期预警邮件 - 发送失败",
                    status="failed",
                    error_message=str(e),
                    items_count=len(person_data['items']),
                    username="系统自动发送",
                    user_id=None
                )
                db.session.add(mail_log)
                db.session.commit()
                
                # 一般错误不重试
                break
    
    # 输出最终发送结果
    app.logger.info(f"总计向 {mail_count} 位负责人发送了邮件")
    return mail_count

def generate_email_content(responsible_person, items):
    """生成邮件HTML内容"""
    html = f'''
    <div style="font-family: Arial, sans-serif;">
        <h2 style="color: #dc3545;">消防安全管理系统 - 物资有效期自动预警通知</h2>
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
    
    for item in items:
        # 获取物品状态文本和颜色
        days_remaining = item['days_remaining']
        
        if days_remaining < 0:
            status_text = "已到期"
            status_color = "#dc3545"  # 红色
        elif days_remaining <= 30:
            status_text = "30天内到期"
            status_color = "#ffc107"  # 黄色
        elif days_remaining <= 60:
            status_text = "60天内到期"
            status_color = "#fd7e14"  # 橙色
        else:
            status_text = "90天内到期"
            status_color = "#17a2b8"  # 青色
        
        html += f'''
        <tr>
            <td style="border: 1px solid #dee2e6; padding: 8px;">{item['name']}</td>
            <td style="border: 1px solid #dee2e6; padding: 8px;">{item['model']}</td>
            <td style="border: 1px solid #dee2e6; padding: 8px;">{item['area_name']}</td>
            <td style="border: 1px solid #dee2e6; padding: 8px;">{item['location']}</td>
            <td style="border: 1px solid #dee2e6; padding: 8px;">{item['expiry_date'].strftime('%Y-%m-%d')}</td>
            <td style="border: 1px solid #dee2e6; padding: 8px; color: {status_color}; font-weight: bold;">
                {status_text}
            </td>
        </tr>
        '''
    
    html += '''
                </tbody>
            </table>
        </div>
        <p>请及时对上述物资进行更换或维护，确保消防安全。</p>
        <p>谢谢您的配合！</p>
        <p style="margin-top: 20px; color: #6c757d; font-size: 0.9em;">
            消防安全管理系统<br>
            发送时间：''' + f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}' + '''<br>
            此邮件由系统自动发送，请勿直接回复
        </p>
    </div>
    '''
    
    return html

def refresh_tasks(app):
    """刷新所有调度任务"""
    with app.app_context():
        app.logger.info('正在刷新调度任务...')
        register_scheduled_tasks(app)

# 添加一个强制启动调度器的函数
def force_start_scheduler(app):
    """强制启动调度器的备用方法"""
    try:
        with app.app_context():
            app.logger.info("尝试强制启动调度器...")
            
            # 如果已经在运行，先停止
            if scheduler.running:
                scheduler.shutdown()
                import time
                time.sleep(1)
            
            # 重新配置并启动
            app.config['SCHEDULER_API_ENABLED'] = True
            scheduler.api_enabled = True
            scheduler.init_app(app)
            
            # 直接调用底层调度器的start方法
            if hasattr(scheduler, '_scheduler'):
                scheduler._scheduler.start()
                app.logger.info(f"强制启动后调度器状态: {scheduler.running}")
                
                if scheduler.running:
                    # 注册任务
                    register_scheduled_tasks(app)
                    return True
            return False
    except Exception as e:
        app.logger.error(f"强制启动调度器失败: {str(e)}")
        traceback.print_exc()
        return False
