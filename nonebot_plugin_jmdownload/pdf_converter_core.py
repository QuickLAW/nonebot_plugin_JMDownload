import os
import tempfile
import math
from concurrent.futures import ProcessPoolExecutor
import psutil
from pathlib import Path
from typing import List
from PIL import Image
from PyPDF2 import PdfMerger
from nonebot import logger

class PDFConverterCore:
    def __init__(self, max_memory_per_core: int = 512):
        self.max_memory_per_core = max_memory_per_core

    def _calculate_chunk_size(self, total_images: int, available_cores: int) -> int:
        """动态计算每个核心处理的图片数量"""
        mem_info = psutil.virtual_memory()
        available_mem = mem_info.available / (1024 ** 2)  # MB
        system_load = psutil.cpu_percent(interval=0.1) / 100
        
        adjusted_cores = max(1, int(available_cores * (1 - system_load * 0.5)))
        
        max_possible_tasks = min(
            math.floor(available_mem / self.max_memory_per_core) if self.max_memory_per_core > 0 else adjusted_cores,
            adjusted_cores if adjusted_cores > 0 else 1
        )
        
        chunk_size = max(1, math.ceil(total_images / max_possible_tasks)) if max_possible_tasks > 0 else 1
        
        logger.info(f"任务分配计算: 总图片={total_images}, 可用内存={available_mem:.2f}MB, "
                     f"系统负载={system_load*100:.1f}%, 调整后核心数={adjusted_cores}, "
                     f"最大任务数={max_possible_tasks}, 分块大小={chunk_size}")
        
        return chunk_size

    def _process_image_chunk(self, chunk_paths: List[Path], temp_dir: str) -> str:
        """处理单个图片块的任务函数"""
        chunk_pdf = tempfile.mktemp(dir=temp_dir, suffix='.pdf')
        
        try:
            images = []
            for img_path in chunk_paths:
                try:
                    with Image.open(str(img_path)) as img:
                        images.append(img.convert('RGB'))
                except Exception as e:
                    logger.warning(f"处理图片 {img_path} 失败: {str(e)}")
            
            if images:
                images[0].save(chunk_pdf, save_all=True, append_images=images[1:])
                
            return chunk_pdf
            
        except Exception as e:
            logger.error(f"处理图片块失败: {str(e)}")
            raise

    def merge_pdfs(self, pdf_files: List[str], output_path: str) -> None:
        """合并多个PDF文件"""
        merger = PdfMerger()
        try:
            for pdf in pdf_files:
                if os.path.exists(pdf):
                    merger.append(pdf)
            
            merger.write(output_path)
            merger.close()
            
        except Exception as e:
            merger.close()
            raise Exception(f"合并PDF失败: {str(e)}")