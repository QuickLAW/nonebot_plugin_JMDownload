from asyncio.events import AbstractEventLoop
from PIL.ImageFile import ImageFile
import tempfile
import psutil  # 导入psutil模块用于获取系统内存信息
from PyPDF2 import PdfMerger

from typing import Any
import math

from pathlib import Path
from PIL import Image
import asyncio
import os
import time
import multiprocessing
from concurrent.futures import ThreadPoolExecutor

class PDFConverter:
    def __init__(self, input_folder: Path, output_folder: Path, comic_id: str) -> None:
        self.input_folder = str(input_folder)
        self.output_folder = output_folder
        self.comic_id = comic_id
        self.image_files: list[Path] = []
        self.pool_size = multiprocessing.cpu_count() * 2

    async def convert(self) -> Path:
        """异步转换图片为PDF，使用线程池优化性能"""
        try:
            start_time = time.time()

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
            
            return pdf_path
            
        except Exception as e:
            raise PDFConvertError(f"转换PDF失败: {str(e)}")

    async def _collect_images(self) -> None:
        """异步递归收集所有图片文件并按自然顺序排序"""
        self.image_files = []
        
        async def process_dir(path: str) -> None:
            """异步处理单个目录"""
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

    async def _convert_to_pdf(self) -> Path:
        """转换图片为PDF，使用多进程并行处理优化性能"""
        self.output_folder.mkdir(parents=True, exist_ok=True)
        pdf_path: Path = self.output_folder / f"{self.comic_id}.pdf"
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        try:
            # 计算工作进程数
            available_cores = multiprocessing.cpu_count()
            max_workers = max(1, available_cores - 1)
            
            # 动态分块
            chunk_size = self._calculate_chunk_size(len(self.image_files), max_workers)
            chunks = [
                self.image_files[i:i + chunk_size]
                for i in range(0, len(self.image_files), chunk_size)
            ]
            
            # 多进程处理
            with multiprocessing.Pool(processes=max_workers) as pool:
                tasks = [(chunk, temp_dir) for chunk in chunks]
                results = pool.starmap(self._process_image_chunk, tasks)
            
            # 合并PDF
            merger = PdfMerger()
            for pdf in results:
                if os.path.exists(pdf):
                    merger.append(pdf)
            merger.write(str(pdf_path))
            merger.close()
            
            return pdf_path
        finally:
            # 清理临时文件
            for f in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, f))
            os.rmdir(temp_dir)
    
    def _calculate_chunk_size(self, total_images, available_cores, max_memory_per_core=512):
        """动态计算每个核心处理的图片数量"""
        mem_info = psutil.virtual_memory()
        available_mem = mem_info.available / (1024 ** 2)  # MB
        max_possible = min(
            math.floor(available_mem / max_memory_per_core) if max_memory_per_core > 0 else available_cores,
            available_cores if available_cores > 0 else 1
        )
        return max(1, math.ceil(total_images / max_possible)) if max_possible > 0 else 1
        
    def _is_image_complete(self, img_path):
        """检查图片文件是否完整"""
        try:
            # 尝试打开图片但不加载像素数据
            with Image.open(str(img_path)) as img:
                img.verify()  # 验证图片完整性
            return True
        except Exception as e:
            return False
    
    def _process_image_chunk(self, chunk_paths, temp_dir):
        """处理单个图片块的任务函数"""
        chunk_pdf = tempfile.mktemp(dir=temp_dir, suffix='.pdf')
        try:
            images = []
            for img_path in chunk_paths:
                try:
                    # 检查图片文件是否完整
                    if not self._is_image_complete(img_path):
                        print(f"跳过损坏的图片文件: {img_path}")
                        continue
                        
                    img = Image.open(str(img_path))
                    if os.path.getsize(str(img_path)) > 5 * 1024 * 1024:
                        img = img.resize((img.width // 2, img.height // 2))
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    images.append(img)
                except Exception as e:
                    print(f"处理图片 {img_path} 时出错: {str(e)}")
                    continue
            
            if images:
                images[0].save(
                    chunk_pdf,
                    "PDF",
                    save_all=True,
                    append_images=images[1:],
                    quality=100,
                    optimize=False
                )
            return chunk_pdf
        except Exception as e:
            if os.path.exists(chunk_pdf):
                os.remove(chunk_pdf)
            raise e

class PDFConvertError(Exception):
    """PDF转换错误异常"""
    pass


if __name__ == "__main__":

    try:
        # 创建测试图片目录结构
        input_dir: Path = Path(r"C:\Users\Elysia\Desktop\Code\Python\QQbotDevelop\data\nonebot_plugin_jmdownload\downloads")
    
        # 设置输出目录
        output_dir: Path = Path(r"C:\Users\Elysia\Desktop\Code\Python\QQbotDevelop\data\nonebot_plugin_jmdownload\output")
        
        # 性能限制测试
        def set_performance_limits():
            """设置性能限制模拟"""
            # 模拟内存限制为512MB
            import psutil
            memory_limit = 512 * 1024 * 1024  # 512MB
            mem_info = psutil.virtual_memory()
            if mem_info.available < memory_limit:
                raise MemoryError("可用内存不足512MB")
            
            # 限制CPU核心数为1
            import multiprocessing
            multiprocessing.cpu_count = lambda: 1
            
            print("已设置性能限制: 内存512MB, CPU 1核心, 图片处理延迟100ms")
        
        # 运行转换
        async def test_convert() -> None:
            set_performance_limits()
            converter: PDFConverter = PDFConverter(input_dir, output_dir, "test_comic")
            pdf_path: Path = await converter.convert()
            print(f"PDF转换完成，保存路径: {pdf_path}")
            
        asyncio.run(test_convert())
    finally:
        pass