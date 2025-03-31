import asyncio
from socket import timeout
from nonebot_plugin_jmdownload.pdf_converter import PDFConverter


from nonebot_plugin_jmdownload.download import DownloadManager


from pathlib import Path
from nonebot import on_command
from nonebot.adapters.onebot.v11.message import MessageSegment, Message
from nonebot.params import CommandArg

from .config import global_config, jm_config
from .download import DownloadManager
from .pdf_converter import PDFConverter
from .utils import logger, ensure_dir

# 获取插件数据目录
data_dir = Path("data/nonebot_plugin_jmdownload")
ensure_dir(data_dir)

# 配置文件路径
config_path = data_dir / "config.yml"

# 注册命令
jm_download = on_command("jm", aliases={"JM", "Jm", "jM"}, priority=5)

@jm_download.handle()
async def handle_jm(args: Message = CommandArg()):
    # 获取参数
    arg_text = args.extract_plain_text().strip().split()
    if len(arg_text) != 2 or arg_text[0] not in ["download", "下载"]:
        await jm_download.finish("格式错误！请使用：/jm download <序号> 或 /jm 下载 <序号>")
    
    comic_id = arg_text[1]
    
    try:
        # 下载漫画
        await jm_download.send(f"开始下载漫画 {comic_id}...\n这可能需要一些时间，请耐心等待。下载过程中会定期发送进度报告。")
        
        # 创建下载管理器
        downloader: DownloadManager = DownloadManager()
        
        # 设置下载超时和进度报告间隔
        download_timeout = 3600  # 1小时超时
        progress_interval = 30   # 30秒报告一次进度
        
        # 创建进度报告任务
        last_progress_time = 0
        
        # 异步下载漫画，添加超时控制
        try:
            comic_dir: Path = await downloader.download_comic(comic_id, timeout=download_timeout, progress_interval=progress_interval)
            
            # 下载完成后发送通知
            await jm_download.send(f"漫画 {comic_id} 下载完成，开始转换为PDF...")
            
            # 转换为PDF
            # 从环境变量中读取输出目录配置，如果不存在则使用默认值
            output_dir = Path(global_config.get('jmdownload_output_dir', 'data/nonebot_plugin_jmdownload/outputs'))
            ensure_dir(output_dir)  # 确保输出目录存在
            converter: PDFConverter = PDFConverter(comic_dir, output_dir, comic_id)
            pdf_path: Path = await converter.convert()
            
            # 清理临时文件
            await downloader.clear()
            
            # 发送文件
            if pdf_path.exists():
                # 使用实际生成的 PDF 路径
                file_uri = f"file:///{pdf_path.resolve().as_posix()}"
                
                # 发送上传开始通知
                await jm_download.send(f"PDF生成完成，开始上传文件...\n文件较大，上传可能需要一些时间，请耐心等待")
                
                # 创建上传进度反馈任务
                upload_feedback_task = None
                
                # 获取文件大小并预估上传时间
                file_size = pdf_path.stat().st_size / (1024 * 1024)  # MB
                estimated_time = max(300, int(file_size * 10))  # 预估时间(10秒/MB)
                
                async def send_upload_progress():
                    count = 0
                    try:
                        while True:
                            count += 1
                            await asyncio.sleep(10)
                            progress = min(100, count*10/estimated_time*100)
                            await jm_download.send(f"文件上传中，进度: {progress:.1f}%，已耗时 {count*10} 秒，预计剩余时间 {max(0, estimated_time-count*10)} 秒")
                    except asyncio.CancelledError:
                        pass
                
                try:
                    # 启动上传进度反馈任务
                    upload_feedback_task = asyncio.create_task(send_upload_progress())
                    
                    # 发送文件
                    try:
                        await jm_download.send(Message(build_cq_file(file_uri)), timeout=600)
                    except Exception as e:
                        if "NetWorkError" in str(e) and "WebSocket call api send_msg timeout" in str(e):
                            logger.warning(f"文件上传超时，但上传仍在后台继续: {str(e)}")
                        else:
                            raise e
                    
                    # 上传完成，取消进度反馈任务
                    if upload_feedback_task and not upload_feedback_task.done():
                        upload_feedback_task.cancel()
                    
                    # 发送上传完成通知
                    await jm_download.send("文件上传完成！")
                    
                    # 删除PDF文件
                    pdf_path.unlink()
                except Exception as e:
                    # 出错时也要取消进度反馈任务
                    if upload_feedback_task and not upload_feedback_task.done():
                        upload_feedback_task.cancel()
                    raise e
            else:
                await jm_download.finish("PDF转换失败！")
                
        except asyncio.TimeoutError:
            await jm_download.finish(f"下载漫画 {comic_id} 超时，请稍后再试或检查网络连接")
            return
            
    except Exception as e:
        logger.error(f"处理漫画 {comic_id} 时发生错误: {str(e)}")
        await jm_download.finish(f"发生错误：{str(e)}")

# 构造 CQ 码格式的文件消息
def build_cq_file(file_path: str) -> str:
    return f"[CQ:file,file={file_path}]"