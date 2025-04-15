from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Optional, NumberRange

class ExpiryRuleForm(FlaskForm):
    """有效期规则表单"""
    # 将字符串字段改为选择字段，限定选择范围
    item_category = SelectField('物品类别', 
                              choices=[
                                  ('防护穿戴', '防护穿戴'),
                                  ('灭火使用', '灭火使用'),
                                  ('应急疏散', '应急疏散')
                              ],
                              validators=[DataRequired('请选择物品类别')])
    item_name = StringField('物品名称', validators=[DataRequired('请输入物品名称')])
    normal_expiry = FloatField('正常使用有效期(年)', 
                             validators=[DataRequired('请输入正常使用有效期'), 
                                       NumberRange(min=0, message='有效期必须为正数')])
    mandatory_expiry = FloatField('强制报废期(年)', 
                                validators=[Optional(), 
                                          NumberRange(min=0, message='报废期必须为正数')])
    description = TextAreaField('规则说明', validators=[Optional()])
