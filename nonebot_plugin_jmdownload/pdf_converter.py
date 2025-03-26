from asyncio.events import AbstractEventLoop
from re import sub


from PIL.ImageFile import ImageFile


from typing import Any


from pathlib import Path
from PIL import Image
import asyncio
import os
import time
from .utils import logger
import multiprocessing
from concurrent.futures import ThreadPoolExecutor

class PDFConverter:
    def __init__(self, input_folder: str, output_folder: Path, comic_id: str) -> None:
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.comic_id = comic_id
        self.image_files: list[Path] = []
        self.pool_size = multiprocessing.cpu_count() * 2

    async def convert(self) -> Path:
        """异步转换图片为PDF，使用线程池优化性能"""
        try:
            start_time = time.time()
            logger.info(f"开始转换漫画 {self.comic_id} 为PDF...")

            # 异步收集图片文件
            await self._collect_images()
            if not self.image_files:
                raise PDFConvertError("没有找到图片文件")

            # 使用线程池异步转换为PDF
            loop: AbstractEventLoop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=self.pool_size) as pool:
                pdf_path: Path = await loop.run_in_executor(
                    pool, lambda: asyncio.run(self._convert_to_pdf()))
            
            end_time: float = time.time()
            run_time: float = end_time - start_time
            logger.info(msg=f"PDF转换完成，运行时间：{run_time:.2f} 秒")
            
            return pdf_path
            
        except Exception as e:
            raise PDFConvertError(f"转换PDF失败: {str(e)}")

    async def _collect_images(self) -> None:
        """异步递归收集所有图片文件并按自然顺序排序"""
        self.image_files = []
        
        async def process_dir(path: str) -> None:
            """异步处理单个目录"""
            logger.debug(f"正在处理目录: {path}")
            logger.debug(f"目录内容: {[f.name for f in os.scandir(path)]}")
            with os.scandir(path) as entries:
                for topic in sorted(entries, key=lambda x: x.name):
                    if not topic.is_dir():
                        continue

                    sub_dirs: list[Any] = []

                    for entry in os.scandir(topic.path):
                        if entry.is_dir():
                            try:
                                sub_dirs.append((int(entry.name), entry.path))
                            except ValueError:
                                pass  # 忽略非数字目录
                    
                    sub_dirs.sort(key=lambda x: x[0])


                    # 收集每个数字子目录中的图片
                    for _, dir_path in sub_dirs:
                        img_files: list[Any] = []
                        for file in os.scandir(dir_path):
                            if file.is_file() and file.name.lower().endswith('.jpg'):
                                img_files.append(file)
                        # 按文件名自然排序（0001, 0002...）
                        img_files.sort(key=lambda x: x.name)
                        self.image_files.extend([Path(f.path) for f in img_files])

                    # 递归处理子目录
        
        # 直接在当前事件循环中运行process_dir
        await process_dir(self.input_folder)
        
        logger.info(f"共找到 {len(self.image_files)} 张图片")

    async def _convert_to_pdf(self) -> Path:
        """转换图片为PDF，使用分批次处理避免内存不足"""
        # 新增目录创建逻辑
        self.output_folder.mkdir(parents=True, exist_ok=True)
        pdf_path: Path = self.output_folder / f"{self.comic_id}.pdf"
        
        # 分批次处理图片，每批100张
        batch_size = 100
        first_batch = True
        
        for i in range(0, len(self.image_files), batch_size):
            batch = self.image_files[i:i + batch_size]
            sources = []
            
            # 处理批次中的所有图片
            for img_path in batch:
                try:
                    img = Image.open(str(img_path))
                    # 检查图片大小，如果超过5MB则压缩
                    if os.path.getsize(str(img_path)) > 5 * 1024 * 1024:
                        img = img.resize((img.width // 2, img.height // 2))
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    sources.append(img)
                except Exception as e:
                    logger.warning(f"处理图片 {img_path} 失败: {str(e)}")
                    continue
            
            # 保存当前批次
            if first_batch:
                # 第一次保存创建新PDF
                sources[0].save(str(pdf_path), "PDF", save_all=True, append_images=sources[1:] if len(sources) > 1 else [])
                first_batch = False
            else:
                # 后续批次追加到PDF
                with Image.open(str(pdf_path)) as existing_pdf:
                    existing_pdf.save(str(pdf_path), "PDF", save_all=True, append_images=sources)
            
        return pdf_path

class PDFConvertError(Exception):
    """PDF转换错误异常"""
    pass