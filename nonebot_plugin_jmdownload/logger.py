import logging
import os
import psutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from threading import Thread, Event
from time import sleep

from nonebot import logger as nonebot_logger
from nonebot_plugin_localstore import get_data_dir

# 日志目录
LOG_DIR = get_data_dir("nonebot_plugin_jmdownload") / "logs"

# 确保日志目录存在
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

class JMDownloadLogger:
    """禁漫下载插件日志处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger("nonebot_plugin_jmdownload")
        self.logger.setLevel(logging.INFO)
        
        # 创建按日期变化的文件处理器
        self._setup_file_handler()
        
        # 添加控制台处理器
        self._setup_console_handler()
    
    def _get_log_file_path(self) -> Path:
        """获取当天日志文件路径"""
        today = datetime.now().strftime("%Y-%m-%d")
        return Path(LOG_DIR) / f"{today}.log"
    
    def _setup_file_handler(self):
        """设置文件日志处理器"""
        log_file = self._get_log_file_path()
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def _setup_console_handler(self):
        """设置控制台日志处理器"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
    
    def info(self, msg: str, *args, **kwargs):
        """记录信息级别日志"""
        self.logger.info(msg, *args, **kwargs)
        nonebot_logger.info(f"[JMDownload] {msg}", *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """记录警告级别日志"""
        self.logger.warning(msg, *args, **kwargs)
        nonebot_logger.warning(f"[JMDownload] {msg}", *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """记录错误级别日志"""
        self.logger.error(msg, *args, **kwargs)
        nonebot_logger.error(f"[JMDownload] {msg}", *args, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        """记录调试级别日志"""
        self.logger.debug(msg, *args, **kwargs)
        nonebot_logger.debug(f"[JMDownload] {msg}", *args, **kwargs)
    
    def log_metrics(self, metrics: Dict[str, Any]):
        """记录系统指标日志"""
        msg = (
            f"系统资源使用情况 - "
            f"CPU: {metrics['cpu']}%, "
            f"内存: {metrics['memory']}%, "
            f"磁盘: {metrics['disk']}%"
        )
        self.info(msg)

class SystemMonitor:
    """系统资源监控器"""
    
    def __init__(self, interval: int = 60):
        self.interval = interval
        self._stop_event = Event()
        self._thread = Thread(target=self._monitor_loop, daemon=True)
    
    def start(self):
        """启动监控线程"""
        self._thread.start()
    
    def stop(self):
        """停止监控线程"""
        self._stop_event.set()
        self._thread.join()
    
    def _monitor_loop(self):
        """监控循环"""
        while not self._stop_event.is_set():
            metrics = self._collect_metrics()
            jm_logger.log_metrics(metrics)
            sleep(self.interval)
    
    def _collect_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        return {
            "cpu": psutil.cpu_percent(interval=1),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('/').percent
        }

# 全局日志实例
jm_logger = JMDownloadLogger()

# 全局系统监控实例
system_monitor = SystemMonitor()