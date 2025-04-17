"""
手动触发定时任务，用于测试任务是否正常工作
"""
from app import create_app
from app.scheduler import send_scheduled_expiry_alerts
import traceback

def manually_trigger_task(config_id=1):
    """手动触发指定ID的定时任务"""
    print(f"准备手动触发定时任务 (ID: {config_id})...")
    
    app = create_app()
    
    with app.app_context():
        try:
            print("开始执行发送预警邮件任务...")
            result = send_scheduled_expiry_alerts(app, config_id)
            print(f"任务执行完成！")
            return True
        except Exception as e:
            print(f"执行任务时出错: {e}")
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("=== 手动触发定时预警邮件发送 ===")
    config_id = input("请输入要触发的任务ID (默认为1): ") or 1
    
    try:
        config_id = int(config_id)
    except ValueError:
        print(f"错误: ID必须是数字")
        exit(1)
        
    success = manually_trigger_task(config_id)
    
    if success:
        print("\n✅ 任务触发成功！请检查邮件是否已发送。")
        print("提示: 检查日志文件可获取更多信息。")
    else:
        print("\n❌ 任务触发失败。请查看上方错误信息。")
