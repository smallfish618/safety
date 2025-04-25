from flask import Blueprint, jsonify, current_app, session, request
from flask_wtf.csrf import generate_csrf, CSRFProtect, CSRFError

admin_csrf_bp = Blueprint('admin_csrf', __name__)

@admin_csrf_bp.route('/get_csrf_token', methods=['GET'])
def get_csrf_token():
    """获取一个新的CSRF令牌"""
    token = generate_csrf()
    current_app.logger.info(f"已生成新的CSRF令牌: {token[:5]}...")
    return jsonify({'token': token})

@admin_csrf_bp.app_errorhandler(CSRFError)
def handle_csrf_error(e):
    """处理CSRF错误，返回JSON响应而不是重定向"""
    request_info = {
        'path': request.path,
        'method': request.method,
        'content_type': request.content_type,
        'has_csrf_token': 'X-CSRFToken' in request.headers or 'X-CSRF-TOKEN' in request.headers
    }
    current_app.logger.warning(f"CSRF验证错误: {str(e)}，请求信息: {request_info}")
    
    if request.content_type == 'application/json' or request.is_xhr:
        return jsonify({
            'success': False,
            'error': 'CSRF令牌验证失败，请刷新页面后重试',
            'error_type': 'CSRFError'
        }), 400
    return 'CSRF验证失败，请刷新页面后重试', 400
