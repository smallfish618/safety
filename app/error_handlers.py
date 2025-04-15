from flask import render_template, flash, current_app, url_for, redirect

def register_error_handlers(app):
    """注册应用错误处理器"""
    
    @app.errorhandler(404)
    def page_not_found(e):
        """处理404错误"""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        """处理500错误"""
        return render_template('errors/404.html', error="服务器内部错误"), 500
    
    @app.errorhandler(401)
    def unauthorized(e):
        """处理401未认证错误"""
        flash('请先登录后再访问此页面', 'warning')
        return redirect(url_for('auth.login'))
    
    @app.errorhandler(403)
    def forbidden(e):
        """处理403权限错误"""
        flash('您没有权限访问该页面', 'warning')
        return render_template('errors/404.html', error="权限不足"), 403
    
    @app.errorhandler(400)
    def bad_request(e):
        """处理400错误，包括CSRF错误"""
        if 'CSRF' in str(e):
            flash('安全验证失败，请重新提交表单', 'danger')
            return redirect(url_for('auth.login'))
        return render_template('errors/404.html', error="请求错误"), 400
