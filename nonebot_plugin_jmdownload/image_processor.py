import os
from pathlib import Path
import logging
from PIL import Image
from PIL.ImageFile import ImageFile
import psutil

class ImageProcessor:
    def _is_image_complete(self, img_path: Path) -> bool:
        """检查图片文件是否完整有效"""
        if not os.path.exists(str(img_path)):
            logging.warning(f"图片文件不存在: {img_path}")
            return False
            
        file_size = os.path.getsize(str(img_path))
        if file_size == 0:
            logging.warning(f"图片文件大小为0: {img_path}")
            try:
                os.remove(str(img_path))
                logging.info(f"已删除空图片文件: {img_path}")
            except Exception as e:
                logging.error(f"删除空图片文件失败: {str(e)}")
            return False
            
        if file_size > 50 * 1024 * 1024:
            logging.warning(f"图片文件过大 ({file_size/1024/1024:.2f}MB): {img_path}")
            
        try:
            with Image.open(str(img_path)) as img:
                img.load()
                width, height = img.size
                if width <= 0 or height <= 0 or width > 10000 or height > 10000:
                    logging.warning(f"图片尺寸异常 ({width}x{height}): {img_path}")
                    return False
                    
                if img.mode not in ['RGB', 'RGBA', 'L', 'CMYK']:
                    logging.warning(f"图片模式异常 ({img.mode}): {img_path}")
                
            return True
            
        except Exception as e:
            logging.warning(f"图片文件 {img_path} 损坏: {str(e)}")
            try:
                os.remove(str(img_path))
                logging.info(f"已删除损坏的图片文件: {img_path}")
            except Exception as e:
                logging.error(f"删除损坏图片文件失败: {str(e)}")
            return False