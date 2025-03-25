from pathlib import Path
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from .config import global_config
from .download import DownloadManager
from .pdf_converter import PDFConverter
from .utils import logger, ensure_dir
from .handlers import jm_download  # 导入处理器


__version__ = '1.2.0'

__plugin_meta__ = PluginMetadata(
    name="JM漫画下载",
    description="下载JM漫画并转换为PDF",
    usage="/jm download <序号> 或 /jm 下载 <序号>",
    type="application",
    homepage="https://github.com/QuickLAW/nonebot_plugin_JMDownload",
    supported_adapters={"~onebot.v11"},
)

# 获取插件数据目录
data_dir = Path("data/nonebot_plugin_jmdownload")
ensure_dir(data_dir)