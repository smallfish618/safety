from flask import current_app, session
import hashlib
import os

def generate_csrf_token():
    """生成CSRF令牌"""
    if '_csrf_token' not in session:
        session['_csrf_token'] = hashlib.sha256(os.urandom(64)).hexdigest()
    return session['_csrf_token']

def validate_csrf_token(token):
    """验证CSRF令牌"""
    if not token or token != session.get('_csrf_token'):
        return False
    return True
