from jmcomic.api import __DOWNLOAD_API_RET


from _asyncio import Task


from jmcomic.api import __DOWNLOAD_API_RET


from jmcomic.jm_option import JmOption
from nonebot import logger


from pathlib import Path
from .config import jm_config, config_path, global_config
from .utils import collect_image_files, check_image_files
import jmcomic
# 导入所需模块
import shutil
import asyncio
import time
import concurrent.futures

class DownloadManager:
    def __init__(self) -> None:
        self.config = jm_config

    async def download_comic(self, comic_id: str, timeout: int = 3600, progress_interval: int = 30) -> Path:
        """下载漫画并返回保存目录
        
        Args:
            comic_id: 漫画ID
            timeout: 下载超时时间（秒），默认1小时
            progress_interval: 进度报告间隔（秒），默认30秒
            
        Returns:
            Path: 下载目录路径
            
        Raises:
            DownloadError: 下载失败时抛出
        """
        # 清空下载目录
        await self.clear()
        download_start_time: float = time.time()
        download_task: Task[__DOWNLOAD_API_RET | set[__DOWNLOAD_API_RET]] = None
        progress_task: Task[None] = None
        
        try:
            # 初始化下载配置
            load_config: JmOption = jmcomic.JmOption.from_file(filepath=config_path.__str__())
            base_dir: Path = Path(jm_config['dir_rule']['base_dir'])
            base_dir.mkdir(parents=True, exist_ok=True)
            
            # 从环境变量中读取输出目录配置，如果不存在则使用默认值
            output_dir: Path = Path(global_config.get('jmdownload_output_dir', 'data/nonebot_plugin_jmdownload/outputs'))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建下载进度报告任务
            progress_task: Task[None] = asyncio.create_task(self._report_download_progress(comic_id, base_dir, progress_interval))
            
            # 最多尝试3次下载（初始1次+重试2次）
            for attempt in range(3):
                logger.info(f"开始下载漫画 {comic_id}，第 {attempt+1} 次尝试")
                
                try:
                    # 使用run_in_executor和超时控制执行下载
                    # 创建线程池执行器
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        # 创建下载任务
                        download_task: Task[__DOWNLOAD_API_RET | set[__DOWNLOAD_API_RET]] = asyncio.create_task(
                            asyncio.wait_for(
                                asyncio.get_event_loop().run_in_executor(
                                    pool, 
                                    lambda: jmcomic.download_album(jm_album_id=comic_id, option=load_config)
                                ),
                                timeout=timeout
                            )
                        )
                        
                        # 等待下载完成
                        await download_task
                        
                except asyncio.TimeoutError:
                    logger.error(f"下载漫画 {comic_id} 超时（{timeout}秒）")
                    raise DownloadError(f"下载漫画 {comic_id} 超时，请稍后再试或检查网络连接")
                except asyncio.CancelledError:
                    logger.warning(f"下载漫画 {comic_id} 任务被取消")
                    raise DownloadError(f"下载漫画 {comic_id} 任务被取消")
                except Exception as e:
                    logger.error(f"下载漫画 {comic_id} 第 {attempt+1} 次尝试失败: {str(e)}")
                    if attempt == 2:  # 最后一次尝试
                        raise DownloadError(f"下载漫画 {comic_id} 失败: {str(e)}")
                    continue  # 继续下一次尝试
                
                # 检查下载的图片文件
                imgs_list: list[Path] = collect_image_files(base_dir)
                if not imgs_list:
                    logger.warning(f"下载漫画 {comic_id} 未找到图片文件，尝试重新下载")
                    continue
                    
                imgs_list, download_again = check_image_files(imgs_list)
                
                # 如果没有损坏的图片，提前结束循环
                if not download_again:
                    download_time = time.time() - download_start_time
                    logger.info(f"漫画 {comic_id} 下载完成，共 {len(imgs_list)} 张图片，耗时 {download_time:.2f} 秒")
                    break
                else:
                    logger.warning(f"漫画 {comic_id} 存在损坏图片，尝试重新下载")
            
            return Path(jm_config['dir_rule']['base_dir'])
            
        except Exception as e:
            logger.error(f"下载漫画 {comic_id} 失败: {str(e)}")
            raise DownloadError(f"下载漫画 {comic_id} 失败: {str(e)}")
        finally:
            # 取消进度报告任务
            if progress_task and not progress_task.done():
                progress_task.cancel()
                try:
                    await progress_task
                except asyncio.CancelledError:
                    pass
        
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


    async def _report_download_progress(self, comic_id: str, base_dir: Path, interval: int = 30) -> None:
        """定期报告下载进度，防止进程被系统关闭
        
        Args:
            comic_id: 漫画ID
            base_dir: 下载目录
            interval: 报告间隔（秒）
        """
        try:
            while True:
                # 等待指定间隔
                await asyncio.sleep(interval)
                
                # 收集当前下载的图片
                try:
                    imgs_list = collect_image_files(base_dir)
                    if imgs_list:
                        logger.info(f"漫画 {comic_id} 下载进度: 已下载 {len(imgs_list)} 张图片")
                    else:
                        logger.info(f"漫画 {comic_id} 下载进度: 正在获取漫画信息...")
                except Exception as e:
                    logger.warning(f"获取下载进度时出错: {str(e)}")
        except asyncio.CancelledError:
            # 任务被取消，正常退出
            pass
        except Exception as e:
            logger.error(f"进度报告任务异常: {str(e)}")


class DownloadError(Exception):
    """下载错误异常"""
    pass