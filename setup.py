from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="nonebot_plugin_jmdownload",
    version="1.5.0b5",
    description="基于NoneBot2的JM漫画下载插件",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="QuickLAW",
    author_email="yewillwork@outlook.com",
    url="https://github.com/QuickLAW/nonebot_plugin_JMDownload",
    packages=["nonebot_plugin_jmdownload"],
    package_dir={"nonebot_plugin_jmdownload":"nonebot_plugin_jmdownload"},
    install_requires=[
        "nonebot2>=2.3.0",
        "nonebot-adapter-onebot>=2.0.0",
        "nonebot-plugin-localstore>=0.4.0",
        "jmcomic>=0.3.0",
        "PyYAML>=6.0",
        "Pillow>=9.0.0",
        "reportlab>=3.6.0",
        "psutil>=5.9.0",
        "PyPDF2>=2.0.0"
    ],
    license="BSD 3-Clause License",
    platforms=["all"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ]
)
