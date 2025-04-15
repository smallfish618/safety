import os
import shutil

# 删除 Flask 的缓存目录
cache_dirs = [
    '__pycache__',
    'app/__pycache__',
    'app/routes/__pycache__',
    'app/models/__pycache__'
]

for cache_dir in cache_dirs:
    if os.path.exists(cache_dir):
        print(f"删除缓存目录: {cache_dir}")
        shutil.rmtree(cache_dir)

print("缓存清理完成，请重新启动应用")
