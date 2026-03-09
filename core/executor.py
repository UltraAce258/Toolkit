#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script executor – runs a Python script in a background thread via QProcess.
脚本执行器 – 通过 QProcess 在后台线程中运行 Python 脚本。

Emitted signals
---------------
output_updated(str)          – a decoded line of stdout/stderr output
progress_updated(float, float, str)  – parsed [PROGRESS] line values
process_finished(int)        – process exit code
"""

import os
import platform
import shlex
import sys

from PyQt6.QtCore import QProcess, QThread, pyqtSignal


class ScriptExecutor(QThread):
    """Executes a script in a separate thread to keep the GUI responsive.

    在独立线程中执行脚本，以保持 GUI 响应性。
    """

    # Signal carrying a decoded output line / 携带已解码输出行的信号
    output_updated = pyqtSignal(str)
    # Signal carrying (current, maximum, description) progress values / 携带进度值的信号
    progress_updated = pyqtSignal(float, float, str)
    # Signal carrying the process exit code / 携带进程退出码的信号
    process_finished = pyqtSignal(int)

    def __init__(self, command: list, working_dir: str | None = None) -> None:
        """
        :param command: List of command arguments (script path + args).
                        命令参数列表（脚本路径 + 参数）。
        :param working_dir: Working directory for the subprocess.
                            子进程的工作目录。
        """
        super().__init__()
        self.command = command
        self.working_dir = working_dir
        self.process: QProcess | None = None
        # Choose encoding based on OS to handle console output correctly.
        # 根据操作系统选择编码，以正确处理控制台输出。
        self.output_encoding = "gbk" if platform.system() == "Windows" else "utf-8"

    # ------------------------------------------------------------------
    # QThread interface
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Main thread logic – starts QProcess and waits for it to finish.

        线程主逻辑 – 启动 QProcess 并等待其结束。
        """
        try:
            display_command = shlex.join(
                [os.path.basename(sys.executable)] + self.command
            )
            self.output_updated.emit(f"Executing command: {display_command}\n")

            self.process = QProcess()
            # Merge stdout and stderr so all output arrives on one channel.
            # 合并 stdout 与 stderr，使所有输出经同一通道传递。
            self.process.setProcessChannelMode(
                QProcess.ProcessChannelMode.MergedChannels
            )
            if self.working_dir:
                self.process.setWorkingDirectory(self.working_dir)

            self.process.readyReadStandardOutput.connect(self._handle_output)
            self.process.finished.connect(self.process_finished.emit)

            self.process.start(sys.executable, self.command)
            self.process.waitForFinished(-1)  # -1 = wait indefinitely / 无限等待
        except Exception as exc:
            self.output_updated.emit(f"Error executing command: {exc}\n")
            self.process_finished.emit(1)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _handle_output(self) -> None:
        """Read buffered output, decode it, and route each line.

        Parses ``[PROGRESS] current/max | description`` lines and emits
        *progress_updated*; all other lines go to *output_updated*.

        读取缓冲输出、解码，并逐行路由。
        解析 [PROGRESS] 行并发出 progress_updated；其余行发出 output_updated。
        """
        if not self.process:
            return
        data: bytes = self.process.readAllStandardOutput().data()
        try:
            decoded_text = data.decode("utf-8")
        except UnicodeDecodeError:
            decoded_text = data.decode(self.output_encoding, errors="replace")

        for line in decoded_text.strip().split("\n"):
            if not line.strip():
                continue
            if line.startswith("[PROGRESS]"):
                try:
                    payload = line[len("[PROGRESS]"):].strip()
                    progress_part, description = payload.split("|", 1)
                    current_str, max_str = progress_part.split("/", 1)
                    current = float(current_str.strip())
                    maximum = float(max_str.strip())
                    self.progress_updated.emit(current, maximum, description.strip())
                except (ValueError, IndexError) as exc:
                    self.output_updated.emit(
                        f"Invalid progress format: {line}\nError: {exc}\n"
                    )
            else:
                self.output_updated.emit(line + "\n")

    # ------------------------------------------------------------------
    # Public control methods
    # ------------------------------------------------------------------

    def send_input(self, text: str) -> None:
        """Write *text* followed by a newline to the running script's stdin.

        向正在运行的脚本的 stdin 写入 *text* 及换行符。
        """
        if (
            self.process
            and self.process.state() == QProcess.ProcessState.Running
        ):
            self.process.write(f"{text}\n".encode("utf-8"))

    def terminate(self) -> None:
        """Gracefully stop the running process; kill it after a 3-second timeout.

        优雅地停止正在运行的进程；3 秒超时后强制结束。
        """
        if (
            self.process
            and self.process.state() == QProcess.ProcessState.Running
        ):
            self.process.terminate()
            if not self.process.waitForFinished(3000):
                self.process.kill()
