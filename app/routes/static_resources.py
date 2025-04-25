from flask import Blueprint, current_app, send_from_directory
import os

static_bp = Blueprint('static_resources', __name__)

@static_bp.route('/fonts/<path:filename>')
def serve_fonts(filename):
    """提供字体文件服务"""
    fonts_folder = os.path.join(current_app.root_path, 'static', 'fonts')
    return send_from_directory(fonts_folder, filename)
