import random
import string
from datetime import datetime, timedelta
from flask import current_app, url_for
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 存储验证码的临时字典（实际应用中可能使用Redis或数据库）
verification_codes = {}

def generate_code(length=6):
    """生成指定长度的数字验证码"""
    return ''.join(random.choices(string.digits, k=length))

def send_verification_email(email):
    """
    发送验证码到指定邮箱
    
    Args:
        email: 目标邮箱地址
    
    Returns:
        bool: 发送成功返回True，失败返回False
    """
    try:
        # 生成验证码
        code = generate_code()
        
        # 设置验证码有效期（30分钟）
        expiry_time = datetime.now() + timedelta(minutes=30)
        verification_codes[email] = {
            'code': code,
            'expiry': expiry_time
        }
        
        # 检查是否配置了邮件服务器
        mail_server = current_app.config.get('MAIL_SERVER')
        mail_port = current_app.config.get('MAIL_PORT')
        mail_username = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')
        mail_use_ssl = current_app.config.get('MAIL_USE_SSL', False)
        mail_use_tls = current_app.config.get('MAIL_USE_TLS', False)
        
        if not all([mail_server, mail_port, mail_username, mail_password]):
            print("邮件服务器配置不完整，无法发送邮件")
            # 测试环境下可直接返回验证码而不发送邮件
            print(f"测试验证码: {code}")
            return True
            
        # 创建邮件内容
        subject = "消防安全管理系统 - 验证码"
        body = f"""
        <html>
            <body>
                <h2>消防安全管理系统验证码</h2>
                <p>您好，您的邮箱验证码是: <strong>{code}</strong></p>
                <p>验证码有效期为30分钟，请尽快使用。</p>
                <p>如果这不是您的操作，请忽略此邮件。</p>
            </body>
        </html>
        """
        
        # 创建消息对象
        message = MIMEMultipart()
        message['From'] = mail_username
        message['To'] = email
        message['Subject'] = subject
        
        # 添加HTML内容
        message.attach(MIMEText(body, 'html'))
        
        # 连接邮件服务器并发送邮件
        if mail_use_ssl:
            server = smtplib.SMTP_SSL(mail_server, mail_port)
        else:
            server = smtplib.SMTP(mail_server, mail_port)
            if mail_use_tls:
                server.starttls()
                
        server.login(mail_username, mail_password)
        server.send_message(message)
        server.quit()
        
        return True
        
    except Exception as e:
        print(f"发送验证码邮件错误: {e}")
        return False

def verify_code(email, code):
    """
    验证邮箱验证码是否正确
    
    Args:
        email: 邮箱地址
        code: 用户提交的验证码
    
    Returns:
        bool: 验证成功返回True，失败返回False
    """
    try:
        # 获取存储的验证码
        stored_data = verification_codes.get(email)
        if not stored_data:
            return False
            
        stored_code = stored_data.get('code')
        expiry_time = stored_data.get('expiry')
        
        # 验证码是否过期
        if datetime.now() > expiry_time:
            # 删除过期验证码
            del verification_codes[email]
            return False
            
        # 验证码是否匹配
        if code == stored_code:
            # 验证成功后删除验证码，防止重复使用
            del verification_codes[email]
            return True
        else:
            return False
            
    except Exception as e:
        print(f"验证码验证错误: {e}")
        return False