from pathlib import Path
from .config import jm_config, jm_config_path
import jmcomic
# 在文件顶部添加导入
import shutil
import asyncio

class DownloadManager:
    def __init__(self):
        self.config = jm_config

    async def download_comic(self, comic_id: str) -> Path:
        """下载漫画并返回保存目录"""
        try:
            # 初始化下载配置
            load_config = jmcomic.JmOption.from_file(jm_config_path)
            
            # 使用asyncio.to_thread将同步下载操作转换为异步
            await asyncio.to_thread(jmcomic.download_album, comic_id, load_config)
                
            return jm_config['dir_rule']['base_dir']
            
        except Exception as e:
            raise DownloadError(f"下载漫画 {comic_id} 失败: {str(e)}")
        
    # 清理临时文件
    async def clear(self):
        """清理临时文件"""
        try:
            # 清理下载目录
            download_dir = Path(jm_config['dir_rule']['base_dir'])
            for item in download_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)

        except Exception as e:
            raise DownloadError(f"清理临时文件失败: {str(e)}")


class DownloadError(Exception):
    """下载错误异常"""
    pass