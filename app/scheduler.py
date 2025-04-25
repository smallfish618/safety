from flask_apscheduler import APScheduler
from datetime import datetime, timedelta
from sqlalchemy import or_, func
from app import db
from app.models.station import FireStation, EquipmentExpiry, ResponsiblePerson
from app.models.equipment import FireEquipment
from app.models.mail_log import MailLog  # 确保在顶层导入MailLog
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
                    minutes=10,  # 从1分钟改为10分钟
                    args=[app],
                    replace_existing=True
                )
                print("[调度器] 已添加测试任务，每10分钟执行一次")
                app.logger.info('已添加测试任务，每10分钟执行一次')
                
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
    """调度器测试函数，每10分钟执行一次"""
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
            
            # 从config.py直接加载邮件配置
            try:
                from config import Config
                app.config['MAIL_SERVER'] = Config.MAIL_SERVER
                app.config['MAIL_PORT'] = Config.MAIL_PORT
                app.config['MAIL_USERNAME'] = Config.MAIL_USERNAME
                app.config['MAIL_PASSWORD'] = Config.MAIL_PASSWORD
                app.config['MAIL_USE_SSL'] = getattr(Config, 'MAIL_USE_SSL', True)
                app.config['MAIL_USE_TLS'] = getattr(Config, 'MAIL_USE_TLS', False)
                app.config['MAIL_DEFAULT_SENDER'] = getattr(Config, 'MAIL_DEFAULT_SENDER', ('消防安全管理系统', Config.MAIL_USERNAME))
                app.logger.info(f"已从config.py直接加载邮件配置: SERVER={app.config['MAIL_SERVER']}, PORT={app.config['MAIL_PORT']}")
            except Exception as e:
                app.logger.error(f"从config.py加载邮件配置失败: {str(e)}")
            
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
                        'id': item.id,
                        'responsible_person': person_dict[area_code]['name'],  # 确保添加负责人信息
                        'responsible_contact': person_dict[area_code]['email']  # 添加负责人联系方式
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

    # 验证邮箱配置是否完整，并提供详细的错误信息
    missing_config = []
    if not mail_server:
        missing_config.append("MAIL_SERVER")
    if not mail_port:
        missing_config.append("MAIL_PORT")
    if not mail_username:
        missing_config.append("MAIL_USERNAME")
    if not mail_password:
        missing_config.append("MAIL_PASSWORD")
    
    if missing_config:
        app.logger.error(f"邮件配置不完整，缺少以下项: {', '.join(missing_config)}")
        app.logger.info(f"当前配置: SERVER={mail_server}, PORT={mail_port}, USERNAME={mail_username}, PASSWORD={'已设置' if mail_password else '未设置'}")
        
        # 尝试从环境变量中读取
        import os
        if 'MAIL_PASSWORD' in missing_config:
            env_password = os.environ.get('MAIL_PASSWORD')
            if env_password:
                mail_password = env_password
                app.logger.info("已从环境变量中读取到MAIL_PASSWORD")
                missing_config.remove('MAIL_PASSWORD')
        
        # 如果仍有缺失项，则中止
        if missing_config:
            return 0
    
    # 设置默认发件人，确保不为空
    default_sender = mail_username or "18184887@qq.com"
    
    # 记录完整的邮件配置用于调试
    app.logger.info(f"邮件配置: SERVER={mail_server}, PORT={mail_port}, SSL={mail_use_ssl}, TLS={mail_use_tls}, USERNAME={mail_username}")
    
    # 添加当前日期和时间用于邮件标题
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 添加重试机制
    max_retries = 3
    
    # 特殊处理管理员收件人
    if recipient_filter == 'admin':
        app.logger.info("收件人设置为管理员，查找所有管理员用户")
        from app.models.user import User
        admin_users = User.query.filter_by(role='admin').all()
        
        if not admin_users:
            app.logger.warning("未找到管理员用户")
            return 0
            
        app.logger.info(f"找到 {len(admin_users)} 个管理员用户")
        
        # 收集所有预警项目，不再按负责人筛选
        all_items = []
        for area_code, area_data in person_dict.items():
            # 确保有负责人信息和联系方式
            responsible_name = area_data.get('name', '未指定')
            responsible_email = area_data.get('email', '无联系方式')
            
            if area_data.get('items'):
                # 为每个物品添加负责人信息
                for item in area_data['items']:
                    item['responsible_person'] = responsible_name
                    item['responsible_contact'] = responsible_email
                all_items.extend(area_data['items'])
                
        if not all_items:
            app.logger.info("没有任何预警物品，不发送邮件")
            return 0
            
        app.logger.info(f"总共有 {len(all_items)} 个预警物品")
        
        # 发送给每位管理员
        for admin in admin_users:
            if not admin.email or '@' not in admin.email:
                app.logger.warning(f"管理员 {admin.username} 没有有效的邮箱地址")
                continue
                
            try:
                app.logger.info(f"准备向管理员 {admin.username} ({admin.email}) 发送预警邮件")
                
                # 生成综合的预警邮件内容
                email_content = generate_admin_email_content(admin.username, all_items)
                
                # 创建邮件对象 - 修改标题添加日期时间
                msg = MIMEMultipart('alternative')
                msg['Subject'] = Header(f'【重要】物资有效期综合预警通知（{current_datetime}）', 'utf-8')
                msg['From'] = mail_username
                msg['To'] = admin.email
                
                # 设置HTML内容
                html_part = MIMEText(email_content, 'html', 'utf-8')
                msg.attach(html_part)
                
                # 尝试发送邮件
                retries = 0
                while retries < max_retries:
                    try:
                        # 使用正确的SMTP类，基于SSL/TLS配置
                        if mail_use_ssl:
                            server = smtplib.SMTP_SSL(mail_server, mail_port, timeout=10)
                        else:
                            server = smtplib.SMTP(mail_server, mail_port, timeout=10)
                            if mail_use_tls:
                                server.starttls()
                                
                        # 登录SMTP服务器
                        server.login(mail_username, mail_password)
                        
                        # 发送邮件
                        server.sendmail(mail_username, [admin.email], msg.as_string())
                        server.quit()
                        
                        # 记录发送成功
                        app.logger.info(f"成功向管理员 {admin.username} 发送预警邮件")
                        mail_count += 1
                        
                        # 记录发送日志
                        mail_log = MailLog(
                            send_time=datetime.now(),
                            sender=mail_username,
                            recipient=admin.email,
                            recipient_name=f"管理员-{admin.username}",
                            subject=f'【重要】物资有效期综合预警通知（{current_datetime}）',
                            content_summary=f"管理员综合预警邮件 - 包含{len(all_items)}个物品",
                            status="success",
                            error_message=None,
                            items_count=len(all_items)
                        )
                        db.session.add(mail_log)
                        db.session.commit()
                        
                        break  # 发送成功，跳出重试循环
                    except Exception as e:
                        retries += 1
                        app.logger.error(f"发送邮件给管理员 {admin.username} 失败 (尝试 {retries}/{max_retries}): {str(e)}")
                        if retries >= max_retries:
                            # 记录发送失败日志
                            mail_log = MailLog(
                                send_time=datetime.now(),
                                sender=mail_username,
                                recipient=admin.email,
                                recipient_name=f"管理员-{admin.username}",
                                subject=f'【重要】物资有效期综合预警通知（{current_datetime}）',
                                content_summary=f"管理员综合预警邮件 - 包含{len(all_items)}个物品",
                                status="failed",
                                error_message=str(e),
                                items_count=len(all_items)
                            )
                            db.session.add(mail_log)
                            db.session.commit()
            except Exception as e:
                app.logger.error(f"处理管理员 {admin.username} 的邮件时出错: {str(e)}")
                
        return mail_count
    
    # 解析选中的负责人列表（原有代码）
    selected_recipients = []
    if recipient_filter and recipient_filter != 'all' and recipient_filter != 'admin':
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
        email_subject = f'【重要】消防安全管理系统 - 物资有效期自动预警通知（{current_datetime}）'
        
        while retries < max_retries:
            try:
                # 生成邮件内容
                person_name = person_data['name']
                email_content = generate_email_content(person_name, person_data['items'])
                
                # 每次尝试都创建新的SMTP连接
                server = None
                try:
                    if mail_use_ssl:
                        app.logger.info(f"创建SSL SMTP连接到 {mail_server}:{mail_port}")
                        server = smtplib.SMTP_SSL(mail_server, mail_port, timeout=10)
                    else:
                        app.logger.info(f"创建标准SMTP连接到 {mail_server}:{mail_port}")
                        server = smtplib.SMTP(mail_server, mail_port, timeout=10)
                        if mail_use_tls:
                            server.starttls()
                    
                    # 登录SMTP服务器
                    app.logger.info(f"使用用户 {mail_username} 登录SMTP服务器")
                    server.login(mail_username, mail_password)
                    
                    # 创建邮件
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = Header(email_subject, 'utf-8')
                    msg['From'] = mail_username
                    msg['To'] = person_data['email']
                    
                    # 设置邮件内容
                    html_part = MIMEText(email_content, 'html', 'utf-8')
                    msg.attach(html_part)
                    
                    # 发送邮件
                    app.logger.info(f"发送邮件到 {person_data['email']}")
                    server.sendmail(mail_username, [person_data['email']], msg.as_string())
                    
                    # 关闭连接
                    server.quit()
                    
                    # 记录邮件日志
                    mail_log = MailLog(
                        send_time=datetime.now(),
                        sender=default_sender,  # 使用默认发件人，确保不为空
                        recipient=person_data['email'],
                        recipient_name=person_name,
                        subject=email_subject,
                        content_summary=f"自动有效期预警邮件 - 包含{len(person_data['items'])}个物品",
                        status="success",
                        items_count=len(person_data['items']),
                        username="系统自动发送",
                        user_id=None,  # 自动发送没有用户ID
                        ip_address="127.0.0.1"  # 添加一个默认IP地址
                    )
                    db.session.add(mail_log)
                    db.session.commit()
                    
                    mail_count += 1
                    app.logger.info(f"成功向 {person_name} ({person_data['email']}) 发送预警邮件")
                    
                    # 成功发送，跳出重试循环
                    break
                    
                except Exception as conn_error:
                    if server:
                        try:
                            server.quit()
                        except:
                            pass
                    
                    retries += 1
                    app.logger.warning(f"邮件发送失败，尝试第{retries}次重试... 错误: {str(conn_error)}")
                    
                    if retries >= max_retries:
                        # 记录失败日志 - 确保sender不为None
                        error_log = MailLog(
                            send_time=datetime.now(),
                            sender=default_sender,  # 使用默认发件人，确保不为空
                            recipient=person_data['email'],
                            recipient_name=person_data['name'],
                            subject=email_subject,
                            content_summary=f"自动有效期预警邮件 - 发送失败",
                            status="failed",
                            error_message=str(conn_error),
                            items_count=len(person_data['items']),
                            username="系统自动发送",
                            user_id=None,
                            ip_address="127.0.0.1"  # 添加一个默认IP地址
                        )
                        db.session.add(error_log)
                        db.session.commit()
                        app.logger.error(f"向 {person_data['name']} 发送邮件失败，已达最大重试次数: {str(conn_error)}")
                    else:
                        time.sleep(2)  # 重试前等待
                
            except Exception as e:
                app.logger.error(f"向 {person_data['name']} 发送邮件时出错: {str(e)}")
                
                # 记录失败日志 - 确保sender不为None
                try:
                    mail_log = MailLog(
                        send_time=datetime.now(),
                        sender=default_sender,  # 使用默认发件人，确保不为空 
                        recipient=person_data['email'],
                        recipient_name=person_data['name'],
                        subject=email_subject,
                        content_summary=f"自动有效期预警邮件 - 发送失败",
                        status="failed",
                        error_message=str(e),
                        items_count=len(person_data['items']),
                        username="系统自动发送",
                        user_id=None,
                        ip_address="127.0.0.1"  # 添加一个默认IP地址
                    )
                    db.session.add(mail_log)
                    db.session.commit()
                except Exception as log_err:
                    app.logger.error(f"记录失败邮件日志时出错: {str(log_err)}")
                    db.session.rollback()
                
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

