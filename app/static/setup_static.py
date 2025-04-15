import os
import shutil
import requests
from zipfile import ZipFile
from io import BytesIO

def setup_bootstrap_icons():
    """设置Bootstrap Icons字体"""
    # 创建目录结构
    icons_dir = os.path.join(os.path.dirname(__file__), 'lib', 'bootstrap-icons')
    fonts_dir = os.path.join(icons_dir, 'fonts')
    css_dir = os.path.join(icons_dir, 'css')
    
    # 确保目录存在
    os.makedirs(fonts_dir, exist_ok=True)
    os.makedirs(css_dir, exist_ok=True)
    
    try:
        # 下载Bootstrap Icons
        print("下载Bootstrap Icons...")
        version = "1.11.3"  # 最新稳定版本
        url = f"https://github.com/twbs/icons/releases/download/v{version}/bootstrap-icons-{version}.zip"
        
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            # 解压文件
            with ZipFile(BytesIO(response.content)) as zip_file:
                # 提取所需文件
                for file in zip_file.namelist():
                    if file.startswith('fonts/'):
                        # 提取字体文件
                        filename = os.path.basename(file)
                        if filename:  # 跳过目录
                            with open(os.path.join(fonts_dir, filename), 'wb') as f:
                                f.write(zip_file.read(file))
                            print(f"已提取: {filename}")
                    
                    if file == 'bootstrap-icons.css':
                        # 提取CSS文件
                        with open(os.path.join(css_dir, 'bootstrap-icons.css'), 'wb') as f:
                            f.write(zip_file.read(file))
                        print("已提取: bootstrap-icons.css")
            
            print("Bootstrap Icons 设置完成！")
        else:
            print(f"下载失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"设置Bootstrap Icons时出错: {e}")
        
    # 创建自定义CSS引用本地字体
    create_custom_bootstrap_icons_css(css_dir, fonts_dir)

def create_custom_bootstrap_icons_css(css_dir, fonts_dir):
    """创建自定义CSS，确保字体路径正确"""
    custom_css = """
@font-face {
  font-display: block;
  font-family: "bootstrap-icons";
  src: url("../fonts/bootstrap-icons.woff2") format("woff2"),
       url("../fonts/bootstrap-icons.woff") format("woff");
}

[class^="bi-"]::before,
[class*=" bi-"]::before {
  display: inline-block;
  font-family: bootstrap-icons !important;
  font-style: normal;
  font-weight: normal !important;
  font-variant: normal;
  text-transform: none;
  line-height: 1;
  vertical-align: -0.125em;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
"""
    # 追加图标定义
    try:
        with open(os.path.join(css_dir, 'bootstrap-icons.css'), 'r', encoding='utf-8') as f:
            content = f.read()
            # 提取图标定义部分
            start = content.find('.bi-')
            if start > -1:
                custom_css += content[start:]
    except Exception as e:
        print(f"处理原始CSS时出错: {e}")
        
    # 写入自定义CSS
    try:
        with open(os.path.join(css_dir, 'bootstrap-icons-custom.css'), 'w', encoding='utf-8') as f:
            f.write(custom_css)
        print("已创建自定义Bootstrap Icons CSS")
    except Exception as e:
        print(f"创建自定义CSS时出错: {e}")

if __name__ == "__main__":
    setup_bootstrap_icons()
