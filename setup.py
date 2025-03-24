from setuptools import setup, find_packages

VERSION = '1.0.0'

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='nonebot-plugin-jmdownload',
    version=VERSION,
    description='A NoneBot2 plugin for downloading JM comics and converting them to PDF format',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='QuickLAW',
    author_email='yewillwork@outlook.com',
    package_dir={'': 'src'},
    license="BSD 3-Clause License",
    packages=find_packages('src'),
    package_data={
        'nonebot_plugin_jmdownload': ['config.yml']
    },
    install_requires=[
        'nonebot2>=2.0.0rc1',
        'nonebot-adapter-onebot>=2.0.0',
        'jmcomic',
        'PyYAML',
        'Pillow',
        'reportlab'
    ],
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD 3-Clause License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Framework :: NoneBot',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    keywords=['nonebot2', 'plugin', 'comic', 'download', 'pdf'],
    project_urls={
        'Homepage': 'https://github.com/QuickLAW/nonebot_plugin_JMDownload',
        'Repository': 'https://github.com/QuickLAW/nonebot_plugin_JMDownload.git',
        'Bug Reports': 'https://github.com/QuickLAW/nonebot_plugin_JMDownload/issues'
    },
)