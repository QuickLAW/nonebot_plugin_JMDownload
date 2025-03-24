from pathlib import Path
from typing import List
from PIL import Image
import asyncio
import os
import time
from .utils import logger

class PDFConverter:
    def __init__(self, input_folder: Path, output_folder: Path, comic_id: str):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.comic_id = comic_id
        self.image_files: List[Path] = []

    async def convert(self) -> Path:
        """异步转换图片为PDF"""
        try:
            start_time = time.time()
            logger.info(f"开始转换漫画 {self.comic_id} 为PDF...")

            # 收集图片文件
            await self._collect_images()
            if not self.image_files:
                raise PDFConvertError("没有找到图片文件")

            # 转换为PDF
            pdf_path = await self._convert_to_pdf()
            
            end_time = time.time()
            run_time = end_time - start_time
            logger.info(f"PDF转换完成，运行时间：{run_time:.2f} 秒")
            
            return pdf_path
            
        except Exception as e:
            raise PDFConvertError(f"转换PDF失败: {str(e)}")

    async def _collect_images(self):
        """递归收集所有图片文件并按自然顺序排序"""
        self.image_files = []
        
        # 遍历顶层目录（如 A、B 或汉字目录），按名称自然排序
        for top_dir in sorted(os.scandir(self.input_folder), key=lambda x: x.name):
            if not top_dir.is_dir():
                continue
            
            # 处理数字子目录（0,1,2...），按数字大小排序
            sub_dirs = []
            for entry in os.scandir(top_dir.path):
                if entry.is_dir():
                    try:
                        sub_dirs.append((int(entry.name), entry.path))
                    except ValueError:
                        pass  # 忽略非数字目录
            sub_dirs.sort(key=lambda x: x[0])
            
            # 收集每个数字子目录中的图片
            for _, dir_path in sub_dirs:
                img_files = []
                for file in os.scandir(dir_path):
                    if file.is_file() and file.name.lower().endswith('.jpg'):
                        img_files.append(file)
                # 按文件名自然排序（0001, 0002...）
                img_files.sort(key=lambda x: x.name)
                self.image_files.extend([Path(f.path) for f in img_files])

    async def _convert_to_pdf(self) -> Path:
        """转换图片为PDF"""
        # 打开第一张图片
        output = Image.open(str(self.image_files[0]))
        sources = []

        # 转换其他图片
        for img_path in self.image_files[1:]:
            img = Image.open(str(img_path))
            if img.mode == "RGB":
                img = img.convert("RGB")
            sources.append(img)

        # 保存PDF
        # 新增目录创建逻辑
        self.output_folder.mkdir(parents=True, exist_ok=True)
        pdf_path = self.output_folder / f"{self.comic_id}.pdf"
        output.save(str(pdf_path), "pdf", save_all=True, append_images=sources)
        return pdf_path

class PDFConvertError(Exception):
    """PDF转换错误异常"""
    pass