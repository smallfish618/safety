from flask import Flask

def disable_template_cache(app):
    """禁用Flask的模板缓存"""
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # 修改Jinja2环境配置
    if hasattr(app, 'jinja_env'):
        app.jinja_env.auto_reload = True
        app.jinja_env.cache_size = 0
