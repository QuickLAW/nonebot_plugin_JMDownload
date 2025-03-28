from jmcomic.jm_option import JmOption
from nonebot import logger


from pathlib import Path
from .config import jm_config, jm_config_path
from .utils import collect_image_files, check_image_files
import jmcomic
# 在文件顶部添加导入
import shutil
import asyncio

class DownloadManager:
    def __init__(self) -> None:
        self.config = jm_config

    async def download_comic(self, comic_id: str) -> Path:
        """下载漫画并返回保存目录"""
        # 清空下载目录
        await self.clear()
        try:
            # 初始化下载配置
            load_config: JmOption = jmcomic.JmOption.from_file(filepath=jm_config_path)
            base_dir = Path(jm_config['dir_rule']['base_dir'])
            
            # 最多尝试3次下载（初始1次+重试2次）
            for attempt in range(3):
                # 使用asyncio.to_thread将同步下载操作转换为异步
                await asyncio.to_thread(jmcomic.download_album, comic_id, load_config)
                
                # 检查下载的图片文件
                imgs_list: list[Path] = collect_image_files(base_dir)
                imgs_list, download_again = check_image_files(imgs_list)
                
                # 如果没有损坏的图片，提前结束循环
                if not download_again:
                    break
                    
            return Path(jm_config['dir_rule']['base_dir'])
            
        except Exception as e:
            logger.error(f"下载漫画 {comic_id} 失败: {str(e)}")
            raise DownloadError(f"下载漫画 {comic_id} 失败: {str(e)}")
        
    # 清理临时文件
    async def clear(self) -> None:
        """清理临时文件"""
        try:
            # 清理下载目录
            download_dir: Path = Path(jm_config['dir_rule']['base_dir'])
            for item in download_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)

        except Exception as e:
            logger.error(f"清理临时文件失败: {str(e)}")
            raise DownloadError(f"清理临时文件失败: {str(e)}")


class DownloadError(Exception):
    """下载错误异常"""
    pass