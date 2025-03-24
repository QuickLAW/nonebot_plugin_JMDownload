from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import yaml
from nonebot import get_driver

driver = get_driver()
global_config = driver.config

# 在原有路径定义后添加检测逻辑
jm_config_path = global_config.jm_config_path

# 新增配置文件检测与生成
config_path = Path(jm_config_path)
# 修改配置文件生成部分
if not config_path.exists():
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 带注释的模板内容
    config_template = """\
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
    batch_count: 45
"""

    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_template)

# 加载yml文件
with open(jm_config_path, 'r', encoding='utf-8') as f:
    jm_config = yaml.safe_load(f)