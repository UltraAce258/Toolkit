#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Entry point – Toolkit launcher.
入口文件 – 工具箱启动器。

Responsibility: initialise the Qt application, load UI texts, and show the
main window.  All application logic lives in the sub-packages:
  core/      – executor, script registry, i18n, utilities
  widgets/   – terminal widget, dynamic-params widget
  ui/        – main window
"""

import os
import platform
import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from core.i18n import load_ui_texts
from core.utils import resource_path
from ui.main_window import ScriptGUI


def _get_best_font_name() -> str:
    """Return a platform-appropriate CJK-capable font name.

    返回适合当前平台且支持 CJK 字符的字体名称。
    """
    system = platform.system()
    if system == "Windows":
        return "Microsoft YaHei"
    if system == "Darwin":
        return "PingFang SC"
    return "WenQuanYi Micro Hei"


def main() -> int:
    """Bootstrap and run the toolkit application.

    启动并运行工具箱应用程序。
    """
    # Populate UI_TEXTS before any widget code references it.
    # 在任何控件代码引用 UI_TEXTS 之前，先填充其内容。
    load_ui_texts(resource_path("ui_texts.json"))

    app = QApplication(sys.argv)
    app.setFont(QFont(_get_best_font_name(), 10))

    scripts_directory = resource_path("scripts")
    if not os.path.exists(scripts_directory):
        os.makedirs(scripts_directory)

    window = ScriptGUI(scripts_directory)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
