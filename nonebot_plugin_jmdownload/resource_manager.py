import os
import tempfile
from typing import Any
import psutil
import logging

class ResourceManager:
    def __init__(self) -> None:
        self.temp_dirs: list[Any] = []
    
    def create_temp_dir(self, prefix: str = "temp_") -> str:
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        self.temp_dirs.append(temp_dir)
        logging.debug(f"创建临时目录: {temp_dir}")
        return temp_dir
    
    def cleanup_temp_files(self, temp_dir: str) -> None:
        """清理临时目录中的文件"""
        try:
            for f in os.listdir(temp_dir):
                try:
                    os.remove(os.path.join(temp_dir, f))
                except Exception as e:
                    logging.warning(f"删除临时文件 {f} 失败: {str(e)}")
            
            os.rmdir(temp_dir)
            logging.debug(f"临时目录清理完成: {temp_dir}")
            
        except Exception as e:
            logging.warning(f"清理临时目录失败: {str(e)}")
    
    def get_system_status(self) -> dict[str, float]:
        """获取系统状态信息"""
        mem_info = psutil.virtual_memory()
        cpu_percent: float = psutil.cpu_percent(interval=0.1)
        
        return {
            "cpu_percent": cpu_percent,
            "mem_percent": mem_info.percent,
            "available_mem": mem_info.available / (1024 * 1024 * 1024)  # GB
        }
    
    def calculate_optimal_workers(self, base_workers: int) -> int:
        """根据系统负载计算最优工作进程数"""
        system_load = psutil.cpu_percent(interval=0.1) / 100
        
        if system_load > 0.8:  # 系统负载高
            return max(1, base_workers // 4)
        elif system_load > 0.5:  # 系统负载中等
            return max(1, base_workers // 2)
        else:  # 系统负载低
            return max(1, base_workers - 1)