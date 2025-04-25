from flask import jsonify
import traceback
from functools import wraps

def json_error_handler(f):
    """装饰器: 确保API总是返回JSON响应，即使在出错时"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            # 记录异常
            traceback.print_exc()
            # 返回JSON格式的错误响应
            return jsonify({
                'success': False,
                'error': str(e),
                'error_type': e.__class__.__name__
            }), 500
    return decorated_function
