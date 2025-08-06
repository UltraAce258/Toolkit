#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
[display-name-zh] 智能字幕生成器
[display-name-en] Intelligent Subtitle Generator

这是一个专为处理中英混合音频设计的全自动字幕生成脚本。它通过一个智能合并算法，将英文和中文两种模式下的识别结果择优合并，最终生成一个高质量的混合语言字幕。

工作流程 (v1.6 - 稳定版):
1. **双语日志**: 所有日志将始终同时显示中文和英文。
2. **健壮的进度条**: 采用全新的、兼容性极强的进度条逻辑，确保在GUI中能精确地单行刷新。
3. **模式选择与中间文件**: 保留了清晰的模式选项，并在合并模式下自动保存中间产物。
4. **依赖引导**: 引导用户安装 `ffmpeg` 和所需的 Python 模块。
~~~
This is a fully automated script for mixed Chinese/English audio. It employs an intelligent merging algorithm to create a single, high-quality, mixed-language subtitle file.

Workflow (v1.6 - Stable Version):
1. **Bilingual Logging**: All logs now display in both Chinese and English simultaneously.
2. **Robust Progress Bar**: Implements a new, highly compatible progress bar logic that ensures precise, single-line refreshing within the GUI.
3. **Mode Selection & Intermediates**: Retains clear mode selection and saves intermediate files in merge mode.
4. **Dependency Guidance**: Guides the user to install `ffmpeg` and required Python modules.
"""

import os
import sys
import subprocess
import argparse
import time
import platform
import shutil
from pathlib import Path

# --- (MODIFIED) Bilingual Reporting / (修改后) 双语报告 ---

MESSAGES = {
    'zh': {
        "init": "--- 初始化字幕生成脚本 (v1.6) ---",
        "ffmpeg_ok": "[OK] FFmpeg 已找到。",
        "ffmpeg_fail": "[错误] 致命: FFmpeg 未安装或未在系统 PATH 中。",
        "ffmpeg_guide": "\n--- 系统安装指南 ---",
        "ffmpeg_important": "\n[重要] 安装后，您必须重启此应用或您的终端。",
        "dep_check": "\n--- 正在检查 Python 依赖 ---",
        "dep_ok": "[OK] 依赖包 '{pkg}' 已安装。",
        "dep_installing": "[信息] 正在安装依赖包 '{pkg}'...",
        "dep_install_ok": "[OK] 成功安装 '{pkg}'。",
        "dep_install_fail": "[错误] 安装 '{pkg}' 失败。请手动安装。",
        "process_file": "\n--- 正在处理文件: {file} ---",
        "model_loading": "[信息] 正在加载 Whisper 模型 '{model}'... (首次使用可能需要较长时间)",
        "model_loaded": "[OK] 模型加载完毕。",
        "mode_merge": "--- 开始混合语言转写 (合并模式) ---",
        "mode_single": "--- 开始单语言转写 ({lang} 模式) ---",
        "pass_start": "[信息] 正在执行 {lang} 语言转写...",
        "pass_progress": "转写进度 / Transcription Progress",
        "pass_complete": "[OK] {lang} 语言转写完成。",
        "merge_start": "[信息] 正在智能合并英文和中文结果...",
        "merge_complete": "[OK] 合并完成。共生成 {count} 个最终片段。",
        "file_saved_intermediate": "[INFO] 已保存中间文件: {path}",
        "file_saved_final": "\n[成功] 已创建最终字幕文件: {path}",
        "total_time": "总耗时: {time:.2f} 秒",
        "all_done": "\n--- 所有任务已完成。 ---",
        "no_files": "未找到有效文件进行处理。",
        "path_skipped": "[警告] 路径不是一个有效文件，将跳过: {path}",
    },
    'en': {
        "init": "--- Initializing Subtitle Generation Script (v1.6) ---",
        "ffmpeg_ok": "[OK] FFmpeg found.",
        "ffmpeg_fail": "[ERROR] FATAL: FFmpeg is not installed or not in your system's PATH.",
        "ffmpeg_guide": "\n--- Installation Guide for Your System ---",
        "ffmpeg_important": "\n[IMPORTANT] After installation, you MUST restart this application or your terminal.",
        "dep_check": "\n--- Checking Python Packages ---",
        "dep_ok": "[OK] Package '{pkg}' is already installed.",
        "dep_installing": "[INFO] Installing package '{pkg}'...",
        "dep_install_ok": "[OK] Successfully installed '{pkg}'.",
        "dep_install_fail": "[ERROR] Failed to install '{pkg}'. Please install it manually.",
        "process_file": "\n--- Processing file: {file} ---",
        "model_loading": "[INFO] Loading Whisper model '{model}'... (This may take a while on first use)",
        "model_loaded": "[OK] Model loaded.",
        "mode_merge": "--- Starting Mixed-Language Transcription (Merge Mode) ---",
        "mode_single": "--- Starting Single-Language Transcription ({lang} Only Mode) ---",
        "pass_start": "[INFO] Performing transcription pass for language: {lang}...",
        "pass_progress": "", # English part is integrated into the Chinese one
        "pass_complete": "[OK] {lang} language pass complete.",
        "merge_start": "[INFO] Executing intelligent merge of English and Chinese results...",
        "merge_complete": "[OK] Merge complete. Generated {count} final segments.",
        "file_saved_intermediate": "[INFO] Saved intermediate subtitle file: {path}",
        "file_saved_final": "\n[SUCCESS] Created final subtitle file: {path}",
        "total_time": "Total time taken: {time:.2f} seconds",
        "all_done": "\n--- All tasks completed. ---",
        "no_files": "No valid audio files found to process.",
        "path_skipped": "[WARN] Path is not a valid file and will be skipped: {path}",
    }
}

def T(key, **kwargs):
    """Formats and returns a bilingual message."""
    zh_msg = MESSAGES['zh'].get(key, key).format(**kwargs)
    en_msg = MESSAGES['en'].get(key, key).format(**kwargs)
    
    if key == "pass_progress":
        return zh_msg
    
    if zh_msg == en_msg:
        return zh_msg
        
    return f"{zh_msg} / {en_msg}"

# --- Dependency Management ---
def check_and_install_ffmpeg():
    if shutil.which("ffmpeg"):
        print(T("ffmpeg_ok"), flush=True)
        return True
    print(T("ffmpeg_fail"), file=sys.stderr, flush=True)
    os_name = platform.system()
    print(T("ffmpeg_guide"), file=sys.stderr, flush=True)
    if os_name == "Windows": print("  - Windows: winget install ffmpeg", file=sys.stderr, flush=True)
    elif os_name == "Darwin": print("  - macOS: brew install ffmpeg", file=sys.stderr, flush=True)
    else:
        print("  - Debian/Ubuntu: sudo apt update && sudo apt install ffmpeg", file=sys.stderr, flush=True)
        print("  - Fedora: sudo dnf install ffmpeg", file=sys.stderr, flush=True)
    print(T("ffmpeg_important"), file=sys.stderr, flush=True)
    return False

def install_python_packages(packages):
    print(T("dep_check"), flush=True)
    for package_name, import_name in packages.items():
        try:
            __import__(import_name)
            print(T("dep_ok", pkg=package_name), flush=True)
        except ImportError:
            print(T("dep_installing", pkg=package_name), flush=True)
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(T("dep_install_ok", pkg=package_name), flush=True)
            except subprocess.CalledProcessError:
                print(T("dep_install_fail", pkg=package_name), file=sys.stderr, flush=True)
                sys.exit(1)

REQUIRED_PYTHON_PACKAGES = {
    "faster-whisper": "faster_whisper", "pydub": "pydub", "opencc-python-reimplemented": "opencc"
}

# --- Core Functions ---
def format_srt_time(seconds):
    m, s = divmod(seconds, 60); h, m = divmod(m, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((seconds - int(s)) * 1000):03d}"

def segments_to_srt(segments):
    from opencc import OpenCC
    cc = OpenCC('t2s'); srt_content = ""
    for i, segment in enumerate(segments, 1):
        start_time = format_srt_time(segment.start); end_time = format_srt_time(segment.end)
        text = segment.text.strip()
        if segment.lang == 'zh': text = cc.convert(text)
        srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"
    return srt_content

def transcribe_pass(model, file_path, lang):
    lang_map = {'en': 'English', 'zh': '中文'}
    print(T("pass_start", lang=lang_map.get(lang, lang)), flush=True)
    
    segments_generator, info = model.transcribe(str(file_path), language=lang, beam_size=5, no_speech_threshold=0.6)
    
    total_duration = round(info.duration, 2)
    segment_list = []
    
    bar_len = 40
    for segment in segments_generator:
        segment_list.append(segment)
        progress = min(100, (segment.end / total_duration) * 100)
        filled_len = int(bar_len * progress / 100)
        bar = '█' * filled_len + '-' * (bar_len - filled_len)
        progress_string = f"\r{T('pass_progress')}: [{bar}] {progress:.2f}%"
        sys.stdout.write(progress_string)
        sys.stdout.flush()
    
    final_bar = f"\r{T('pass_progress')}: [{'█' * bar_len}] 100.00%\n"
    sys.stdout.write(final_bar)
    sys.stdout.flush()

    print(T("pass_complete", lang=lang_map.get(lang, lang)), flush=True)
    
    for s in segment_list: s.lang = lang
    return segment_list

def intelligent_merge(en_segments, zh_segments):
    print(T("merge_start"), flush=True)
    final_segments = []; zh_segments_pool = list(zh_segments)
    for en_seg in en_segments:
        overlapping_zh = [zh_seg for zh_seg in zh_segments_pool if max(en_seg.start, zh_seg.start) < min(en_seg.end, zh_seg.end)]
        if not overlapping_zh: final_segments.append(en_seg); continue
        avg_zh_confidence = sum(s.no_speech_prob for s in overlapping_zh) / len(overlapping_zh)
        if en_seg.no_speech_prob < avg_zh_confidence: final_segments.append(en_seg)
        else: final_segments.extend(overlapping_zh)
        for zh_seg in overlapping_zh:
            if zh_seg in zh_segments_pool: zh_segments_pool.remove(zh_seg)
    final_segments.extend(zh_segments_pool)
    final_segments.sort(key=lambda s: s.start)
    print(T("merge_complete", count=len(final_segments)), flush=True)
    return final_segments

def to_srt_single_pass(segments, is_chinese):
    from opencc import OpenCC
    cc = OpenCC('t2s') if is_chinese else None; srt_content = ""
    for i, segment in enumerate(segments, 1):
        text = segment.text.strip();
        if is_chinese and cc: text = cc.convert(text)
        srt_content += f"{i}\n{format_srt_time(segment.start)} --> {format_srt_time(segment.end)}\n{text}\n\n"
    return srt_content

def transcribe_audio(file_path, model_name, mode):
    from faster_whisper import WhisperModel
    print(T("process_file", file=file_path.name), flush=True)
    print(T("model_loading", model=model_name), flush=True)
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    print(T("model_loaded"), flush=True)
    p = Path(file_path); start_time = time.time()
    
    if mode == 'merge':
        print(T("mode_merge"), flush=True)
        en_segments = transcribe_pass(model, file_path, 'en')
        en_srt_filename = p.with_name(f"{p.stem}_en.srt")
        with open(en_srt_filename, "w", encoding="utf-8") as f: f.write(to_srt_single_pass(en_segments, is_chinese=False))
        print(T("file_saved_intermediate", path=en_srt_filename), flush=True)
        
        zh_segments = transcribe_pass(model, file_path, 'zh')
        zh_srt_filename = p.with_name(f"{p.stem}_zh.srt")
        with open(zh_srt_filename, "w", encoding="utf-8") as f: f.write(to_srt_single_pass(zh_segments, is_chinese=True))
        print(T("file_saved_intermediate", path=zh_srt_filename), flush=True)

        merged_segments = intelligent_merge(en_segments, zh_segments)
        srt_output = segments_to_srt(merged_segments)
        srt_filename = p.with_name(f"{p.stem}_merged.srt")
    else:
        print(T("mode_single", lang=mode.upper()), flush=True)
        segments = transcribe_pass(model, file_path, mode)
        is_chinese = mode == 'zh'
        srt_output = to_srt_single_pass(segments, is_chinese)
        srt_filename = p.with_name(f"{p.stem}_{mode}.srt")

    with open(srt_filename, "w", encoding="utf-8") as f: f.write(srt_output)
    duration = time.time() - start_time
    print(T("file_saved_final", path=srt_filename), flush=True)
    print(T("total_time", time=duration), flush=True)

def main():
    parser = argparse.ArgumentParser(description="Generate SRT subtitles from audio/video files.", formatter_class=argparse.RawTextHelpFormatter)
    
    # --- Standard GUI arguments ---
    parser.add_argument('files', nargs='*', help="Paths to audio/video files passed from the GUI.")
    parser.add_argument('--gui-mode', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--lang', type=str, default='en', choices=['zh', 'en'], help=argparse.SUPPRESS)
    
    # --- Custom visual parameters ---
    parser.add_argument('--model', type=str, default='large-v3', help="Whisper model to use. (default: large-v3)")
    parser.add_argument('--mode', type=str, default='merge', choices=['merge', 'en', 'zh'], 
                        help="Transcription mode:\n'merge': (Default) For mixed Chinese/English audio.\n'en': English only.\n'zh': Chinese only.")
    
    args = parser.parse_args()

    print(T("init"), flush=True)
    if not check_and_install_ffmpeg(): sys.exit(1)
    install_python_packages(REQUIRED_PYTHON_PACKAGES)
    
    files_to_process = []
    for p in args.files:
        try:
            normalized_path = Path(os.path.normpath(p))
            if normalized_path.is_file(): files_to_process.append(normalized_path)
            else: print(T("path_skipped", path=p), file=sys.stderr, flush=True)
        except Exception as e: print(f"[WARN] Could not process path '{p}': {e}", file=sys.stderr, flush=True)

    if not files_to_process:
        print(T("no_files"), file=sys.stderr, flush=True); sys.exit(0)

    for file_path in files_to_process:
        transcribe_audio(file_path, args.model, args.mode)

    print(T("all_done"), flush=True)

if __name__ == "__main__":
    main()