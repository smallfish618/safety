import os
import requests
import shutil

def download_bootstrap_icons():
    """下载Bootstrap Icons字体文件"""
    # 创建目录结构
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, 'lib', 'bootstrap-icons', 'fonts')
    os.makedirs(fonts_dir, exist_ok=True)
    
    # 下载字体文件
    font_files = {
        'bootstrap-icons.woff': 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/fonts/bootstrap-icons.woff',
        'bootstrap-icons.woff2': 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/fonts/bootstrap-icons.woff2'
    }
    
    for filename, url in font_files.items():
        filepath = os.path.join(fonts_dir, filename)
        try:
            print(f"下载 {filename}...")
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)
                print(f"成功下载 {filename}")
            else:
                print(f"下载 {filename} 失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"下载 {filename} 出错: {e}")

if __name__ == "__main__":
    download_bootstrap_icons()
    print("完成下载任务，请重启应用。")
