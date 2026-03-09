#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script registry – discovers scripts and parses their parameters.
脚本注册表 – 发现脚本并解析其参数。

Parameter-parsing strategy (backward-compatible)
-------------------------------------------------
1. Try ``python script.py --gui-schema``.  If the script exits 0 and prints
   valid JSON, use that schema directly.
2. Otherwise fall back to running ``python script.py --help`` and applying a
   regex heuristic – exactly as the original code did.

参数解析策略（向后兼容）
1. 尝试 ``python script.py --gui-schema``。若脚本以 0 退出并打印有效 JSON，
   则直接使用该 schema。
2. 否则回退到运行 ``python script.py --help`` 并使用正则表达式启发式解析，
   与原代码完全一致。

Expected --gui-schema JSON format
----------------------------------
[
  {
    "name": "--sort",
    "type": "choice",          # "choice" | "value" | "flag"
    "choices": ["asc", "desc"],
    "default": "asc",
    "help": "Sort order [display: asc=升序,Ascending | desc=降序,Descending]"
  },
  ...
]
"""

import glob
import json
import os
import re
import subprocess
import sys
from typing import Any


# ------------------------------------------------------------------
# Docstring extraction
# ------------------------------------------------------------------

def extract_docstring(content: str) -> str:
    """Return the module-level docstring from *content*, or an empty string.

    从 *content* 中提取模块级文档字符串，若无则返回空字符串。
    """
    match = re.search(
        r'^\s*("""(.*?)"""|\'\'\'(.*?)\'\'\')',
        content,
        re.DOTALL | re.MULTILINE,
    )
    if match:
        return (match.group(2) or match.group(3)).strip()
    return ""


# ------------------------------------------------------------------
# Script scanning
# ------------------------------------------------------------------

def scan(scripts_dir: str) -> list[dict[str, Any]]:
    """Scan *scripts_dir* for ``*.py`` files and return a list of info dicts.

    Each dict has the keys: ``path``, ``name_zh``, ``name_en``.

    扫描 *scripts_dir* 中的 ``*.py`` 文件，返回信息字典列表。
    每个字典包含键：path、name_zh、name_en。
    """
    results: list[dict[str, Any]] = []
    if not os.path.exists(scripts_dir):
        os.makedirs(scripts_dir)
        return results

    for script_path in sorted(glob.glob(os.path.join(scripts_dir, "*.py"))):
        try:
            with open(script_path, "r", encoding="utf-8") as fh:
                content = fh.read()
            docstring = extract_docstring(content)

            zh_name_match = re.search(r"\[display-name-zh\](.*?)\n", docstring)
            en_name_match = re.search(r"\[display-name-en\](.*?)\n", docstring)

            zh_name = (
                zh_name_match.group(1).strip()
                if zh_name_match
                else os.path.basename(script_path)
            )
            en_name = (
                en_name_match.group(1).strip()
                if en_name_match
                else os.path.basename(script_path)
            )

            results.append({"path": script_path, "name_zh": zh_name, "name_en": en_name})
        except Exception as exc:  # noqa: BLE001
            print(f"Error loading script {script_path}: {exc}")

    return results


# ------------------------------------------------------------------
# Parameter parsing
# ------------------------------------------------------------------

def parse_params(script_path: str) -> list[dict[str, Any]]:
    """Return a list of parameter dicts for *script_path*.

    Tries ``--gui-schema`` first; falls back to ``--help`` regex.

    返回 *script_path* 的参数字典列表。
    优先尝试 --gui-schema；失败则回退至 --help 正则解析。
    """
    params = _try_gui_schema(script_path)
    if params is not None:
        return params
    return _parse_help_text(script_path)


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------

def _try_gui_schema(script_path: str) -> list[dict[str, Any]] | None:
    """Attempt to obtain parameters via ``--gui-schema``.

    Returns the parsed list on success, or *None* if the script does not
    support the flag or returns invalid JSON.

    尝试通过 --gui-schema 获取参数列表。
    成功则返回解析后的列表；若脚本不支持该标志或返回无效 JSON，则返回 None。
    """
    try:
        result = subprocess.run(
            [sys.executable, script_path, "--gui-schema"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        if result.returncode != 0:
            return None
        schema = json.loads(result.stdout)
        if not isinstance(schema, list):
            return None
        # Filter internal flags just in case.
        # 过滤内部标志以防万一。
        return [p for p in schema if p.get("name") not in ("--gui-mode", "--lang")]
    except Exception:  # noqa: BLE001
        return None


def _parse_help_text(script_path: str) -> list[dict[str, Any]]:
    """Parse parameters from ``python script.py --help`` output using regex.

    通过正则表达式从 ``--help`` 输出中解析参数。
    This is the original heuristic, kept 100% intact for backward compatibility.
    这是原始的启发式方法，保持 100% 不变以确保向后兼容。
    """
    params: list[dict[str, Any]] = []
    try:
        result = subprocess.run(
            [sys.executable, script_path, "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        help_text = result.stdout

        # Regex groups:
        # 1 – optional short flag (e.g. '-v, ')
        # 2 – long flag name     (e.g. 'verbose')
        # 3 – optional METAVAR   (indicates a value is expected)
        # 4 – optional choices   (e.g. 'name,date')
        # 5 – optional default
        pattern = re.compile(
            r"^\s+(-[a-zA-Z],\s+)?--([a-zA-Z0-9_-]+)\s*([A-Z_]+)?.*?"
            r"(?:\{([^}]+)\})?.*?(?:\(default:\s*([^)]+)\))?",
            re.MULTILINE | re.IGNORECASE,
        )

        for match in pattern.finditer(help_text):
            name = f"--{match.group(2)}"
            # Skip internal flags used by the launcher itself.
            # 跳过启动器自身使用的内部标志。
            if name in ("--gui-mode", "--lang"):
                continue

            metavar = match.group(3)
            choices = match.group(4)
            default_val = match.group(5)

            param_info: dict[str, Any] = {"name": name}

            if choices:
                param_info["type"] = "choice"
                param_info["choices"] = [c.strip() for c in choices.split(",")]
            elif metavar:
                param_info["type"] = "value"
            else:
                param_info["type"] = "flag"

            if default_val:
                param_info["default"] = default_val.strip()

            # help text is not available from --help regex; leave as empty string.
            # 正则解析无法获取 help 文本；置为空字符串。
            param_info["help"] = ""

            params.append(param_info)

    except Exception as exc:  # noqa: BLE001
        print(
            f"Could not parse parameters for {os.path.basename(script_path)}: {exc}"
        )
    return params
