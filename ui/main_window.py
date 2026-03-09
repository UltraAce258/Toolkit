#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ScriptGUI – the application's main window.
ScriptGUI – 应用程序主窗口。

Imports sub-components from:
  core.executor        – ScriptExecutor
  core.script_registry – scan / parse_params / extract_docstring
  widgets.terminal     – EnhancedTerminalWidget
  widgets.dynamic_params – DynamicParamsWidget
"""

import configparser
import os
import platform
import re
import shlex
import subprocess

from PyQt6.QtCore import Qt, QProcess
from PyQt6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QKeyEvent,
    QKeySequence,
    QPalette,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.executor import ScriptExecutor
from core.i18n import UI_TEXTS
from core.utils import resource_path
import core.script_registry as registry
from widgets.dynamic_params import DynamicParamsWidget
from widgets.terminal import EnhancedTerminalWidget


class ScriptGUI(QMainWindow):
    """The main application window.

    主应用程序窗口。
    """

    def __init__(self, scripts_dir: str) -> None:
        """Initialise the main window.

        初始化主窗口。

        :param scripts_dir: Path to the directory containing task scripts.
                            包含任务脚本的目录路径。
        """
        super().__init__()

        # ------------------------------------------------------------------
        # Configuration
        # ------------------------------------------------------------------
        self.config_path = resource_path("config.ini")
        self.config = configparser.ConfigParser()
        self._load_config()

        # ------------------------------------------------------------------
        # Instance variables
        # ------------------------------------------------------------------
        self.scripts_dir = scripts_dir
        self.current_script_path: str | None = None
        self.current_script_docstring: str = ""
        self.script_executor: ScriptExecutor | None = None
        self.system_process: QProcess | None = None
        self.current_lang: str = "zh"
        self.undo_stack: list[list] = [[]]
        self.redo_stack: list[list] = []

        self.original_palette = QApplication.instance().palette()

        # Menu action handles (assigned in _create_menu_bar)
        self.light_theme_action: QAction | None = None
        self.dark_theme_action: QAction | None = None
        self.system_theme_action: QAction | None = None

        # ------------------------------------------------------------------
        # Build UI
        # ------------------------------------------------------------------
        self._init_ui()
        self._create_actions()
        self.load_scripts()
        self._update_ui_language()
        self._apply_config()

    # ==================================================================
    # Configuration persistence
    # ==================================================================

    def _load_config(self) -> None:
        """Load settings from config.ini, creating it when absent.

        从 config.ini 加载设置，不存在时自动创建。
        """
        self.config.read(self.config_path, encoding="utf-8")
        if not self.config.has_section("Preferences"):
            self.config.add_section("Preferences")

    def _save_config(self) -> None:
        """Persist the current settings to config.ini.

        将当前设置持久化到 config.ini。
        """
        with open(self.config_path, "w", encoding="utf-8") as fh:
            self.config.write(fh)

    def _apply_config(self) -> None:
        """Apply the loaded configuration to the UI.

        将已加载的配置应用到 UI。
        """
        theme = self.config.get("Preferences", "theme", fallback="system")
        action_map = {
            "light": self.light_theme_action,
            "dark": self.dark_theme_action,
            "system": self.system_theme_action,
        }
        action = action_map.get(theme, self.system_theme_action)
        if action:
            action.setChecked(True)
        self._set_theme(theme, initializing=True)

    # ==================================================================
    # Theming
    # ==================================================================

    def _set_theme(self, theme_name: str, initializing: bool = False) -> None:
        """Apply a colour theme and optionally persist the preference.

        应用颜色主题，并可选地持久化该偏好。

        :param theme_name: ``'light'``, ``'dark'``, or ``'system'``.
        :param initializing: ``True`` during startup – skips writing config.
                             启动期间为 True，跳过写入配置。
        """
        app = QApplication.instance()
        if theme_name == "dark":
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(
                QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black
            )
            app.setPalette(dark_palette)
        else:
            app.setPalette(self.original_palette)

        if not initializing:
            self.config.set("Preferences", "theme", theme_name)
            self._save_config()

        self._update_widget_styles()

    def _update_widget_styles(self) -> None:
        """Re-apply custom stylesheets to all theme-aware widgets.

        This is the single source of truth for theme-dependent styles.

        将自定义样式表重新应用于所有需要感知主题的控件。
        这是依赖主题样式的唯一事实来源。
        """
        is_dark = self.palette().color(QPalette.ColorRole.Window).lightness() < 128
        highlight_color = self.palette().color(QPalette.ColorRole.Highlight).name()
        highlighted_text_color = (
            self.palette().color(QPalette.ColorRole.HighlightedText).name()
            if is_dark
            else "#ffffff"
        )

        list_style = f"""
            QListWidget {{ outline: 0; }}
            QListWidget::item {{ padding: 4px; }}
            QListWidget::item:selected {{
                background-color: {highlight_color};
                color: {highlighted_text_color};
                border-radius: 4px;
            }}
        """
        self.path_list_widget.setStyleSheet(list_style)
        self.script_list.setStyleSheet(list_style)
        self.terminal.apply_theme()

    # ==================================================================
    # UI construction
    # ==================================================================

    def _init_ui(self) -> None:
        """Initialise the overall UI layout.

        初始化整体 UI 布局。
        """
        self._create_menu_bar()
        self.setGeometry(100, 100, 1200, 800)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.setAcceptDrops(True)

        main_layout = QHBoxLayout(central_widget)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)

        main_splitter.addWidget(self._create_left_panel())
        main_splitter.addWidget(self._create_right_panel())
        main_splitter.setSizes([400, 800])

        self.statusBar()
        self.setStyleSheet(
            "QPushButton { min-height: 30px; padding: 5px; }"
            " QLineEdit, QComboBox { min-height: 28px; }"
        )
        self._update_widget_styles()

    def _create_menu_bar(self) -> None:
        """Create the main menu bar with theme-switching actions.

        创建带有主题切换动作的主菜单栏。
        """
        self.menu_bar = self.menuBar()
        lang = UI_TEXTS[self.current_lang]

        self.prefs_menu = self.menu_bar.addMenu(lang["prefs_menu"])
        self.theme_menu = self.prefs_menu.addMenu(lang["theme_menu"])

        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)

        self.light_theme_action = QAction(lang["theme_light"], self, checkable=True)
        self.light_theme_action.triggered.connect(lambda: self._set_theme("light"))

        self.dark_theme_action = QAction(lang["theme_dark"], self, checkable=True)
        self.dark_theme_action.triggered.connect(lambda: self._set_theme("dark"))

        self.system_theme_action = QAction(lang["theme_system"], self, checkable=True)
        self.system_theme_action.triggered.connect(lambda: self._set_theme("system"))
        self.system_theme_action.setChecked(True)

        for action in (
            self.light_theme_action,
            self.dark_theme_action,
            self.system_theme_action,
        ):
            theme_group.addAction(action)
            self.theme_menu.addAction(action)

    def _create_left_panel(self) -> QWidget:
        """Create the left panel: script list + description.

        创建左侧面板：脚本列表 + 描述区。
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)

        header_layout = QHBoxLayout()
        self.script_list_label = QLabel()
        header_layout.addWidget(self.script_list_label)
        header_layout.addStretch()
        self.refresh_button = QPushButton("🔄")
        self.refresh_button.clicked.connect(self._refresh_scripts)
        self.refresh_button.setFixedSize(30, 30)
        header_layout.addWidget(self.refresh_button)
        layout.addLayout(header_layout)

        self.script_list = QListWidget()
        self.script_list.setAlternatingRowColors(True)
        self.script_list.itemClicked.connect(self._on_script_selected)
        self.script_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.script_list.customContextMenuRequested.connect(
            self._show_script_context_menu
        )

        self.script_info_label = QLabel()
        self.script_info = QTextEdit()
        self.script_info.setReadOnly(True)
        self.switch_lang_button = QPushButton()
        self.switch_lang_button.clicked.connect(self._toggle_language)

        layout.addWidget(self.script_list)
        layout.addWidget(self.script_info_label)
        layout.addWidget(self.script_info)
        layout.addWidget(self.switch_lang_button)
        return panel

    def _create_right_panel(self) -> QWidget:
        """Create the right panel: file list, params, run controls, output tabs.

        创建右侧面板：文件列表、参数区、运行控制区、输出选项卡。
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # File list --------------------------------------------------
        self.path_list_label = QLabel()
        self.path_list_widget = QListWidget()
        self.path_list_widget.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection
        )
        self.path_list_widget.itemChanged.connect(self._on_path_item_changed)
        self.path_list_widget.itemDoubleClicked.connect(
            self.path_list_widget.editItem
        )
        layout.addWidget(self.path_list_label)
        layout.addWidget(self.path_list_widget)

        # File-management buttons ------------------------------------
        button_layout = QHBoxLayout()
        self.browse_files_button = QPushButton()
        self.browse_files_button.clicked.connect(self._browse_files)
        self.browse_dir_button = QPushButton()
        self.browse_dir_button.clicked.connect(self._browse_directories)
        self.select_all_button = QPushButton()
        self.select_all_button.clicked.connect(self._on_select_all_button_clicked)
        self.remove_button = QPushButton()
        self.remove_button.clicked.connect(self._on_remove_button_clicked)

        button_layout.addWidget(self.browse_files_button)
        button_layout.addWidget(self.browse_dir_button)
        button_layout.addStretch()
        button_layout.addWidget(self.select_all_button)
        button_layout.addWidget(self.remove_button)
        layout.addLayout(button_layout)

        # Dynamic params widget --------------------------------------
        self.dynamic_params = DynamicParamsWidget()
        layout.addWidget(self.dynamic_params)

        # Separator --------------------------------------------------
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Manual params input ----------------------------------------
        params_layout = QHBoxLayout()
        self.params_label = QLabel()
        self.script_params = QLineEdit()
        params_layout.addWidget(self.params_label)
        params_layout.addWidget(self.script_params)
        layout.addLayout(params_layout)

        # Run / Stop buttons -----------------------------------------
        run_stop_layout = QHBoxLayout()
        run_stop_layout.setSpacing(10)

        self.run_button = QPushButton()
        self.run_button.clicked.connect(self._run_script)
        self.run_button.setEnabled(False)
        self.run_button.setStyleSheet(
            "QPushButton { font-weight: bold; font-size: 14pt;"
            " padding: 8px; min-height: 40px; }"
        )

        self.stop_button = QPushButton()
        self.stop_button.clicked.connect(self._stop_script)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet(
            "QPushButton { font-weight: bold; font-size: 14pt;"
            " padding: 8px; min-height: 40px; color: #D32F2F; }"
        )

        run_stop_layout.addWidget(self.run_button)
        run_stop_layout.addWidget(self.stop_button)
        layout.addLayout(run_stop_layout)

        # Progress bar -----------------------------------------------
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()

        self.progress_label = QLabel("...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.hide()

        layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_label)

        # Output tabs ------------------------------------------------
        self.output_label = QLabel()
        self.tabs = QTabWidget()

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet(
            "background-color: #282c34; color: #abb2bf;"
            " font-family: Consolas, 'Courier New', monospace;"
        )

        self.terminal = EnhancedTerminalWidget()
        self.terminal.command_entered.connect(self._handle_terminal_input)

        self.tabs.addTab(self.console, "")
        self.tabs.addTab(self.terminal, "")
        layout.addWidget(self.output_label)
        layout.addWidget(self.tabs)

        return panel

    def _create_actions(self) -> None:
        """Create global keyboard shortcuts (Undo / Redo).

        创建全局键盘快捷键（撤销/重做）。
        """
        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        self.undo_action.triggered.connect(self.undo)
        self.addAction(self.undo_action)

        self.redo_action = QAction("Redo", self)
        if platform.system() == "Darwin":
            self.redo_action.setShortcut(QKeySequence("Ctrl+Shift+Z"))
        else:
            self.redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        self.redo_action.triggered.connect(self.redo)
        self.addAction(self.redo_action)

    # ==================================================================
    # Language / i18n
    # ==================================================================

    def _update_ui_language(self) -> None:
        """Refresh all UI text labels to match the current language.

        将所有 UI 文字标签刷新为当前语言。
        """
        lang = UI_TEXTS[self.current_lang]
        self.setWindowTitle(lang["window_title"])
        self.script_list_label.setText(lang["available_scripts"])
        self.script_info_label.setText(lang["script_info"])
        self.path_list_label.setText(lang["path_list_label"])
        self.run_button.setText(lang["run_button"])
        self.stop_button.setText(lang.get("stop_button", "Stop Script"))
        self.browse_files_button.setText(lang["browse_files_button"])
        self.browse_dir_button.setText(lang["browse_dir_button"])
        self.params_label.setText(lang["params_label"])
        self.script_params.setPlaceholderText(lang["params_placeholder"])
        self.output_label.setText(lang["output_label"])
        self.tabs.setTabText(0, lang["stdout_tab"])
        self.tabs.setTabText(1, lang["terminal_tab"])
        self.statusBar().showMessage(lang["status_ready"])
        self.switch_lang_button.setText(lang["switch_lang_button"])
        self.refresh_button.setToolTip(lang["refresh_button_tooltip"])
        self.terminal.set_language(self.current_lang)
        self._update_script_list_display()
        self._update_remove_button_state()
        self._update_script_info_display()
        self._update_select_all_button_state()

        if hasattr(self, "prefs_menu"):
            self.prefs_menu.setTitle(lang["prefs_menu"])
            self.theme_menu.setTitle(lang["theme_menu"])
            self.light_theme_action.setText(lang["theme_light"])
            self.dark_theme_action.setText(lang["theme_dark"])
            self.system_theme_action.setText(lang["theme_system"])

    def _toggle_language(self) -> None:
        """Toggle the UI language between Chinese and English.

        在中文与英文之间切换 UI 语言。
        """
        self.current_lang = "en" if self.current_lang == "zh" else "zh"
        self._update_ui_language()

    # ==================================================================
    # Script list management
    # ==================================================================

    def _refresh_scripts(self) -> None:
        """Reload the script list from disk.

        从磁盘重新加载脚本列表。
        """
        self.script_list.clear()
        self.script_info.clear()
        self.current_script_path = None
        self.run_button.setEnabled(False)
        self.dynamic_params.clear()
        self.load_scripts()
        self.statusBar().showMessage(UI_TEXTS[self.current_lang]["status_ready"], 2000)

    def load_scripts(self) -> None:
        """Scan the scripts directory and populate the script list widget.

        扫描脚本目录并填充脚本列表控件。
        """
        for info in registry.scan(self.scripts_dir):
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, info)
            self.script_list.addItem(item)
        self._update_script_list_display()

    def _update_script_list_display(self) -> None:
        """Update all list-item display texts to the current language.

        将所有列表项的显示文字更新为当前语言。
        """
        for i in range(self.script_list.count()):
            item = self.script_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if data:
                display_name = (
                    data["name_zh"] if self.current_lang == "zh" else data["name_en"]
                )
                item.setText(display_name)

    def _show_script_context_menu(self, position) -> None:
        """Show a context menu with 'Show in folder' for the right-clicked script.

        为右键点击的脚本显示包含「在文件夹中显示」的上下文菜单。
        """
        item = self.script_list.itemAt(position)
        if not item:
            return
        script_data = item.data(Qt.ItemDataRole.UserRole)
        script_path = script_data.get("path")
        if not script_path:
            return

        context_menu = QMenu(self)
        title_action = QAction(os.path.basename(script_path), self)
        title_action.setEnabled(False)
        context_menu.addAction(title_action)
        context_menu.addSeparator()

        show_action = QAction("在文件夹中显示", self)
        show_action.triggered.connect(
            lambda: self._open_in_file_explorer(script_path)
        )
        context_menu.addAction(show_action)
        context_menu.exec(self.script_list.mapToGlobal(position))

    def _open_in_file_explorer(self, path: str) -> None:
        """Open the system file explorer and highlight *path*.

        打开系统文件资源管理器并高亮 *path*。
        """
        if not os.path.exists(path):
            return
        system = platform.system()
        try:
            if system == "Windows":
                subprocess.run(["explorer", "/select,", os.path.normpath(path)])
            elif system == "Darwin":
                subprocess.run(["open", "-R", path])
            else:
                subprocess.run(["xdg-open", os.path.dirname(path)])
        except Exception as exc:  # noqa: BLE001
            QMessageBox.information(
                self,
                "File Path",
                f"Could not open explorer.\nThe file is located at:\n{path}\n({exc})",
            )

    # ==================================================================
    # Script selection & parameter parsing
    # ==================================================================

    def _on_script_selected(self, item: QListWidgetItem) -> None:
        """Handle a script being selected from the list.

        处理从列表中选择脚本的事件。
        """
        script_data = item.data(Qt.ItemDataRole.UserRole)
        self.current_script_path = script_data["path"]
        try:
            with open(self.current_script_path, "r", encoding="utf-8") as fh:
                content = fh.read()
            self.current_script_docstring = registry.extract_docstring(content)
            self.run_button.setEnabled(True)
            params = registry.parse_params(self.current_script_path)
            self.dynamic_params.build_ui(params, self.current_lang)
        except Exception as exc:  # noqa: BLE001
            self.current_script_docstring = (
                f"{UI_TEXTS[self.current_lang]['info_read_error']}{exc}"
            )
            self.run_button.setEnabled(False)
            self.dynamic_params.clear()
        self._update_script_info_display()

    def _update_script_info_display(self) -> None:
        """Show the relevant language block of the script's docstring.

        显示脚本文档字符串中对应语言的部分。
        Uses ``~~~`` as the primary language separator.
        使用 ``~~~`` 作为语言分隔符。
        """
        doc = self.current_script_docstring
        display_text = doc if doc else UI_TEXTS[self.current_lang]["info_no_docstring"]

        if "~~~" in doc:
            try:
                parts = doc.split("~~~", 1)
                chinese_doc = parts[0]
                english_doc = parts[1] if len(parts) > 1 else ""
                selected_doc = chinese_doc if self.current_lang == "zh" else english_doc
                display_text = re.sub(
                    r"\[display-name-..\](.*?)\n", "", selected_doc, count=2
                ).strip()
            except Exception as exc:  # noqa: BLE001
                print(f"Error parsing docstring with '~~~': {exc}")
                display_text = doc

        self.script_info.setText(display_text)

    # ==================================================================
    # File / path list management
    # ==================================================================

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        """Accept drag events that carry file URLs.

        接受携带文件 URL 的拖拽事件。
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # type: ignore[override]
        """Add dropped files/directories to the path list.

        将拖放的文件/目录添加到路径列表。
        """
        self._save_state_for_undo()
        for url in event.mimeData().urls():
            self._add_path_to_list(url.toLocalFile())
        self._update_remove_button_state()

    def _add_path_to_list(self, path: str) -> None:
        """Add a single path item with checkbox and editable flags.

        添加带复选框和可编辑标志的单个路径项。
        """
        if os.path.exists(path):
            item = QListWidgetItem(path)
            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEditable
            )
            item.setCheckState(Qt.CheckState.Unchecked)
            self.path_list_widget.addItem(item)

    def _browse_files(self) -> None:
        """Open a file-picker dialog and add selected files.

        打开文件选择对话框并添加所选文件。
        """
        self._save_state_for_undo()
        files, _ = QFileDialog.getOpenFileNames(
            self, UI_TEXTS[self.current_lang]["browse_files_button"]
        )
        if files:
            for f in files:
                self._add_path_to_list(f)
            self._update_remove_button_state()

    def _browse_directories(self) -> None:
        """Open a directory-picker dialog and add selected directories.

        打开目录选择对话框并添加所选目录。
        """
        self._save_state_for_undo()
        dialog = QFileDialog(self, UI_TEXTS[self.current_lang]["browse_dir_button"])
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        if dialog.exec():
            directories = dialog.selectedFiles()
            if directories:
                for d in directories:
                    self._add_path_to_list(d)
                self._update_remove_button_state()

    def _on_path_item_changed(self, item: QListWidgetItem) -> None:
        """Save undo state when an item's text or check state changes.

        当项目文字或勾选状态变化时保存撤销状态。
        """
        self._save_state_for_undo()
        self._update_remove_button_state()
        self._update_select_all_button_state()

    def _get_checked_items(self) -> list[QListWidgetItem]:
        """Return all checked items in the path list.

        返回路径列表中所有被勾选的项目。
        """
        return [
            self.path_list_widget.item(i)
            for i in range(self.path_list_widget.count())
            if self.path_list_widget.item(i).checkState() == Qt.CheckState.Checked
        ]

    def _get_union_of_marked_items(self) -> list[QListWidgetItem]:
        """Return the union of selected (highlighted) and checked items.

        返回被选中（高亮）与被勾选项目的并集。
        ``QListWidgetItem`` is not hashable, so we build the list manually.
        ``QListWidgetItem`` 不可哈希，因此手动构建列表。
        """
        combined = self.path_list_widget.selectedItems() + self._get_checked_items()
        unique: list[QListWidgetItem] = []
        for item in combined:
            if item not in unique:
                unique.append(item)
        return unique

    def _on_remove_button_clicked(self) -> None:
        """Remove the union of selected and checked items, or clear all.

        移除选中与勾选项目的并集；若无标记项目则清空全部。
        """
        self._save_state_for_undo()
        items_to_delete = self._get_union_of_marked_items()
        if items_to_delete:
            for item in items_to_delete:
                self.path_list_widget.takeItem(self.path_list_widget.row(item))
        else:
            self.path_list_widget.clear()
        self._update_remove_button_state()
        self._update_select_all_button_state()

    def _update_remove_button_state(self) -> None:
        """Update the remove button label based on whether any items are marked.

        根据是否有标记项目更新移除按钮的文字。
        """
        lang = UI_TEXTS[self.current_lang]
        is_any_marked = bool(
            self.path_list_widget.selectedItems() or self._get_checked_items()
        )
        self.remove_button.setText(
            lang["remove_selected_button"] if is_any_marked else lang["remove_all_button"]
        )

    def _update_select_all_button_state(self) -> None:
        """Update the Select All / Deselect All button label.

        更新「勾选全部/取消选择」按钮的文字。
        """
        lang = UI_TEXTS[self.current_lang]
        self.select_all_button.setText(
            lang["deselect_all"] if self._get_checked_items() else lang["select_all"]
        )

    def _on_select_all_button_clicked(self) -> None:
        """Toggle check state on all path list items.

        切换所有路径列表项的勾选状态。
        """
        self._save_state_for_undo()
        new_state = (
            Qt.CheckState.Unchecked
            if self._get_checked_items()
            else Qt.CheckState.Checked
        )
        for i in range(self.path_list_widget.count()):
            self.path_list_widget.item(i).setCheckState(new_state)
        self._update_select_all_button_state()

    # ==================================================================
    # Undo / Redo
    # ==================================================================

    def _save_state_for_undo(self) -> None:
        """Push the current path-list state onto the undo stack.

        将当前路径列表状态压入撤销栈。
        """
        state = [
            {
                "text": self.path_list_widget.item(i).text(),
                "checked": self.path_list_widget.item(i).checkState()
                == Qt.CheckState.Checked,
            }
            for i in range(self.path_list_widget.count())
        ]
        if not self.undo_stack or state != self.undo_stack[-1]:
            self.undo_stack.append(state)
            self.redo_stack.clear()

    def _restore_state(self, state: list) -> None:
        """Restore the path list from a saved state dict.

        从已保存的状态字典中恢复路径列表。
        """
        self.path_list_widget.clear()
        for item_data in state:
            item = QListWidgetItem(item_data["text"])
            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEditable
            )
            item.setCheckState(
                Qt.CheckState.Checked if item_data["checked"] else Qt.CheckState.Unchecked
            )
            self.path_list_widget.addItem(item)
        self._update_remove_button_state()
        self._update_select_all_button_state()

    def undo(self) -> None:
        """Undo the last path-list modification.

        撤销最近一次路径列表修改。
        """
        if len(self.undo_stack) > 1:
            self.redo_stack.append(self.undo_stack.pop())
            self._restore_state(self.undo_stack[-1])
        else:
            self.statusBar().showMessage(
                UI_TEXTS[self.current_lang]["undo_stack_empty"], 2000
            )

    def redo(self) -> None:
        """Redo the last undone path-list modification.

        重做最近一次撤销的路径列表修改。
        """
        if self.redo_stack:
            state_to_restore = self.redo_stack.pop()
            self.undo_stack.append(state_to_restore)
            self._restore_state(state_to_restore)
        else:
            self.statusBar().showMessage(
                UI_TEXTS[self.current_lang]["redo_stack_empty"], 2000
            )

    # ==================================================================
    # Key-press handling
    # ==================================================================

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle global shortcuts: Esc unchecks all; Delete/Backspace removes items.

        处理全局快捷键：Esc 取消勾选；Delete/Backspace 移除项目。
        """
        if event.key() == Qt.Key.Key_Escape:
            changed = False
            for item in self._get_checked_items():
                item.setCheckState(Qt.CheckState.Unchecked)
                changed = True
            if changed:
                self._save_state_for_undo()
                self._update_select_all_button_state()
            return

        if self.path_list_widget.hasFocus() and event.key() in (
            Qt.Key.Key_Delete,
            Qt.Key.Key_Backspace,
        ):
            items_to_delete = self._get_union_of_marked_items()
            if items_to_delete:
                self._save_state_for_undo()
                for item in items_to_delete:
                    self.path_list_widget.takeItem(self.path_list_widget.row(item))
                self._update_remove_button_state()
                self._update_select_all_button_state()
            return

        super().keyPressEvent(event)

    # ==================================================================
    # Script execution
    # ==================================================================

    def _run_script(self) -> None:
        """Assemble the command and launch the ScriptExecutor thread.

        组装命令并启动 ScriptExecutor 线程。
        """
        lang = UI_TEXTS[self.current_lang]
        if not self.current_script_path:
            QMessageBox.warning(
                self, lang["warn_select_script_title"], lang["warn_select_script_msg"]
            )
            return

        checked_items = self._get_checked_items()
        if checked_items:
            paths = [item.text() for item in checked_items]
        else:
            paths = [
                self.path_list_widget.item(i).text()
                for i in range(self.path_list_widget.count())
            ]

        if not paths:
            QMessageBox.warning(
                self, lang["warn_no_paths_title"], lang["warn_no_paths_msg"]
            )
            return

        arguments = ["--gui-mode", "--lang", self.current_lang]
        arguments.extend(self.dynamic_params.build_args())

        user_params = self.script_params.text().strip()
        if user_params:
            arguments.extend(shlex.split(user_params))

        arguments.extend(paths)
        command = [self.current_script_path] + arguments

        self.console.clear()
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.statusBar().showMessage(lang["status_running"])
        self.tabs.setCurrentWidget(self.terminal)
        self.progress_bar.hide()
        self.progress_label.hide()
        self.progress_bar.setValue(0)
        self.progress_label.setText("...")

        self.script_executor = ScriptExecutor(command)
        self.script_executor.output_updated.connect(self._append_to_console)
        self.script_executor.output_updated.connect(self.terminal.append_output)
        self.script_executor.progress_updated.connect(self._update_progress_display)
        self.script_executor.process_finished.connect(self._on_script_finished)
        self.script_executor.start()

    def _stop_script(self) -> None:
        """Terminate the currently running script.

        终止当前正在运行的脚本。
        """
        if self.script_executor and self.script_executor.isRunning():
            lang = UI_TEXTS[self.current_lang]
            self.script_executor.terminate()
            stop_msg = (
                f"\n--- {lang.get('script_stopped_msg', 'Script execution stopped by user.')} ---\n"
            )
            self._append_to_console(stop_msg)
            self.terminal.append_output(stop_msg)
            self._on_script_finished(-1)

    def _on_script_finished(self, exit_code: int) -> None:
        """Clean up and reset the UI after the script finishes.

        脚本结束后执行清理并重置 UI。
        """
        lang = UI_TEXTS[self.current_lang]
        msg = lang["script_finished_msg"].format(exit_code=exit_code)
        self._append_to_console(msg)
        self.terminal.append_output(msg)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.statusBar().showMessage(lang["status_ready"])
        self.progress_bar.hide()
        self.progress_label.hide()
        self.script_executor = None

    def _append_to_console(self, text: str) -> None:
        """Append *text* to the Standard Output tab.

        将 *text* 追加到标准输出选项卡。
        """
        from PyQt6.QtGui import QTextCursor

        cursor = self.console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.console.setTextCursor(cursor)
        self.console.insertPlainText(text)
        self.console.ensureCursorVisible()

    def _update_progress_display(
        self, current_float: float, max_float: float, description: str
    ) -> None:
        """Update the progress bar from float progress values.

        从浮点进度值更新进度条。
        Maps floats to an integer scale to smooth out fractional steps.
        将浮点数映射到整数刻度以平滑小数步长。
        """
        if self.progress_bar.isHidden():
            self.progress_bar.show()
            self.progress_label.show()
        max_int = int(max_float * 100)
        current_int = int(current_float * 100)
        self.progress_bar.setRange(0, max_int)
        self.progress_bar.setValue(current_int)
        self.progress_label.setText(description)

    # ==================================================================
    # Terminal / system-command handling
    # ==================================================================

    def _handle_terminal_input(self, text: str) -> None:
        """Route user input to the running script or the system shell.

        将用户输入路由到正在运行的脚本或系统 shell。
        """
        if self.script_executor and self.script_executor.isRunning():
            self.script_executor.send_input(text)
        else:
            self._execute_system_command(text)

    def _execute_system_command(self, command_str: str) -> None:
        """Execute a system command when no script is running.

        无脚本运行时执行系统命令。
        """
        if not command_str.strip():
            self.terminal.append_output(
                f"\n{self.terminal.prompt_label.text()} "
            )
            return

        if command_str.lower() == "exit":
            self.close()
            return

        try:
            cmd_parts = shlex.split(command_str)
        except ValueError as exc:
            self.terminal.append_output(f"Error parsing command: {exc}\n")
            return

        if not cmd_parts:
            return

        if cmd_parts[0].lower() == "cd":
            if len(cmd_parts) > 1:
                try:
                    os.chdir(cmd_parts[1])
                    self.terminal._update_prompt()
                except FileNotFoundError:
                    self.terminal.append_output(
                        f"Error: Directory does not exist: {cmd_parts[1]}\n"
                    )
            else:
                self.terminal.append_output("Error: Please specify a directory\n")
            return

        self.system_process = QProcess()
        self.system_process.readyReadStandardOutput.connect(
            self._handle_system_output
        )
        self.system_process.finished.connect(self._on_system_command_finished)
        self.system_process.start(cmd_parts[0], cmd_parts[1:])
        if not self.system_process.waitForStarted():
            self.terminal.append_output(
                f"Error starting command: {cmd_parts[0]}\n"
            )

    def _handle_system_output(self) -> None:
        """Forward system-command stdout to the terminal widget.

        将系统命令的标准输出转发到终端控件。
        """
        if self.system_process:
            raw = self.system_process.readAllStandardOutput().data()
            try:
                decoded = raw.decode("utf-8")
            except UnicodeDecodeError:
                decoded = raw.decode("gbk", errors="replace")
            self.terminal.append_output(decoded)

    def _on_system_command_finished(self, exit_code: int) -> None:
        """Clean up after a system command finishes.

        系统命令结束后执行清理。
        """
        self.terminal.append_output(
            f"\nCommand finished with exit code: {exit_code}\n"
        )
        self.system_process = None
        self.terminal._update_prompt()

    # ==================================================================
    # Window close
    # ==================================================================

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Terminate all child processes before the window closes.

        窗口关闭前终止所有子进程。
        """
        if self.script_executor and self.script_executor.isRunning():
            self.script_executor.terminate()
        if (
            self.system_process
            and self.system_process.state() == QProcess.ProcessState.Running
        ):
            self.system_process.terminate()
        event.accept()
