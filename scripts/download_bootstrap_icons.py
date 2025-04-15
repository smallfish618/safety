"""
下载Bootstrap Icons字体文件到正确的目录
"""
import os
import requests
import shutil
from pathlib import Path

# 创建目标目录
target_dir = Path('app/static/lib/bootstrap-icons/fonts')
os.makedirs(target_dir, exist_ok=True)

# Bootstrap Icons CDN字体URL
font_urls = {
    'woff2': 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.woff2',
    'woff': 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.woff',
}

print("开始下载Bootstrap Icons字体文件...")

# 下载字体文件
for ext, url in font_urls.items():
    try:
        print(f"正在下载 {ext} 字体文件...")
        response = requests.get(url, stream=True)
        response.raise_for_status()  # 如果请求失败，抛出异常
        
        # 保存文件
        file_path = target_dir / f"bootstrap-icons.{ext}"
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
            
        print(f"{ext} 字体文件已保存到 {file_path}")
    except Exception as e:
        print(f"下载 {ext} 字体文件失败: {str(e)}")

print("下载完成！")
