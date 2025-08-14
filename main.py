#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
import glob
import shlex
import platform
import subprocess
import configparser
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QListWidget, QTextEdit, QLabel,
                            QSplitter, QFileDialog, QPushButton, QMessageBox, QMenu,
                            QListWidgetItem, QTabWidget, QLineEdit, QCheckBox,
                            QFormLayout, QComboBox, QFrame, QGridLayout, QProgressBar)
from PyQt6.QtCore import Qt, QProcess, pyqtSignal, QThread
from PyQt6.QtGui import (QFont, QTextCursor, QKeyEvent, QAction, QKeySequence, 
                         QPalette, QActionGroup, QColor)

# Resource Path Function / 资源路径函数 
def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    获取资源的绝对路径，无论是在开发环境还是在PyInstaller打包后都能正常工作。
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # PyInstaller会创建一个临时文件夹，并将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        # If not packaged, use the normal script directory
        # 如果没有被打包，则使用常规的脚本目录
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# Constants / 全局常量 
# UI text for different languages / 不同语言的界面文本
UI_TEXTS = {
    'zh': {
        'window_title': "奥创王牌工具箱 - 用户: UltraAce258",
        'available_scripts': "可用脚本:",
        'script_info': "脚本介绍:",
        'path_list_label': "文件/文件夹列表 (支持拖放、复选框、双击编辑):",
        'run_button': "执行脚本",
        'remove_selected_button': "移除选中项",
        'remove_all_button': "清空所有",
        'browse_files_button': "添加文件(可多选)",
        'browse_dir_button': "添加文件夹(可多选)",
        'params_label': "手动参数:",
        'params_placeholder': "输入额外的手动参数",
        'output_label': "输出:",
        'stdout_tab': "标准输出",
        'terminal_tab': "增强型终端",
        'status_ready': "就绪",
        'status_running': "脚本执行中...",
        'terminal_welcome': "欢迎使用增强型终端\n",
        'switch_lang_button': "切换语言 (Switch Language)",
        'refresh_button_tooltip': "刷新脚本列表",
        'info_no_docstring': "此脚本没有提供文档字符串。",
        'info_read_error': "读取脚本信息时出错: ",
        'warn_select_script_title': "警告",
        'warn_select_script_msg': "请先选择一个脚本",
        'warn_no_paths_title': "警告",
        'warn_no_paths_msg': "请先添加至少一个文件或文件夹",
        'script_finished_msg': "\n脚本执行完成，退出代码: {exit_code}",
        'undo_stack_empty': "没有可撤销的操作",
        'redo_stack_empty': "没有可重做的操作",
        'select_all': "勾选全部",
        'deselect_all': "取消选择",
        'prefs_menu': "偏好设置(&P)",
        'theme_menu': "主题",
        'theme_light': "浅色模式",
        'theme_dark': "深色模式",
        'theme_system': "跟随系统",
        'dynamic_params_label': "可视化参数:"
    },
    'en': {
        'window_title': "UltraAce Toolkit - User: UltraAce258",
        'available_scripts': "Available Scripts:",
        'script_info': "Script Info:",
        'path_list_label': "File/Folder List (Drag-drop, Checkbox, Double-click to edit):",
        'run_button': "Run Script",
        'remove_selected_button': "Remove Selected",
        'remove_all_button': "Clear All",
        'browse_files_button': "Add Files (Multi-select)",
        'browse_dir_button': "Add Folders (Multi-select)",
        'params_label': "Manual Parameters:",
        'params_placeholder': "Enter additional manual parameters",
        'output_label': "Output:",
        'stdout_tab': "Standard Output",
        'terminal_tab': "Enhanced Terminal",
        'status_ready': "Ready",
        'status_running': "Script running...",
        'terminal_welcome': "Welcome to the Enhanced Terminal\n",
        'switch_lang_button': "Switch Language (切换语言)",
        'refresh_button_tooltip': "Refresh script list",
        'info_no_docstring': "This script does not provide a docstring.",
        'info_read_error': "Error reading script info: ",
        'warn_select_script_title': "Warning",
        'warn_select_script_msg': "Please select a script first.",
        'warn_no_paths_title': "Warning",
        'warn_no_paths_msg': "Please add at least one file or folder.",
        'script_finished_msg': "\nScript finished with exit code: {exit_code}",
        'undo_stack_empty': "Nothing to undo",
        'redo_stack_empty': "Nothing to redo",
        'select_all': "Select All",
        'deselect_all': "Deselect All",
        'prefs_menu': "Preferences(&P)",
        'theme_menu': "Theme",
        'theme_light': "Light Mode",
        'theme_dark': "Dark Mode",
        'theme_system': "Follow System",
        'dynamic_params_label': "Visual Parameters:"
    }
}

class ScriptExecutor(QThread):
    """
    Executes a script in a separate thread to keep the GUI responsive.
    在一个独立的线程中执行脚本，以保持GUI的响应性。
    """
    # Signal to send script output back to the main thread / 将脚本输出发送回主线程的信号
    output_updated = pyqtSignal(str)
    # Signal to notify the main thread when the process is updated / 进程更新时通知主线程的信号
    progress_updated = pyqtSignal(float, float, str)
    # Signal to notify the main thread when the process is finished / 进程结束时通知主线程的信号
    process_finished = pyqtSignal(int)

    def __init__(self, command, working_dir=None):
        """
        Initializes the executor with the command to run.
        使用要运行的命令初始化执行器。

        :param command: A list of command arguments. / 命令参数列表。
        :param working_dir: The working directory for the script. / 脚本的工作目录。
        """
        super().__init__()
        self.command = command
        self.working_dir = working_dir
        self.process = None
        # Set default encoding based on OS to handle console output correctly
        # 根据操作系统设置默认编码，以正确处理控制台输出
        self.output_encoding = 'gbk' if platform.system() == "Windows" else 'utf-8'

    def run(self):
        """
        The main logic of the thread. Starts the QProcess.
        线程的主要逻辑。启动QProcess。
        """
        try:
            display_command = shlex.join([os.path.basename(sys.executable)] + self.command)
            self.output_updated.emit(f"Executing command: {display_command}\n")
            
            self.process = QProcess()
            # Merge stdout and stderr so we get all output in one channel
            # 合并 stdout 和 stderr，以便在一个通道中获取所有输出
            self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            if self.working_dir:
                self.process.setWorkingDirectory(self.working_dir)

            # Connect signals from the process to our handlers
            # 将进程的信号连接到我们的处理器
            self.process.readyReadStandardOutput.connect(self._handle_output)
            self.process.finished.connect(self.process_finished.emit)

            # Start the process and wait for it to finish
            # 启动进程并等待其完成
            self.process.start(sys.executable, self.command)
            self.process.waitForFinished(-1) # -1 means wait indefinitely / -1表示无限期等待
        except Exception as e:
            self.output_updated.emit(f"Error executing command: {e}\n")
            self.process_finished.emit(1) # Emit failure signal / 发出失败信号

    def _handle_output(self):
        """
        Reads output and intelligently routes it, now parsing progress values as floats.
        读取输出并智能分发，现在将进度值解析为浮点数。
        """
        if not self.process: return
        data = self.process.readAllStandardOutput().data()
        try:
            decoded_text = data.decode('utf-8')
        except UnicodeDecodeError:
            decoded_text = data.decode(self.output_encoding, errors='replace')

        for line in decoded_text.strip().split('\n'):
            if not line.strip(): continue

            if line.startswith('[PROGRESS]'):
                try:
                    payload = line[len('[PROGRESS]'):].strip()
                    progress_part, description = payload.split('|', 1)
                    current_str, max_str = progress_part.split('/', 1)
                    
                    # 将字符串解析为浮点数
                    current = float(current_str.strip())
                    maximum = float(max_str.strip())
                    
                    self.progress_updated.emit(current, maximum, description.strip())
                except (ValueError, IndexError) as e:
                    self.output_updated.emit(f"Invalid progress format: {line}\nError: {e}\n")
            else:
                self.output_updated.emit(line + '\n')
            
                        
    def send_input(self, text):
        """
        Sends input text to the running script (for interactive scripts).
        向正在运行的脚本发送输入文本（用于交互式脚本）。
        """
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.write(f"{text}\n".encode('utf-8'))

    def terminate(self):
        """
        Forcefully stops the running process.
        强制停止正在运行的进程。
        """
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.terminate()
            # If terminate() fails, kill() it after a 3-second timeout
            # 如果 terminate() 失败，在3秒超时后执行 kill()
            if not self.process.waitForFinished(3000):
                self.process.kill()

