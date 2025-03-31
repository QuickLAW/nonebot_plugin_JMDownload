from pathlib import Path
from nonebot.plugin import PluginMetadata
from nonebot_plugin_localstore import get_data_dir
from .config import global_config
from .download import DownloadManager
from .pdf_converter import PDFConverter
from .utils import logger, ensure_dir
from .handlers import jm_download  # 导入处理器


__version__ = '1.5.0b5'

__plugin_meta__ = PluginMetadata(
    name="JM漫画下载",
    description="下载JM漫画并转换为PDF",
    usage="/jm download <序号> 或 /jm 下载 <序号>",
    type="application",
    homepage="https://github.com/QuickLAW/nonebot_plugin_JMDownload",
    supported_adapters={"~onebot.v11"},
)

# 使用localstore获取插件数据目录
data_dir = get_data_dir("nonebot_plugin_jmdownload")
ensure_dir(data_dir)

# 确保下载和输出目录存在
from .config import jm_config, global_config
downloads_dir = Path(jm_config['dir_rule']['base_dir'])
# 从环境变量中读取输出目录配置，如果不存在则使用默认值
outputs_dir = Path(global_config.get('jmdownload_output_dir', 'data/nonebot_plugin_jmdownload/outputs'))
ensure_dir(downloads_dir)
ensure_dir(outputs_dir)

logger.info(f"插件初始化完成，数据目录: {data_dir}")
logger.info(f"下载目录: {downloads_dir}")
logger.info(f"输出目录: {outputs_dir}")