#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
[display-name-zh] 文本文件合并器
[display-name-en] Text File Merger

功能:
  本脚本可以将大量 .txt 文件进行排序、分组，并将每组内的文件内容合并成一个新的 .txt 文件。

核心特性:
  1. 批量处理: 支持一次性拖入多个 .txt 文件或包含它们的文件夹。
  2. 可选递归: 可勾选是否深入所有子文件夹查找 .txt 文件 (默认为否)。
  3. 智能排序: 支持按文件名 (自然语言排序) 或按文件修改时间排序，且可选择升序或降序。
  4. 自定义分组: 用户可以自由设定每多少个文件合并成一个新文件 (输入0则合并全部)。
  5. 上下文感知输出: 在源目录或工具箱目录旁创建“合并的文本_Merged_Text”文件夹存放结果。
  6. 可控的命名: 用户可以指定输出文件的前缀，脚本会自动附加批次编号。
  7. GUI深度集成: 专为“奥创王牌工具箱”设计，提供清晰的双语进度反馈和可视化参数。
~~~
Function:
  This script sorts and groups a large number of .txt files, then merges the content of each group into a new .txt file.

Core Features:
  1. Batch Processing: Supports dragging and dropping multiple .txt files or folders containing them.
  2. Optional Recursion: A checkbox to enable/disable searching all subdirectories for .txt files (default: off).
  3. Smart Sorting: Supports sorting by filename (natural sort) or by modification time, with ascending/descending options.
  4. Custom Grouping: The user can define how many files are merged into each new file (0 means merge all).
  5. Context-Aware Output: Creates a "合并的文本_Merged_Text" folder next to the source or toolkit to store results.
  6. Controllable Naming: The user can specify a prefix for the output files, and the script will automatically append a batch number.
  7. Deep GUI Integration: Designed for the "UltraAce Toolkit" with clear bilingual progress feedback and visual parameters.
