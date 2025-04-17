"""
检查定时任务配置和执行状态
"""
from app import create_app, db
from app.models.scheduler_config import SchedulerConfig
from app.scheduler import scheduler
import datetime
import pprint

app = create_app()

with app.app_context():
    # 检查数据库中的定时任务配置
    configs = SchedulerConfig.query.all()
    print(f"\n共有 {len(configs)} 个定时任务配置:")
    
    for config in configs:
        print(f"\n任务ID: {config.id}")
        print(f"名称: {config.name}")
        print(f"启用状态: {'已启用' if config.enabled else '已禁用'}")
        print(f"频率: {config.frequency_type}")
        print(f"执行时间: {config.execution_time}")
        if config.frequency_type == 'weekly':
            print(f"星期几: {config.day_of_week}")
        elif config.frequency_type == 'monthly':
            print(f"每月几号: {config.day_of_month}")
        print(f"预警级别: {config.warning_levels}")
        print(f"接收人筛选: {config.recipient_filter}")
        
    # 检查APScheduler中的任务
    print("\n=====================")
    print("APScheduler中的任务:")
    
    jobs = scheduler.get_jobs()
    print(f"当前注册的任务数: {len(jobs)}")
    
    for job in jobs:
        print(f"\n任务ID: {job.id}")
        
        # 检查job属性并安全获取
        try:
            # 使用dir()获取所有可用属性
            print(f"可用属性: {', '.join([attr for attr in dir(job) if not attr.startswith('_')])}")
            
            # 显示关键属性
            print(f"触发器类型: {job.trigger.__class__.__name__}")
            
            # 检查不同类型的触发器
            if hasattr(job.trigger, 'fields'):
                # 对于CronTrigger
                fields = job.trigger.fields
                field_values = {}
                for field in fields:
                    if hasattr(field, 'name') and hasattr(field, 'expressions'):
                        exprs = [str(e) for e in field.expressions]
                        field_values[field.name] = exprs
                
                print("触发器字段:")
                pprint.pprint(field_values, width=100)
            
            # 尝试获取函数信息
            func_name = job.func.__name__ if hasattr(job.func, '__name__') else str(job.func)
            print(f"执行函数: {func_name}")
            
            # 尝试获取参数
            if hasattr(job, 'args') and job.args:
                print(f"参数: {job.args}")
                
            # 尝试获取下次运行时间（可能不存在）
            if hasattr(job, 'next_run_time'):
                print(f"下次运行时间: {job.next_run_time}")
            else:
                # 计算下次运行时间
                now = datetime.datetime.now()
                if hasattr(job.trigger, 'fields'):  # 修复: 直接检查trigger对象的属性
                    fields = job.trigger.fields
                    # 尝试从字段值构建时间信息
                    hour = None
                    minute = None
                    for field in fields:
                        if hasattr(field, 'name'):
                            if field.name == 'hour' and hasattr(field, 'expressions'):
                                hour_expr = field.expressions[0]
                                hour = hour_expr.first
                            elif field.name == 'minute' and hasattr(field, 'expressions'):
                                minute_expr = field.expressions[0]
                                minute = minute_expr.first
                    
                    if hour is not None and minute is not None:
                        # 构建下次可能的运行时间
                        next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        if next_time < now:
                            next_time = next_time + datetime.timedelta(days=1)
                        print(f"预计下次运行时间: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        print("无法确定下次运行时间")
                else:
                    print("无法确定下次运行时间(不是Cron触发器或没有fields属性)")
                
        except Exception as e:
            print(f"获取作业详情时出错: {str(e)}")
            import traceback
            traceback.print_exc()

    # 检查当前时间
    print("\n=====================")
    current_time = datetime.datetime.now()
    print(f"当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=====================")

if __name__ == "__main__":
    # 此脚本可直接运行
    pass
