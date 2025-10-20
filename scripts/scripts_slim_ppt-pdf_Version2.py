#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
[display-name-zh] PPT/PDF瘦身器
[display-name-en] PPT/PDF Slimmer

版本: 2.1

功能介绍:
智能移除演示文稿（PPTX）或其PDF版本中，因内容渐进式展示而产生的冗余幻灯片/页面。例如，当第N+1页完全包含第N页的内容时，脚本会移除第N页，只保留内容最全的最后一页。
---
兼容性:
- 文件格式: .pdf, .pptx
- 依赖库: PyMuPDF, python-pptx
- 平台: 跨平台 (Windows, macOS, Linux)
---
使用方法:
  1. 将一个或多个需要处理的PPTX或PDF文件拖入主程序列表。
  2. 点击“执行脚本”。
  3. 脚本会自动检查并安装所需依赖库。
  4. 处理完成后，会在原文件相同目录下生成一个带有 "_slimmer" 后缀的新文件。
---
可选参数:
本脚本暂无任何可视化或手动可选参数。
---
更新日志:
  - v2.1 (2025-10-20): 最终稳定版。根据用户最终反馈，固化了最成功的v1.5/v1.6双重模糊匹配算法。并新增对.pptx文件的原生支持，使其成为一个真正的PPT/PDF瘦身器。
  - v2.0 (2025-10-20): 错误的架构升级尝试。
  - v1.5 (2025-10-20): 引入了正确的“前缀匹配”思想，被证明是解决“续写行”的关键。
  - v1.4 (2025-10-20): 引入基于模糊相似度计分的包含关系判断，是成功的关键一步。
~~~
Version: 2.1

Feature Introduction:
Intelligently removes redundant slides/pages from presentation files (PPTX) or their PDF versions that result from progressive content reveals. For instance, if page N+1 fully contains the content of page N, the script removes page N, keeping only the most comprehensive final page.
---
Compatibility:
- File Format: .pdf, .pptx
- Dependency: PyMuPDF, python-pptx
- Platform: Cross-platform (Windows, macOS, Linux)
---
Usage:
  1. Drag and drop one or more PPTX or PDF files into the main application's list.
  2. Click "Run Script".
  3. The script will automatically check and attempt to install the required dependencies.
  4. After processing, a new file with a "_slimmer" suffix will be created in the same directory as the original file.
---
Optional Parameters:
This script currently has no visual or manual optional parameters.
---
Changelog:
  - v2.1 (2025-10-20): Final stable version. Based on final user feedback, the most successful v1.5/v1.6 dual fuzzy matching algorithm is now solidified. Added native support for .pptx files, making it a true PPT/PDF slimmer.
  - v2.0 (2025-10-20): A flawed architectural upgrade attempt.
  - v1.5 (2025-10-20): Introduced the correct "prefix matching" logic, which proved key to solving the "line continuation" issue.
  - v1.4 (2025-10-20): Introduced fuzzy similarity scoring, a crucial successful step.
