#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Internationalisation helper.
Stores the UI text dictionary that is shared across all modules.
模块间共享的 UI 文字字典。

Usage
-----
    # Load once at application startup:
    from core.i18n import load_ui_texts, UI_TEXTS
    load_ui_texts(json_path)

    # Then, in any module:
    from core.i18n import UI_TEXTS
    label = UI_TEXTS['zh']['run_button']
"""

import json

# The single shared dict – populated by load_ui_texts() before the GUI starts.
# 单一共享字典 – 在 GUI 启动前由 load_ui_texts() 填充。
UI_TEXTS: dict = {}


def load_ui_texts(json_path: str) -> None:
    """Read *json_path* and populate the global UI_TEXTS dict in-place.

    Using ``dict.update`` keeps existing references valid, so modules that
    imported ``UI_TEXTS`` before the call will see the new data.

    读取 JSON 文件并就地更新全局 UI_TEXTS 字典。
    由于使用 dict.update，之前已导入 UI_TEXTS 的模块也能看到新数据。
    """
    with open(json_path, "r", encoding="utf-8") as fh:
        UI_TEXTS.update(json.load(fh))
