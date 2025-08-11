#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
[display-name-zh] 剪贴板增量保存器
[display-name-en] Clipboard Incremental Saver

功能:
  一个强大的剪贴板内容捕捉工具。它可以按顺序将您复制到剪贴板的文本，保存为一系列独立的文件。
  非常适合用于收集资料、记录灵感或拆分大段文本。

核心特性:
  - **双模式**: 支持“手动模式”（按Enter保存）和“监控模式”（内容变化时自动保存）。
  - **多种命名**: 支持按数字、时间戳或自定义前缀命名文件。
  - **自定义格式**: 可选择保存为 .txt 或 .md 文件。
  - **智能输出**: 自动在您指定的文件夹内创建文件。
~~~
Function:
  A powerful tool for capturing clipboard content. It saves text you copy to the clipboard into a series of separate files sequentially.
  Ideal for collecting research, jotting down ideas, or splitting large blocks of text.

Core Features:
  - **Dual Modes**: Supports "Manual Mode" (press Enter to save) and "Monitor Mode" (saves automatically on change).
  - **Multiple Naming**: Supports naming files by number, timestamp, or a custom prefix.
  - **Custom Formats**: Choose to save as .txt or .md files.
  - **Smart Output**: Automatically creates files in your specified directory.
"""

import os
import sys
import argparse
import time
import platform
from pathlib import Path

# --- (NEW) Non-blocking input handling ---
# --- (新增) 非阻塞输入处理 ---
if platform.system() == "Windows":
    import msvcrt
else:
    import select

def check_for_input():
    """Checks if there is input waiting on stdin without blocking."""
    if platform.system() == "Windows":
        return msvcrt.kbhit()
    else:
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

# --- Dependency Check for Pyperclip ---
try:
    import pyperclip
except ImportError:
    print("Info: 'pyperclip' not found. Attempting to auto-install...", flush=True)
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", 'pyperclip'],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Success: 'pyperclip' has been installed.", flush=True)
        import pyperclip
    except Exception as e:
        print(f"Error: Auto-install of 'pyperclip' failed: {e}", flush=True)
        print("Please run 'pip install pyperclip' manually.", flush=True)
        sys.exit(1)

# --- Refactored Saving Logic ---
def save_content(content, output_dir, filename_mode, file_format, prefix, counter):
    """Handles the file naming and saving logic."""
    if filename_mode == 'timestamp':
        filename = f"{time.strftime('%Y-%m-%d_%H-%M-%S')}.{file_format}"
    else:  # number
        filename = f"{prefix}_{counter}.{file_format}"
    
    file_path = output_dir / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path

# --- Main Logic ---
def main():
    parser = argparse.ArgumentParser(description="Saves clipboard content to sequentially named files.")
    parser.add_argument('files', nargs='*', help=argparse.SUPPRESS)
    parser.add_argument('--gui-mode', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--lang', type=str, default='en', choices=['zh', 'en'], help=argparse.SUPPRESS)

    parser.add_argument('--mode', type=str, choices=['manual', 'monitor'], default='manual',
                        help="工作模式: 'manual' (手动按Enter保存), 'monitor' (自动监控剪贴板变化)。\nOperating mode: 'manual' (press Enter to save), 'monitor' (auto-save on clipboard change).")
    parser.add_argument('--output-dir', type=str, help="指定保存文件的目录 (可选)。\nDirectory to save files (optional).")
    parser.add_argument('--filename-mode', type=str, choices=['number', 'timestamp'], default='number', help="文件命名模式。\nFile naming mode.")
    parser.add_argument('--prefix', type=str, default='clip', help="文件名前缀 (用于数字模式)。\nFile prefix (for number mode).")
    parser.add_argument('--start-number', type=int, default=1, help="起始编号 (用于数字模式)。\nStart number (for number mode).")
    parser.add_argument('--format', type=str, choices=['txt', 'md'], default='txt', help="输出文件格式。\nOutput file format.")
    parser.add_argument('--interval', type=float, default=0.5, help="监控模式下的检查间隔(秒)。\nCheck interval in seconds for monitor mode.")

    args = parser.parse_args()

    if args.output_dir and Path(args.output_dir).is_dir():
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path.cwd() / "剪贴板内容_Clipboard_Content"
    
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory {output_dir}: {e}", flush=True)
        return

    lang_prompts = {
        'zh': {
            'start_manual': f"\n--- 手动模式已启动，将保存到: {output_dir} ---",
            'start_monitor': f"\n--- 监控模式已启动，将保存到: {output_dir} ---",
            'prompt_manual': "请复制内容，然后按 Enter 保存，或输入 'q' 退出: ",
            'prompt_monitor': "正在监控剪贴板... 在下方输入 'q' 或 'exit' 并按Enter可退出。",
            'saved': "已保存到: {path}",
            'error': "错误: {e}",
            'exit': "--- 程序已退出 ---"
        },
        'en': {
            'start_monitor': f"\n--- Monitor Mode started. Saving to: {output_dir} ---",
            'prompt_manual': "Please copy content, then press Enter to save, or type 'q' to quit: ",
            'prompt_monitor': "Monitoring clipboard... Type 'q' or 'exit' below and press Enter to quit.",
            'saved': "Saved to: {path}",
            'error': "Error: {e}",
            'exit': "--- Program exited ---"
        }
    }
    T = lang_prompts.get(args.lang, lang_prompts['en'])
    counter = args.start_number

    if args.mode == 'manual':
        print(T['start_manual'], flush=True)
        while True:
            try:
                user_input = input(T['prompt_manual']).strip().lower()
                if user_input == 'q':
                    break
                content = pyperclip.paste()
                file_path = save_content(content, output_dir, args.filename_mode, args.format, args.prefix, counter)
                print(T['saved'].format(path=file_path), flush=True)
                if args.filename_mode == 'number':
                    counter += 1
            except (KeyboardInterrupt, EOFError):
                break
            except Exception as e:
                print(T['error'].format(e=e), flush=True)
    
    elif args.mode == 'monitor':
        print(T['start_monitor'], flush=True)
        print(T['prompt_monitor'], flush=True)
        recent_value = pyperclip.paste()
        try:
            while True:
                # (FIX) Non-blocking check for quit command
                if check_for_input():
                    line = sys.stdin.readline().strip().lower()
                    if line in ('q', 'exit'):
                        break
                
                new_value = pyperclip.paste()
                if new_value != recent_value and new_value:
                    recent_value = new_value
                    file_path = save_content(recent_value, output_dir, args.filename_mode, args.format, args.prefix, counter)
                    # (FIX) Add flush=True to ensure immediate output
                    print(T['saved'].format(path=file_path), flush=True)
                    if args.filename_mode == 'number':
                        counter += 1
                
                time.sleep(args.interval)
        except (KeyboardInterrupt, EOFError):
            pass
        except Exception as e:
            print(T['error'].format(e=e), flush=True)

    print(T['exit'], flush=True)

if __name__ == "__main__":
    main()