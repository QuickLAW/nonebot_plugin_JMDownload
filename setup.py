from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="nonebot-plugin-jmdownload",
    version="1.1.0",
    description="基于NoneBot2的JM漫画下载插件",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="QuickLAW",
    author_email="yewillwork@outlook.com",
    url="https://github.com/QuickLAW/nonebot_plugin_JMDownload",
    packages=["nonebot_plugin_jmdownload"],
    package_dir={"nonebot_plugin_jmdownload":"src"},
    install_requires=[
        "nonebot2>=2.0.0rc1",
        "nonebot-adapter-onebot>=2.0.0",
        "jmcomic",
        "PyYAML",
        "Pillow",
        "reportlab"
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
