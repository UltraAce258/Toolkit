#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
[display-name-zh] PDF与图片合并器
[display-name-en] PDF & Image Merger

功能:
  将大量图片和PDF文件，按文件名顺序合并成一个单一的、高质量的PDF文档。非常适合将报告、幻灯片或漫画章节整理归档。

核心特性:
  1. 混合输入: 支持一次性拖入图片 (JPG, PNG, BMP...)、PDF文件或包含它们的文件夹。
  2. 递归搜索: 自动深入所有子文件夹查找支持的文件。
  3. 智能排序: 采用自然语言排序，确保 'page2.png' 在 'page10.png' 之前，完美处理数字编号。
  4. 两种图片模式:
     a) (默认) 适应A4画幅: 将图片缩放并居中放置在横向A4页面上，保留可调整的边距。
     b) 等尺寸转换: 将图片直接转换为与其尺寸完全相同的PDF页面。
  5. 无缝PDF拼接: 直接将输入的PDF文件按页面顺序完整地插入到最终文档中。
  6. 上下文感知输出: 在源目录或工具箱目录旁创建“合并的PDF_Merged_PDF”文件夹存放结果，并以时间戳命名。
~~~
Function:
  Merges a large number of images and PDF files, sorted by filename, into a single, high-quality PDF document. Ideal for archiving reports, slides, or comic book chapters.

Core Features:
  1. Mixed Input: Supports dragging and dropping images (JPG, PNG, BMP...), PDF files, or folders containing them all at once.
  2. Recursive Search: Automatically searches all subdirectories for supported files.
  3. Smart Sorting: Uses natural language sorting to ensure 'page2.png' comes before 'page10.png', handling numerical order correctly.
  4. Two Image Modes:
     a) (Default) Fit to A4: Scales and centers the image on a landscape A4 page with adjustable margins.
     b) Same Size: Converts the image directly into a PDF page of the exact same dimensions.
  5. Seamless PDF Splicing: Inserts all pages from input PDF files directly and in order into the final document.
  6. Context-Aware Output: Creates a "合并的PDF_Merged_PDF" folder next to the source or toolkit directory to store the result, named with a timestamp.
