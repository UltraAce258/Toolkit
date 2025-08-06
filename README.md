# 奥创王牌工具箱 (UltraAce Toolkit)

**(For English documentation, please scroll down)**

[![Author](https://img.shields.io/badge/作者-UltraAce258-blue.svg)](https://github.com/UltraAce258)
[![Python](https://img.shields.io/badge/Python-3.8+-brightgreen.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/UI-PyQt6-orange.svg)](https://riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/许可-MIT-green.svg)](https://opensource.org/licenses/MIT)

---

奥创王牌工具箱的设计初衷，是将各类实用但需要通过命令行运行的Python自动化脚本，封装进一个统一、美观、且极易上手的图形用户界面（GUI）中。用户无需记忆任何复杂的命令，只需通过简单的点击、拖拽和填写，即可轻松完成批量文件处理、数据转换、代码分析等各类任务。

它的核心理念是 **“一次编写，处处运行，人人可用”**。

## ✨ 核心特性

*   **高度可扩展**: 只需将符合规范的Python脚本放入`scripts`文件夹，工具箱即可自动识别并加载，无需修改任何主程序代码。
*   **用户友好**: 直观的界面设计，支持文件/文件夹拖放、多选、复选框批量操作、撤销/重做等现代化功能。
*   **动态参数界面**: 能自动解析脚本的`argparse`参数，并为之生成对应的复选框、下拉菜单和输入框，告别手动拼写参数。
*   **双语支持**: 界面和脚本输出均支持中/英双语切换，为不同语言用户提供一致的体验。
*   **内置增强型终端**: 不仅能实时显示脚本的输出日志，还能在脚本未运行时作为标准的系统命令行工具使用。
*   **个性化主题**: 支持浅色、深色及跟随系统的显示模式，关爱你的眼睛。
*   **详尽的交互反馈**: 无论是代码注释、界面提示还是终端输出，我们都力求详尽、清晰，让用户和开发者随时了解程序动态。

## ⚠️ Alpha版本警告

**请注意，本工具箱目前处于早期的Alpha开发阶段。**

这意味着它可能包含未知的错误（Bug），且部分功能尚不完善。我们非常欢迎并感谢您通过GitHub Issues提交错误报告、提出功能建议，或通过Pull Request直接贡献代码。您的任何反馈与贡献都对项目的成长至关重要！

## 🚀 快速上手指南

对于初次接触本工具的小白用户，请严格遵循以下步骤，这能保证你顺利地第一次运行本工具。

### 第一步：环境准备

确保你的电脑已经安装了 **Python 3.8** 或更高版本。你可以在命令行（终端）中输入以下命令来检查：

```bash
python --version
# 或者
python3 --version
```

如果未安装，请前往 [Python官方网站](https://www.python.org/downloads/) 下载并安装。

### 第二步：下载核心文件

1.  从本仓库下载最重要的两个部分：
    *   主程序文件: `main.py`
    *   任务脚本文件夹: `scripts` (里面可能包含一些示例脚本，如`文档页数统计器.py`)

2.  将它们放在你电脑的任意位置，但**必须保持以下文件夹结构**：

    ```
    你的工作区/
    ├── main.py          (主程序)
    └── scripts/         (存放所有任务脚本的文件夹)
        └── 任务脚本1.py
        └── 任务脚本2.py
        ...
    ```

    > **警告**: `main.py` 和 `scripts` 文件夹必须位于同一级目录，否则程序将无法找到任何任务脚本！

### 第三步：运行工具箱

打开你的命令行（终端），进入 `main.py` 所在的目录，然后运行它：

```bash
cd /path/to/你的工作区/
python main.py
```

如果一切顺利，你应该能看到“奥创王牌工具箱”的主界面了。
#### **方法二：使用IDE（如 VS Code）运行**

如果你更习惯使用代码编辑器，这也是一个非常推荐的方式：

1.  在你的IDE中，选择 **“打开文件夹”**，然后打开包含`main.py`的整个工作区文件夹。
2.  在IDE的文件浏览器中，单击打开`main.py`文件。
3.  **关键步骤**: 找到并点击IDE的“运行”按钮。请务必选择 **“运行Python文件”** 或 **“以Python文件形式调试”** 选项。

> **警告**: 不要使用“运行选定代码”(Run Code)功能，因为它可能无法正确启动GUI。在VS Code中，这通常指右上角的绿色三角形“播放”按钮。
  
### 第四步：执行你的第一个任务

1.  **选择脚本**: 在程序窗口左侧的“可用脚本”列表中，点击一个你想运行的脚本（例如“文档页数统计器”）。
2.  **添加文件**: 直接从你的电脑桌面或文件夹中，将一个或多个文件拖拽到程序窗口中。
3.  **执行**: 点击窗口右下角那个最大、最显眼的蓝色按钮“执行脚本”。
4.  **查看结果**: 程序会自动切换到“增强型终端”选项卡，你可以在这里看到脚本运行的全部过程和最终结果。

恭喜你！你已经成功地使用了奥创王牌工具箱。

## 🔧 GUI 详细使用与配置

工具箱的每一个功能都为提升你的效率而设计。了解它们，能让你事半功倍。

### 主界面布局

*   **左侧面板**: 用于选择和了解脚本。
    *   **可用脚本列表**: 显示`scripts`文件夹中所有可用的任务。右键点击脚本项，可以选择“在文件夹中显示”，快速定位到脚本源文件。
    *   **脚本介绍**: 显示当前选中脚本的详细说明文档。
*   **右侧面板**: 核心操作区域，用于配置任务和查看结果。

### 交互功能详解

#### 文件/文件夹列表

*   **添加**: 支持 **拖放** 或点击 **“添加文件/文件夹”** 按钮。
*   **编辑**: **双击** 列表中的任意一项，可以直接修改其路径。
*   **标记**: 每一项前面都有一个 **复选框(Checkbox)**。这是本工具箱最关键的批量处理机制：
    *   **当有任意项被勾选时**: 点击“执行脚本”，将**只处理被勾选**的项。
    *   **当没有任何项被勾选时**: 点击“执行脚本”，将**处理列表中的所有项**。
*   **移除**:
    *   选中（高亮）或勾选任意项后，点击“移除选中项”按钮可删除它们。
    *   在没有任何项被选中或勾选时，该按钮会变为“清空所有”，点击可清空整个列表。
    *   选中列表后，按 `Delete` 或 `Backspace` 键也能快速移除。
*   **全选/取消全选**:
    *   点击“勾选全部”按钮可以一键勾选列表中的所有项。
    *   此时按钮会变为“取消选择”，再次点击可取消所有勾选。
    *   按 `Esc` 键可以快速取消所有勾选。

#### 参数配置

*   **可视化参数**: 当你选择一个脚本后，这里会自动出现为该脚本定制的配置选项。你无需知道它们背后对应的命令行参数是什么，只需像填写问卷一样操作即可。
*   **手动参数**: 如果你需要输入一些临时的、或者脚本并未提供可视化界面的高级参数，可以在这里手动填写。格式与标准命令行完全一致（例如 `-v --output "my file.txt"`）。

#### 输出区域

*   **标准输出**: 一个简洁的、只显示脚本最终输出的文本框。
*   **增强型终端**:
    *   **实时日志**: 完整显示脚本执行的每一步，包括依赖安装、调试信息等。
    *   **交互式输入**: 如果脚本在运行过程中需要你输入“yes/no”之类的确认信息，你可以在终端下方的输入行中输入并按回车。
    *   **系统命令**: 当没有脚本在执行时，这里就是一个标准的系统终端。你可以使用`cd`, `ls`, `dir`, `pip`等常用命令。输入`exit`可关闭程序。

### 菜单栏配置

*   **偏好设置 -> 主题**: 在这里可以切换“浅色模式”、“深色模式”或“跟随系统”。你的选择会被自动保存，下次启动时无需重新设置。

---

## ✍️ 任务脚本开发指南

想为你自己开发一个专属的任务脚本吗？非常简单！遵循以下“黄金法则”，你就能创造出与本工具箱完美集成的强大工具。

### 第一步：文件命名与存放

*   将你的Python脚本文件（`.py`）直接放入`scripts`文件夹内。
*   文件名可以任意取，但推荐使用能清晰描述其功能的名称，例如 `视频格式转换器.py`。

### 第二步：撰写“GUI友好”的文档字符串（核心）

这是你的脚本与GUI沟通的 **唯一方式**。一个格式正确的文档字符串能让GUI完全理解你的脚本。请将它放在脚本文件的最顶端。

**标准模板**:

```python
"""
[display-name-zh] 你的脚本中文名
[display-name-en] Your English Script Name

这里是脚本的中文介绍，用几句话描述它的核心功能、使用场景和注意事项。
你可以使用Markdown的换行、列表等来排版，让它更易读。

---
兼容性:
- 文件格式: .mp4, .mkv
- 平台: 跨平台
---
更新日志:
  - v1.0 (2025-08-06): 初始版本。
~~~
This is the English description of the script. Explain its core features,
use cases, and any important notes for English-speaking users.

---
Compatibility:
- File Formats: .mp4, .mkv
- Platform: Cross-platform
---
Changelog:
  - v1.0 (2025-08-06): Initial release.
"""
```

*   `[display-name-zh]`: **必需**。GUI在中文模式下显示的脚本名称。
*   `[display-name-en]`: **必需**。GUI在英文模式下显示的脚本名称。
*   `~~~`: **必需**。中/英文介绍的分隔符。分隔符以上为中文区，以下为英文区。

### 第三步：使用`argparse`搭建沟通的桥梁

GUI通过在后台执行`python your_script.py --help`来解析你的参数。因此，你**必须**使用`argparse`模块来定义所有用户可配置的选项。

**标准模板**:

```python
import argparse

parser = argparse.ArgumentParser(description="你的脚本描述.")

# --- GUI交互参数 (必需，请直接复制) ---
parser.add_argument('--lang', type=str, default='en', choices=['zh', 'en'], help=argparse.SUPPRESS)
parser.add_argument('--gui-mode', action='store_true', help=argparse.SUPPRESS)

# --- 文件/文件夹输入 (必需，请直接复制) ---
parser.add_argument('files', nargs='*', help="由GUI传入的文件/文件夹路径列表.")

# --- 自定义可视化参数 (示例) ---
# 示例1: 生成一个复选框 (Checkbox)
parser.add_argument('-v', '--verbose', action='store_true', help="开启后会输出更详细的日志。")

# 示例2: 生成一个下拉选择菜单 (ComboBox)
parser.add_argument('--mode', type=str, choices=['fast', 'quality', 'balance'], default='balance', help="选择处理模式。")

# 示例3: 生成一个文本输入框 (LineEdit)
parser.add_argument('--output-name', type=str, default='output', help="指定输出文件的前缀名。")

# --- 解析参数 ---
args = parser.parse_args()

# --- 在代码中使用 ---
if args.verbose:
    print("详细模式已开启。")

print(f"当前选择的语言是: {args.lang}")
print(f"要处理的文件列表是: {args.files}")
```

### 第四步：编写对用户友好的脚本逻辑

1.  **自给自足**: 如果你的脚本依赖第三方库（如`requests`, `numpy`），请在脚本内部实现自动检查和安装。这能极大地方便用户。
2.  **提供国际化输出**: 对于所有`print()`到控制台的信息，请根据`args.lang`参数的值来决定显示中文还是英文。
3.  **拥抱标准输入输出**: 使用`print()`来输出信息，使用`input()`来接收用户的交互式输入。GUI会为你处理好这一切。

## 🗺️ 蓝图与未来计划

*   **功能完善**: 修复所有已知问题，包括动态主题切换。
*   **应用打包**: 在项目进入Beta或稳定版后，我们会将其打包为Windows (`.exe`)、macOS (`.app`) 等平台的可执行文件，实现真正的开箱即用，无需手动安装Python环境。

## ❓ 常见问题与故障排查 (FAQ)

**Q: 暗色/亮色模式切换似乎不工作？**

A: 这是一个已知问题。目前，主题功能的工作方式如下：“跟随系统”选项可以在程序启动时正确应用您当前的系统主题（亮色或暗色）。但是，如果您在程序运行时切换系统主题，本工具需要**重启**才能应用新主题。直接点击“浅色模式”或“深色模式”按钮可能无法立即生效。我们正在努力在未来的版本中修复此问题。

**Q: 我启动`main.py`时，程序闪退，并提示DLL加载失败，该怎么办？**

A: 这是PyQt6库在某些环境下可能出现的问题。请在命令行（终端）中执行以下命令，它会强制重新安装一个干净的PyQt6，通常能解决此问题：

```bash
python -m pip install --no-cache-dir --force-reinstall PyQt6 PyQt6-Qt6
```

**Q: 为什么我启动了程序，但是左边的“可用脚本”列表是空的？**

A: 请检查并确保：
1.  存在一个名为`scripts`的文件夹。
2.  `scripts`文件夹与`main.py`在同一个目录下。
3.  `scripts`文件夹内至少有一个`.py`结尾的Python脚本文件。

**Q: 如何让我的任务脚本支持交互，比如中途需要用户输入"yes"？**

A: 只需在你的脚本代码中使用标准的`input()`函数即可。例如：

```python
user_confirmation = input("Are you sure you want to proceed? (yes/no): ")
if user_confirmation.lower() == 'yes':
    # ...继续执行...
```

当脚本运行到这里时，GUI的“增强型终端”会自动等待用户输入。

---
<br>

# UltraAce Toolkit (English Documentation)

[![Author](https://img.shields.io/badge/Author-UltraAce258-blue.svg)](https://github.com/UltraAce258)
[![Python](https://img.shields.io/badge/Python-3.8+-brightgreen.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/UI-PyQt6-orange.svg)](https://riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

---

The UltraAce Toolkit is designed to wrap various useful command-line Python automation scripts into a unified, elegant, and extremely user-friendly Graphical User Interface (GUI). Users no longer need to memorize complex commands; instead, they can perform bulk file processing, data conversion, code analysis, and more through simple clicks, drags, and fills.

Its core philosophy is **"Write once, run anywhere, for everyone."**

## ✨ Core Features

*   **Highly Extensible**: Simply place a compliant Python script into the `scripts` folder, and the toolkit will automatically recognize and load it without any changes to the main program.
*   **User-Friendly**: Intuitive interface design supporting drag-and-drop, multi-selection, checkbox-based batch operations, undo/redo, and other modern features.
*   **Dynamic Parameter Interface**: Automatically parses a script's `argparse` parameters and generates corresponding checkboxes, dropdown menus, and input fields, eliminating manual parameter typing.
*   **Bilingual Support**: The interface and script outputs support both Chinese and English, providing a consistent experience for users of different languages.
*   **Built-in Enhanced Terminal**: Not only displays real-time script output logs but also functions as a standard system command-line tool when no script is running.
*   **Personalized Themes**: Supports light, dark, and system-following display modes to care for your eyes.
*   **Detailed Interactive Feedback**: From code comments and UI tooltips to terminal output, we strive for exhaustive clarity, keeping users and developers informed at all times.

## ⚠️ Alpha Version Warning

**Please note that this toolkit is currently in an early Alpha development stage.**

This means it may contain unknown bugs, and some features might be incomplete. We warmly welcome and appreciate you submitting bug reports or suggesting features via GitHub Issues, or contributing code directly through Pull Requests. Your feedback and contributions are crucial for the project's growth!

## 🚀 Quick Start Guide

For new users, please strictly follow these steps to ensure you can run the tool successfully for the first time.

### Step 1: Environment Setup

Ensure you have **Python 3.8** or a newer version installed on your computer. You can check by typing the following command in your command line (terminal):

```bash
python --version
# or
python3 --version
```

If it's not installed, please download and install it from the [official Python website](https://www.python.org/downloads/).

### Step 2: Download Core Files

1.  Download the two most important parts from this repository:
    *   The main program file: `main.py`
    *   The task script folder: `scripts` (which may contain example scripts like `Document Page Counter.py`)

2.  Place them anywhere on your computer, but **you must maintain the following folder structure**:

    ```
    Your-Workspace/
    ├── main.py          (The main program)
    └── scripts/         (Folder for all task scripts)
        └── Task-Script-1.py
        └── Task-Script-2.py
        ...
    ```

    > **Warning**: `main.py` and the `scripts` folder must be in the same directory, otherwise the program will not find any task scripts!

### Step 3: Run the Toolkit

Open your command line (terminal), navigate to the directory containing `main.py`, and run it:

```bash
cd /path/to/Your-Workspace/
python main.py
```

If everything is correct, you should see the main interface of the "UltraAce Toolkit".

### Step 4: Execute Your First Task

1.  **Select a Script**: In the "Available Scripts" list on the left side of the program window, click on a script you want to run (e.g., "Document Page Counter").
2.  **Add Files**: Drag one or more files from your desktop or a folder directly into the program window.
3.  **Execute**: Click the largest and most prominent blue button, "Run Script," in the bottom right.
4.  **View Results**: The program will automatically switch to the "Enhanced Terminal" tab, where you can see the entire execution process and the final result of the script.

Congratulations! You have successfully used the UltraAce Toolkit.

---

#### **Alternative: Run with an IDE (e.g., VS Code)**

If you prefer using a code editor, this is also a highly recommended method:

1.  In your IDE, select **"Open Folder"** and open the entire workspace folder containing `main.py`.
2.  In the IDE's file explorer, click to open the `main.py` file.
3.  **Crucial Step**: Find and click the "Run" button. Make sure you select the option **"Run Python File"** or **"Debug Python File"**.

> **Warning**: Do not use the "Run Code" feature, as it may fail to launch the GUI correctly. In VS Code, this typically refers to the green triangular "play" button in the top-right corner.
  
## 🔧 Detailed GUI Usage and Configuration

Every feature of the toolkit is designed to enhance your efficiency. Understanding them will make you even more productive.

### Main Interface Layout

*   **Left Panel**: For selecting and understanding scripts.
    *   **Available Scripts List**: Displays all available tasks from the `scripts` folder. Right-clicking a script item allows you to "Show in Folder" to quickly locate the source file.
    *   **Script Info**: Shows the detailed documentation for the currently selected script.
*   **Right Panel**: The core operation area for configuring tasks and viewing results.

### Interactive Features Explained

#### File/Folder List

*   **Add**: Supports **drag-and-drop** or clicking the **"Add Files/Folders"** buttons.
*   **Edit**: **Double-click** any item in the list to directly edit its path.
*   **Marking**: Each item has a **Checkbox** in front of it. This is the key mechanism for batch processing:
    *   **When any item is checked**: Clicking "Run Script" will **only process the checked items**.
    *   **When no items are checked**: Clicking "Run Script" will **process all items** in the list.
*   **Remove**:
    *   After selecting (highlighting) or checking any items, click "Remove Selected" to delete them.
    *   When no items are selected or checked, this button becomes "Clear All," which clears the entire list.
    *   You can also press `Delete` or `Backspace` to quickly remove items.
*   **Select/Deselect All**:
    *   Click "Select All" to check all items in the list with one click.
    *   The button will then change to "Deselect All." Clicking it again will uncheck everything.
    *   Pressing the `Esc` key also quickly deselects all items.

#### Parameter Configuration

*   **Visual Parameters**: When you select a script, custom configuration options for that script will automatically appear here. You don't need to know the underlying command-line arguments; just fill it out like a form.
*   **Manual Parameters**: If you need to input temporary or advanced parameters that don't have a visual interface, you can type them here. The format is identical to the standard command line (e.g., `-v --output "my file.txt"`).

#### Output Area

*   **Standard Output**: A simple text box that displays only the final output of the script.
*   **Enhanced Terminal**:
    *   **Real-time Logs**: Shows every step of the script's execution, including dependency installation, debug info, etc.
    *   **Interactive Input**: If a script requires user input during execution (like "yes/no"), you can type in the input line at the bottom of the terminal and press Enter.
    *   **System Commands**: When no script is running, this acts as a standard system terminal. You can use common commands like `cd`, `ls`, `dir`, `pip`, etc. Type `exit` to close the program.

### Menu Bar Configuration

*   **Preferences -> Theme**: Here you can switch between "Light Mode," "Dark Mode," or "Follow System." Your choice is saved automatically for the next launch.

---

## ✍️ Task Script Development Guide

Want to develop your own custom task script? It's very simple! Follow these "Golden Rules" to create powerful tools that integrate perfectly with the toolkit.

### Step 1: File Naming and Placement

*   Place your Python script file (`.py`) directly into the `scripts` folder.
*   You can name the file anything, but it's recommended to use a name that clearly describes its function, e.g., `Video Format Converter.py`.

### Step 2: Write a "GUI-Friendly" Docstring (Crucial)

This is the **only way** your script communicates with the GUI. A correctly formatted docstring allows the GUI to fully understand your script. Place it at the very top of your script file.

**Standard Template**:

```python
"""
[display-name-zh] 你的脚本中文名
[display-name-en] Your English Script Name

这里是脚本的中文介绍，用几句话描述它的核心功能、使用场景和注意事项。
你可以使用Markdown的换行、列表等来排版，让它更易读。

---
兼容性:
- 文件格式: .mp4, .mkv
- 平台: 跨平台
---
更新日志:
  - v1.0 (2025-08-06): 初始版本。
~~~
This is the English description of the script. Explain its core features,
use cases, and any important notes for English-speaking users.

---
Compatibility:
- File Formats: .mp4, .mkv
- Platform: Cross-platform
---
Changelog:
  - v1.0 (2025-08-06): Initial release.
"""
```

*   `[display-name-zh]`: **Required**. The script name displayed by the GUI in Chinese mode.
*   `[display-name-en]`: **Required**. The script name displayed by the GUI in English mode.
*   `~~~`: **Required**. The separator for Chinese/English descriptions. Above the separator is the Chinese section, below is the English section.

### Step 3: Use `argparse` to Build the Communication Bridge

The GUI parses your parameters by running `python your_script.py --help` in the background. Therefore, you **must** use the `argparse` module to define all user-configurable options.

**Standard Template**:

```python
import argparse

parser = argparse.ArgumentParser(description="Your script's description.")

# --- GUI Interaction Parameters (Required, copy this directly) ---
parser.add_argument('--lang', type=str, default='en', choices=['zh', 'en'], help=argparse.SUPPRESS)
parser.add_argument('--gui-mode', action='store_true', help=argparse.SUPPRESS)

# --- File/Folder Input (Required, copy this directly) ---
parser.add_argument('files', nargs='*', help="List of file/folder paths passed in by the GUI.")

# --- Custom Visual Parameters (Examples) ---
# Example 1: Generates a Checkbox
parser.add_argument('-v', '--verbose', action='store_true', help="Enable for more detailed logging.")

# Example 2: Generates a ComboBox (dropdown menu)
parser.add_argument('--mode', type=str, choices=['fast', 'quality', 'balance'], default='balance', help="Select the processing mode.")

# Example 3: Generates a LineEdit (text input box)
parser.add_argument('--output-name', type=str, default='output', help="Specify the prefix for the output file.")

# --- Parse Arguments ---
args = parser.parse_args()

# --- Use in your code ---
if args.verbose:
    print("Verbose mode is enabled.")

print(f"The currently selected language is: {args.lang}")
print(f"The list of files to process is: {args.files}")
```

### Step 4: Write User-Friendly Script Logic

1.  **Be Self-Sufficient**: If your script depends on third-party libraries (like `requests`, `numpy`), implement logic to automatically check and install them. Users will love this feature.
2.  **Provide Internationalized Output**: For all information printed to the console (`print()`), decide whether to display Chinese or English based on the value of `args.lang`.
3.  **Embrace Standard I/O**: Use `print()` to output information and `input()` to receive interactive user input. The GUI will handle all of this for you.

## 🗺️ Roadmap & Future Plans

*   **Feature Completion**: Fix all known issues, including dynamic theme switching.
*   **Application Packaging**: Once the project reaches a Beta or stable version, we will package it into executable files for Windows (`.exe`), macOS (`.app`), etc., to provide a true out-of-the-box experience without needing a manual Python environment setup.

## ❓ FAQ & Troubleshooting

**Q: The dark/light mode toggle doesn't seem to work?**

A: This is a known issue. Currently, the theme functionality works as follows: The "Follow System" option correctly applies your current system theme (light or dark) upon application startup. However, if you change your system theme while the application is running, the toolkit needs to be **restarted** to apply the new theme. Directly clicking the "Light Mode" or "Dark Mode" buttons may not work as expected. We are working on fixing this in a future release.

**Q: When I run `main.py`, the program crashes with a DLL loading error. What should I do?**

A: This is a known issue with the PyQt6 library in some environments. Run the following command in your command line (terminal). It will force a clean reinstallation of PyQt6 and usually resolves the problem:

```bash
python -m pip install --no-cache-dir --force-reinstall PyQt6 PyQt6-Qt6
```

**Q: Why is the "Available Scripts" list empty when I start the program?**

A: Please check and ensure that:
1.  A folder named `scripts` exists.
2.  The `scripts` folder is in the same directory as `main.py`.
3.  There is at least one Python script file ending in `.py` inside the `scripts` folder.

**Q: How can I make my task script interactive, for example, requiring the user to type "yes" midway?**

A: Simply use the standard `input()` function in your script's code. For example:

```python
user_confirmation = input("Are you sure you want to proceed? (yes/no): ")
if user_confirmation.lower() == 'yes':
    # ...continue execution...
```

When the script reaches this point, the GUI's "Enhanced Terminal" will automatically wait for the user's input.

---

*Documentation last updated: 2025-08-06. Authored by @UltraAce258, written with Copilot.*
