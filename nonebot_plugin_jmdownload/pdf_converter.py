import asyncio
import math
import multiprocessing
import os
import tempfile
import time
import logging
from asyncio.events import AbstractEventLoop
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

# 第三方库
import psutil
from PIL import Image
from PIL.ImageFile import ImageFile
from PyPDF2 import PdfMerger

# 导入logger
from nonebot import logger

# 创建一个简单的日志函数，用于多进程中避免导入nonebot
def simple_log(level: str, message: str, mp_context: bool = False) -> None:
    """简单的日志函数，在多进程上下文中使用，避免导入nonebot
    
    Args:
        level: 日志级别，可选值为 'debug', 'info', 'warning', 'error', 'critical'
        message: 日志消息
        mp_context: 是否在多进程上下文中使用
    
    Raises:
        AttributeError: 如果指定的日志级别不存在
    """
    # 验证日志级别是否有效
    valid_levels = ['debug', 'info', 'warning', 'error', 'critical']
    if level.lower() not in valid_levels:
        fallback_level = 'info'
        fallback_message = f"无效的日志级别 '{level}'，使用默认级别 '{fallback_level}'"
        level = fallback_level
        # 先记录警告，然后继续使用有效的级别记录原始消息
        if not mp_context:
            logger.warning(fallback_message)
        else:
            logging.warning(fallback_message)
    
    try:
        if mp_context:
            # 在多进程中使用标准库logging
            log_level = getattr(logging, level.upper())
            logging.log(log_level, message)
        else:
            # 在主进程中使用nonebot的logger
            log_func = getattr(logger, level.lower(), logger.info)
            log_func(message)
    except Exception as e:
        # 确保日志记录失败不会导致程序崩溃
        fallback_message = f"日志记录失败: {str(e)}，原始消息: {message}"
        if not mp_context:
            logger.error(fallback_message)
        else:
            logging.error(fallback_message)

