import os
from typing import Any
from PIL import Image
from pathlib import Path

# 导入nonebot的logger
from nonebot import logger

def ensure_dir(path: Path) -> Path:
    """确保目录存在，如果不存在则创建"""
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_safe_filename(filename: str) -> str:
    """获取安全的文件名，移除不合法字符"""
    return ''.join(c for c in filename if c.isalnum() or c in '._- ')

def check_image_files(image_files: list[Path]) -> tuple[list[Path], bool]:
    """
    检查图片文件是否完整，删除损坏的文件
    
    执行多项检查确保图片文件完整可用:
    1. 检查文件是否存在且大小合理
    2. 尝试打开并验证图片数据
    3. 检查图片尺寸是否合理
    
    Args:
        image_files: 要检查的图片文件路径列表
        
    Returns:
        tuple: (有效的图片文件路径列表, 是否存在损坏文件)
    """
    valid_files: list[Path] = []
    has_corrupted_files: bool = False
    processed_count: int = 0
    total_count: int = len(image_files)
    
    logger.info(f"开始检查 {total_count} 个图片文件")
    
    for img_path in image_files:
        processed_count += 1
        
        # 每检查50个文件输出一次进度
        if processed_count % 50 == 0 or processed_count == total_count:
            logger.debug(f"图片检查进度: {processed_count}/{total_count}")
        
        # 检查文件是否存在
        if not img_path.exists():
            logger.warning(f"图片文件不存在: {img_path}")
            has_corrupted_files = True
            continue
            
        # 检查文件大小
        try:
            file_size = img_path.stat().st_size
            if file_size == 0:
                logger.warning(f"图片文件大小为0: {img_path}")
                has_corrupted_files = True
                try:
                    img_path.unlink()
                    logger.info(f"已删除空图片文件: {img_path}")
                except Exception as e:
                    logger.error(f"删除空图片文件失败: {str(e)}")
                continue
                
            # 检查文件是否过大（超过50MB可能是错误文件）
            if file_size > 50 * 1024 * 1024:  # 50MB
                logger.warning(f"图片文件过大 ({file_size/1024/1024:.2f}MB): {img_path}")
                # 不自动删除过大文件，可能是高分辨率图片
        except Exception as e:
            logger.error(f"检查文件大小失败: {str(e)}")
            has_corrupted_files = True
            continue
        
        # 验证图片内容
        try:
            with Image.open(img_path) as img:
                # 加载像素数据验证图片完整性
                img.load()
                
                # 检查图片尺寸是否合理
                width, height = img.size
                if width <= 0 or height <= 0 or width > 10000 or height > 10000:
                    logger.warning(f"图片尺寸异常 ({width}x{height}): {img_path}")
                    has_corrupted_files = True
                    try:
                        img_path.unlink()
                        logger.info(f"已删除尺寸异常的图片文件: {img_path}")
                    except Exception as e:
                        logger.error(f"删除尺寸异常图片文件失败: {str(e)}")
                    continue
            
            # 图片验证通过，添加到有效列表
            valid_files.append(img_path)
            
        except Exception as e:
            logger.warning(f"图片文件 {img_path} 损坏: {str(e)}")
            has_corrupted_files = True
            try:
                img_path.unlink()
                logger.info(f"已删除损坏的图片文件: {img_path}")
            except Exception as e:
                logger.error(f"删除损坏图片文件失败: {str(e)}")
    
    logger.info(f"图片检查完成: 有效={len(valid_files)}/{total_count}, 损坏={total_count-len(valid_files)}")
    return valid_files, has_corrupted_files


def collect_image_files(input_folder: Path) -> list[Path]:
    """
    递归收集指定目录下的所有图片文件并按自然顺序排序
    
    Args:
        input_folder: 要扫描的目录路径
        
    Returns:
        排序后的图片文件路径列表
    """
    image_files: list[Path] = []
    
    def process_dir(path: str) -> None:
        """处理单个目录"""
        with os.scandir(path) as entries:
            for topic in sorted(entries, key=lambda x: x.name):
                if not topic.is_dir():
                    continue

                sub_dirs: list[tuple[int, str]] = []

                for entry in os.scandir(topic.path):
                    if entry.is_dir():
                        try:
                            sub_dirs.append((int(entry.name), entry.path))
                        except ValueError:
                            pass  # 忽略非数字目录
                
                sub_dirs.sort(key=lambda x: x[0])

                # 收集每个数字子目录中的图片
                for _, dir_path in sub_dirs:
                    img_files: list[Path] = []
                    for file in os.scandir(dir_path):
                        if file.is_file() and file.name.lower().endswith('.jpg'):
                            img_files.append(Path(file))
                    # 按文件名自然排序（0001, 0002...）
                    img_files.sort(key=lambda x: x.name)
                    image_files.extend([Path(f) for f in img_files])
    
    process_dir(str(input_folder))
    return image_files

if __name__ == "__main__":
    # 创建测试图片目录结构
    input_dir: Path = Path(r"C:\Users\Elysia\Downloads\Compressed\32D阿西 11-12月福利")

    # 设置输出目录
    output_dir: Path = Path(r"C:\Users\Elysia\Downloads\Compressed\32D阿西 11-12月福利")

    # 收集图片文件
    image_files: list[Path] = collect_image_files(input_dir)

    # 检查并删除损坏的图片文件
    valid_image_files, has_corrupted_files = check_image_files(image_files)
    # 记录结果
    logger.info("有效图片文件:")
    for img_path in valid_image_files:
        logger.info(str(img_path))