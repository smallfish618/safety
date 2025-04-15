from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    """登录表单"""
    username = StringField('用户名', validators=[
        DataRequired('请输入用户名'),
        Length(min=3, max=30, message='用户名长度必须在3-30字符之间')
    ])
    password = PasswordField('密码', validators=[
        DataRequired('请输入密码')
    ])
    remember = BooleanField('记住我')
    submit = SubmitField('登录')
