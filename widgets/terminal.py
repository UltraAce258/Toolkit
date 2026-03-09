#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EnhancedTerminalWidget – a terminal-style widget that displays script output
and accepts interactive input.
EnhancedTerminalWidget – 显示脚本输出并接受交互输入的终端风格控件。
"""

import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QPalette, QTextCursor
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QTextEdit, QVBoxLayout, QWidget

from core.i18n import UI_TEXTS


class EnhancedTerminalWidget(QWidget):
    """A widget that emulates a basic terminal for script output and input.

    模拟基本终端的控件，用于脚本输出与交互输入。
    """

    # Emitted when the user presses Enter in the input line.
    # 用户在输入行按下 Enter 时发出。
    command_entered = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.history: list[str] = []
        self.history_index: int = 0
        self.current_lang: str = "zh"
        self._init_ui()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        """Build the widget's internal layout.

        构建控件内部布局。
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)

        input_layout = QHBoxLayout()
        self.prompt_label = QLabel("$")
        self.prompt_label.setStyleSheet(
            "color: #61afef; font-weight: bold; font-size: 12pt;"
        )
        self.command_input = QLineEdit()
        self.command_input.returnPressed.connect(self._on_command_entered)

        input_layout.addWidget(self.prompt_label)
        input_layout.addWidget(self.command_input)

        layout.addWidget(self.output_display)
        layout.addLayout(input_layout)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_language(self, lang: str) -> None:
        """Update the terminal's language and reset the welcome message.

        更新终端语言并重置欢迎信息。
        """
        self.current_lang = lang
        self.output_display.clear()
        self.append_output(UI_TEXTS[self.current_lang]["terminal_welcome"])
        self._update_prompt()

    def append_output(self, text: str) -> None:
        """Append *text* to the display, handling ``\\r`` for in-place updates.

        将 *text* 追加到显示区，智能处理 ``\\r`` 以支持进度条等原地更新。
        """
        cursor = self.output_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output_display.setTextCursor(cursor)

        lines = text.replace("\r\n", "\n").split("\n")
        for line in lines:
            if not line:
                continue
            if line.endswith("\r"):
                cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
                cursor.movePosition(
                    QTextCursor.MoveOperation.EndOfLine,
                    QTextCursor.MoveMode.KeepAnchor,
                )
                cursor.removeSelectedText()
                cursor.insertText(line[:-1])
            else:
                cursor.insertText(line + "\n")

        self.output_display.ensureCursorVisible()

    def apply_theme(self) -> None:
        """Re-apply theme-aware stylesheets to the terminal sub-widgets.

        重新将感知主题的样式表应用于终端子控件。
        """
        is_dark = self.palette().color(QPalette.ColorRole.Window).lightness() < 128
        if is_dark:
            self.output_display.setStyleSheet(
                "background-color: #282c34; color: #abb2bf;"
                " font-family: Consolas, 'Courier New', monospace; font-size: 11pt;"
            )
            self.prompt_label.setStyleSheet(
                "color: #61afef; font-weight: bold; font-size: 12pt;"
            )
            self.command_input.setStyleSheet(
                "background-color: #282c34; color: #e06c75;"
                " font-family: Consolas, 'Courier New', monospace;"
                " font-size: 11pt; border: none;"
            )
        else:
            base_color = self.palette().color(QPalette.ColorRole.Base).name()
            text_color = self.palette().color(QPalette.ColorRole.Text).name()
            highlight_color = self.palette().color(QPalette.ColorRole.Highlight).name()
            self.output_display.setStyleSheet(
                f"background-color: {base_color}; color: {text_color};"
                " font-family: Consolas, 'Courier New', monospace; font-size: 11pt;"
            )
            self.prompt_label.setStyleSheet(
                f"color: {highlight_color}; font-weight: bold; font-size: 12pt;"
            )
            self.command_input.setStyleSheet(
                f"background-color: {base_color}; color: #d12f2f;"
                " font-family: Consolas, 'Courier New', monospace;"
                " font-size: 11pt; border: none;"
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_prompt(self) -> None:
        """Update the prompt label to show the current working directory.

        更新提示符标签以显示当前工作目录。
        """
        self.prompt_label.setText(f"[{os.path.basename(os.getcwd())}]$")

    def _on_command_entered(self) -> None:
        """Handle Enter key press – emit signal and clear the input field.

        处理 Enter 键按下事件 – 发出信号并清空输入框。
        """
        command = self.command_input.text()
        if command.strip():
            self.history.append(command.strip())
            self.history_index = len(self.history)
        self.command_entered.emit(command)
        self.command_input.clear()

    # ------------------------------------------------------------------
    # Event overrides
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Navigate command history with Up/Down arrow keys.

        使用上/下方向键浏览命令历史。
        """
        if event.key() == Qt.Key.Key_Up and self.history and self.history_index > 0:
            self.history_index -= 1
            self.command_input.setText(self.history[self.history_index])
        elif event.key() == Qt.Key.Key_Down:
            if self.history and self.history_index < len(self.history) - 1:
                self.history_index += 1
                self.command_input.setText(self.history[self.history_index])
            else:
                self.history_index = len(self.history)
                self.command_input.clear()
        else:
            super().keyPressEvent(event)