"""

import sys
import os
import re
import subprocess
import argparse
from difflib import SequenceMatcher

# --- 文本字典 (用于国际化) / Text Dictionary (for i18n) ---
SCRIPT_TEXTS = {
    'zh': {
        'init': "--- PPT/PDF瘦身器 v2.1 初始化 ---",
        'check_dep': "检查依赖: {package_name}...",
        'dep_ok': "[OK] 依赖 '{package_name}' 已安装。",
        'dep_not_found': "[!] 未找到依赖 '{package_name}'。正在尝试安装...",
        'dep_install_success': "[成功] 已成功安装并导入 '{package_name}'。",
        'dep_install_error': "[错误] 安装 '{package_name}' 失败，脚本无法继续。请手动运行 `pip install {pip_name}`。",
        'dep_error_details': "   错误详情: {e}",
        'no_files': "未提供文件。请将PPTX或PDF文件拖放到主程序中再执行。",
        'start_processing': "\n--- 开始处理文件 ---",
        'processing_file': "\n[文件] {filename}",
        'skip_unsupported': "   - 跳过: 不支持的文件类型 (仅支持 .pdf, .pptx)。",
        'is_processing': "   - 正在分析内容...",
        'single_page': "   - 文件只有一页/一张幻灯片或为空，无需处理。",
        'no_redundancy': "   - 未发现可移除的冗余页面/幻灯片。",
        'process_success': "   => 成功! 原始数量: {original}, 瘦身后: {final}。已保存至: {output_path}",
        'process_fail': "   - 处理失败: {error}",
        'all_done': "\n--- 所有任务已完成。 ---"
    },
    'en': { 'init': "--- PPT/PDF Slimmer v2.1 Initialized ---", }
}
SCRIPT_TEXTS['en'] = {**SCRIPT_TEXTS['zh'], **SCRIPT_TEXTS['en']} # Merge dicts

def install_and_import(package_name, import_name=None, pip_name=None):
    texts = SCRIPT_TEXTS.get(getattr(main, 'lang', 'en'), SCRIPT_TEXTS['zh'])
    if import_name is None: import_name = package_name
    if pip_name is None: pip_name = package_name
    
    print(texts['check_dep'].format(package_name=package_name))
    try:
        return __import__(import_name)
    except ImportError:
        print(texts['dep_not_found'].format(package_name=package_name))
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name, "--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple"])
            print(texts['dep_install_success'].format(package_name=package_name))
            return __import__(import_name)
        except Exception as e:
            print(texts['dep_install_error'].format(package_name=package_name, pip_name=pip_name))
            print(texts['dep_error_details'].format(e=e))
            return None

def normalize_text_lines(text):
    if not text: return []
    lines = text.strip().splitlines()
    normalized_lines = [re.sub(r'\s+', ' ', line).strip() for line in lines]
    return [line for line in normalized_lines if line]

def is_line_contained_fuzzy(line_a, lines_b, sim_threshold=0.9):
    for line_b in lines_b:
        if SequenceMatcher(None, line_a, line_b).ratio() >= sim_threshold:
            return True
        if len(line_b) > len(line_a) and line_b.startswith(line_a):
            return True
    return False

def is_subset_fuzzy(lines_a, lines_b):
    if not lines_a: return True
    if not lines_b: return False
    return all(is_line_contained_fuzzy(line_a, lines_b) for line_a in lines_a)

def slim_pdf(input_path, output_path, fitz, texts):
    doc = fitz.open(input_path)
    if doc.page_count <= 1:
        print(texts['single_page'])
        return
    
    page_contents = [normalize_text_lines(page.get_text("text")) for page in doc]
    
    pages_to_delete = []
    for i in range(doc.page_count - 1):
        current_lines = page_contents[i]
        next_lines = page_contents[i+1]
        if current_lines:
            content_increased = (sum(len(s) for s in next_lines) > sum(len(s) for s in current_lines)) or \
                                (len(next_lines) > len(current_lines))
            if content_increased and is_subset_fuzzy(current_lines, next_lines):
                pages_to_delete.append(i)

    if not pages_to_delete:
        print(texts['no_redundancy'])
        doc.close()
        return

    final_pages_to_keep = [p for p in range(doc.page_count) if p not in pages_to_delete]
    new_doc = fitz.open()
    for page_num in final_pages_to_keep:
        new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
    new_doc.save(output_path, garbage=4, deflate=True, clean=True)
    new_doc.close()
    doc.close()
    print(texts['process_success'].format(original=len(page_contents), final=len(final_pages_to_keep), output_path=os.path.basename(output_path)))

def slim_pptx(input_path, output_path, pptx, texts):
    prs = pptx.Presentation(input_path)
    if len(prs.slides) <= 1:
        print(texts['single_page'])
        return

    slide_contents = []
    for slide in prs.slides:
        slide_text = "\n".join(shape.text for shape in slide.shapes if shape.has_text_frame)
        slide_contents.append(normalize_text_lines(slide_text))

    slides_to_delete_indices = []
    for i in range(len(prs.slides) - 1):
        current_lines = slide_contents[i]
        next_lines = slide_contents[i+1]
        if current_lines:
            content_increased = (sum(len(s) for s in next_lines) > sum(len(s) for s in current_lines)) or \
                                (len(next_lines) > len(current_lines))
            if content_increased and is_subset_fuzzy(current_lines, next_lines):
                slides_to_delete_indices.append(i)

    if not slides_to_delete_indices:
        print(texts['no_redundancy'])
        return

    # 从后往前删除幻灯片以避免索引错误
    for index in sorted(slides_to_delete_indices, reverse=True):
        rId = prs.slides._sldIdLst[index].rId
        prs.part.drop_rel(rId)
        del prs.slides._sldIdLst[index]

    prs.save(output_path)
    print(texts['process_success'].format(original=len(slide_contents), final=len(prs.slides), output_path=os.path.basename(output_path)))

def main():
    parser = argparse.ArgumentParser(description="Slims PPTX/PDF files.")
    parser.add_argument('files', nargs='*', help="Paths to files.")
    parser.add_argument('--lang', type=str, default='en', choices=['zh', 'en'], help=argparse.SUPPRESS)
    parser.add_argument('--gui-mode', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('-r', '--recursive', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    
    main.lang = args.lang
    texts = SCRIPT_TEXTS.get(args.lang, SCRIPT_TEXTS['zh'])
    print(texts['init'])

    # 检查所有依赖
    fitz = install_and_import('PyMuPDF', 'fitz')
    pptx = install_and_import('python-pptx', 'pptx')
    
    all_deps_ok = fitz and pptx
    if not all_deps_ok:
        sys.exit(1)

    if not args.files:
        print(texts['no_files'])
        sys.exit(1)

    print(texts['start_processing'])
    for file_path in args.files:
        if not os.path.exists(file_path): continue
        
        print(texts['processing_file'].format(filename=os.path.basename(file_path)))
        
        try:
            directory, filename = os.path.split(file_path)
            name, ext = os.path.splitext(filename)
            output_filepath = os.path.join(directory, f"{name}_slimmer{ext}")
            
            print(texts['is_processing'])
            if file_path.lower().endswith('.pdf'):
                slim_pdf(file_path, output_filepath, fitz, texts)
            elif file_path.lower().endswith('.pptx'):
                slim_pptx(file_path, output_filepath, pptx, texts)
            else:
                print(texts['skip_unsupported'])
        except Exception as e:
            print(texts['process_fail'].format(error=e))

    print(texts['all_done'])

if __name__ == '__main__':
    main()