"""

import os
import sys
import argparse
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime

# --- Internationalization (i18n) Setup ---
MESSAGES = {
    'zh': {
        "init": "--- PDF与图片合并器 v1.3 (渲染修正版) 启动 ---",
        "dep_checking": "--- 正在检查依赖库: {libs} ---",
        "dep_missing": "提示: 未找到 '{lib}'，正在尝试自动安装...",
        "dep_success": "成功: '{lib}' 已安装。",
        "dep_fail": "错误: 自动安装 '{lib}' 失败。请手动运行 'pip install {package}'。",
        "files_found": "\n发现 {count} 个有效文件待处理 (已递归搜索):",
        "files_none": "\n在指定路径下未找到任何支持的图片或PDF文件。",
        "processing": "\n[处理中] -> 正在合并文件 {i}/{total}: {filename}",
        "process_pdf": "  -> 识别为PDF，将插入 {num_pages} 页。",
        "process_img": "  -> 识别为图片，模式: {mode}。",
        "success_save": "\n[成功] -> 已合并 {count} 个文件到: {path}",
        "failure_merge": "\n[失败] -> 合并文件时出错: {e}",
        "output_dir_creating": "创建输出目录: {path}",
        "output_dir_fail": "错误: 创建输出目录失败: {e}",
        "all_done": "\n--- 所有任务已完成 ---",
    },
    'en': {
        "init": "--- PDF & Image Merger v1.3 (Render Fix) Started ---",
        "dep_checking": "--- Checking dependencies: {libs} ---",
        "dep_missing": "Info: '{lib}' not found. Attempting to auto-install...",
        "dep_success": "Success: '{lib}' has been installed.",
        "dep_fail": "Error: Auto-install of '{lib}' failed. Please run 'pip install {package}' manually.",
        "files_found": "\nFound {count} valid files to process (Recursive Search enabled):",
        "files_none": "\nNo supported image or PDF files found in the specified paths.",
        "processing": "\n[Processing] -> Merging file {i}/{total}: {filename}",
        "process_pdf": "  -> Identified as PDF, will insert {num_pages} pages.",
        "process_img": "  -> Identified as Image, Mode: {mode}.",
        "success_save": "\n[SUCCESS] -> Merged {count} files to: {path}",
        "failure_merge": "\n[FAILURE] -> Error during merge: {e}",
        "output_dir_creating": "Creating output directory: {path}",
        "output_dir_fail": "Error: Failed to create output directory: {e}",
        "all_done": "\n--- All tasks completed ---",
    }
}

def T(key, lang='en', **kwargs):
    return MESSAGES.get(lang, MESSAGES['en']).get(key, key).format(**kwargs)

# --- Dependency Management ---
DEPS = { 'fitz': 'PyMuPDF', 'PIL': 'Pillow', 'natsort': 'natsort' }

def setup_dependencies(lang):
    print(T("dep_checking", lang, libs=", ".join(DEPS.values())))
    for lib, package in DEPS.items():
        if importlib.util.find_spec(lib): continue
        print(T("dep_missing", lang, lib=lib))
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(T("dep_success", lang, lib=lib)); importlib.invalidate_caches()
        except subprocess.CalledProcessError:
            print(T("dep_fail", lang, lib=lib, package=package)); return False
    return True

# --- Main Logic ---
def get_files_to_process(paths):
    supported_exts = ['.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff']
    files_to_process = set()
    for path in paths:
        p = Path(path)
        if p.is_file() and p.suffix.lower() in supported_exts:
            files_to_process.add(str(p.resolve()))
        elif p.is_dir():
            for ext in supported_exts:
                for f in p.rglob(f'*{ext}'):
                    files_to_process.add(str(f.resolve()))
    return list(files_to_process)

def main():
    parser = argparse.ArgumentParser(description="Merges images and PDFs into a single PDF.", add_help=False)
    custom_args = parser.add_argument_group('Custom Parameters')
    custom_args.add_argument('--help', action='help', help='Show this help message and exit.')
    custom_args.add_argument('--mode', type=str, default="a4", choices=["a4", "same"], help="图片处理模式 [display: a4=适应A4画幅 | same=等尺寸转换]")
    custom_args.add_argument('--margin-percent', type=int, default=20, help="A4模式下的横向总边距百分比 (0-100)\nTotal horizontal margin percentage in A4 mode (0-100).")

    gui_args = parser.add_argument_group('GUI Internal')
    gui_args.add_argument('files', nargs='*', help=argparse.SUPPRESS)
    gui_args.add_argument('--gui-mode', action='store_true', help=argparse.SUPPRESS)
    gui_args.add_argument('--lang', type=str, default='en', choices=['zh', 'en'], help=argparse.SUPPRESS)
    
    args = parser.parse_args()
    lang = args.lang

    print(T("init", lang))
    if not setup_dependencies(lang): sys.exit(1)

    import fitz
    from PIL import Image
    from natsort import natsorted

    files_to_process = get_files_to_process(args.files)

    if not files_to_process:
        print(T("files_none", lang)); return

    files_to_process = natsorted(files_to_process)
    
    print(T("files_found", lang, count=len(files_to_process)))
    for f in files_to_process: print(f"- {Path(f).name}")

    parent_dirs = {Path(f).parent for f in files_to_process}
    output_base_dir = Path.cwd() / "合并的PDF_Merged_PDF" if len(parent_dirs) != 1 else list(parent_dirs)[0] / "合并的PDF_Merged_PDF"

    if not output_base_dir.exists():
        try:
            print(T("output_dir_creating", lang, path=output_base_dir)); output_base_dir.mkdir(parents=True)
        except OSError as e:
            print(T("output_dir_fail", lang, e=e)); return

    final_doc = fitz.open()

    try:
        for i, file_path_str in enumerate(files_to_process):
            file_path = Path(file_path_str)
            print(T("processing", lang, i=i+1, total=len(files_to_process), filename=file_path.name))

            if file_path.suffix.lower() == '.pdf':
                with fitz.open(file_path) as doc_to_insert:
                    print(T("process_pdf", lang, num_pages=len(doc_to_insert)))
                    final_doc.insert_pdf(doc_to_insert)
            else:
                mode_text = "适应A4(Fit to A4)" if args.mode == 'a4' else "等尺寸(Same Size)"
                print(T("process_img", lang, mode=mode_text if lang == 'zh' else args.mode.upper()))
                
                image_bytes = file_path.read_bytes()
                with Image.open(file_path) as img:
                    img_width, img_height = img.size

                if args.mode == "a4":
                    # --- START OF CORRECTION v1.3 ---
                    # Explicitly define page dimensions
                    page_width, page_height = fitz.paper_size("a4-l")
                    page = final_doc.new_page(width=page_width, height=page_height)
                    
                    # Define available drawing area based on horizontal and vertical margins
                    margin_x = page.rect.width * (args.margin_percent / 100.0) / 2
                    margin_y = page.rect.height * 0.05  # A small, fixed vertical margin
                    
                    available_width = page.rect.width - (2 * margin_x)
                    available_height = page.rect.height - (2 * margin_y)

                    # Calculate scaling factor
                    scale_w = available_width / img_width
                    scale_h = available_height / img_height
                    scale = min(scale_w, scale_h)

                    # Calculate final dimensions of the image
                    final_w = img_width * scale
                    final_h = img_height * scale
                    
                    # Center the image on the page
                    x0 = (page.rect.width - final_w) / 2
                    y0 = (page.rect.height - final_h) / 2
                    x1 = x0 + final_w
                    y1 = y0 + final_h
                    
                    img_rect = fitz.Rect(x0, y0, x1, y1)
                    page.insert_image(img_rect, stream=image_bytes)
                    # --- END OF CORRECTION v1.3 ---

                else: # same size
                    page = final_doc.new_page(width=img_width, height=img_height)
                    page.insert_image(page.rect, stream=image_bytes)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_base_dir / f"merged_{timestamp}.pdf"
        final_doc.save(output_path, garbage=4, deflate=True, clean=True)
        print(T("success_save", lang, count=len(files_to_process), path=output_path))

    except Exception as e:
        print(T("failure_merge", lang, e=e))
    finally:
        final_doc.close()
        print(T("all_done", lang))

if __name__ == "__main__":
    main()