def generate_admin_email_content(admin_name, all_items):
    """生成管理员专用的综合预警邮件内容"""
    # 当前日期
    current_date = datetime.now().date()
    
    # 按区域和负责人分组 - 确保负责人信息正确传递
    items_by_area = {}
    for item in all_items:
        area_name = item.get('area_name', '未知区域')
        if area_name not in items_by_area:
            items_by_area[area_name] = {
                'responsible': item.get('responsible_person', '未指定'),
                'contact': item.get('responsible_contact', '无联系方式'),
                'items': []
            }
        items_by_area[area_name]['items'].append(item)
    
    # 生成HTML内容
    html = f'''
    <div style="font-family: Arial, sans-serif;">
        <h2 style="color: #dc3545;">消防安全管理系统 - 物资有效期综合预警通知</h2>
        <p>尊敬的管理员 {admin_name}：</p>
        <p>系统检测到以下物资即将到期或已经到期，请关注：</p>
        
        <div style="margin-top: 20px;">
            <h3 style="margin-bottom: 10px; border-bottom: 1px solid #dee2e6; padding-bottom: 5px;">
                综合预警数据 - 共 {len(all_items)} 项
            </h3>
    '''
    
    # 添加预警统计
    expired_count = sum(1 for item in all_items if item.get('days_remaining', 0) < 0)
    days30_count = sum(1 for item in all_items if 0 <= item.get('days_remaining', 0) <= 30)
    days60_count = sum(1 for item in all_items if 30 < item.get('days_remaining', 0) <= 60)
    days90_count = sum(1 for item in all_items if 60 < item.get('days_remaining', 0) <= 90)
    
    html += f'''
            <div style="margin-bottom: 20px; padding: 10px; background-color: #f8f9fa; border-radius: 5px;">
                <h4 style="margin-top: 0;">预警统计：</h4>
                <ul>
                    <li><span style="color: #dc3545; font-weight: bold;">已过期：{expired_count}项</span></li>
                    <li><span style="color: #ffc107; font-weight: bold;">30天内到期：{days30_count}项</span></li>
                    <li><span style="color: #fd7e14; font-weight: bold;">60天内到期：{days60_count}项</span></li>
                    <li><span style="color: #17a2b8; font-weight: bold;">90天内到期：{days90_count}项</span></li>
                </ul>
            </div>
    '''
    
    # 按区域添加详细预警信息
    for area_name, area_data in items_by_area.items():
        # 更新区域标题，显示更详细的负责人信息
        html += f'''
            <div style="margin-top: 30px;">
                <h4 style="margin-bottom: 5px; background-color: #f1f1f1; padding: 5px 10px; border-radius: 5px;">
                    区域：{area_name} | 负责人：{area_data['responsible']} | 联系方式：{area_data['contact']}
                </h4>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <thead>
                        <tr style="background-color: #f8f9fa;">
                            <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">物品名称</th>
                            <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">型号</th>
                            <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">位置</th>
                            <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">到期日期</th>
                            <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">状态</th>
                        </tr>
                    </thead>
                    <tbody>
        '''
        
        # 添加该区域的所有物品
        for item in area_data['items']:
            days_remaining = item.get('days_remaining', 0)
            
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
                    <td style="border: 1px solid #dee2e6; padding: 8px;">{item.get('name', '')}</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px;">{item.get('model', '')}</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px;">{item.get('location', '')}</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px;">{item.get('expiry_date').strftime('%Y-%m-%d') if item.get('expiry_date') else ''}</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px; color: {status_color}; font-weight: bold;">
                        {status_text}
                    </td>
                </tr>
            '''
            
        html += '''
                    </tbody>
                </table>
            </div>
        '''
    
    # 完成HTML内容
    html += '''
        </div>
        <p>请及时关注物资到期情况，确保消防安全。</p>
        <p>谢谢您的关注！</p>
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