import flet as ft
import os
import sys
import glob
import re
import shlex
import subprocess
import threading
from pathlib import Path

UI_TEXTS = {
    "zh": {
        "window_title": "脚本工具箱",
        "available_scripts": "可用脚本",
        "script_info": "脚本信息",
        "path_list_label": "文件/文件夹路径",
        "run_button": "执行脚本",
        "stop_button": "停止",
        "browse_files_button": "添加文件",
        "browse_dir_button": "添加文件夹",
        "remove_selected_button": "移除选中",
        "params_label": "手动参数:",
        "status_ready": "就绪",
        "status_running": "正在执行...",
        "warn_select_script_title": "警告",
        "warn_select_script_msg": "请先选择一个脚本。",
        "warn_no_paths_title": "警告",
        "warn_no_paths_msg": "请至少添加一个文件或文件夹路径。",
        "script_finished_msg": "脚本执行完毕，退出代码: {exit_code}",
        "script_stopped_msg": "脚本被用户终止。",
        "info_no_docstring": "未找到此脚本的文档字符串。",
        "theme_light": "浅色模式",
        "theme_dark": "深色模式",
    },
    "en": {
        "window_title": "Script Toolkit",
        "available_scripts": "Available Scripts",
        "script_info": "Script Information",
        "path_list_label": "File/Directory Paths",
        "run_button": "Run Script",
        "stop_button": "Stop",
        "browse_files_button": "Add Files",
        "browse_dir_button": "Add Folder",
        "remove_selected_button": "Remove Selected",
        "params_label": "Manual Params:",
        "status_ready": "Ready",
        "status_running": "Running...",
        "warn_select_script_title": "Warning",
        "warn_select_script_msg": "Please select a script first.",
        "warn_no_paths_title": "Warning",
        "warn_no_paths_msg": "Please add at least one file or folder path.",
        "script_finished_msg": "Script finished with exit code: {exit_code}",
        "script_stopped_msg": "Script execution stopped by user.",
        "info_no_docstring": "No docstring found for this script.",
        "theme_light": "Light Mode",
        "theme_dark": "Dark Mode",
    }
}

class ScriptExecutor(subprocess.Popen):
    def __init__(self, command, on_output, on_finish):
        self.on_output = on_output
        self.on_finish = on_finish
        super().__init__(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )

    def listen(self):
        for line in self:
            if not self.stdout: break
            self.on_output(line)
        self.wait()
        if self.returncode is not None:
            self.on_finish(self.returncode)