"""

import os
import sys
import argparse
import subprocess
import importlib.util
from pathlib import Path

# --- Internationalization (i18n) Setup ---
MESSAGES = {
    'zh': {
        "init": "--- 文本文件合并器 v1.2 (修正版) 启动 ---",
        "dep_checking": "--- 正在检查依赖库 'natsort' ---",
        "dep_missing": "提示: 未找到 'natsort'，正在尝试自动安装...",
        "dep_success": "成功: 'natsort' 已安装。",
        "dep_fail": "错误: 自动安装 'natsort' 失败。请手动运行 'pip install natsort'。",
        "mode_sort_by": "排序方式: {sort_by}, 顺序: {order}",
        "files_found": "\n发现 {count} 个 .txt 文件待处理 (递归搜索: {recursive}):",
        "files_none": "\n在指定路径下未找到任何 .txt 文件。",
        "group_info": "将按每 {group_size} 个文件为一组进行合并，预计生成 {num_groups} 个文件。",
        "processing": "\n[处理中] -> 正在合并第 {i}/{total} 组...",
        "success_save": "  [成功] -> 已合并 {num_files} 个文件到: {path}",
        "failure_merge": "  [失败] -> 合并第 {i} 组时出错: {e}",
        "output_dir_creating": "创建输出目录: {path}",
        "output_dir_fail": "错误: 创建输出目录失败: {e}",
        "all_done": "\n--- 所有任务已完成 ---",
    },
    'en': {
        "init": "--- Text File Merger v1.2 (Corrected) Started ---",
        "dep_checking": "--- Checking dependency 'natsort' ---",
        "dep_missing": "Info: 'natsort' not found. Attempting to auto-install...",
        "dep_success": "Success: 'natsort' has been installed.",
        "dep_fail": "Error: Auto-install of 'natsort' failed. Please run 'pip install natsort' manually.",
        "mode_sort_by": "Sorting by: {sort_by}, Order: {order}",
        "files_found": "\nFound {count} .txt files to process (Recursive Search: {recursive}):",
        "files_none": "\nNo .txt files found in the specified paths.",
        "group_info": "Files will be merged in groups of {group_size}, expecting to generate {num_groups} files.",
        "processing": "\n[Processing] -> Merging group {i}/{total}...",
        "success_save": "  [SUCCESS] -> Merged {num_files} files to: {path}",
        "failure_merge": "  [FAILURE] -> Error merging group {i}: {e}",
        "output_dir_creating": "Creating output directory: {path}",
        "output_dir_fail": "Error: Failed to create output directory: {e}",
        "all_done": "\n--- All tasks completed ---",
    }
}

def T(key, lang='en', **kwargs):
    return MESSAGES.get(lang, MESSAGES['en']).get(key, key).format(**kwargs)

# --- Dependency Management ---
def setup_dependencies(lang):
    print(T("dep_checking", lang))
    if importlib.util.find_spec('natsort'): return True
    print(T("dep_missing", lang));
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", 'natsort'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(T("dep_success", lang)); importlib.invalidate_caches(); return True
    except subprocess.CalledProcessError:
        print(T("dep_fail", lang)); return False

# --- Main Logic ---
def get_txt_files(paths, recursive=False):
    """
    (CORRECTED) Finds all .txt files. Supports optional recursive search.
    (已修正) 查找所有 .txt 文件。支持可选的递归搜索。
    """
    files_to_process = set()
    glob_method = 'rglob' if recursive else 'glob'
    for path in paths:
        p = Path(path)
        if p.is_file() and p.suffix.lower() == '.txt':
            files_to_process.add(str(p.resolve()))
        elif p.is_dir():
            # Use the selected glob method based on the 'recursive' flag.
            # 根据 'recursive' 标志使用选定的 glob 方法。
            for f in getattr(p, glob_method)('*.txt'):
                files_to_process.add(str(f.resolve()))
    return list(files_to_process)

def main():
    parser = argparse.ArgumentParser(description="Merges multiple .txt files into groups.", add_help=False)
    custom_args = parser.add_argument_group('Custom Parameters')
    custom_args.add_argument('--help', action='help', help='Show this help message and exit.')
    # (NEW) Added the --recursive flag as a boolean checkbox.
    # (新) 添加了 --recursive 标志作为布尔复选框。
    custom_args.add_argument('--recursive', action='store_true', help="勾选后将搜索所有子文件夹。\nSearch all subfolders if checked.")
    custom_args.add_argument('--sort-by', type=str, default="name", choices=["name", "date"], help="排序依据 [display: name=文件名,File Name | date=修改日期,Date Modified]")
    custom_args.add_argument('--sort-order', type=str, default="asc", choices=["asc", "desc"], help="排序顺序 [display: asc=升序,Ascending | desc=降序,Descending]")
    custom_args.add_argument('--group-size', type=int, default=3, help="每组包含的文件数量 (0 = 合并全部)\nNumber of files per group (0 = merge all).")
    custom_args.add_argument('--output-prefix', type=str, default="merged", help="输出文件的前缀名。\nPrefix for the output files.")
    
    gui_args = parser.add_argument_group('GUI Internal')
    gui_args.add_argument('files', nargs='*', help=argparse.SUPPRESS)
    gui_args.add_argument('--gui-mode', action='store_true', help=argparse.SUPPRESS)
    gui_args.add_argument('--lang', type=str, default='en', choices=['zh', 'en'], help=argparse.SUPPRESS)
    
    args = parser.parse_args()
    lang = args.lang

    print(T("init", lang))
    if not setup_dependencies(lang): sys.exit(1)

    from natsort import natsorted
    
    files_to_process = get_txt_files(args.files, args.recursive)

    if not files_to_process:
        print(T("files_none", lang)); return

    # Sort files
    reverse_order = args.sort_order == 'desc'
    if args.sort_by == 'date':
        files_to_process.sort(key=lambda x: Path(x).stat().st_mtime, reverse=reverse_order)
    else: # name
        files_to_process = natsorted(files_to_process, reverse=reverse_order)
    
    print(T("files_found", lang, count=len(files_to_process), recursive=('是' if args.recursive else '否') if lang == 'zh' else ('Yes' if args.recursive else 'No')))
    for f in files_to_process: print(f"- {Path(f).name}")

    # Determine output directory
    parent_dirs = {Path(f).parent for f in files_to_process}
    output_base_dir = Path.cwd() / "合并的文本_Merged_Text" if len(parent_dirs) != 1 else list(parent_dirs)[0] / "合并的文本_Merged_Text"

    # --- (CORRECTED) Rock-solid grouping logic ---
    group_size_arg = args.group_size
    if group_size_arg == 0:
        file_groups = [files_to_process] if files_to_process else []
        print(T("group_info", lang, group_size="所有(All)", num_groups=len(file_groups)))
    else:
        group_size = max(1, group_size_arg)
        file_groups = [files_to_process[i:i + group_size] for i in range(0, len(files_to_process), group_size)]
        print(T("group_info", lang, group_size=group_size, num_groups=len(file_groups)))

    if not file_groups or not file_groups[0]: return

    # Create output directory
    if not output_base_dir.exists():
        try:
            print(T("output_dir_creating", lang, path=output_base_dir)); output_base_dir.mkdir(parents=True)
        except OSError as e:
            print(T("output_dir_fail", lang, e=e)); return

    # Process each group
    for i, group in enumerate(file_groups):
        if not group: continue
        print(T("processing", lang, i=i+1, total=len(file_groups)))
        output_filename = f"{args.output_prefix}_{i+1}.txt"
        output_path = output_base_dir / output_filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as outfile:
                for file_path in group:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                        outfile.write(infile.read()); outfile.write('\n\n')
            print(T("success_save", lang, num_files=len(group), path=output_path))
        except Exception as e:
            print(T("failure_merge", lang, i=i+1, e=e))

    print(T("all_done", lang))

if __name__ == "__main__":
    main()