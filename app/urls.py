from flask import Flask
from werkzeug.routing import BaseConverter, ValidationError

class IntegerOrEmptyConverter(BaseConverter):
    """处理整数或空字符串的URL参数转换器"""
    
    def to_python(self, value):
        if value == '':
            return None
        try:
            return int(value)
        except ValueError:
            raise ValidationError()
    
    def to_url(self, value):
        if value is None:
            return ''
        return str(value)

def register_converters(app):
    """向应用注册自定义URL转换器"""
    app.url_map.converters['int_or_empty'] = IntegerOrEmptyConverter
