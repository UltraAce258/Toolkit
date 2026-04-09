#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Shared utility helpers.
共享工具函数。
"""

import os
import sys


def resource_path(relative_path: str) -> str:
    """Return absolute path to *relative_path*, compatible with PyInstaller bundles.

    返回相对路径对应的绝对路径，兼容 PyInstaller 打包环境。
    """
    try:
        # PyInstaller stores the unpacked bundle in sys._MEIPASS.
        # PyInstaller 将解压后的包存储在 sys._MEIPASS 中。
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        # In development the project root is the parent of this file's directory.
        # 开发环境下，项目根目录是本文件所在目录的上一级。
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, relative_path)
