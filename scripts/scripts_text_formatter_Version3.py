"""
[display-name-zh] 通用文本格式化器
[display-name-en] Universal Text Formatter

功能:
  这是一个强大的文本批量处理工具，提供了多种格式化选项，并能智能处理文件和文件夹。

核心特性:
  - 文件夹支持: 可自动递归搜索文件夹内的所有文本文件。
  - 上下文感知输出: 智能判断输出位置，避免文件混乱。
    - 单文件: 在原文件旁生成新文件。
    - 多文件 (同目录): 在该目录内创建 "格式化文本_Formatted_Text" 子文件夹。
    - 多文件 (跨目录): 在程序主目录创建 "格式化文本_Formatted_Text" 文件夹。
  - Tab转空格: 可将所有制表符 (Tab) 转换成指定数量的空格。
  - 行首/行尾加空格: 可在每行开头或结尾添加空格，用于Markdown换行或代码缩进。
~~~
Function:
  A powerful tool for batch text processing, offering various formatting options and smart handling of files and folders.

Core Features:
  - Folder Support: Can automatically and recursively search for all text files within folders.
  - Context-Aware Output: Intelligently determines the output location to avoid file clutter.
    - Single File: Generates the new file next to the original.
    - Multiple Files (Same Dir): Creates a "Formatted_Text" subfolder within that directory.
    - Multiple Files (Cross-Dir): Creates a "Formatted_Text" folder in the main program directory.
  - Tabs to Spaces: Can convert all Tab characters into a specified number of spaces.
  - Add Spaces to Lines: Can add spaces to the beginning or end of each line, useful for Markdown line breaks or code indentation.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

def process_text(input_text, add_spaces_pos=None, add_spaces_num=0, tab_size=None):
    """
    Processes text with multiple formatting options.
    The order is: 1. Tabs to spaces, 2. Add spaces to lines.
    """
    lines = input_text.split('\n')
    
    # 1. (新) Tab转空格
    if tab_size is not None and tab_size > 0:
        lines = [line.replace('\t', ' ' * tab_size) for line in lines]

    # 2. (原) 添加行首/行尾空格
    if add_spaces_pos and add_spaces_num > 0:
        if add_spaces_pos == 'start':
            lines = [' ' * add_spaces_num + line for line in lines]
        elif add_spaces_pos == 'end':
            lines = [line + ' ' * add_spaces_num for line in lines]
            
    return "\n".join(lines)

def find_all_text_files(paths):
    """Recursively finds all files from a list of paths (files or folders)."""
    # 定义一个广泛的文本文件后缀列表，可以按需增删
    text_exts = [
        '.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
        '.c', '.cpp', '.h', '.java', '.cs', '.go', '.rs', '.sh', '.bat', '.ini', '.cfg'
    ]
    files_to_process = set()
    for path in paths:
        p = Path(path)
        if p.is_file():
            # 如果是文件，直接添加
            files_to_process.add(p)
        elif p.is_dir():
            # 如果是文件夹，递归搜索所有文本文件
            for ext in text_exts:
                files_to_process.update(p.rglob(f'*{ext}'))
    return [str(f) for f in sorted(list(files_to_process))]


def main():
    parser = argparse.ArgumentParser(description="通用文本格式化器。")
    parser.add_argument('--lang', type=str, default='en', choices=['zh', 'en'], help=argparse.SUPPRESS)
    parser.add_argument('--gui-mode', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('files', nargs='*', help="由GUI传入的文件/文件夹路径列表。")

    # --- 可视化参数 ---
    # (新) Tab转空格
    parser.add_argument(
        '--tabs-to-spaces', 
        type=int, 
        metavar='SIZE',
        help="[新] 将Tab转换为空格，不转换请留空。\n[New] Convert tabs to spaces (leave empty to ignore)."
    )
    # 行首/行尾加空格
    parser.add_argument(
        '--add-spaces-pos', 
        type=str, 
        choices=['end', 'start'], 
        help="添加空格的位置 (行首/行尾)。\nPosition to add spaces (start/end)."
    )
    parser.add_argument(
        '--add-spaces-num', 
        type=int,
        metavar='NUM',
        help="要添加的空格数量。\nNumber of spaces to add."
    )
    args = parser.parse_args()

    # --- 查找文件 ---
    files_to_process = find_all_text_files(args.files)
    if not files_to_process:
        print("未找到任何可处理的文本文件。\nNo processable text files found.")
        sys.exit(0)

    # --- 上下文感知输出目录逻辑 ---
    output_base_dir = None
    if len(files_to_process) > 1:
        parent_dirs = {Path(f).parent for f in files_to_process}
        if len(parent_dirs) == 1:
            output_base_dir = list(parent_dirs)[0] / "格式化文本_Formatted_Text"
        else:
            output_base_dir = Path.cwd() / "格式化文本_Formatted_Text"
    
    if output_base_dir and not output_base_dir.exists():
        output_base_dir.mkdir(parents=True)

    # --- 主处理循环 ---
    total_files = len(files_to_process)
    for i, file_path_str in enumerate(files_to_process):
        p = Path(file_path_str)
        print(f"[{i+1}/{total_files}] 正在处理: {p.name}")
        if args.gui_mode:
            print(f"[PROGRESS] {i + 1} / {total_files} | {p.name}", flush=True)

        try:
            # 决定输出路径
            if output_base_dir:
                # 多文件模式
                output_path = output_base_dir / p.name
            else:
                # 单文件模式，使用 _formatted 后缀
                output_path = p.parent / f"{p.stem}_formatted{p.suffix}"

            with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            processed_content = process_text(
                content, 
                add_spaces_pos=args.add_spaces_pos, 
                add_spaces_num=args.add_spaces_num or 0, 
                tab_size=args.tabs_to_spaces
            )
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            
            if not output_base_dir:
                 print(f"  ✅ 已保存到: {output_path}")

        except Exception as e:
            print(f"  ❌ 处理文件 '{p.name}' 时出错: {e}")

    if output_base_dir:
        print(f"\n所有文件处理完成！结果已统一保存到目录:\n{output_base_dir}")
    else:
        print("\n处理完成！")

if __name__ == "__main__":
    main()