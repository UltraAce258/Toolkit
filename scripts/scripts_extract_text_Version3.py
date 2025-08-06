#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
[display-name-zh] 通用文本提取器
[display-name-en] Universal Text Extractor

功能:
  本脚本是文档和图片文本提取的终极工具。它可以从多种格式中批量提取纯文本内容，并为每一个输入文件生成一个对应的.txt文本文件。

支持的格式:
  - 文档: .pdf, .docx, .pptx, .doc (旧版Word, 仅限Windows)
  - 图片: .jpg, .jpeg, .png, .bmp, .webp, .heic, .heif, .raw, .cr2, .nef, .arw

核心特性:
  1. 依赖自动安装: 运行时若发现缺少必要的库，会尝试自动安装。
  2. 智能递归: 当拖入文件夹时，会自动递归查找所有支持的文件。
  3. 智能排序: 支持按文件名 (自然语言排序) 或按文件修改时间排序。
  4. (新) 上下文感知输出:
     - 处理单个文件时，提取的文本保存在原文件旁，后缀为“_extracted.txt”。
     - 处理来自同一文件夹的多个文件时，会在该文件夹内创建“提取的文本_Extracted_Text”子文件夹来存放所有结果。
     - 处理来自不同文件夹的多个文件时，会在工具箱主程序旁创建“提取的文本_Extracted_Text”文件夹作为统一输出目录。
  5. GUI深度集成: 专为“奥创王牌工具箱”设计，提供清晰的双语进度反馈和可视化参数。
~~~
Function:
  This script is the ultimate tool for document and image text extraction. It batch extracts plain text from various formats and generates a corresponding .txt file for each input file.

Supported Formats:
  - Documents: .pdf, .docx, .pptx, .doc (Legacy Word, Windows only)
  - Images: .jpg, .jpeg, .png, .bmp, .webp, .heic, .heif, .raw, .cr2, .nef, .arw

Core Features:
  1. Auto-Dependency Installation: Attempts to automatically install required libraries if they are missing.
  2. Smart Recursion: Automatically and recursively finds all supported files within a folder.
  3. Smart Sorting: Supports sorting by filename (natural sort) or by file modification time.
  4. (New) Context-Aware Output:
     - For a single file, the extracted text is saved alongside the original with an "_extracted.txt" suffix.
     - For multiple files from the same folder, a subfolder named "提取的文本_Extracted_Text" is created within that folder to store all results.
     - For multiple files from different folders, a folder named "提取的文本_Extracted_Text" is created next to the main toolkit program as a unified output directory.
  5. Deep GUI Integration: Designed for the "UltraAce Toolkit" with clear bilingual progress feedback and visual parameters.
