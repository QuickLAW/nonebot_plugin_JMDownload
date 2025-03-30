from nonebot.internal.driver.abstract import Driver

from typing import Any
import yaml
import os
from nonebot import get_driver, logger
from nonebot_plugin_localstore import get_config_file, get_data_dir

driver: Driver = get_driver()
global_config: dict[str, Any] = driver.config.model_dump()

# 使用localstore获取配置文件路径
config_path = get_config_file("nonebot_plugin_jmdownload", "config.yml")
logger.info(f"配置文件路径: {config_path}")

# 默认配置模板
DEFAULT_CONFIG = """\
# Github Actions 下载脚本配置
version: '1.0'

dir_rule:
  base_dir: data/nonebot_plugin_jmdownload/downloads  # 基础存储目录
  rule: Bd_Atitle_Pindex           # 目录命名规则

client:
  domain:
    - www.jmapiproxyxxx.vip
    - www.18comic-mygo.vip
    - 18comic-MHWs.CC
    - 18comic.vip
    - 18comic.org

download:
  cache: true    # 文件存在时跳过下载
  image:
    decode: true  # 还原被混淆的图片
    suffix: .jpg  # 统一图片后缀格式
  threading:
    # 数值大，下得快，配置要求高，对禁漫压力大
    # 数值小，下得慢，配置要求低，对禁漫压力小
    # PS: 禁漫网页一般是一次请求50张图
    batch_count: 20
"""

# 配置文件检测与生成
def ensure_config_file():
    """确保配置文件存在，如果不存在则创建"""
    if not config_path.exists():
        logger.info(f"配置文件不存在，创建默认配置: {config_path}")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(DEFAULT_CONFIG)
        logger.info("默认配置文件创建成功")
    else:
        logger.info(f"配置文件已存在: {config_path}")

# 验证配置文件
def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    """验证配置文件，确保所有必要的配置项都存在"""
    # 检查基本结构
    if not isinstance(config, dict):
        logger.error("配置文件格式错误，使用默认配置")
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    # 检查必要的配置项
    required_sections = ['dir_rule', 'client', 'download']
    for section in required_sections:
        if section not in config:
            logger.warning(f"配置文件缺少 {section} 部分，将使用默认值")
            # 重新加载默认配置
            ensure_config_file()
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
    
    # 检查dir_rule部分
    if 'dir_rule' in config:
        dir_rule = config['dir_rule']
        if not isinstance(dir_rule, dict):
            logger.warning("dir_rule 配置格式错误，将使用默认值")
            dir_rule = {}
        
        # 确保base_dir存在
        if 'base_dir' not in dir_rule:
            logger.warning("配置中缺少 base_dir，使用默认值")
            dir_rule['base_dir'] = 'data/nonebot_plugin_jmdownload/downloads'
        
        # output_dir从环境变量中读取，不再存储在配置文件中
        # 确保不会在配置文件中添加output_dir字段
        
        # 确保rule存在
        if 'rule' not in dir_rule:
            logger.warning("配置中缺少 rule，使用默认值")
            dir_rule['rule'] = 'Bd_Atitle_Pindex'
        
        config['dir_rule'] = dir_rule
    
    return config

# 确保配置文件存在
ensure_config_file()

# 加载yml文件
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        jm_config = yaml.safe_load(f)
    
    # 验证配置
    jm_config: dict[str, Any] = validate_config(jm_config)
    logger.info("配置文件加载成功")
    
except Exception as e:
    logger.error(f"加载配置文件失败: {str(e)}，使用默认配置")
    # 重新创建配置文件
    ensure_config_file()
    with open(config_path, 'r', encoding='utf-8') as f:
        jm_config = yaml.safe_load(f)
    jm_config = validate_config(jm_config)