def main(page: ft.Page):
    
    # --- App State ---
    state = {
        "current_script_path": None,
        "current_lang": "zh",
        "process": None
    }

    # --- Core Logic & Event Handlers (Defined BEFORE UI components) ---

    def get_ui_text(key, **kwargs):
        return UI_TEXTS[state["current_lang"]].get(key, key).format(**kwargs)

    def on_process_output(line):
        output_console.controls.append(ft.Text(line.strip(), font_family="monospace"))
        page.update()
    
    def on_process_finish(exit_code):
        msg = get_ui_text("script_stopped_msg") if exit_code == -9 else get_ui_text("script_finished_msg", exit_code=exit_code)
        on_process_output(f"\n--- {msg} ---")
        run_button.disabled = False
        stop_button.disabled = True
        status_bar.value = get_ui_text("status_ready")
        state["process"] = None
        page.update()

    def run_script(e):
        if not state["current_script_path"]:
            page.dialog = ft.AlertDialog(title=ft.Text(get_ui_text("warn_select_script_title")), content=ft.Text(get_ui_text("warn_select_script_msg")))
            page.dialog.open = True
            page.update()
            return
        
        paths = [c.label for c in path_list.controls if c.value]
        if not paths:
            page.dialog = ft.AlertDialog(title=ft.Text(get_ui_text("warn_no_paths_title")), content=ft.Text(get_ui_text("warn_no_paths_msg")))
            page.dialog.open = True
            page.update()
            return

        output_console.controls.clear()
        run_button.disabled = True
        stop_button.disabled = False
        status_bar.value = get_ui_text("status_running")

        args = ["--gui-mode", "--lang", state["current_lang"]]
        for switch in dynamic_params_view.controls:
            if switch.value:
                args.append(switch.data)
        
        if manual_params_input.value:
            args.extend(shlex.split(manual_params_input.value))
        
        args.extend(paths)
        command = [sys.executable, state["current_script_path"]] + args
        
        on_process_output(f"$ {' '.join(command)}\n")
        state["process"] = ScriptExecutor(command, on_process_output, on_process_finish)
        threading.Thread(target=state["process"].listen, daemon=True).start()
        
    def stop_script(e):
        if state["process"]:
            state["process"].kill()
            on_process_finish(-9)

    def on_script_selected(control):
        for c in script_list.controls:
            c.bgcolor = None
        control.bgcolor = ft.colors.PRIMARY_CONTAINER
        
        data = control.data
        state["current_script_path"] = data["path"]
        
        doc_parts = data["doc"].split('~~~', 1)
        doc_text = doc_parts[0] if state["current_lang"] == 'zh' else (doc_parts[1] if len(doc_parts) > 1 else doc_parts[0])
        doc_text_clean = re.sub(r'\[display-name-..\](.*?)\n', '', doc_text, count=2).strip()
        script_info.value = doc_text_clean or get_ui_text("info_no_docstring")
        
        run_button.disabled = False
        parse_and_display_params(state["current_script_path"])
        page.update()

    def load_scripts():
        script_list.controls.clear()
        scripts_dir = Path("scripts")
        scripts_dir.mkdir(exist_ok=True)
        
        for script_path in sorted(scripts_dir.glob("*.py")):
            try:
                content = script_path.read_text(encoding='utf-8')
                docstring = re.search(r'^\s*("""(.*?)"""|\'\'\'(.*?)\'\'\')', content, re.DOTALL | re.MULTILINE)
                doc = (docstring.group(2) or docstring.group(3)).strip() if docstring else ""
                
                name_match = re.search(r'\[display-name-en\](.*?)\n', doc)
                name_en = name_match.group(1).strip() if name_match else script_path.name
                name_match = re.search(r'\[display-name-zh\](.*?)\n', doc)
                name_zh = name_match.group(1).strip() if name_match else script_path.name

                script_list.controls.append(
                    ft.Container(
                        content=ft.Text(name_zh if state["current_lang"] == "zh" else name_en),
                        data={"path": str(script_path), "doc": doc, "name_zh": name_zh, "name_en": name_en},
                        padding=ft.padding.symmetric(vertical=8, horizontal=12),
                        border_radius=ft.border_radius.all(5),
                        on_click=lambda e: on_script_selected(e.control),
                    )
                )
            except Exception as e:
                print(f"Error loading script {script_path}: {e}")
        page.update()

    def parse_and_display_params(script_path):
        dynamic_params_view.controls.clear()
        try:
            result = subprocess.run(
                [sys.executable, script_path, '--help'],
                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=2
            )
            pattern = re.compile(r"^\s+--([a-zA-Z0-9_-]+)", re.MULTILINE)
            for match in pattern.finditer(result.stdout):
                name = f"--{match.group(1)}"
                if name not in ['--gui-mode', '--lang']:
                    dynamic_params_view.controls.append(ft.Switch(label=name, data=name))
        except Exception as e:
            print(f"Could not parse params: {e}")
        dynamic_params_view.visible = bool(dynamic_params_view.controls)
        page.update()
        
    def pick_files_result(e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                path_list.controls.append(ft.Checkbox(label=f.path, value=True))
            page.update()

    def pick_dir_result(e: ft.FilePickerResultEvent):
        if e.path:
            path_list.controls.append(ft.Checkbox(label=e.path, value=True))
            page.update()

    def remove_selected_paths(e):
        path_list.controls = [c for c in path_list.controls if not c.value]
        page.update()

    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        theme_toggle.label = get_ui_text("theme_light") if page.theme_mode == ft.ThemeMode.DARK else get_ui_text("theme_dark")
        page.update()
    
    def toggle_lang(e):
        state["current_lang"] = "en" if state["current_lang"] == "zh" else "zh"
        update_ui_text()
        
    def update_ui_text():
        page.title = get_ui_text("window_title")
        script_list_title.value = get_ui_text("available_scripts")
        script_info_title.value = get_ui_text("script_info")
        path_list_title.value = get_ui_text("path_list_label")
        run_button.text = get_ui_text("run_button")
        stop_button.text = get_ui_text("stop_button")
        add_files_button.text = get_ui_text("browse_files_button")
        add_dir_button.text = get_ui_text("browse_dir_button")
        remove_button.text = get_ui_text("remove_selected_button")
        manual_params_input.label = get_ui_text("params_label")
        status_bar.value = get_ui_text("status_ready") if not state["process"] else get_ui_text("status_running")
        theme_toggle.label = get_ui_text("theme_light") if page.theme_mode == ft.ThemeMode.DARK else get_ui_text("theme_dark")

        for c in script_list.controls:
            c.content.value = c.data["name_zh"] if state["current_lang"] == "zh" else c.data["name_en"]
        
        if state["current_script_path"]:
            selected_control = next((c for c in script_list.controls if c.data["path"] == state["current_script_path"]), None)
            if selected_control:
                on_script_selected(selected_control)
        else:
            script_info.value = ""

        page.update()

    # --- UI Components (Defined AFTER handlers) ---
    
    # Left Panel
    script_list = ft.ListView(expand=1, spacing=5)
    script_info = ft.Markdown("", expand=1)

    # Right Panel
    path_list = ft.ListView(expand=1, spacing=5)
    manual_params_input = ft.TextField(label=get_ui_text("params_label"), expand=True)
    dynamic_params_view = ft.Column(spacing=10, visible=False)
    output_console = ft.ListView(expand=1, auto_scroll=True, spacing=5)
    run_button = ft.ElevatedButton(get_ui_text("run_button"), icon=ft.icons.PLAY_ARROW, on_click=run_script, disabled=True, height=40)
    stop_button = ft.ElevatedButton(get_ui_text("stop_button"), icon=ft.icons.STOP, on_click=stop_script, disabled=True, height=40, color="red")
    status_bar = ft.Text(get_ui_text("status_ready"))

    # --- UI Layout ---
    page.title = get_ui_text("window_title")
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10
    
    file_picker = ft.FilePicker(on_result=pick_files_result)
    dir_picker = ft.FilePicker(on_result=pick_dir_result)
    page.overlay.extend([file_picker, dir_picker])

    script_list_title = ft.Text(get_ui_text("available_scripts"), style=ft.TextThemeStyle.TITLE_MEDIUM)
    script_info_title = ft.Text(get_ui_text("script_info"), style=ft.TextThemeStyle.TITLE_MEDIUM)
    path_list_title = ft.Text(get_ui_text("path_list_label"), style=ft.TextThemeStyle.TITLE_MEDIUM)
    
    theme_toggle = ft.Switch(label=get_ui_text("theme_dark"), on_change=toggle_theme)
    lang_toggle = ft.IconButton(icon=ft.icons.LANGUAGE, on_click=toggle_lang, tooltip="切换语言 (Switch Language)")
    add_files_button = ft.ElevatedButton(get_ui_text("browse_files_button"), icon=ft.icons.ADD, on_click=lambda _: file_picker.pick_files(allow_multiple=True))
    add_dir_button = ft.ElevatedButton(get_ui_text("browse_dir_button"), icon=ft.icons.FOLDER_OPEN, on_click=lambda _: dir_picker.get_directory_path())
    remove_button = ft.ElevatedButton(get_ui_text("remove_selected_button"), icon=ft.icons.REMOVE, on_click=remove_selected_paths)

    left_panel = ft.Column([
        ft.Row([script_list_title, ft.Row([theme_toggle, lang_toggle])], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        script_list,
        ft.Divider(),
        script_info_title,
        script_info,
    ], expand=2)

    right_panel = ft.Column([
        path_list_title,
        path_list,
        ft.Row([add_files_button, add_dir_button, remove_button]),
        ft.Divider(),
        ft.Row([manual_params_input]),
        dynamic_params_view,
        ft.Row([run_button, stop_button]),
        ft.Divider(),
        output_console
    ], expand=5)

    page.add(
        ft.Row([left_panel, ft.VerticalDivider(), right_panel], expand=True),
        status_bar
    )

    load_scripts()

if __name__ == "__main__":
    ft.app(target=main)
