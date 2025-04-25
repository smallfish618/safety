from waitress import serve
from run import app
import logging
import os
import time
from datetime import datetime
import threading
import sys
import signal
import traceback

# 配置日志
def setup_logging():
    """设置日志系统"""
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    # 配置文件日志
    file_handler = logging.FileHandler(os.path.join(log_dir, f'server_{datetime.now().strftime("%Y%m%d")}.log'))
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # 配置控制台日志
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # 配置根日志
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 设置waitress的日志级别
    logging.getLogger('waitress').setLevel(logging.INFO)
    
    return root_logger

class ServerManager:
    """服务器管理类，处理服务启动、监控和保活"""
    def __init__(self):
        self.logger = setup_logging()
        self.server_thread = None
        self.keepalive_thread = None
        self.running = False
        self.port = 5000
        self.host = '0.0.0.0'
        self.threads = 8  # waitress工作线程数
        
    def log_banner(self):
        """显示启动横幅信息"""
        banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                消防安全管理系统服务器                        ║
║                                                              ║
║  启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                      ║
║  监听地址: {self.host}:{self.port}                                    ║
║  工作线程: {self.threads}                                               ║
║  日志路径: /logs/server_*.log                                ║
╚══════════════════════════════════════════════════════════════╝
"""
        print(banner)
        self.logger.info(f"服务器正在启动 - 监听 {self.host}:{self.port}")
    
    def start_server(self):
        """在单独的线程中启动Waitress服务器"""
        def run_server():
            self.logger.info("Waitress服务器线程启动")
            try:
                serve(
                    app, 
                    host=self.host, 
                    port=self.port, 
                    threads=self.threads,
                    url_scheme='http',
                    channel_timeout=120,  # 通道超时时间
                    connection_limit=1000,  # 最大连接数
                    cleanup_interval=30,  # 清理间隔
                    asyncore_use_poll=True  # 使用poll替代select，可能在某些情况下更有效率
                )
            except Exception as e:
                self.running = False
                self.logger.error(f"服务器启动失败: {str(e)}")
                traceback.print_exc()
        
        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.running = True
        self.logger.info("服务器线程已启动")
    
    def start_keepalive(self):
        """启动保活线程，确保定时任务能正常执行"""
        def keepalive_worker():
            import requests
            interval = 300  # 每5分钟发送一次请求
            self.logger.info("保活线程已启动，将每5分钟请求一次服务以保持活跃")
            health_check_endpoint = f"http://localhost:{self.port}/test"
            
            while self.running:
                try:
                    response = requests.get(health_check_endpoint, timeout=10)
                    status = response.status_code
                    self.logger.info(f"保活请求: HTTP {status}")
                    
                    # 修改: 不再尝试访问app.scheduler
                    # 仅记录保活请求成功的信息
                    if status == 200:
                        self.logger.info("保活请求成功，服务正常运行")
                    else:
                        self.logger.warning(f"保活请求返回非正常状态码: {status}")
                    
                    # 睡眠指定间隔
                    time.sleep(interval)
                except requests.RequestException as e:
                    self.logger.warning(f"保活请求失败: {str(e)}")
                    time.sleep(60)  # 如果失败，等待1分钟后重试
                except Exception as e:
                    self.logger.error(f"保活线程错误: {str(e)}")
                    self.logger.debug(traceback.format_exc())  # 添加详细错误堆栈
                    time.sleep(60)
        
        self.keepalive_thread = threading.Thread(target=keepalive_worker)
        self.keepalive_thread.daemon = True
        self.keepalive_thread.start()
        self.logger.info("保活线程已启动")
    
    def monitor_server(self):
        """监控服务器状态"""
        try:
            while True:
                if not self.server_thread.is_alive():
                    self.logger.error("服务器线程已停止，尝试重新启动...")
                    self.start_server()
                
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            self.logger.info("收到键盘中断，服务器正在关闭...")
            self.running = False
    
    def handle_signals(self):
        """处理信号，以确保干净的退出"""
        def signal_handler(sig, frame):
            self.logger.info(f"收到信号 {sig}，服务器正在关闭...")
            self.running = False
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):  # Windows可能没有SIGTERM
            signal.signal(signal.SIGTERM, signal_handler)

    def start(self):
        """启动服务器和所有相关线程"""
        self.log_banner()
        self.handle_signals()
        
        # 启动服务器
        self.start_server()
        
        # 等待服务器就绪
        time.sleep(2)
        
        # 启动保活线程
        self.start_keepalive()
        
        # 监控服务器状态
        self.monitor_server()


# 作为主模块运行
if __name__ == "__main__":
    try:
        # 启动带有管理功能的服务器
        server = ServerManager()
        server.start()
    except Exception as e:
        print(f"服务器启动失败: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
