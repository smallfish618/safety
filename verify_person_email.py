#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证邮件修复 - 测试负责人邮件发送
"""
import sys
sys.path.insert(0, '.')

from app import create_app, db
from app.models.station import ResponsiblePerson
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formatdate, make_msgid
import smtplib
from config import Config

app = create_app()

print("=" * 70)
print("邮件修复验证 - 测试负责人邮件发送")
print("=" * 70)

# 获取配置
mail_config = {
    'server': Config.MAIL_SERVER,
    'port': Config.MAIL_PORT,
    'use_ssl': Config.MAIL_USE_SSL,
    'username': Config.MAIL_USERNAME,
    'password': Config.MAIL_PASSWORD,
    'sender': Config.MAIL_DEFAULT_SENDER,
}

with app.app_context():
    # 获取所有负责人
    responsible_persons = ResponsiblePerson.query.all()
    print(f"\n找到 {len(responsible_persons)} 个负责人")
    
    if not responsible_persons:
        print("✗ 没有负责人数据")
        sys.exit(1)
    
    # 选择第一个负责人进行测试
    test_person = responsible_persons[0]
    print(f"\n选择用于测试的负责人: {test_person.person_name}")
    print(f"邮箱地址: {test_person.email}")
    
    # 处理发件人格式
    if isinstance(mail_config['sender'], tuple):
        sender_name, sender_email = mail_config['sender']
        mail_sender_email = sender_email
        print(f"发件人邮箱: {sender_email}")
        print(f"发件人名称: {sender_name}")
    else:
        mail_sender_email = mail_config['sender']
        print(f"发件人邮箱: {mail_sender_email}")
    
    # 创建测试邮件
    print("\n【创建邮件】")
    msg = MIMEMultipart('alternative')
    
    # ★ 关键检查：From头格式
    print(f"设置From头: {mail_sender_email}")
    msg['From'] = mail_sender_email  # ★ 只使用邮箱地址，不带显示名
    msg['To'] = test_person.email
    msg['Subject'] = Header('消防系统 - 负责人邮件测试', 'utf-8')
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid()
    msg['X-Priority'] = '3'
    msg['X-Mailer'] = 'Fire Safety Management System'
    
    # 邮件内容
    html_content = f"""
    <html>
        <body>
            <h2>消防安全预警邮件</h2>
            <p>尊敬的 {test_person.person_name} 负责人：</p>
            <p>您有物资即将到期，请及时更换维修。</p>
            <p>详情请登录系统查看。</p>
            <p>时间: {formatdate(localtime=True)}</p>
        </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    print(f"邮件大小: {len(msg.as_string())} 字节")
    
    # 发送测试邮件
    print(f"\n【发送邮件】")
    try:
        if mail_config['use_ssl']:
            print(f"使用SSL连接: {mail_config['server']}:{mail_config['port']}")
            server = smtplib.SMTP_SSL(mail_config['server'], mail_config['port'], timeout=30)
        else:
            print(f"使用普通连接: {mail_config['server']}:{mail_config['port']}")
            server = smtplib.SMTP(mail_config['server'], mail_config['port'], timeout=30)
        
        print("✓ 已连接到SMTP服务器")
        
        # 登录
        server.login(mail_config['username'], mail_config['password'])
        print("✓ 身份认证成功")
        
        # 发送
        server.sendmail(mail_sender_email, [test_person.email], msg.as_string())
        print(f"✓ 邮件已发送给 {test_person.person_name} ({test_person.email})")
        
        # 关闭连接
        try:
            server.quit()
            print("✓ 连接已正常关闭")
        except:
            server.close()
            print("✓ 连接已强制关闭")
        
        print("\n✅ 邮件发送成功！")
        print(f"\n📧 请检查 {test_person.email} 的邮箱以验证邮件是否送达")
        
    except smtplib.SMTPServerDisconnected as e:
        print(f"✗ SMTP服务器连接被关闭: {e}")
        print("可能的原因: From头格式错误, 邮件内容过大, 或服务器超时")
        
    except smtplib.SMTPException as e:
        print(f"✗ SMTP错误: {e}")
        print("错误代码和详情请检查上方")
        
    except Exception as e:
        print(f"✗ 错误: {e}")

print("\n" + "=" * 70)