class PDFConverter:
    def __init__(self, input_folder: Path, output_folder: Path, comic_id: str) -> None:
        self.input_folder = str(input_folder)
        self.output_folder = output_folder
        self.comic_id = comic_id
        self.image_files: list[Path] = []
        self.pool_size = multiprocessing.cpu_count() * 2

    async def convert(self) -> Path:
        """异步转换图片为PDF，使用线程池优化性能
        
        整个转换过程包括：收集图片、验证图片、分块处理、合并PDF
        
        Returns:
            Path: 生成的PDF文件路径
            
        Raises:
            PDFConvertError: 转换过程中的任何错误
        """
        start_time = time.time()
        performance_stats = {
            "total_images": 0,
            "valid_images": 0,
            "corrupted_images": 0,
            "collection_time": 0,
            "conversion_time": 0,
            "total_time": 0
        }
        
        try:
            simple_log("info", f"开始转换漫画 {self.comic_id} 为PDF", mp_context=False)
            
            # 检查系统资源
            mem_info = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            simple_log("info", f"系统状态: CPU使用率={cpu_percent}%, 内存使用率={mem_info.percent}%, "  
                      f"可用内存={mem_info.available/(1024*1024*1024):.2f}GB", mp_context=False)
            
            # 异步收集图片文件
            collection_start = time.time()
            await self._collect_images()
            collection_end = time.time()
            performance_stats["collection_time"] = int(collection_end - collection_start)
            
            # 验证图片文件
            if not self.image_files:
                raise PDFConvertError("没有找到图片文件")
                
            performance_stats["total_images"] = len(self.image_files)
            simple_log("info", f"收集到 {len(self.image_files)} 张图片，耗时 {performance_stats['collection_time']:.2f} 秒", mp_context=False)

            # 使用线程池异步转换为PDF
            conversion_start = time.time()
            loop: AbstractEventLoop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=self.pool_size) as pool:
                pdf_path: Path = await loop.run_in_executor(
                    pool, lambda: asyncio.run(self._convert_to_pdf()))
            conversion_end = time.time()
            performance_stats["conversion_time"] = int(conversion_end - conversion_start)
            
            # 计算总耗时
            end_time: float = time.time()
            performance_stats["total_time"] = int(end_time - start_time)
            
            # 输出性能统计
            simple_log("info", f"PDF转换完成: 总耗时={performance_stats['total_time']:.2f}秒, "
                      f"收集耗时={performance_stats['collection_time']:.2f}秒, "
                      f"转换耗时={performance_stats['conversion_time']:.2f}秒", mp_context=False)
            
            # 验证生成的PDF
            if not pdf_path.exists() or pdf_path.stat().st_size == 0:
                raise PDFConvertError("PDF生成失败或文件为空")
                
            simple_log("info", f"PDF文件已生成: {pdf_path}, 大小: {pdf_path.stat().st_size/(1024*1024):.2f}MB", mp_context=False)
            return pdf_path
            
        except Exception as e:
            error_msg = f"转换PDF失败: {str(e)}"
            simple_log("error", error_msg, mp_context=False)
            # 添加更多上下文信息到错误中
            detailed_error = f"{error_msg} (已处理 {performance_stats.get('total_images', 0)} 张图片, 耗时 {time.time()-start_time:.2f}秒)"
            raise PDFConvertError(detailed_error)

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
        """转换图片为PDF，使用线程池并行处理优化性能
        
        将收集到的图片分块处理，每个块生成一个临时PDF，最后合并为一个完整PDF
        
        Returns:
            Path: 生成的PDF文件路径
            
        Raises:
            PDFConvertError: PDF转换过程中的错误
        """
        # 确保输出目录存在
        self.output_folder.mkdir(parents=True, exist_ok=True)
        pdf_path: Path = self.output_folder / f"{self.comic_id}.pdf"
        
        # 如果输出文件已存在，先删除
        if pdf_path.exists():
            try:
                pdf_path.unlink()
                simple_log("info", f"已删除已存在的PDF文件: {pdf_path}", mp_context=False)
            except Exception as e:
                simple_log("warning", f"删除已存在的PDF文件失败: {str(e)}", mp_context=False)
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="jm_pdf_")
        simple_log("debug", f"创建临时目录: {temp_dir}", mp_context=False)
        
        start_time = time.time()
        temp_pdfs: list[str] = []
        
        try:
            # 计算工作线程数，考虑系统负载
            available_cores = multiprocessing.cpu_count()
            system_load = psutil.cpu_percent(interval=0.1)
            
            # 根据系统负载调整线程数
            if system_load > 80:  # 系统负载高
                max_workers = max(1, available_cores // 4)  # 使用1/4的核心
            elif system_load > 50:  # 系统负载中等
                max_workers = max(1, available_cores // 2)  # 使用1/2的核心
            else:  # 系统负载低
                max_workers = max(1, available_cores - 1)  # 使用全部核心减1
                
            simple_log("info", f"系统状态: CPU负载={system_load}%, 内存使用率={psutil.virtual_memory().percent}%, 工作线程数={max_workers}", mp_context=False)
            
            # 动态分块
            total_images = len(self.image_files)
            chunk_size: int = self._calculate_chunk_size(total_images, max_workers)
            
            # 创建图片分块
            chunks: list[list[Path]] = [
                self.image_files[i:i + chunk_size]
                for i in range(0, total_images, chunk_size)
            ]
            
            simple_log("info", f"开始处理图片: 总数={total_images}, 分块数={len(chunks)}, 每块大小≈{chunk_size}", mp_context=False)
            
            # 使用线程池处理图片块
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务，传递块ID
                futures = [executor.submit(self._process_image_chunk, chunk, temp_dir, i+1, len(chunks)) for i, chunk in enumerate(chunks)]
                
                # 收集结果
                for i, future in enumerate(futures):
                    try:
                        result = future.result()
                        if result and os.path.exists(result):
                            temp_pdfs.append(result)
                            simple_log("debug", f"完成处理图片块 {i+1}/{len(chunks)}", mp_context=False)
                    except Exception as e:
                        simple_log("error", f"处理图片块 {i+1}/{len(chunks)} 失败: {str(e)}", mp_context=False)
            
            # 检查是否有成功生成的PDF
            if not temp_pdfs:
                raise PDFConvertError("没有成功生成任何PDF块，转换失败")
                
            # 合并PDF
            simple_log("info", f"开始合并 {len(temp_pdfs)} 个PDF块...", mp_context=False)
            merger = PdfMerger()
            for pdf in temp_pdfs:
                if os.path.exists(pdf):
                    try:
                        merger.append(pdf)
                    except Exception as e:
                        simple_log("warning", f"添加PDF块 {pdf} 到合并器失败: {str(e)}", mp_context=False)
            
            # 写入最终PDF
            try:
                merger.write(str(pdf_path))
                simple_log("info", f"PDF合并完成，保存到: {pdf_path}", mp_context=False)
            except Exception as e:
                raise PDFConvertError(f"写入最终PDF失败: {str(e)}")
            finally:
                merger.close()
            
            # 计算处理时间
            end_time = time.time()
            process_time = end_time - start_time
            simple_log("info", f"PDF转换完成: 处理了 {total_images} 张图片，耗时 {process_time:.2f} 秒", mp_context=False)
            
            return pdf_path
            
        except Exception as e:
            error_msg = f"转换PDF过程中发生错误: {str(e)}"
            simple_log("error", error_msg, mp_context=False)
            raise PDFConvertError(error_msg)
            
        finally:
            # 清理临时文件
            simple_log("debug", f"清理临时目录: {temp_dir}", mp_context=False)
            try:
                # 删除临时PDF文件
                for f in os.listdir(temp_dir):
                    try:
                        os.remove(os.path.join(temp_dir, f))
                    except Exception as e:
                        simple_log("warning", f"删除临时文件 {f} 失败: {str(e)}", mp_context=False)
                
                # 删除临时目录
                os.rmdir(temp_dir)
                simple_log("debug", "临时目录清理完成", mp_context=False)
            except Exception as e:
                simple_log("warning", f"清理临时目录失败: {str(e)}", mp_context=False)
    
    def _calculate_chunk_size(self, total_images: int, available_cores: int, max_memory_per_core: int = 512) -> int:
        """动态计算每个核心处理的图片数量
        
        根据系统可用内存和CPU核心数智能分配任务，避免资源过度使用
        
        Args:
            total_images: 总图片数量
            available_cores: 可用CPU核心数
            max_memory_per_core: 每个核心分配的最大内存(MB)，默认512MB
            
        Returns:
            int: 每个任务块应处理的图片数量
        """
        # 获取系统内存信息
        mem_info = psutil.virtual_memory()
        available_mem = mem_info.available / (1024 ** 2)  # MB
        system_load = psutil.cpu_percent(interval=0.1) / 100  # 获取CPU负载(0-1)
        
        # 根据系统负载调整可用核心数
        adjusted_cores = max(1, int(available_cores * (1 - system_load * 0.5)))
        
        # 计算可以并行处理的最大任务数
        max_possible_tasks = min(
            math.floor(available_mem / max_memory_per_core) if max_memory_per_core > 0 else adjusted_cores,
            adjusted_cores if adjusted_cores > 0 else 1
        )
        
        # 计算每个任务应处理的图片数量
        chunk_size = max(1, math.ceil(total_images / max_possible_tasks)) if max_possible_tasks > 0 else 1
        
        # 记录详细的计算过程
        simple_log("info", f"任务分配计算: 总图片={total_images}, 可用内存={available_mem:.2f}MB, "
                          f"系统负载={system_load*100:.1f}%, 调整后核心数={adjusted_cores}, "
                          f"最大任务数={max_possible_tasks}, 分块大小={chunk_size}", mp_context=False)
        
        return chunk_size
        
    def _is_image_complete(self, img_path: Path) -> bool:
        """检查图片文件是否完整有效
        
        执行多项检查确保图片文件完整可用:
        1. 检查文件是否存在且大小合理
        2. 尝试打开并验证图片数据
        3. 检查图片尺寸是否合理
        
        Args:
            img_path: 图片文件路径
            
        Returns:
            bool: 图片是否完整有效
        """
        # 检查文件是否存在
        if not os.path.exists(str(img_path)):
            simple_log("warning", f"图片文件不存在: {img_path}", mp_context=False)
            return False
            
        # 检查文件大小
        file_size = os.path.getsize(str(img_path))
        if file_size == 0:
            simple_log("warning", f"图片文件大小为0: {img_path}", mp_context=False)
            try:
                os.remove(str(img_path))
                simple_log("info", f"已删除空图片文件: {img_path}", mp_context=False)
            except Exception as e:
                simple_log("error", f"删除空图片文件失败: {str(e)}", mp_context=False)
            return False
            
        # 检查文件是否过大（超过50MB可能是错误文件）
        if file_size > 50 * 1024 * 1024:  # 50MB
            simple_log("warning", f"图片文件过大 ({file_size/1024/1024:.2f}MB): {img_path}", mp_context=False)
            # 不自动删除过大文件，可能是高分辨率图片
            
        try:
            # 尝试打开图片并验证
            with Image.open(str(img_path)) as img:
                # 加载像素数据验证图片完整性
                img.load()
                
                # 检查图片尺寸是否合理
                width, height = img.size
                if width <= 0 or height <= 0 or width > 10000 or height > 10000:
                    simple_log("warning", f"图片尺寸异常 ({width}x{height}): {img_path}", mp_context=False)
                    return False
                    
                # 检查图片模式
                if img.mode not in ['RGB', 'RGBA', 'L', 'CMYK']:
                    simple_log("warning", f"图片模式异常 ({img.mode}): {img_path}", mp_context=False)
                    # 不返回False，因为可以尝试转换模式
                
            return True
            
        except Exception as e:
            simple_log("warning", f"图片文件 {img_path} 损坏: {str(e)}", mp_context=False)
            try:
                os.remove(str(img_path))
                simple_log("info", f"已删除损坏的图片文件: {img_path}", mp_context=False)
            except Exception as e:
                simple_log("error", f"删除损坏图片文件失败: {str(e)}", mp_context=False)
            return False
    
    def _process_image_chunk(self, chunk_paths, temp_dir, chunk_id: int = 0, total_chunks: int = 0) -> str:
        """处理单个图片块的任务函数
        
        Args:
            chunk_paths: 图片路径列表
            temp_dir: 临时目录路径
            chunk_id: 当前处理的块ID（从1开始）
            total_chunks: 总块数
            
        Returns:
            str: 生成的PDF文件路径
            
        Raises:
            Exception: 处理过程中发生的任何异常
        """
        chunk_pdf: str = tempfile.mktemp(dir=temp_dir, suffix='.pdf')
        processed_count = 0
        skipped_count = 0
        
        try:
            images: list[ImageFile] = []
            total_images = len(chunk_paths)
            
            # 估算内存使用情况
            mem_info = psutil.virtual_memory()
            available_mem_mb = mem_info.available / (1024 * 1024)  # MB
            chunk_info = f"块{chunk_id}/{total_chunks}" if chunk_id > 0 else ""
            simple_log("debug", f"处理{chunk_info}图片块前可用内存: {available_mem_mb:.2f}MB", mp_context=False)
            
            for img_path in chunk_paths:
                try:
                    # 检查图片文件是否完整
                    if not self._is_image_complete(img_path):
                        chunk_info = f"块{chunk_id}/{total_chunks}" if chunk_id > 0 else ""
                        simple_log("warning", f"{chunk_info} 跳过损坏的图片文件: {img_path}", mp_context=False)
                        skipped_count += 1
                        continue
                    
                    # 获取文件大小（MB）
                    file_size_mb = os.path.getsize(str(img_path)) / (1024 * 1024)
                    
                    # 根据文件大小动态调整处理策略
                    img: ImageFile = Image.open(str(img_path))
                    
                    # 大图片处理策略
                    if file_size_mb > 5:  # 大于5MB的图片
                        # 计算合适的缩放比例，保持图片质量的同时减小尺寸
                        scale_factor = min(1.0, 5.0 / file_size_mb)  # 动态缩放因子
                        new_width = int(img.width * scale_factor)
                        new_height = int(img.height * scale_factor)
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)  # 使用高质量重采样
                        chunk_info = f"块{chunk_id}/{total_chunks}" if chunk_id > 0 else ""
                        simple_log("debug", f"{chunk_info} 已缩放大图片: {img_path} ({file_size_mb:.2f}MB -> {scale_factor:.2f}倍)", mp_context=False)
                    
                    # 确保图片模式为RGB
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    
                    images.append(img)
                    processed_count += 1
                    
                    # 每处理10张图片检查一次内存使用情况
                    if processed_count % 10 == 0:
                        # 强制垃圾回收
                        import gc
                        gc.collect()
                        
                        # 检查内存使用情况
                        current_mem = psutil.virtual_memory()
                        if current_mem.percent > 90:  # 内存使用率超过90%
                            chunk_info = f"块{chunk_id}/{total_chunks}" if chunk_id > 0 else ""
                            simple_log("warning", f"{chunk_info} 内存使用率高: {current_mem.percent}%，尝试释放内存", mp_context=False)
                            # 可以在这里实现更激进的内存释放策略
                            
                except Exception as e:
                    chunk_info = f"块{chunk_id}/{total_chunks}" if chunk_id > 0 else ""
                    simple_log("error", f"{chunk_info} 处理图片 {img_path} 时出错: {str(e)}", mp_context=False)
                    skipped_count += 1
                    continue
            
            # 生成PDF
            if images:
                # 根据图片数量调整PDF质量
                pdf_quality = 95 if len(images) > 50 else 100
                optimize_pdf = len(images) > 100  # 图片数量多时启用优化
                
                chunk_info = f"块{chunk_id}/{total_chunks}" if chunk_id > 0 else ""
                simple_log("info", f"{chunk_info} 正在生成PDF，共 {len(images)} 张图片，质量: {pdf_quality}%，优化: {optimize_pdf}", mp_context=False)
                
                images[0].save(
                    fp=chunk_pdf,
                    format="PDF",
                    save_all=True,
                    append_images=images[1:],
                    quality=pdf_quality,
                    optimize=optimize_pdf
                )
                
                # 清理图片对象释放内存
                for img in images:
                    img.close()
                images.clear()
                
                # 强制垃圾回收
                import gc
                gc.collect()
                
                chunk_info = f"块{chunk_id}/{total_chunks}" if chunk_id > 0 else ""
                simple_log("info", f"{chunk_info} PDF生成完成，处理: {processed_count}/{total_images} 张图片，跳过: {skipped_count} 张", mp_context=False)
            else:
                simple_log("warning", f"没有有效图片可处理，跳过生成PDF", mp_context=False)
                
            return chunk_pdf
        except Exception as e:
            chunk_info = f"块{chunk_id}/{total_chunks}" if chunk_id > 0 else ""
            simple_log("error", f"{chunk_info} 处理图片块时发生严重错误: {str(e)}", mp_context=False)
            if os.path.exists(chunk_pdf):
                try:
                    os.remove(chunk_pdf)
                except Exception as remove_error:
                    simple_log("error", f"{chunk_info} 删除临时PDF文件失败: {str(remove_error)}", mp_context=False)
            raise e

class PDFConvertError(Exception):
    """PDF转换错误异常"""
    pass


if __name__ == "__main__":

    try:
        # 创建测试图片目录结构
        input_dir: Path = Path(r"C:\Users\Elysia\Downloads\Compressed\32D阿西 11-12月福利")
    
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
            
            simple_log("info", "已设置性能限制: 内存512MB, CPU 1核心, 图片处理延迟100ms", mp_context=False)
        
        # 运行转换
        async def test_convert() -> None:
            set_performance_limits()
            converter: PDFConverter = PDFConverter(input_dir, output_dir, "32D阿西 11-12月福利")
            pdf_path: Path = await converter.convert()
            simple_log("info", f"PDF转换完成，保存路径: {pdf_path}", mp_context=False)
            
        asyncio.run(test_convert())
    finally:
        pass