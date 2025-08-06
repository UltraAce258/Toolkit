#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
[display-name-zh] 文档页数统计器
[display-name-en] Document Page Counter

版本: 0.1

功能介绍:
一个可以统计一个或多个文档总可打印页数的工具。
---
兼容性:
- 文件格式: .pdf, .pptx, .docx, .doc, .ppt
- 平台 (DOC/DOCX 精确统计): 需要 Windows 系统并安装 Microsoft Word。
- 平台 (近似统计): 跨平台 (Windows, macOS, Linux)。
---
使用方法:
  1. 将一个或多个支持的文档文件拖入主程序列表。
  2. 点击“执行脚本”。
  3. 脚本会自动检查并尝试安装所需依赖库。
  4. 在终端查看每个文件的页数和最终的总页数统计。
---
可选参数:
本脚本暂无任何可视化或手动可选参数。
---
更新日志:
  - v0.1 (2025-08-05): Alpha版本。修复了在Windows环境下因打印特殊字符导致的UnicodeEncodeError。
~~~
Version: 0.1

Feature Introduction:
A tool to count the total number of printable pages for one or more documents.
---
Compatibility:
- File Formats: .pdf, .pptx, .docx, .doc, .ppt
- Platform (for exact DOC/DOCX count): Requires Windows OS with Microsoft Word installed.
- Platform (for approximate count): Cross-platform (Windows, macOS, Linux).
---
Usage:
  1. Drag one or more supported document files into the main program's list.
  2. Click "Run Script".
  3. The script will automatically check and attempt to install any required dependencies.
  4. Check the terminal for the page count of each file and the final total.
---
Optional Parameters:
This script currently has no visual or manual optional parameters.
---
Changelog:
  - v0.1 (2025-08-05): Alpha release. Fixed an encoding error on Windows environment.
