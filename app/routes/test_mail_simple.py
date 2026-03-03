# test_mail_simple.py
import smtplib
from email.mime.text import MIMEText

# 邮件配置
mail_server = 'smtp.qq.com'
mail_port = 465
mail_user = '18184887@qq.com'
mail_pass = 'hqchnwmlbvhhbidg'  # 授权码
sender = '18184887@qq.com'
receiver = '18184887@qq.com'

# 创建邮件内容 - 简化头部格式
message = MIMEText('这是一封测试邮件，验证邮件发送功能是否正常。', 'plain', 'utf-8')
message['From'] = sender  # 直接使用邮箱地址
message['To'] = receiver  # 直接使用邮箱地址
message['Subject'] = '邮件发送测试'

try:
    print(f'正在连接 {mail_server}:{mail_port}...')
    smtp = smtplib.SMTP_SSL(mail_server, mail_port)
    smtp.login(mail_user, mail_pass)
    print('登录成功，正在发送邮件...')
    smtp.sendmail(sender, [receiver], message.as_string())
    smtp.quit()
    print('✅ 邮件发送成功！')
except smtplib.SMTPAuthenticationError:
    print('❌ 认证失败：请检查邮箱授权码是否正确')
except smtplib.SMTPConnectError:
    print('❌ 连接失败：请检查网络或 SMTP 服务器配置')
except Exception as e:
    print(f'❌ 发送失败：{e}')