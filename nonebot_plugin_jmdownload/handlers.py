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
        await jm_download.send(f"开始下载漫画 {comic_id}...")
        # 替换原来的async with用法
        downloader: DownloadManager = DownloadManager()
        comic_dir: Path = await downloader.download_comic(comic_id)
        
        # 转换为PDF
        await jm_download.send("开始转换为PDF...")
        converter: PDFConverter = PDFConverter(comic_dir, data_dir / "output", comic_id)
        pdf_path: Path = await converter.convert()
        # 清理临时文件
        await downloader.clear()
        
        # 发送文件
        if pdf_path.exists():
            # 使用实际生成的 PDF 路径
            file_uri = f"file:///{pdf_path.resolve().as_posix()}"
            await jm_download.send(Message(build_cq_file(file_uri)))
            # 删除PDF文件
            pdf_path.unlink()
        else:
            await jm_download.finish("PDF转换失败！")
            
    except Exception as e:
        logger.error(f"处理漫画 {comic_id} 时发生错误: {str(e)}")
        await jm_download.finish(f"发生错误：{str(e)}")

# 构造 CQ 码格式的文件消息
def build_cq_file(file_path: str) -> str:
    return f"[CQ:file,file={file_path}]"