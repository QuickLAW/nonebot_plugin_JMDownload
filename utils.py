import logging
from pathlib import Path

# 配置日志记录器
logger = logging.getLogger('nonebot_plugin_jmdownload')
logger.setLevel(logging.INFO)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 设置日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# 添加处理器到日志记录器
logger.addHandler(console_handler)

def ensure_dir(path: Path) -> Path:
    """确保目录存在，如果不存在则创建"""
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_safe_filename(filename: str) -> str:
    """获取安全的文件名，移除不合法字符"""
    return ''.join(c for c in filename if c.isalnum() or c in '._- ')