"""

import sys
import os
import subprocess
import platform

# --- Dependency Management / 依赖管理 ---
def install_and_import(package_name, import_name=None):
    """
    检查库是否已安装，如果未安装则尝试使用pip安装，然后导入。
    Checks if a library is installed, tries to install it via pip if not, then imports it.
    """
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"[OK] Dependency '{package_name}' is already installed.")
    except ImportError:
        print(f"[!] Dependency '{package_name}' not found. Attempting to install...")
        try:
            # 使用 --index-url 来增加安装成功率
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package_name,
                "--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple"
            ])
            __import__(import_name)
            print(f"[SUCCESS] Successfully installed and imported '{package_name}'.")
        except Exception as e:
            print(f"[ERROR] Failed to install '{package_name}'. Please install it manually.")
            print(f"   Error details: {e}")
            return None
    return __import__(import_name)

# --- Page Counting Functions / 页数计算函数 ---

def get_pdf_page_count(file_path, pypdf):
    """使用pypdf库获取PDF文件的页数。"""
    try:
        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            return len(reader.pages)
    except Exception as e:
        print(f"    - Error reading PDF file: {e}")
        return 0

def get_pptx_page_count(file_path, pptx):
    """使用python-pptx库获取PPTX文件的幻灯片数量。"""
    try:
        presentation = pptx.Presentation(file_path)
        return len(presentation.slides)
    except Exception as e:
        print(f"    - Error reading PPTX file: {e}")
        return 0

def get_docx_page_count_windows(file_path, win32com_client):
    """[仅Windows] 使用COM接口获取DOC/DOCX的精确页数。"""
    try:
        word = win32com_client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(os.path.abspath(file_path), ReadOnly=True)
        page_count = doc.ComputeStatistics(2) # 2 corresponds to wdStatisticPages
        doc.Close(False)
        word.Quit()
        return page_count
    except Exception as e:
        print(f"    - COM Error (is MS Word installed?): {e}")
        return get_docx_page_count_approx(file_path)

def get_docx_page_count_approx(file_path, python_docx=None):
    """[跨平台] 通过估算字数获取DOCX的近似页数。"""
    if python_docx is None: return 0
    try:
        doc = python_docx.Document(file_path)
        word_count = sum(len(p.text.split()) for p in doc.paragraphs)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    word_count += len(cell.text.split())
        WORDS_PER_PAGE = 500
        page_count = (word_count + WORDS_PER_PAGE - 1) // WORDS_PER_PAGE
        print(f"    - (Approximation based on {word_count} words)")
        return max(1, page_count)
    except Exception as e:
        print(f"    - Error reading DOCX for approximation: {e}")
        return 0

# --- Main Logic / 主逻辑 ---
# --- Main Logic / 主逻辑 ---
def main():
    """
    The main execution function of the script.
    脚本的主执行函数。
    """
    # Text dictionary for bilingual console output
    # 用于双语控制台输出的文本字典
    SCRIPT_TEXTS = {
        'zh': {
            'dep_ok': "[OK] 依赖 '{package_name}' 已安装。",
            'dep_not_found': "[!] 未找到依赖 '{package_name}'。正在尝试安装...",
            'dep_install_success': "[成功] 已成功安装并导入 '{package_name}'。",
            'dep_install_error': "[错误] 安装 '{package_name}' 失败。请手动安装。",
            'dep_error_details': "   错误详情: {e}",
            'office_ok': "[OK] 已检测到支持Office的Windows环境。",
            'office_client_fail': "[!] 已安装pywin32，但未找到其client模块。",
            'office_not_avail': "[!] pywin32不可用。Word文件将使用近似值统计。",
            'no_files': "未提供文件。请将文件拖放到主程序中。",
            'init': "--- 奥创王牌页数统计器 v0.1 初始化 ---",
            'check_dep': "检查依赖...",
            'start_count': "\n--- 开始页数统计 ---",
            'skip_nonexistent': "\n正在跳过不存在的文件: {file_path}",
            'processing': "\n[文件] 正在处理: {filename}",
            'pdf_error': "    - 读取PDF文件时出错: {e}",
            'pptx_error': "    - 读取PPTX文件时出错: {e}",
            'com_error': "    - COM错误 (是否已安装MS Word?): {e}",
            'approx_method': "    - (使用字数估算方法)",
            'approx_error': "    - 估算DOCX时出错: {e}",
            'approx_details': "    - (基于 {word_count} 字的估算)",
            'skip_ext': "    - 跳过 '{ext}' 文件：精确统计需要Windows环境下的MS Office。",
            'unsupported_type': "    - 不支持的文件类型。",
            'pages_found': "   => 找到的页数/幻灯片数: {pages}",
            'all_done': "\n--- 所有任务已完成。 ---",
            'total_pages': "\n[总计] 估算的总页数: {total_pages}"
        },
        'en': {
            'dep_ok': "[OK] Dependency '{package_name}' is already installed.",
            'dep_not_found': "[!] Dependency '{package_name}' not found. Attempting to install...",
            'dep_install_success': "[SUCCESS] Successfully installed and imported '{package_name}'.",
            'dep_install_error': "[ERROR] Failed to install '{package_name}'. Please install it manually.",
            'dep_error_details': "   Error details: {e}",
            'office_ok': "[OK] Windows environment with Office support detected.",
            'office_client_fail': "[!] pywin32 installed, but client module not found.",
            'office_not_avail': "[!] pywin32 is not available. Will use approximation for Word files.",
            'no_files': "No files provided. Please drag and drop files into the application.",
            'init': "--- UltraAce Page Counter v0.1 Initialized ---",
            'check_dep': "Checking dependencies...",
            'start_count': "\n--- Starting Page Count ---",
            'skip_nonexistent': "\nSkipping non-existent file: {file_path}",
            'processing': "\n[FILE] Processing: {filename}",
            'pdf_error': "    - Error reading PDF file: {e}",
            'pptx_error': "    - Error reading PPTX file: {e}",
            'com_error': "    - COM Error (is MS Word installed?): {e}",
            'approx_method': "    - (Using word count approximation method)",
            'approx_error': "    - Error reading DOCX for approximation: {e}",
            'approx_details': "    - (Approximation based on {word_count} words)",
            'skip_ext': f"    - Skipping '{{ext}}' file: Precise counting requires MS Office on Windows.",
            'unsupported_type': "    - Unsupported file type.",
            'pages_found': "   => Pages/Slides found: {pages}",
            'all_done': "\n--- All tasks completed. ---",
            'total_pages': "\n[TOTAL] Total Estimated Page Count: {total_pages}"
        }
    }

    import argparse
    parser = argparse.ArgumentParser(description="Count pages of various document types.")
    parser.add_argument('files', nargs='*', help="Paths to document files.")
    # Add arguments for GUI interaction, suppressed from standard help.
    # 添加用于GUI交互的参数，并从标准帮助信息中抑制。
    parser.add_argument('--lang', type=str, default='en', choices=['zh', 'en'], help=argparse.SUPPRESS)
    parser.add_argument('--gui-mode', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('-r', '--recursive', action='store_true', help=argparse.SUPPRESS) # Keep for potential future use / 保留以备将来使用
    args = parser.parse_args()

    # Select the language dictionary based on the --lang argument
    # 根据 --lang 参数选择语言字典
    lang_texts = SCRIPT_TEXTS.get(args.lang, SCRIPT_TEXTS['en'])

    if not args.files:
        print(lang_texts['no_files'])
        sys.exit(1)

    print(lang_texts['init'])
    print(lang_texts['check_dep'])
    
    # Redefine the dependency installer to use the bilingual text dictionary
    # 重新定义依赖安装器以使用双语文本字典
    def install_and_import(package_name, import_name=None):
        if import_name is None: import_name = package_name
        try:
            __import__(import_name)
            print(lang_texts['dep_ok'].format(package_name=package_name))
        except ImportError:
            print(lang_texts['dep_not_found'].format(package_name=package_name))
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package_name,
                    "--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple"
                ])
                __import__(import_name)
                print(lang_texts['dep_install_success'].format(package_name=package_name))
            except Exception as e:
                print(lang_texts['dep_install_error'].format(package_name=package_name))
                print(lang_texts['dep_error_details'].format(e=e))
                return None
        return __import__(import_name)

    # Redefine page counting functions to accept the text dictionary for printing errors
    # 重新定义页数计算函数以接受文本字典来打印错误
    def get_pdf_page_count(file_path, pypdf):
        try:
            with open(file_path, 'rb') as f: return len(pypdf.PdfReader(f).pages)
        except Exception as e:
            print(lang_texts['pdf_error'].format(e=e)); return 0

    def get_pptx_page_count(file_path, pptx):
        try:
            return len(pptx.Presentation(file_path).slides)
        except Exception as e:
            print(lang_texts['pptx_error'].format(e=e)); return 0

    def get_docx_page_count_windows(file_path, win32com_client):
        try:
            word = win32com_client.Dispatch("Word.Application")
            word.Visible = False
            doc = word.Documents.Open(os.path.abspath(file_path), ReadOnly=True)
            page_count = doc.ComputeStatistics(2)
            doc.Close(False); word.Quit()
            return page_count
        except Exception as e:
            print(lang_texts['com_error'].format(e=e))
            return get_docx_page_count_approx(file_path, install_and_import('python-docx', 'docx'))

    def get_docx_page_count_approx(file_path, python_docx):
        if python_docx is None: return 0
        try:
            doc = python_docx.Document(file_path)
            word_count = sum(len(p.text.split()) for p in doc.paragraphs)
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells: word_count += len(cell.text.split())
            WORDS_PER_PAGE = 500
            page_count = (word_count + WORDS_PER_PAGE - 1) // WORDS_PER_PAGE
            print(lang_texts['approx_details'].format(word_count=word_count))
            return max(1, page_count)
        except Exception as e:
            print(lang_texts['approx_error'].format(e=e)); return 0

    # Main logic with bilingual output
    # 使用双语输出的主逻辑
    pypdf = install_and_import('pypdf')
    pptx = install_and_import('python-pptx', 'pptx')
    python_docx = install_and_import('python-docx', 'docx')
    
    is_windows_office_ready = False
    if platform.system() == "Windows":
        win32com = install_and_import('pywin32', 'win32com')
        if win32com:
            try:
                __import__('win32com.client')
                is_windows_office_ready = True
                print(lang_texts['office_ok'])
            except ImportError:
                print(lang_texts['office_client_fail'])
        else:
            print(lang_texts['office_not_avail'])
            
    total_pages = 0
    print(lang_texts['start_count'])

    for file_path in args.files:
        if not os.path.exists(file_path):
            print(lang_texts['skip_nonexistent'].format(file_path=file_path))
            continue

        print(lang_texts['processing'].format(filename=os.path.basename(file_path)))
        ext = os.path.splitext(file_path)[1].lower()
        pages = 0

        if ext == '.pdf':
            if pypdf: pages = get_pdf_page_count(file_path, pypdf)
        elif ext == '.pptx':
            if pptx: pages = get_pptx_page_count(file_path, pptx)
        elif ext in ['.docx', '.doc', '.ppt']:
            if is_windows_office_ready:
                # Must re-import client here as it's scoped within the conditional import
                # 必须在此处重新导入client，因为它作用域在条件导入内
                win32_client = __import__('win32com.client').client
                pages = get_docx_page_count_windows(file_path, win32_client)
            elif ext == '.docx':
                print(lang_texts['approx_method'])
                pages = get_docx_page_count_approx(file_path, python_docx)
            else:
                print(lang_texts['skip_ext'].format(ext=ext))
        else:
            print(lang_texts['unsupported_type'])

        if pages > 0:
            print(lang_texts['pages_found'].format(pages=pages))
            total_pages += pages

    print(lang_texts['all_done'])
    print(lang_texts['total_pages'].format(total_pages=total_pages))


if __name__ == '__main__':
    main()