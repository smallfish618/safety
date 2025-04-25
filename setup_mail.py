import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configparser

def clear_screen():
    """清空控制台"""
    if sys.platform == 'win32':
        os.system('cls')
    else:
        os.system('clear')

def create_env_file(settings):
    """创建或更新.env文件"""
    with open('.env', 'w') as f:
        for key, value in settings.items():
            f.write(f"{key}={value}\n")
    print("✅ .env文件已创建/更新!")

def test_smtp_connection(server, port, username, password, use_ssl=True, use_tls=False):
    """测试SMTP连接"""
    try:
        print(f"📧 正在测试到 {server}:{port} 的连接...")
        
        if use_ssl:
            smtp = smtplib.SMTP_SSL(server, port, timeout=10)
        else:
            smtp = smtplib.SMTP(server, port, timeout=10)
            if use_tls:
                print("启用TLS...")
                smtp.starttls()
        
        print("✓ 连接成功!")
        
        if username and password:
            print(f"🔑 使用账户 {username} 登录...")
            smtp.login(username, password)
            print("✓ 登录成功!")
            
            # 尝试发送测试邮件
            if input("是否发送测试邮件? (y/n): ").lower() == 'y':
                recipient = input("请输入测试邮件接收地址: ")
                if not recipient or '@' not in recipient:
                    print("❌ 无效的接收地址，跳过测试邮件发送")
                else:
                    msg = MIMEMultipart()
                    msg['Subject'] = "消防安全管理系统邮件测试"
                    msg['From'] = username
                    msg['To'] = recipient
                    
                    content = MIMEText("""
                    <h2>消防安全管理系统</h2>
                    <p>这是一封测试邮件，如果您收到这封邮件，说明系统邮件功能已正确配置。</p>
                    <p>感谢您使用我们的系统!</p>
                    """, 'html', 'utf-8')
                    msg.attach(content)
                    
                    print("📤 正在发送测试邮件...")
                    smtp.sendmail(username, [recipient], msg.as_string())
                    print("✅ 测试邮件发送成功!")
        
        smtp.quit()
        print("✓ SMTP测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ SMTP测试失败: {str(e)}")
        return False

def setup_mail_config():
    """设置邮件服务器配置"""
    clear_screen()
    print("="*60)
    print("      消防安全管理系统 - 邮件服务器配置向导      ")
    print("="*60)
    print("\n此向导将帮助您配置系统邮件服务器设置。")
    print("这些设置将允许系统发送自动预警邮件和通知。\n")
    
    # 初始化配置
    config = {
        'MAIL_SERVER': '',
        'MAIL_PORT': '',
        'MAIL_USE_SSL': '',
        'MAIL_USE_TLS': '',
        'MAIL_USERNAME': '',
        'MAIL_PASSWORD': '',
        'MAIL_DEFAULT_SENDER': ''
    }
    
    # 读取现有配置
    if os.path.exists('.env'):
        print("发现现有配置，正在加载...")
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    if key in config:
                        config[key] = value
    
    # 配置向导
    print("\n请输入以下信息 (直接按回车使用当前值):\n")
    
    # SMTP服务器
    default = config['MAIL_SERVER'] or 'smtp.qq.com'
    config['MAIL_SERVER'] = input(f"SMTP服务器地址 [{default}]: ") or default
    
    # 端口
    default = config['MAIL_PORT'] or '465'
    config['MAIL_PORT'] = input(f"SMTP端口 [{default}]: ") or default
    
    # SSL/TLS
    default = config['MAIL_USE_SSL'] or 'True'
    use_ssl = input(f"使用SSL连接? (True/False) [{default}]: ") or default
    config['MAIL_USE_SSL'] = use_ssl
    
    if use_ssl.lower() == 'false':
        default = config['MAIL_USE_TLS'] or 'False'
        config['MAIL_USE_TLS'] = input(f"使用TLS连接? (True/False) [{default}]: ") or default
    else:
        config['MAIL_USE_TLS'] = 'False'
    
    # 邮箱账户
    default = config['MAIL_USERNAME'] or ''
    config['MAIL_USERNAME'] = input(f"邮箱账户 [{default}]: ") or default
    
    # 密码/授权码
    if config['MAIL_PASSWORD']:
        use_existing = input("是否使用已保存的密码/授权码? (y/n): ").lower() == 'y'
        if not use_existing:
            config['MAIL_PASSWORD'] = input("邮箱密码/授权码: ")
    else:
        config['MAIL_PASSWORD'] = input("邮箱密码/授权码: ")
    
    # 发件人
    default = config['MAIL_DEFAULT_SENDER'] or config['MAIL_USERNAME']
    config['MAIL_DEFAULT_SENDER'] = input(f"发件人显示名 [{default}]: ") or default
    
    # 测试连接
    print("\n正在测试SMTP连接...")
    connection_success = test_smtp_connection(
        config['MAIL_SERVER'], 
        int(config['MAIL_PORT']), 
        config['MAIL_USERNAME'], 
        config['MAIL_PASSWORD'],
        config['MAIL_USE_SSL'].lower() == 'true',
        config['MAIL_USE_TLS'].lower() == 'true'
    )
    
    if connection_success or input("\n是否保存这些设置? (y/n): ").lower() == 'y':
        create_env_file(config)
        print("\n✅ 邮件服务器配置已保存!")
        print("系统将在下次启动时使用这些设置。")
    else:
        print("\n❌ 配置未保存。")
    
    input("\n按回车键继续...")

if __name__ == "__main__":
    setup_mail_config()
