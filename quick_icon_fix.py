"""
快速修复Bootstrap Icons字体问题
此脚本在不下载字体文件的情况下，通过CDN引用解决问题
"""
import os

def fix_icons():
    # 路径定义
    base_dir = os.path.dirname(os.path.abspath(__file__))
    css_dir = os.path.join(base_dir, 'app', 'static', 'css')
    icons_dir = os.path.join(base_dir, 'app', 'static', 'lib', 'bootstrap-icons')
    
    # 确保目录存在
    os.makedirs(os.path.join(icons_dir, 'fonts'), exist_ok=True)
    
    # 修改或创建bootstrap-icons.css
    css_content = """/* CDN版Bootstrap Icons */
@import url('https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.css');
"""
    
    with open(os.path.join(css_dir, 'bootstrap-icons.css'), 'w', encoding='utf-8') as f:
        f.write(css_content)
    
    print("Bootstrap Icons问题已修复：现在使用CDN版本")

if __name__ == "__main__":
    fix_icons()
