#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DynamicParamsWidget – builds a grid of input widgets from a parameter list
and serialises them back to command-line arguments.
DynamicParamsWidget – 根据参数列表构建输入控件网格，并将其序列化为命令行参数。
"""

import re
from typing import Any

from PyQt6.QtGui import QResizeEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QWidget,
)


class DynamicParamsWidget(QWidget):
    """Container that generates and manages dynamic parameter input widgets.

    管理动态参数输入控件的容器控件。

    Public API
    ----------
    build_ui(params, lang)  – populate the grid from a parameter list
    build_args()            – return a flat list of CLI argument strings
    clear()                 – remove all generated widgets
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 10, 0, 10)
        self._layout.setSpacing(10)
        self._param_widgets: list[QWidget] = []
        self.setVisible(False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_ui(self, params: list[dict[str, Any]], lang: str) -> None:
        """Create widgets for *params* and make the panel visible.

        根据 *params* 创建控件并显示面板。

        :param params: List of parameter dicts (from ``script_registry.parse_params``).
                       参数字典列表（来自 script_registry.parse_params）。
        :param lang:   Current UI language code (``'zh'`` or ``'en'``).
                       当前 UI 语言代码（'zh' 或 'en'）。
        """
        self.clear()
        if not params:
            return

        params = sorted(params, key=lambda x: x["name"])

        row, col, max_rows = 0, 0, 3
        for param in params:
            name = param["name"]
            p_type = param.get("type", "flag")
            p_default = param.get("default")
            p_help = param.get("help", "")

            widget: QWidget | None = None

            if p_type == "choice":
                label = QLabel(f"{name}:")
                combo = QComboBox()

                # Parse optional display-name map from the help string.
                # 从 help 字符串中解析可选的显示名称映射。
                # Format: [display: value=zh_name,en_name | ...]
                display_map: dict[str, dict[str, str]] = {}
                display_match = re.search(r"\[display:\s*(.*?)\]", p_help)
                if display_match:
                    for entry in display_match.group(1).split("|"):
                        try:
                            value, names = entry.split("=", 1)
                            zh_name, en_name = names.split(",", 1)
                            display_map[value.strip()] = {
                                "zh": zh_name.strip(),
                                "en": en_name.strip(),
                            }
                        except ValueError:
                            continue

                for choice_value in param.get("choices", []):
                    display_name = choice_value
                    if choice_value in display_map:
                        display_name = display_map[choice_value].get(lang, choice_value)
                    combo.addItem(display_name, userData=choice_value)

                if p_default:
                    idx = combo.findData(p_default)
                    if idx != -1:
                        combo.setCurrentIndex(idx)

                widget = combo
                self._layout.addWidget(label, row, col * 2)
                self._layout.addWidget(widget, row, col * 2 + 1)

            elif p_type == "value":
                label = QLabel(f"{name}:")
                line_edit = QLineEdit()
                if p_default:
                    line_edit.setText(p_default)
                widget = line_edit
                self._layout.addWidget(label, row, col * 2)
                self._layout.addWidget(widget, row, col * 2 + 1)

            else:  # 'flag'
                checkbox = QCheckBox(name)
                if p_default:
                    checkbox.setChecked(True)
                widget = checkbox
                self._layout.addWidget(widget, row, col * 2, 1, 2)

            if widget is not None:
                # Use the plain-text part of the help string as the tooltip.
                # 使用 help 字符串的纯文本部分作为工具提示。
                widget.setToolTip(p_help.split("[display:")[0].strip())
                widget.setProperty("param_name", name)
                widget.setProperty("param_type", p_type)
                self._param_widgets.append(widget)

            row += 1
            if row >= max_rows:
                row = 0
                col += 1

        self.setVisible(True)
        self._apply_max_widths()

    def build_args(self) -> list[str]:
        """Serialise the current widget values to a flat CLI argument list.

        将当前控件值序列化为扁平 CLI 参数列表。
        """
        args: list[str] = []
        for widget in self._param_widgets:
            p_name: str = widget.property("param_name")
            p_type: str = widget.property("param_type")

            if p_type == "flag" and isinstance(widget, QCheckBox) and widget.isChecked():
                args.append(p_name)
            elif p_type == "choice" and isinstance(widget, QComboBox):
                internal_value = widget.currentData()
                args.extend([p_name, internal_value])
            elif p_type == "value" and isinstance(widget, QLineEdit):
                value = widget.text()
                if value:
                    args.extend([p_name, value])
        return args

    def clear(self) -> None:
        """Remove all dynamically generated widgets and hide the panel.

        移除所有动态生成的控件并隐藏面板。
        """
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._param_widgets = []
        self.setVisible(False)

    # ------------------------------------------------------------------
    # Qt overrides
    # ------------------------------------------------------------------

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Keep each param widget to at most 1/3 of the panel width.

        将每个参数控件的最大宽度限制为面板宽度的 1/3。
        """
        self._apply_max_widths()
        super().resizeEvent(event)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _apply_max_widths(self) -> None:
        total_width = self.width()
        max_param_width = max(int(total_width / 3), 180)
        for widget in self._param_widgets:
            widget.setMaximumWidth(max_param_width)