"""

import os
import sys
import argparse
import platform
import subprocess
import importlib.util
from pathlib import Path

# --- Internationalization (i18n) Setup ---
MESSAGES = {
    'zh': {
        "init": "--- 通用文本提取器 v4.2 启动 ---",
        "dep_checking": "--- 正在检查依赖库 ---",
        "dep_missing": "提示: 未找到 '{module}'，正在尝试自动安装 '{pkg}'...",
        "dep_success": "成功: '{pkg}' 已安装。",
        "dep_fail": "错误: 自动安装 '{pkg}' 失败。请手动运行 'pip install {pkg}'。",
        "dep_warn_ocr": "警告: OCR引擎 'easyocr' 安装失败。图片提取功能将不可用。",
        "search_mode": "搜索模式: 自动 (文件直接处理，文件夹递归搜索)",
        "mode_sort_by": "排序方式: {sort_by}",
        "files_found": "\n发现 {count} 个待处理文件:",
        "files_none": "\n未找到任何支持的文档或图片文件。",
        "ocr_init": "首次运行，正在初始化OCR引擎 (可能需要下载模型)...",
        "ocr_ready": "OCR引擎准备就绪。",
        "processing": "\n[处理中 {i}/{total}] -> {filename}",
        "success_save": "  [成功] -> 已保存到: {path}",
        "failure_write": "  [失败] -> 写入文件时出错: {e}",
        "failure_process": "  [失败] -> 处理文件时出错: {e}",
        "failure_read_img": "  [失败] -> 读取图片失败: {e}",
        "unsupported": "  跳过不支持的文件。",
        "doc_only_windows": "错误: .doc文件仅在Windows系统且安装了Word后才能处理。",
        "output_dir_creating": "  创建输出目录: {path}",
        "output_dir_fail": "  错误: 创建输出目录失败: {e}",
        "all_done": "\n--- 所有任务已完成 ---",
    },
    'en': {
        "init": "--- Universal Text Extractor v4.2 Started ---",
        "dep_checking": "--- Checking Dependencies ---",
        "dep_missing": "Info: '{module}' not found. Attempting to auto-install '{pkg}'...",
        "dep_success": "Success: '{pkg}' has been installed.",
        "dep_fail": "Error: Auto-install of '{pkg}' failed. Please run 'pip install {pkg}' manually.",
        "dep_warn_ocr": "Warning: OCR engine 'easyocr' failed to install. Image extraction will be unavailable.",
        "search_mode": "Search Mode: Automatic (Files processed directly, folders searched recursively)",
        "mode_sort_by": "Sorting by: {sort_by}",
        "files_found": "\nFound {count} files to process:",
        "files_none": "\nNo supported document or image files found.",
        "ocr_init": "First run, initializing OCR engine (may download models)...",
        "ocr_ready": "OCR engine is ready.",
        "processing": "\n[Processing {i}/{total}] -> {filename}",
        "success_save": "  [SUCCESS] -> Saved to: {path}",
        "failure_write": "  [FAILURE] -> Error writing file: {e}",
        "failure_process": "  [FAILURE] -> Error processing file: {e}",
        "failure_read_img": "  [FAILURE] -> Failed to read image: {e}",
        "unsupported": "  Skipping unsupported file.",
        "doc_only_windows": "Error: .doc files can only be processed on Windows with MS Word installed.",
        "output_dir_creating": "  Creating output directory: {path}",
        "output_dir_fail": "  Error: Failed to create output directory: {e}",
        "all_done": "\n--- All tasks completed ---",
    }
}

def T(key, lang='en', **kwargs):
    return MESSAGES.get(lang, MESSAGES['en']).get(key, key).format(**kwargs)

# --- Dependency Management ---
def check_and_install(pkg_name, module_name=None, lang='en', extra_args=None):
    if module_name is None: module_name = pkg_name
    if importlib.util.find_spec(module_name): return True
    print(T("dep_missing", lang, pkg=pkg_name, module=module_name))
    try:
        command = [sys.executable, "-m", "pip", "install", pkg_name]
        if extra_args: command.extend(extra_args)
        subprocess.check_call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(T("dep_success", lang, pkg=pkg_name))
        importlib.invalidate_caches()
        return True
    except subprocess.CalledProcessError:
        print(T("dep_fail", lang, pkg=pkg_name))
        return False

def setup_dependencies(lang):
    print(T("dep_checking", lang))
    check_and_install('python-docx', 'docx', lang)
    check_and_install('python-pptx', 'pptx', lang)
    check_and_install('PyMuPDF', 'fitz', lang)
    if platform.system() == "Windows":
        check_and_install('pywin32', 'win32com', lang)
    check_and_install('natsort', 'natsort', lang)
    check_and_install('pillow-heif', 'pillow_heif', lang)
    check_and_install('rawpy', 'rawpy', lang)
    if not check_and_install('easyocr', extra_args=['--extra-index-url', 'https://download.pytorch.org/whl/cpu'], lang=lang):
        print(T("dep_warn_ocr", lang))

# --- Extraction Functions ---
def extract_text_from_docx(file_path):
    import docx
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_pptx(file_path):
    import pptx
    prs = pptx.Presentation(file_path)
    return "\n".join([shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text")])

def extract_text_from_pdf(file_path):
    import fitz
    with fitz.open(file_path) as doc:
        return "".join([page.get_text() for page in doc])

def extract_text_from_doc(file_path, lang):
    if platform.system() != "Windows": return T("doc_only_windows", lang)
    try:
        import win32com.client, pythoncom
        pythoncom.CoInitialize()
        word_app = win32com.client.Dispatch("Word.Application")
        word_app.Visible = False
        doc = word_app.Documents.Open(os.path.abspath(file_path))
        text = doc.Content.Text
        doc.Close()
        word_app.Quit()
        pythoncom.CoUninitialize()
        return text
    except Exception: return T("doc_only_windows", lang)

def extract_text_from_image(file_path, ocr_reader, lang):
    import numpy as np
    from PIL import Image
    try:
        ext = Path(file_path).suffix.lower()
        if ext in ['.heic', '.heif']:
            import pillow_heif
            heif_file = pillow_heif.read_heif(file_path)
            image = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data, "raw")
        elif ext in ['.raw', '.cr2', '.nef', '.arw', '.dng']:
            import rawpy
            with rawpy.imread(file_path) as raw: image = Image.fromarray(raw.postprocess())
        else: image = Image.open(file_path)
        image_np = np.array(image.convert('RGB'))
        result = ocr_reader.readtext(image_np, detail=0, paragraph=True)
        return "\n".join(result)
    except Exception as e: raise IOError(T("failure_read_img", lang, e=e)) from e

# --- Main Logic ---
def get_all_supported_files(paths, sort_by):
    doc_exts = ['.pdf', '.docx', '.pptx', '.doc']
    img_exts = ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.heic', '.heif', '.raw', '.cr2', '.nef', '.arw', '.dng']
    supported_exts = doc_exts + img_exts
    files_to_process = set()
    for path in paths:
        p = Path(path)
        if p.is_file() and p.suffix.lower() in supported_exts:
            files_to_process.add(str(p))
        elif p.is_dir():
            for ext in supported_exts:
                files_to_process.update(str(f) for f in p.rglob(f"*{ext}"))
    file_list = list(files_to_process)
    if sort_by == 'date': file_list.sort(key=os.path.getmtime)
    else:
        from natsort import natsorted
        file_list = natsorted(file_list)
    return file_list, img_exts

def main():
    parser = argparse.ArgumentParser(description="Universal Text Extractor for documents and images.")
    parser.add_argument('files', nargs='*', help="Paths to files or folders from the GUI.")
    parser.add_argument('--gui-mode', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--lang', type=str, default='en', choices=['zh', 'en'], help=argparse.SUPPRESS)
    parser.add_argument('--sort-by', type=str, default="name", choices=["name", "date"], help="Sort files by 'name' (natural) or 'date' (modification time).")
    args = parser.parse_args()
    lang = args.lang

    print(T("init", lang))
    setup_dependencies(lang)
    print(T("search_mode", lang))
    print(T("mode_sort_by", lang, sort_by=args.sort_by))

    files_to_process, img_exts = get_all_supported_files(args.files, args.sort_by)

    if not files_to_process:
        print(T("files_none", lang))
        return

    print(T("files_found", lang, count=len(files_to_process)))
    for f in files_to_process: print(f"- {f}")

    # ======================================================================
    # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    # (MODIFIED) Context-Aware Output Directory Logic
    # ======================================================================
    output_base_dir = None
    if len(files_to_process) > 1:
        parent_dirs = {Path(f).parent for f in files_to_process}
        if len(parent_dirs) == 1:
            # Batch mode, same source directory
            output_base_dir = list(parent_dirs)[0] / "提取的文本_Extracted_Text"
        else:
            # Batch mode, multiple source directories
            output_base_dir = Path.cwd() / "提取的文本_Extracted_Text"
    # If single file mode, output_base_dir remains None
    # ======================================================================
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    ocr_reader = None
    if any(Path(f).suffix.lower() in img_exts for f in files_to_process):
        try:
            import easyocr
            print(T("ocr_init", lang))
            ocr_reader = easyocr.Reader(['ch_sim', 'en'])
            print(T("ocr_ready", lang))
        except (ImportError, Exception): ocr_reader = None

    for i, file_path in enumerate(files_to_process):
        p = Path(file_path)
        print(T("processing", lang, i=i+1, total=len(files_to_process), filename=p.name))
        
        # Determine final output directory for this specific file
        if output_base_dir:
            output_dir = output_base_dir
        else:
            # Single file mode
            output_dir = p.parent

        # Create output directory if it doesn't exist
        if not output_dir.exists():
            try:
                print(T("output_dir_creating", lang, path=output_dir))
                output_dir.mkdir(parents=True)
            except OSError as e:
                print(T("output_dir_fail", lang, e=e))
                continue # Skip this file if its output dir can't be created

        output_path = output_dir / f"{p.stem}_extracted.txt"
        text_content = ""
        
        try:
            ext = p.suffix.lower()
            if ext in ['.pdf']: text_content = extract_text_from_pdf(p)
            elif ext in ['.docx']: text_content = extract_text_from_docx(p)
            elif ext in ['.pptx']: text_content = extract_text_from_pptx(p)
            elif ext in ['.doc']: text_content = extract_text_from_doc(p, lang)
            elif ext in img_exts:
                if ocr_reader: text_content = extract_text_from_image(p, ocr_reader, lang)
                else: continue
            else:
                print(T("unsupported", lang)); continue

            with open(output_path, 'w', encoding='utf-8') as f: f.write(text_content)
            print(T("success_save", lang, path=output_path))
        except Exception as e:
            print(T("failure_process", lang, e=e))

    print(T("all_done", lang))

if __name__ == "__main__":
    main()