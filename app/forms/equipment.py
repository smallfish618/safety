from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length

class EquipmentForm(FlaskForm):
    """物资信息表单"""
    area_code = StringField('区域编码', validators=[DataRequired('请输入区域编码')])
    area_name = StringField('区域名称', validators=[DataRequired('请输入区域名称')])
    category = StringField('物资类别', validators=[DataRequired('请输入物资类别')])
    name = StringField('物资名称', validators=[DataRequired('请输入物资名称')])
    model = StringField('规格型号')  
    unit = StringField('计量单位', validators=[DataRequired('请输入计量单位')])
    quantity = StringField('数量', validators=[DataRequired('请输入数量')])
    description = TextAreaField('备注说明')
    manufacturer = StringField('生产厂家')
    status = SelectField('状态', choices=[
        ('normal', '正常'),
        ('maintenance', '维护中'),
        ('repair', '维修中'),
        ('scrapped', '已报废')
    ], default='normal')