class EnhancedTerminalWidget(QWidget):
    """
    A custom widget that emulates a basic terminal for output and input.
    一个自定义小部件，模拟用于输出和输入的基本终端。
    """
    # Signal emitted when the user presses Enter in the input line / 用户在输入行中按Enter键时发出的信号
    command_entered = pyqtSignal(str)
    def apply_theme(self):
        """Applies theme-aware stylesheets to terminal widgets."""
        is_dark = self.palette().color(QPalette.ColorRole.Window).lightness() < 128
        if is_dark:
            self.output_display.setStyleSheet("background-color: #282c34; color: #abb2bf; font-family: Consolas, 'Courier New', monospace; font-size: 11pt;")
            self.prompt_label.setStyleSheet("color: #61afef; font-weight: bold; font-size: 12pt;")
            self.command_input.setStyleSheet("background-color: #282c34; color: #e06c75; font-family: Consolas, 'Courier New', monospace; font-size: 11pt; border: none;")
        else:
            base_color = self.palette().color(QPalette.ColorRole.Base).name()
            text_color = self.palette().color(QPalette.ColorRole.Text).name()
            highlight_color = self.palette().color(QPalette.ColorRole.Highlight).name()
            self.output_display.setStyleSheet(f"background-color: {base_color}; color: {text_color}; font-family: Consolas, 'Courier New', monospace; font-size: 11pt;")
            self.prompt_label.setStyleSheet(f"color: {highlight_color}; font-weight: bold; font-size: 12pt;")
            self.command_input.setStyleSheet(f"background-color: {base_color}; color: #d12f2f; font-family: Consolas, 'Courier New', monospace; font-size: 11pt; border: none;")    
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history, self.history_index, self.current_lang = [], 0, 'zh'
        self._init_ui()

    def _init_ui(self):
        """
        Sets up the UI components of the terminal widget.
        设置终端小部件的UI组件。
        """
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0)
        self.output_display = QTextEdit(); self.output_display.setReadOnly(True)
        
        input_layout = QHBoxLayout()
        self.prompt_label = QLabel("$")
        self.prompt_label.setStyleSheet("color: #61afef; font-weight: bold; font-size: 12pt;")
        self.command_input = QLineEdit()
        self.command_input.returnPressed.connect(self._on_command_entered)
        
        input_layout.addWidget(self.prompt_label)
        input_layout.addWidget(self.command_input)
        layout.addWidget(self.output_display)
        layout.addLayout(input_layout)

    def set_language(self, lang):
        """
        Sets the language for the terminal's welcome message.
        设置终端欢迎消息的语言。
        """
        self.current_lang = lang
        self.output_display.clear()
        self.append_output(UI_TEXTS[self.current_lang]['terminal_welcome'])
        self._update_prompt()

    def _update_prompt(self):
        """
        Updates the command prompt to show the current working directory.
        更新命令提示符以显示当前工作目录。
        """
        self.prompt_label.setText(f"[{os.path.basename(os.getcwd())}]$")

    def append_output(self, text):
        """
        Appends text to the display, intelligently handling carriage returns ('\r')
        for progress bars without overwriting normal log lines.
        将文本追加到显示区，智能地处理用于进度条的回车符（'\r'），而不会覆盖正常的日志行。
        """
        cursor = self.output_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output_display.setTextCursor(cursor)
        
        lines = text.replace('\r\n', '\n').split('\n')

        for line in lines:
            if not line:
                continue
            
            if line.endswith('\r'):
                cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
                cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
                cursor.removeSelectedText()
                # The correct method for a QTextCursor is insertText(), not insertPlainText().
                # QTextCursor 的正确方法是 insertText()，而不是 insertPlainText()。
                cursor.insertText(line[:-1])
            else:
                # The correct method for a QTextCursor is insertText(), not insertPlainText().
                # QTextCursor 的正确方法是 insertText()，而不是 insertPlainText()。
                cursor.insertText(line + '\n')

        self.output_display.ensureCursorVisible()


    def _on_command_entered(self):
        """
        Handles the user pressing Enter. It now unconditionally processes the input,
        even if it's empty, mimicking a real terminal.
        处理用户按Enter键的事件。现在它会无条件地处理输入，即使是空的，
        以模仿一个真实的终端。
        """
        command = self.command_input.text()  # Get the raw text

        # Add to history only if it's a non-empty command
        # 仅当命令非空时才将其添加到历史记录
        if command.strip():
            self.history.append(command.strip())
            self.history_index = len(self.history)
        
        # Always emit the signal with the raw command. The parent will decide what to do.
        # 始终使用原始命令发出信号。父级将决定如何处理。
        self.command_entered.emit(command)
        
        # Clear the input for the next command
        # 为下一条命令清空输入
        self.command_input.clear()

    def keyPressEvent(self, event: QKeyEvent):
        """
        Implements command history navigation with up/down arrow keys.
        使用上/下箭头键实现命令历史导航。
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

class ScriptGUI(QMainWindow):
    """
    The main application window.
    主应用程序窗口。
    """
    
    def __init__(self, scripts_dir):
        """
        Initializes the main window and its components.
        初始化主窗口及其组件。
        """
        super().__init__()

        # Configuration Setup / 配置设置
        self.config_path = resource_path('config.ini')
        self.config = configparser.ConfigParser()
        self._load_config()

        # Instance Variables / 实例变量
        self.scripts_dir = scripts_dir
        self.current_script_path, self.current_script_docstring = None, ""
        self.script_executor, self.system_process = None, None
        self.current_lang = 'zh'
        self.undo_stack, self.redo_stack = [[]], []
        self.dynamic_param_widgets = []
        self.progress_bar = None
        self.progress_label = None
        
        self.original_palette = QApplication.instance().palette()
        
        self.light_theme_action = None
        self.dark_theme_action = None
        self.system_theme_action = None
        
        # UI Initialization / UI初始化
        self._init_ui()
        self._create_actions()
        self.load_scripts()
        self._update_ui_language()
        self._apply_config()

    def _load_config(self):
        """Loads settings from config.ini, creating it if it doesn't exist."""
        self.config.read(self.config_path, encoding='utf-8')
        if not self.config.has_section('Preferences'):
            self.config.add_section('Preferences')

    def _save_config(self):
        """Saves the current settings to config.ini."""
        with open(self.config_path, 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def _apply_config(self):
        """Applies loaded configuration to the UI."""
        theme = self.config.get('Preferences', 'theme', fallback='system')
        if theme == 'light':
            self.light_theme_action.setChecked(True)
        elif theme == 'dark':
            self.dark_theme_action.setChecked(True)
        else: # 'system'
            self.system_theme_action.setChecked(True)
        self._set_theme(theme, initializing=True)

    def _set_theme(self, theme_name, initializing=False):
        """
        Sets the application's color theme and saves the preference.
        :param theme_name: 'light', 'dark', or 'system'.
        :param initializing: True if called during startup to prevent double saving.
        """
        app = QApplication.instance()
        if theme_name == 'dark':
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
            dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
            app.setPalette(dark_palette)
        else:
            app.setPalette(self.original_palette)
        
        if not initializing:
            self.config.set('Preferences', 'theme', theme_name)
            self._save_config()
            
        self._update_widget_styles()
        
    def _update_widget_styles(self):
        """
        Re-applies custom stylesheets to all theme-aware widgets.
        This is the single source of truth for theme-dependent styles.
        将自定义样式表重新应用于所有需要感知主题的小部件。
        这是依赖于主题的样式的唯一事实来源。
        """
        # Define explicit colors for light and dark themes
        # 为浅色和深色主题定义明确的颜色
        is_dark = self.palette().color(QPalette.ColorRole.Window).lightness() < 128
        
        if is_dark:
            highlight_color = self.palette().color(QPalette.ColorRole.Highlight).name()
            # For dark mode, highlighted text is often black or a dark color
            # 对于深色模式，高亮文本通常是黑色或深色
            highlighted_text_color = self.palette().color(QPalette.ColorRole.HighlightedText).name()
        else:
            # For light mode, explicitly set highlighted text to white for contrast
            # 对于浅色模式，为形成对比，明确地将高亮文本设置为白色
            highlight_color = self.palette().color(QPalette.ColorRole.Highlight).name()
            highlighted_text_color = "#ffffff" # Explicitly white / 明确设为白色

        style = f"""
            QListWidget {{ outline: 0; }}
            QListWidget::item {{ padding: 4px; }}
            QListWidget::item:selected {{ 
                background-color: {highlight_color}; 
                color: {highlighted_text_color}; 
                border-radius: 4px; 
            }}
        """
        self.path_list_widget.setStyleSheet(style)
        self.script_list.setStyleSheet(style)

        # Update Enhanced Terminal Style
        # 更新增强型终端的样式
        self.terminal.apply_theme()

    def _init_ui(self):
        """
        Initializes the overall UI layout and sub-panels.
        初始化整体UI布局和子面板。
        """
        self._create_menu_bar()
        self.setGeometry(100, 100, 1200, 800)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # Enable drag-and-drop on the main window
        # 在主窗口上启用拖放功能
        self.setAcceptDrops(True)
        
        main_layout = QHBoxLayout(central_widget)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)
        
        left_panel, right_panel = self._create_left_panel(), self._create_right_panel()
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([400, 800]) # Initial size ratio / 初始尺寸比例
        
        self.statusBar()
        self.setStyleSheet("QPushButton { min-height: 30px; padding: 5px; } QLineEdit, QComboBox { min-height: 28px; }")
        self._update_widget_styles()
        
    def _create_menu_bar(self):
        """
        Creates the main menu bar and connects theme switching actions.
        为应用程序创建主菜单栏，并连接主题切换动作。
        """
        self.menu_bar = self.menuBar()
        lang = UI_TEXTS[self.current_lang]

        # Preferences Menu / 偏好设置菜单
        self.prefs_menu = self.menu_bar.addMenu(lang['prefs_menu'])

        # Theme Sub-Menu / 主题子菜单
        self.theme_menu = self.prefs_menu.addMenu(lang['theme_menu'])
        
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)

        # Create actions and connect them to the theme-setting method
        # 创建动作并将其连接到主题设置方法
        self.light_theme_action = QAction(lang['theme_light'], self, checkable=True)
        self.light_theme_action.triggered.connect(lambda: self._set_theme('light'))
        
        self.dark_theme_action = QAction(lang['theme_dark'], self, checkable=True)
        self.dark_theme_action.triggered.connect(lambda: self._set_theme('dark'))
        
        self.system_theme_action = QAction(lang['theme_system'], self, checkable=True)
        self.system_theme_action.triggered.connect(lambda: self._set_theme('system'))
        self.system_theme_action.setChecked(True) # Default option / 默认选项

        theme_group.addAction(self.light_theme_action)
        theme_group.addAction(self.dark_theme_action)
        theme_group.addAction(self.system_theme_action)
        
        self.theme_menu.addAction(self.light_theme_action)
        self.theme_menu.addAction(self.dark_theme_action)
        self.theme_menu.addAction(self.system_theme_action)
    

        
    def _create_left_panel(self):
        """
        Creates the left panel containing the script list and info display.
        创建包含脚本列表和信息显示的左侧面板。
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
         # 1. 激活自定义上下文菜单策略
        self.script_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        # 2. 连接信号到我们即将创建的处理器
        self.script_list.customContextMenuRequested.connect(self._show_script_context_menu)
        # 3. 正确处理高亮样式
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

    def _create_right_panel(self):
        """
        Creates the right panel containing the file list, parameters, and output tabs.
        创建包含文件列表、参数和输出选项卡的右侧面板。
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # File list section / 文件列表部分
        self.path_list_label = QLabel()
        self.path_list_widget = QListWidget()
        self.path_list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.path_list_widget.itemChanged.connect(self._on_path_item_changed)
        self.path_list_widget.itemDoubleClicked.connect(self.path_list_widget.editItem)
        layout.addWidget(self.path_list_label)
        layout.addWidget(self.path_list_widget)
        
        # File management buttons / 文件管理按钮部分
        button_layout = QHBoxLayout()
        self.browse_files_button = QPushButton()
        self.browse_files_button.clicked.connect(self._browse_files)
        self.browse_dir_button = QPushButton()
        self.browse_dir_button.clicked.connect(self._browse_directories)
        # Create the new "Select/Deselect All" button
        # 创建新的“勾选/取消全选”按钮
        self.select_all_button = QPushButton()
        self.select_all_button.clicked.connect(self._on_select_all_button_clicked)
        self.remove_button = QPushButton()
        self.remove_button.clicked.connect(self._on_remove_button_clicked)
        button_layout.addWidget(self.browse_files_button)
        button_layout.addWidget(self.browse_dir_button)
        button_layout.addStretch()
        # Add the new button to the layout, to the left of the remove button
        # 将新按钮添加到布局中，位于移除按钮的左侧
        button_layout.addWidget(self.select_all_button)
        button_layout.addWidget(self.remove_button)
        layout.addLayout(button_layout)
        
        # Dynamic parameter section / 动态参数部分
        self.dynamic_params_group = QWidget()
        self.dynamic_params_layout = QGridLayout(self.dynamic_params_group)
        self.dynamic_params_layout.setContentsMargins(0, 10, 0, 10)
        self.dynamic_params_layout.setSpacing(10)
        layout.addWidget(self.dynamic_params_group)

        # Separator line / 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Manual parameter section / 手动参数部分
        params_layout = QHBoxLayout()
        self.params_label = QLabel()
        self.script_params = QLineEdit()
        params_layout.addWidget(self.params_label)
        params_layout.addWidget(self.script_params)
        layout.addLayout(params_layout)
        
        # Run button / 执行按钮
        self.run_button = QPushButton()
        self.run_button.clicked.connect(self._run_script)
        self.run_button.setEnabled(False)
        self.run_button.setStyleSheet("QPushButton { font-weight: bold; font-size: 14pt; padding: 8px; min-height: 40px; }")
        layout.addWidget(self.run_button)
        # Progress Bar Section / 进度条部分
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
        
        # Output tabs / 输出选项卡
        self.output_label = QLabel()
        self.tabs = QTabWidget()
        self.console = QTextEdit() # The "Standard Output" tab / “标准输出”选项卡
        self.console.setReadOnly(True)
        self.console.setStyleSheet("background-color: #282c34; color: #abb2bf; font-family: Consolas, 'Courier New', monospace;")
        self.terminal = EnhancedTerminalWidget() # The "Enhanced Terminal" tab / “增强型终端”选项卡
        self.terminal.command_entered.connect(self._handle_terminal_input)
        self.tabs.addTab(self.console, "")
        self.tabs.addTab(self.terminal, "")
        layout.addWidget(self.output_label)
        layout.addWidget(self.tabs)
        
        return panel

    def _create_actions(self):
        """
        Creates global actions and shortcuts (e.g., Undo, Redo).
        创建全局操作和快捷键（例如，撤销、重做）。
        """
        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        self.undo_action.triggered.connect(self.undo)
        self.addAction(self.undo_action)
        
        self.redo_action = QAction("Redo", self)
        # Set platform-specific shortcut for Redo / 为重做设置特定于平台的快捷键
        if platform.system() == "Darwin": # macOS
            self.redo_action.setShortcut(QKeySequence("Ctrl+Shift+Z"))
        else: # Windows, Linux
            self.redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        self.redo_action.triggered.connect(self.redo)
        self.addAction(self.redo_action)

    def _update_ui_language(self):
        """
        Updates all text labels in the UI to the currently selected language.
        将UI中的所有文本标签更新为当前选择的语言。
        """
        lang = UI_TEXTS[self.current_lang]
        self.setWindowTitle(lang['window_title'])
        self.script_list_label.setText(lang['available_scripts'])
        self.script_info_label.setText(lang['script_info'])
        self.path_list_label.setText(lang['path_list_label'])
        self.run_button.setText(lang['run_button'])
        self.browse_files_button.setText(lang['browse_files_button'])
        self.browse_dir_button.setText(lang['browse_dir_button'])
        self.params_label.setText(lang['params_label'])
        self.script_params.setPlaceholderText(lang['params_placeholder'])
        self.output_label.setText(lang['output_label'])
        self.tabs.setTabText(0, lang['stdout_tab'])
        self.tabs.setTabText(1, lang['terminal_tab'])
        self.statusBar().showMessage(lang['status_ready'])
        self.switch_lang_button.setText(lang['switch_lang_button'])
        self.refresh_button.setToolTip(lang['refresh_button_tooltip'])
        self.terminal.set_language(self.current_lang)
        self._update_script_list_display()
        self._update_remove_button_state()
        self._update_script_info_display()
        self._update_select_all_button_state()
        # Update menu text if menus have been created
        # 如果菜单已创建，则更新菜单文本
        if hasattr(self, 'prefs_menu'):
            self.prefs_menu.setTitle(lang['prefs_menu'])
            self.theme_menu.setTitle(lang['theme_menu'])
            self.light_theme_action.setText(lang['theme_light'])
            self.dark_theme_action.setText(lang['theme_dark'])
            self.system_theme_action.setText(lang['theme_system'])
            
            
    def _toggle_language(self):
        """
        Switches the UI language between Chinese and English.
        在中英文之间切换UI语言。
        """
        self.current_lang = 'en' if self.current_lang == 'zh' else 'zh'
        self._update_ui_language()

    def _refresh_scripts(self):
        """
        Reloads the list of available scripts from the scripts directory.
        从脚本目录重新加载可用脚本列表。
        """
        self.script_list.clear()
        self.script_info.clear()
        self.current_script_path = None
        self.run_button.setEnabled(False)
        self._clear_dynamic_params_ui()
        self.load_scripts()
        self.statusBar().showMessage(UI_TEXTS[self.current_lang]['status_ready'], 2000)

    def load_scripts(self):
        """
        Scans the scripts directory, extracts display names, and populates the script list.
        扫描脚本目录，提取显示名称，并填充脚本列表。
        """
        if not os.path.exists(self.scripts_dir):
            os.makedirs(self.scripts_dir)
            return
            
        for script_path in sorted(glob.glob(os.path.join(self.scripts_dir, "*.py"))):
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                docstring = self._extract_docstring(content)
                
                # Extract display names for both languages from the docstring.
                # 从文档字符串中为两种语言提取显示名称。
                zh_name_match = re.search(r'\[display-name-zh\](.*?)\n', docstring)
                en_name_match = re.search(r'\[display-name-en\](.*?)\n', docstring)
                
                # Use extracted names if found, otherwise fall back to the filename.
                # 如果找到则使用提取的名称，否则回退到使用文件名。
                zh_name = zh_name_match.group(1).strip() if zh_name_match else os.path.basename(script_path)
                en_name = en_name_match.group(1).strip() if en_name_match else os.path.basename(script_path)

                item = QListWidgetItem() # Create an empty item first / 首先创建一个空项目
                
                # Store all necessary data in the item. The text will be set by _update_ui_language.
                # 将所有必要的数据存储在项目中。其显示的文本将由 _update_ui_language 设置。
                item.setData(Qt.ItemDataRole.UserRole, {
                    'path': script_path,
                    'name_zh': zh_name,
                    'name_en': en_name
                })
                
                self.script_list.addItem(item)
            except Exception as e:
                print(f"Error loading script {script_path}: {e}")
        
        # After loading, update the display text for all items based on the current language.
        # 加载后，根据当前语言更新所有项目的显示文本。
        self._update_script_list_display()
    def _update_script_list_display(self):
        """
        Updates the display text of all items in the script list based on the current UI language.
        根据当前UI语言，更新脚本列表中所有项目的显示文本。
        """
        for i in range(self.script_list.count()):
            item = self.script_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            # Ensure data exists before trying to access it
            # 确保在访问数据前其存在
            if data:
                display_name = data['name_zh'] if self.current_lang == 'zh' else data['name_en']
                item.setText(display_name)
    
    def _show_script_context_menu(self, position):
        """
        Creates and displays a context menu when a script item is right-clicked.
        当脚本项被右键点击时，创建并显示上下文菜单。
        """
        # Get the item under the cursor
        # 获取光标下的项目
        item = self.script_list.itemAt(position)
        if not item:
            return

        # Retrieve the script's data
        # 检索脚本的数据
        script_data = item.data(Qt.ItemDataRole.UserRole)
        script_path = script_data.get('path')
        if not script_path:
            return
            
        script_filename = os.path.basename(script_path)
        lang = UI_TEXTS[self.current_lang]

        # Create the context menu
        # 创建上下文菜单
        context_menu = QMenu(self)

        # Add the filename as a disabled title item
        # 将文件名作为禁用的标题项添加
        filename_action = QAction(script_filename, self)
        filename_action.setEnabled(False)
        context_menu.addAction(filename_action)
        
        context_menu.addSeparator()

        # Add the "Show in Folder" action
        # 添加“在文件夹中显示”动作
        show_action = QAction("在文件夹中显示", self)
        show_action.triggered.connect(lambda: self._open_in_file_explorer(script_path))
        context_menu.addAction(show_action)

        # Show the menu at the cursor's global position
        # 在光标的全局位置显示菜单
        context_menu.exec(self.script_list.mapToGlobal(position))  
    def _open_in_file_explorer(self, path):
        """
        Opens the system's file explorer and highlights the given file.
        This function is platform-aware.
        打开系统的文件资源管理器并高亮给定的文件。
        此函数能感知平台差异。
        """
        if not os.path.exists(path):
            return

        system = platform.system()
        try:
            if system == "Windows":
                # The /select switch selects and highlights the item.
                # /select 开关会选中并高亮该项。
                subprocess.run(['explorer', '/select,', os.path.normpath(path)])
            elif system == "Darwin": # macOS
                # The -R switch reveals the file in Finder.
                # -R 开关会在Finder中显示该文件。
                subprocess.run(['open', '-R', path])
            else: # Linux and other Unix-like systems
                # Highlighting is not universally supported, so we just open the directory.
                # 高亮功能并非被普遍支持，因此我们只打开其所在的目录。
                dir_path = os.path.dirname(path)
                subprocess.run(['xdg-open', dir_path])
        except Exception as e:
            print(f"Error opening file explorer: {e}")
            # Fallback for safety: just print the path
            # 安全回退：仅打印路径
            QMessageBox.information(self, "File Path", f"Could not open explorer.\nThe file is located at:\n{path}")

    def _on_script_selected(self, item):
        """
        Handles the event when a script is selected from the list.
        处理从列表中选择脚本的事件。
        """
        script_data = item.data(Qt.ItemDataRole.UserRole)
        self.current_script_path = script_data['path']
        try:
            with open(self.current_script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.current_script_docstring = self._extract_docstring(content)
            self.run_button.setEnabled(True)
            # Parse the script for argparse parameters to build the dynamic UI
            # 解析脚本的argparse参数以构建动态UI
            params = self._parse_script_for_params(self.current_script_path)
            self._update_dynamic_params_ui(params)
        except Exception as e:
            self.current_script_docstring = f"{UI_TEXTS[self.current_lang]['info_read_error']}{e}"
            self.run_button.setEnabled(False)
            self._clear_dynamic_params_ui()
        self._update_script_info_display()
    
    def _parse_script_for_params(self, script_path):
        """
        Runs the script with '--help' to capture and parse its argparse parameters.
        This version uses a robust regex to differentiate between flags, value inputs, and choices
        based on the presence of a metavar or a choice list.
        使用'--help'运行脚本以捕获并解析其argparse参数。
        此版本使用健壮的正则表达式，根据元变量或选项列表的存在来区分标志、值输入和选项。
        """
        params = []
        try:
            result = subprocess.run(
                [sys.executable, script_path, '--help'], 
                capture_output=True, text=True, encoding='utf-8', errors='replace'
            )
            help_text = result.stdout
            
            # This new regex is designed to capture the key parts of an argparse argument definition.
            # 这个新正则表达式旨在捕获argparse参数定义的关键部分。
            # Group 1: Optional short flag (e.g., '-v, ')
            # Group 2: The long flag name (e.g., 'verbose')
            # Group 3: Optional metavar, indicating a value is expected (e.g., 'GROUP_SIZE')
            # Group 4: Optional choices list (e.g., 'name,date')
            # Group 5: Optional default value
            pattern = re.compile(
                r"^\s+(-[a-zA-Z],\s+)?--([a-zA-Z0-9_-]+)\s*([A-Z_]+)?.*?(?:\{([^}]+)\})?.*?(?:\(default:\s*([^)]+)\))?",
                re.MULTILINE | re.IGNORECASE
            )

            for match in pattern.finditer(help_text):
                name = f"--{match.group(2)}"
                # Ignore internal flags
                # 忽略内部标志
                if name in ['--gui-mode', '--lang']: continue

                metavar = match.group(3)
                choices = match.group(4)
                default_val = match.group(5)

                param_info = {'name': name}

                if choices:
                    # If it has choices, it's a ComboBox.
                    # 如果有选项，它就是下拉框。
                    param_info['type'] = 'choice'
                    param_info['choices'] = [c.strip() for c in choices.split(',')]
                elif metavar:
                    # If it has a metavar but no choices, it's a LineEdit (value input).
                    # 如果有元变量但没有选项，它就是输入框（值输入）。
                    param_info['type'] = 'value'
                else:
                    # Otherwise, it's a CheckBox (flag).
                    # 否则，它就是复选框（标志）。
                    param_info['type'] = 'flag'
                
                if default_val:
                    param_info['default'] = default_val.strip()
                
                params.append(param_info)

        except Exception as e:
            print(f"Could not parse parameters for {os.path.basename(script_path)}: {e}")
        return params

    def _clear_dynamic_params_ui(self):
        """
        Removes all dynamically generated parameter widgets from the layout.
        从布局中移除所有动态生成的参数小部件。
        """
        while self.dynamic_params_layout.count():
            item = self.dynamic_params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.dynamic_param_widgets = []
        self.dynamic_params_group.setVisible(False)

    def _update_dynamic_params_ui(self, params):
        """
        Creates and displays UI widgets based on parsed parameters.
        This version now supports internationalized display names for choices
        by parsing a special format in the help string: [display: value=zh_name,en_name].
        根据解析出的参数创建并显示UI小部件。
        此版本现在通过解析帮助字符串中的特殊格式 [display: value=zh_name,en_name] 来支持选项的国际化显示名称。
        """
        self._clear_dynamic_params_ui()
        if not params: return

        params.sort(key=lambda x: x['name'])

        row, col, max_rows = 0, 0, 3
        for param in params:
            name = param['name']
            p_type = param.get('type', 'flag')
            p_default = param.get('default')
            # (NEW) Get the full help text for parsing display names.
            # (新) 获取完整的帮助文本以解析显示名称。
            p_help = param.get('help', '')

            widget = None
            if p_type == 'choice':
                label = QLabel(f"{name}:")
                combo = QComboBox()
                
                # (NEW) Logic to parse display names from help text.
                # (新) 从帮助文本中解析显示名称的逻辑。
                display_map = {}
                display_match = re.search(r'\[display:\s*(.*?)\]', p_help)
                if display_match:
                    # e.g., "asc=升序,Ascending | desc=降序,Descending"
                    entries = display_match.group(1).split('|')
                    for entry in entries:
                        try:
                            value, names = entry.split('=', 1)
                            zh_name, en_name = names.split(',', 1)
                            display_map[value.strip()] = {'zh': zh_name.strip(), 'en': en_name.strip()}
                        except ValueError:
                            continue # Ignore malformed entries

                # Populate the ComboBox
                for choice_value in param['choices']:
                    display_name = choice_value # Default to the internal value
                    if choice_value in display_map:
                        display_name = display_map[choice_value].get(self.current_lang, choice_value)
                    
                    # Add the display name to the UI, but store the internal value in UserRole.
                    # 将显示名称添加到UI，但将内部值存储在UserRole中。
                    combo.addItem(display_name, userData=choice_value)

                # Set the default value based on the internal value, not the display name.
                # 根据内部值而不是显示名称来设置默认值。
                if p_default:
                    index = combo.findData(p_default)
                    if index != -1:
                        combo.setCurrentIndex(index)

                widget = combo
                self.dynamic_params_layout.addWidget(label, row, col * 2)
                self.dynamic_params_layout.addWidget(widget, row, col * 2 + 1)

            elif p_type == 'value':
                label = QLabel(f"{name}:")
                line_edit = QLineEdit()
                if p_default: line_edit.setText(p_default)
                widget = line_edit
                self.dynamic_params_layout.addWidget(label, row, col * 2)
                self.dynamic_params_layout.addWidget(widget, row, col * 2 + 1)
            
            else: # 'flag' type
                checkbox = QCheckBox(name)
                if p_default: checkbox.setChecked(True)
                widget = checkbox
                self.dynamic_params_layout.addWidget(widget, row, col * 2, 1, 2)

            if widget:
                widget.setToolTip(p_help.split('[display:')[0].strip()) # Use help text before our tag as tooltip
                widget.setProperty('param_name', name)
                widget.setProperty('param_type', p_type)
                self.dynamic_param_widgets.append(widget)

            row += 1
            if row >= max_rows:
                row = 0
                col += 1
        
        self.dynamic_params_group.setVisible(True)

    def _update_script_info_display(self):
        """
        Extracts and displays the relevant part of the script's docstring based on the current UI language,
        using '~~~' as the primary language separator.
        根据当前的UI语言，提取并显示脚本文档字符串的相关部分。
        使用 '~~~' 作为主要的语言分隔符。
        """
        doc = self.current_script_docstring
        display_text = doc if doc else UI_TEXTS[self.current_lang]['info_no_docstring']
        
        # New logic: Use '~~~' to split the docstring into language blocks.
        # 新逻辑: 使用 '~~~' 将文档字符串分割为语言块。
        if '~~~' in doc:
            try:
                # Assume the first part is Chinese, the second is English.
                # 假设第一部分是中文，第二部分是英文。
                parts = doc.split('~~~', 1)
                chinese_doc = parts[0]
                english_doc = parts[1] if len(parts) > 1 else ''
                
                # Select the correct block based on the current language.
                # 根据当前语言选择正确的块。
                selected_doc = chinese_doc if self.current_lang == 'zh' else english_doc
                
                # Remove the initial display name tags from the selected block for clean display.
                # 从选定的块中移除开头的显示名称标签，以实现干净的显示。
                display_text = re.sub(r'\[display-name-..\](.*?)\n', '', selected_doc, count=2).strip()

            except Exception as e:
                # If parsing fails, fall back to showing the whole docstring.
                # 如果解析失败，则回退到显示整个文档字符串。
                print(f"Error parsing docstring with '~~~': {e}")
                display_text = doc

        self.script_info.setText(display_text)
    def _extract_docstring(self, content):
        """
        Extracts the module-level docstring from a script's content using regex.
        使用正则表达式从脚本内容中提取模块级别的文档字符串。
        """
        match = re.search(r'^\s*("""(.*?)"""|\'\'\'(.*?)\'\'\')', content, re.DOTALL | re.MULTILINE)
        return (match.group(2) or match.group(3)).strip() if match else ""

    def dragEnterEvent(self, event):
        """
        Accepts drag-and-drop events if they contain file URLs.
        如果拖放事件包含文件URL，则接受该事件。
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """
        Handles dropped files by adding them to the path list.
        通过将文件添加到路径列表来处理拖放的文件。
        """
        self._save_state_for_undo()
        for url in event.mimeData().urls():
            self._add_path_to_list(url.toLocalFile())
        self._update_remove_button_state()

    def _add_path_to_list(self, path):
        """
        Adds a single path to the QListWidget with checkbox and editable flags.
        将单个路径添加到QListWidget，并带有复选框和可编辑标志。
        """
        if os.path.exists(path):
            item = QListWidgetItem(path)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEditable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.path_list_widget.addItem(item)
    
    def _browse_files(self):
        """
        Opens a file dialog to add multiple files.
        打开文件对话框以添加多个文件。
        """
        self._save_state_for_undo()
        files, _ = QFileDialog.getOpenFileNames(self, UI_TEXTS[self.current_lang]['browse_files_button'])
        if files:
            for file in files:
                self._add_path_to_list(file)
            self._update_remove_button_state()

    def _browse_directories(self):
        """
        Opens a directory dialog to add multiple directories.
        打开目录对话框以添加多个目录。
        """
        self._save_state_for_undo()
        dialog = QFileDialog(self, UI_TEXTS[self.current_lang]['browse_dir_button'])
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        if dialog.exec():
            directories = dialog.selectedFiles()
            if directories:
                for directory in directories:
                    self._add_path_to_list(directory)
                self._update_remove_button_state()

    def _on_path_item_changed(self, item):
        """
        Saves state for undo when a path item's text or check state changes.
        当路径项的文本或勾选状态更改时，保存状态以供撤销。
        """
        self._save_state_for_undo()
        self._update_remove_button_state()
        self._update_select_all_button_state()



    def _on_remove_button_clicked(self):
        """
        Removes the union of all selected and checked items. If none are marked, clears the entire list.
        移除所有被选中和被勾选项目的并集。如果没有任何项目被标记，则清空整个列表。
        """
        self._save_state_for_undo()

        # QListWidgetItem is not hashable, so we cannot use a set directly.
        # We must manually create a list of unique items.
        # QListWidgetItem 不可哈希，所以我们不能直接使用set。
        # 我们必须手动创建一个包含唯一项的列表。
        selected_items = self.path_list_widget.selectedItems()
        checked_items = self._get_checked_items()
        
        combined_list = selected_items + checked_items
        items_to_delete = []
        for item in combined_list:
            if item not in items_to_delete:
                items_to_delete.append(item)

        if items_to_delete:
            # If any items are marked, remove them.
            # 如果有任何项目被标记，则移除它们。
            for item in items_to_delete: # Iterating over the new unique list
                self.path_list_widget.takeItem(self.path_list_widget.row(item))
        else:
            # If no items are marked, clear the entire list.
            # 如果没有任何项目被标记，则清空整个列表。
            self.path_list_widget.clear()

        # Update the state of related buttons.
        # 更新相关按钮的状态。
        self._update_remove_button_state()
        self._update_select_all_button_state()
    
    def _get_checked_items(self):
        """
        Returns a list of all checked items in the path list.
        返回路径列表中所有被勾选的项目。
        """
        return [self.path_list_widget.item(i) for i in range(self.path_list_widget.count()) if self.path_list_widget.item(i).checkState() == Qt.CheckState.Checked]

    def _update_remove_button_state(self):
        """
        Updates the remove button text. It shows "Remove Selected" if any item is selected OR checked.
        更新移除按钮的文本。如果任何项目被选中或被勾选，按钮将显示“移除选中项”。
        """
        lang = UI_TEXTS[self.current_lang]

        # Check if any item is either selected (highlighted) or checked.
        # 检查是否有任何项目被选中（高亮）或被勾选。
        is_any_item_marked = bool(self.path_list_widget.selectedItems() or self._get_checked_items())

        if is_any_item_marked:
            # The user has marked items for action.
            # 用户已经标记了要操作的项目。
            self.remove_button.setText(lang['remove_selected_button'])
        else:
            # No items are marked, the button's action will be to clear all.
            # 没有任何项目被标记，按钮的操作将是清空所有。
            self.remove_button.setText(lang['remove_all_button'])
            
    def _update_select_all_button_state(self):
        """
        Updates the text of the "Select/Deselect All" button based on the current check state.
        根据当前的勾选状态，更新“勾选/取消全选”按钮的文本。
        """
        lang = UI_TEXTS[self.current_lang]
        # If any item is checked, the button should offer to "Deselect All".
        # 如果有任何一项被勾选，按钮应提供“取消全选”功能。
        if any(self._get_checked_items()):
            self.select_all_button.setText(lang['deselect_all'])
        # Otherwise, it should offer to "Select All".
        # 否则，它应提供“勾选全部”功能。
        else:
            self.select_all_button.setText(lang['select_all'])
            
    def _on_select_all_button_clicked(self):
        """
        Handles the click event for the "Select/Deselect All" button.
        处理“勾选/取消全选”按钮的点击事件。
        """
        self._save_state_for_undo()
        
        # Determine the action based on whether any items are currently checked.
        # 根据当前是否有项目被勾选来决定执行何种操作。
        is_anything_checked = any(self._get_checked_items())
        
        # The new state to be applied to all items.
        # 将要应用到所有项目的新状态。
        new_state = Qt.CheckState.Unchecked if is_anything_checked else Qt.CheckState.Checked
        
        for i in range(self.path_list_widget.count()):
            self.path_list_widget.item(i).setCheckState(new_state)
        
        # After the action, update the button's text for the next click.
        # 操作完成后，更新按钮的文本以备下次点击。
        self._update_select_all_button_state()
        
    def _save_state_for_undo(self):
        """
        Saves the current state of the path list to the undo stack.
        将路径列表的当前状态保存到撤销堆栈。
        """
        state = [{'text': self.path_list_widget.item(i).text(), 'checked': self.path_list_widget.item(i).checkState() == Qt.CheckState.Checked} for i in range(self.path_list_widget.count())]
        if not self.undo_stack or state != self.undo_stack[-1]:
            self.undo_stack.append(state)
            self.redo_stack.clear()

    def _restore_state(self, state):
        """
        Restores the path list to a previous state from the undo/redo stack.
        从撤销/重做堆栈中将路径列表恢复到先前的状态。
        """
        self.path_list_widget.clear()
        for item_data in state:
            item = QListWidgetItem(item_data['text'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEditable)
            item.setCheckState(Qt.CheckState.Checked if item_data['checked'] else Qt.CheckState.Unchecked)
            self.path_list_widget.addItem(item)
        self._update_remove_button_state()
        self._update_select_all_button_state()

    def undo(self):
        """
        Performs the undo action.
        执行撤销操作。
        """
        if len(self.undo_stack) > 1:
            self.redo_stack.append(self.undo_stack.pop())
            self._restore_state(self.undo_stack[-1])
        else:
            self.statusBar().showMessage(UI_TEXTS[self.current_lang]['undo_stack_empty'], 2000)

    def redo(self):
        """
        Performs the redo action.
        执行重做操作。
        """
        if self.redo_stack:
            state_to_restore = self.redo_stack.pop()
            self.undo_stack.append(state_to_restore)
            self._restore_state(state_to_restore)
        else:
            self.statusBar().showMessage(UI_TEXTS[self.current_lang]['redo_stack_empty'], 2000)


    def keyPressEvent(self, event: QKeyEvent):
        """
        Handles global key presses for shortcuts.
        处理快捷键的全局按键事件。
        """
        # Esc to uncheck all items / Esc键取消所有勾选
        if event.key() == Qt.Key.Key_Escape:
            changed = False
            for item in self._get_checked_items():
                item.setCheckState(Qt.CheckState.Unchecked)
                changed = True
            if changed: 
                self._save_state_for_undo()
                self._update_select_all_button_state()
            return

        # Delete/Backspace to remove selected and/or checked items
        # Delete/Backspace键移除被选中和/或被勾选的项目
        if self.path_list_widget.hasFocus() and (event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace):
            # Get the union of selected and checked items manually, because QListWidgetItem is not hashable.
            # 手动获取选中和勾选项目的并集，因为QListWidgetItem不可哈希。
            selected_items = self.path_list_widget.selectedItems()
            checked_items = self._get_checked_items()

            combined_list = selected_items + checked_items
            items_to_delete = []
            for item in combined_list:
                if item not in items_to_delete:
                    items_to_delete.append(item)

            if items_to_delete:
                self._save_state_for_undo()
                for item in items_to_delete:
                    self.path_list_widget.takeItem(self.path_list_widget.row(item))
                
                # Update button states after deletion.
                # 删除后更新按钮状态。
                self._update_remove_button_state()
                self._update_select_all_button_state()
            return
            
        super().keyPressEvent(event)
    def _append_to_console(self, text):
        """
        Appends text to the "Standard Output" tab.
        将文本追加到“标准输出”选项卡。
        """
        cursor = self.console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.console.setTextCursor(cursor)
        self.console.insertPlainText(text)
        self.console.ensureCursorVisible()

    def _update_progress_display(self, current_float, max_float, description):
        """
        Updates the progress bar by mapping float progress values to an integer scale.
        通过将浮点进度值映射到整数刻度来更新进度条。
        """
        if self.progress_bar.isHidden():
            self.progress_bar.show()
            self.progress_label.show()
        
        # 为了平滑显示，我们将浮点数乘以100转换为整数
        # 例如：(2.5 / 41.58) -> (250 / 4158)
        max_int = int(max_float * 100)
        current_int = int(current_float * 100)
        
        self.progress_bar.setRange(0, max_int)
        self.progress_bar.setValue(current_int)
        self.progress_label.setText(description) 
               
    def _run_script(self):
        """
        Assembles the command and starts the ScriptExecutor thread.
        It now intelligently selects paths based on checkbox states.
        组装命令并启动ScriptExecutor线程。
        现在会根据复选框状态智能选择路径。
        """
        lang = UI_TEXTS[self.current_lang]
        if not self.current_script_path:
            QMessageBox.warning(self, lang['warn_select_script_title'], lang['warn_select_script_msg']); return

        # First, get the list of all checked items.
        # 首先，获取所有被勾选项目的列表。
        checked_items = self._get_checked_items()

        paths = []
        if checked_items:
            # If there are checked items, process ONLY those.
            # 如果有项目被勾选，则只处理这些项目。
            paths = [item.text() for item in checked_items]
        else:
            # If no items are checked, process ALL items in the list.
            # 如果没有项目被勾选，则处理列表中的所有项目。
            paths = [self.path_list_widget.item(i).text() for i in range(self.path_list_widget.count())]

        if not paths:
            QMessageBox.warning(self, lang['warn_no_paths_title'], lang['warn_no_paths_msg']); return
        
        # Build the argument list, starting with the GUI flag
        # 构建参数列表，以GUI标志开头
        arguments = ["--gui-mode"]
        # Pass the current language to the script
        # 将当前语言传递给脚本
        arguments.extend(["--lang", self.current_lang])
        # Add arguments from dynamic widgets
        # 从动态小部件添加参数
        for widget in self.dynamic_param_widgets:
            p_name = widget.property('param_name')
            p_type = widget.property('param_type')
            if p_type == 'flag' and widget.isChecked():
                arguments.append(p_name)
            elif p_type == 'choice':
                # (MODIFIED) Get the internal value from userData.
                # (已修改) 从userData获取内部值。
                internal_value = widget.currentData()
                arguments.extend([p_name, internal_value])
            elif p_type == 'value':
                value = widget.text()
                if value: arguments.extend([p_name, value])

        # Add arguments from the manual input box
        # 从手动输入框添加参数
        user_params = self.script_params.text().strip()
        if user_params:
            arguments.extend(shlex.split(user_params))
        
        # Add the file/folder paths at the end
        # 在末尾添加文件/文件夹路径
        arguments.extend(paths)
        
        command = [self.current_script_path] + arguments
        
        self.console.clear()
        self.run_button.setEnabled(False)
        self.statusBar().showMessage(lang['status_running'])
        self.tabs.setCurrentWidget(self.terminal) # Switch to terminal tab on run / 运行时切换到终端选项卡
        self.progress_bar.hide()
        self.progress_label.hide()
        self.progress_bar.setValue(0)
        self.progress_label.setText("...")
        
        # Create and start the executor thread
        # 创建并启动执行器线程
        self.script_executor = ScriptExecutor(command)
        self.script_executor.output_updated.connect(self._append_to_console) # Also send to simple console / 也发送到简单控制台
        self.script_executor.output_updated.connect(self.terminal.append_output) # Send to enhanced terminal / 发送到增强型终端
        self.script_executor.progress_updated.connect(self._update_progress_display)
        self.script_executor.process_finished.connect(self._on_script_finished)
        self.script_executor.start()

    def _on_script_finished(self, exit_code):
        """
        Handles cleanup and UI updates after the script finishes.
        处理脚本完成后的清理和UI更新。
        """
        lang = UI_TEXTS[self.current_lang]
        msg = lang['script_finished_msg'].format(exit_code=exit_code)
        self._append_to_console(msg)
        self.terminal.append_output(msg)
        self.run_button.setEnabled(True)
        self.statusBar().showMessage(lang['status_ready'])
        self.progress_bar.hide()
        self.progress_label.hide()
        self.script_executor = None

    def _handle_terminal_input(self, text):
        """
        Directs user input to the running script or the system shell.
        将用户输入定向到正在运行的脚本或系统shell。
        """
        if self.script_executor and self.script_executor.isRunning():
            self.script_executor.send_input(text)
        else:
            self._execute_system_command(text)

    def _execute_system_command(self, command_str):
        """
        Executes a system command in the terminal if no script is running.
        如果没有脚本正在运行，则在终端中执行系统命令。
        """
        # (NEW) Handle empty Enter press when no script is running
        # (新) 处理无脚本运行时按下的空Enter
        if not command_str.strip():
            self.terminal.append_output(f"\n{self.terminal.prompt_label.text()} ")
            return
    
        if command_str.lower() == 'exit':
            self.close()
            return
        try:
            cmd_parts = shlex.split(command_str)
        except ValueError as e:
            self.terminal.append_output(f"Error parsing command: {e}\n")
            return
        if not cmd_parts:
            return
        
        # Handle 'cd' command internally as it affects the GUI's process
        # 在内部处理'cd'命令，因为它会影响GUI的进程
        if cmd_parts[0].lower() == 'cd':
            if len(cmd_parts) > 1:
                try:
                    os.chdir(cmd_parts[1])
                    self.terminal._update_prompt()
                except FileNotFoundError:
                    self.terminal.append_output(f"Error: Directory does not exist: {cmd_parts[1]}\n")
            else:
                self.terminal.append_output("Error: Please specify a directory\n")
            return
            
        self.system_process = QProcess()
        self.system_process.readyReadStandardOutput.connect(self._handle_system_output)
        self.system_process.finished.connect(self._on_system_command_finished)
        self.system_process.start(cmd_parts[0], cmd_parts[1:])
        if not self.system_process.waitForStarted():
            self.terminal.append_output(f"Error starting command: {cmd_parts[0]}\n")

    def _handle_system_output(self):
        """
        Handles output from the system command process.
        处理来自系统命令进程的输出。
        """
        if self.system_process:
            output = self.system_process.readAllStandardOutput().data()
            try:
                decoded_output = output.decode('utf-8')
            except UnicodeDecodeError:
                decoded_output = output.decode('gbk', errors='replace')
            self.terminal.append_output(decoded_output)

    def _on_system_command_finished(self, exit_code):
        """
        Handles cleanup after a system command finishes.
        处理系统命令完成后的清理工作。
        """
        self.terminal.append_output(f"\nCommand finished with exit code: {exit_code}\n")
        self.system_process = None
        self.terminal._update_prompt()

    def closeEvent(self, event):
        """
        Ensures all child processes are terminated when the GUI is closed.
        确保在关闭GUI时所有子进程都被终止。
        """
        if self.script_executor and self.script_executor.isRunning():
            self.script_executor.terminate()
        if self.system_process and self.system_process.state() == QProcess.ProcessState.Running:
            self.system_process.terminate()
        event.accept()
        
    

def _get_best_font_name():
    """
    Selects a suitable default font based on the operating system.
    根据操作系统选择合适的默认字体。
    """
    system = platform.system()
    if system == "Windows": return "Microsoft YaHei"
    elif system == "Darwin": return "PingFang SC"
    else: return "WenQuanYi Micro Hei"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont(_get_best_font_name(), 10))
    scripts_directory = resource_path("scripts")
    if not os.path.exists(scripts_directory):
        os.makedirs(scripts_directory)
    window = ScriptGUI(scripts_directory)
    window.show()
    sys.exit(app.exec())
    
    