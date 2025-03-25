<div align="center">

# nonebot-plugin-JMDownload

_✨ NoneBot 插件简单描述 ✨_

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/QuickLAW/nonebot_plugin_JMDownload" alt="license">
</a>
<a href="https://pypi.org/project/nonebot-plugin-jmdownload/">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-jmdownload" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">
<img src="https://img.shields.io/badge/NoneBot-2.0.0rc1+-green.svg" alt="python">

</div>

✨ 基于 NoneBot2 的 JM 漫画下载插件，支持下载漫画并转换为 PDF 格式。本项目使用 DeepSeek 辅助完成编写，代码可能需要进一步优化。

## 📦 功能特点

- ✅ 支持通过序号下载 JM 漫画
- ✅ 自动将下载的图片转换为 PDF 格式
- ✅ 支持QQ群文件直接上传
- ✅ 完善的错误提示系统
- ✅ 自动清理临时文件

## 🛠️ 安装方法

### 前置要求
- 已安装 NoneBot 2.0 框架
- Python 3.8+ 环境

### 安装步骤

1. 安装必要依赖

```bash
pip install jmcomic -i https://pypi.org/project -U
```

2. 使用 pip 安装插件（推荐）

```bash
pip install nonebot-plugin-jmdownload
```

3. 手动安装（备选）
   - 下载本插件代码
   - 解压至 `plugins` 目录
   - 安装依赖 `pip install -r requirements.txt`

安装完成后，在 nonebot2 项目的 `pyproject.toml` 文件中添加插件名称：

```ini
plugins = ["nonebot_plugin_jmdownload"]
```

## ⚙️ 使用方法

### 基础配置

1. 在 NoneBot2 项目的 `.env` 文件中添加配置（未来移除此项的必须性）：

```plaintext
jm_config_path="data/nonebot_plugin_jmdownload/config.yml"
```

2. 首次运行时会自动生成配置文件，包含以下内容：

```yaml
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
    batch_count: 45  # 批量下载数量
```

### 🚀 命令使用

```
/jm download <序号>
/jm 下载 <序号>
```

### ⚠️ 注意事项

1. 请确保机器人具有足够的存储空间
2. 下载完成后会自动清理临时文件
3. PDF 文件生成后会自动发送给用户

## ❓ 常见问题

Q: 下载失败怎么办？
A: 请检查网络连接和配置文件中的域名是否可用。

Q: 为什么下载速度很慢？
A: 目前需要获取所有图片后再进行转换，会造成阻塞并且导致下载速度较慢。

Q: 为什么转换 PDF 很慢？
A: 转换速度取决于图片数量和大小，请耐心等待。

## 📝 更新日志

### v1.2.0 (2025-03-25)
- 下载使用异步
- 优化阻塞问题

### v1.0.0 (2025-03-25)
- 初始版本发布
- 支持基本的下载和 PDF 转换功能
- 添加自动清理功能
- 支持 QQ 群文件上传

## 🎯 开发计划

- [ ] 优化 PDF 转换速度
- [ ] 优化下载速度及阻塞问题
- [ ] 体验必须优化！
- [ ] 添加下载进度显示
- [ ] 支持批量下载功能

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进这个项目。

## 📄 许可证

本项目采用 [BSD 3-Clause License](LICENSE) 开源许可证。

## 🙏 致谢

- [NoneBot2](https://github.com/nonebot/nonebot2)
- [PIL](https://python-pillow.org/)
- [jmcomic](https://github.com/hect0x7/JMComic-Crawler-Python)
- [image2pdf](https://github.com/salikx/image2pdf)

## ⚖️ 免责声明

本项目仅供学习交流使用，请勿用于非法用途。使用本项目所造成的任何后果由使用者自行承担。