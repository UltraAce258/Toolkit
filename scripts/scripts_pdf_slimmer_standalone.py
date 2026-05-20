#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[display-name-zh] PDF重复页瘦身器（独立版）
[display-name-en] PDF Duplicate Page Slimmer (Standalone)

独立版 PDF 瘦身脚本：无需 PyMuPDF / python-pptx，直接基于 PDF 原始对象结构
分析相邻页面的文本内容，若后一页完整包含前一页，则删除前一页。
当未发现可删除页面时，会原样复制输出为 ``*_slimmer.pdf``。

---
兼容性:
- 文件格式: .pdf
- 依赖库: 仅标准库
- 平台: 跨平台
---
使用方法:
  1. 将一个或多个 PDF 文件拖入主程序列表，或直接命令行传入。
  2. 执行脚本后，会在原文件同目录生成带有 ``_slimmer`` 后缀的新文件。
  3. 若发现“后页包含前页”的冗余页面，则会输出已瘦身版本。
---
Optional Parameters:
This script has no visual or manual optional parameters.
---
"""

from __future__ import annotations

import argparse
import binascii
import base64
import os
import re
import shutil
import sys
import zlib
from dataclasses import dataclass, field
from difflib import SequenceMatcher


SCRIPT_TEXTS = {
    "zh": {
        "init": "--- PDF重复页瘦身器（独立版）初始化 ---",
        "no_files": "未提供文件。",
        "start_processing": "\n--- 开始处理文件 ---",
        "processing_file": "\n[文件] {filename}",
        "skip_unsupported": "   - 跳过: 仅支持 .pdf。",
        "missing_file": "   - 跳过: 文件不存在: {path}",
        "analyzing": "   - 正在分析内容...",
        "single_page": "   - 文件只有一页或为空，无需处理。",
        "no_redundancy": "   - 未发现可移除的冗余页面，已原样复制输出。",
        "process_success": "   => 完成! 原始数量: {original}, 瘦身后: {final}。已保存至: {output_path}",
        "process_fail": "   - 处理失败: {error}",
        "all_done": "\n--- 所有任务已完成。 ---",
    },
    "en": {
        "init": "--- PDF Duplicate Page Slimmer (Standalone) Initialized ---",
        "no_files": "No files were provided.",
        "start_processing": "\n--- Starting processing ---",
        "processing_file": "\n[File] {filename}",
        "skip_unsupported": "   - Skipped: only .pdf is supported.",
        "missing_file": "   - Skipped: file does not exist: {path}",
        "analyzing": "   - Analyzing content...",
        "single_page": "   - File has only one page or is empty; nothing to do.",
        "no_redundancy": "   - No removable redundant pages found; copied as-is.",
        "process_success": "   => Done! Original: {original}, Slimmed: {final}. Saved to: {output_path}",
        "process_fail": "   - Failed: {error}",
        "all_done": "\n--- All tasks completed. ---",
    },
}
# English values take precedence; any missing keys fall back to the Chinese block
# so the runtime always has a complete message set.
SCRIPT_TEXTS["en"] = {**SCRIPT_TEXTS["zh"], **SCRIPT_TEXTS["en"]}


@dataclass
class PdfObject:
    number: int
    generation: int
    raw: bytes
    start: int
    end: int
    body: bytes = field(init=False)

    def __post_init__(self) -> None:
        self.body = self.raw[self.raw.find(b"obj") + 3 : self.raw.rfind(b"endobj")]

    @property
    def dict_part(self) -> bytes:
        if b"stream" not in self.body:
            return self.body
        return self.body[: self.body.find(b"stream")]

    def is_stream(self) -> bool:
        return b"stream" in self.body


def install_and_import(*_args, **_kwargs):  # kept for script-registry parity
    """Compatibility stub for legacy script-registry expectations.

    Older Toolkit scripts expose an ``install_and_import`` helper, so this
    no-op keeps the standalone script drop-in compatible without adding any
    runtime dependency bootstrap logic.
    """
    return None


def normalize_text_lines(text: str) -> list[str]:
    if not text:
        return []
    lines = text.strip().splitlines()
    normalized = [re.sub(r"\s+", " ", line).strip() for line in lines]
    return [line for line in normalized if line]


def is_line_contained_fuzzy(line_a: str, lines_b: list[str], sim_threshold: float = 0.9) -> bool:
    for line_b in lines_b:
        if SequenceMatcher(None, line_a, line_b).ratio() >= sim_threshold:
            return True
        if len(line_b) > len(line_a) and line_b.startswith(line_a):
            return True
    return False


def is_subset_fuzzy(lines_a: list[str], lines_b: list[str]) -> bool:
    if not lines_a:
        return True
    if not lines_b:
        return False
    return all(is_line_contained_fuzzy(line_a, lines_b) for line_a in lines_a)


def decode_pdf_literal(data: bytes) -> str:
    out = bytearray()
    i = 0
    while i < len(data):
        c = data[i]
        if c == 0x5C:  # backslash
            i += 1
            if i >= len(data):
                break
            nxt = data[i]
            if nxt == ord("n"):
                out += b"\n"
            elif nxt == ord("r"):
                out += b"\r"
            elif nxt == ord("t"):
                out += b"\t"
            elif nxt == ord("b"):
                out += b"\b"
            elif nxt == ord("f"):
                out += b"\f"
            elif nxt in b"()\\":
                out.append(nxt)
            elif 48 <= nxt <= 55:
                oct_digits = bytes([nxt])
                for _ in range(2):
                    if i + 1 < len(data) and 48 <= data[i + 1] <= 55:
                        i += 1
                        oct_digits += bytes([data[i]])
                    else:
                        break
                out.append(int(oct_digits, 8) & 0xFF)
            elif nxt in b"\n\r":
                if nxt == 0x0D and i + 1 < len(data) and data[i + 1] == 0x0A:
                    i += 1
            else:
                out.append(nxt)
        else:
            out.append(c)
        i += 1
    return out.decode("latin1", errors="replace")


def _apply_filters(stream: bytes, filters: list[str]) -> bytes:
    data = stream
    for flt in filters:
        if flt == "ASCIIHexDecode":
            hex_data = re.sub(rb"\s+", b"", data)
            hex_data = hex_data.rstrip(b">")
            if len(hex_data) % 2 == 1:
                hex_data += b"0"
            data = bytes.fromhex(hex_data.decode("ascii"))
        elif flt == "ASCII85Decode":
            data = base64.a85decode(data, adobe=True)
        elif flt == "FlateDecode":
            data = zlib.decompress(data)
    return data


def _parse_filters(dict_part: bytes) -> list[str]:
    filters: list[str] = []
    match = re.search(rb"/Filter\s+(\[.*?\]|/[A-Za-z0-9]+)", dict_part, re.S)
    if not match:
        return filters
    token = match.group(1)
    filters = re.findall(rb"/([A-Za-z0-9]+)", token)
    return [f.decode("ascii", errors="ignore") for f in filters]


def extract_stream_bytes(obj: PdfObject) -> bytes | None:
    if b"stream" not in obj.body:
        return None
    match = re.search(rb"stream\r?\n", obj.body)
    if not match:
        return None
    start = match.end()
    end = obj.body.rfind(b"endstream")
    if end < 0:
        return None
    stream = obj.body[start:end]
    if stream.endswith(b"\r\n"):
        stream = stream[:-2]
    elif stream.endswith(b"\n") or stream.endswith(b"\r"):
        stream = stream[:-1]
    filters = _parse_filters(obj.dict_part)
    try:
        return _apply_filters(stream, filters) if filters else stream
    except Exception:
        return stream


def extract_text_from_stream(raw: bytes) -> list[str]:
    if not raw:
        return []
    texts: list[str] = []
    pattern = re.compile(
        rb"(\[(?:[^\[\]]|\[(?:[^\[\]]|\[[^\]]*\])*\])*\]|\((?:[^\\()]|\\.)*\)|<[^>]+>)\s*T[Jj]",
        re.S,
    )
    for match in pattern.finditer(raw):
        token = match.group(1)
        if token.startswith(b"["):
            parts: list[str] = []
            for piece in re.finditer(rb"\((?:[^\\()]|\\.)*\)|<[^>]+>", token):
                part = piece.group(0)
                if part.startswith(b"("):
                    parts.append(decode_pdf_literal(part[1:-1]))
                else:
                    hexs = re.sub(rb"\s+", b"", part[1:-1])
                    if len(hexs) % 2 == 1:
                        hexs += b"0"
                    parts.append(
                        bytes.fromhex(hexs.decode("ascii")).decode("latin1", errors="replace")
                    )
            texts.append("".join(parts))
        elif token.startswith(b"("):
            texts.append(decode_pdf_literal(token[1:-1]))
        else:
            hexs = re.sub(rb"\s+", b"", token[1:-1])
            if len(hexs) % 2 == 1:
                hexs += b"0"
            texts.append(bytes.fromhex(hexs.decode("ascii")).decode("latin1", errors="replace"))
    return normalize_text_lines("\n".join(texts))


def parse_objects(data: bytes) -> dict[tuple[int, int], PdfObject]:
    objects: dict[tuple[int, int], PdfObject] = {}
    for match in re.finditer(rb"(?m)^(\d+)\s+(\d+)\s+obj\b", data):
        start = match.start()
        end = data.find(b"endobj", match.end())
        if end < 0:
            continue
        obj = PdfObject(
            number=int(match.group(1)),
            generation=int(match.group(2)),
            raw=data[start : end + 6],
            start=start,
            end=end + 6,
        )
        objects[(obj.number, obj.generation)] = obj
    return objects


def _ref_text(ref: tuple[int, int]) -> str:
    return f"{ref[0]} {ref[1]} R"


def _find_catalog(objects: dict[tuple[int, int], PdfObject]) -> tuple[int, int]:
    for key, obj in objects.items():
        if b"/Type /Catalog" in obj.body or b"/Type/Catalog" in obj.body:
            return key
    raise ValueError("Catalog object not found")


def _extract_ref(obj_body: bytes, field_name: bytes) -> tuple[int, int] | None:
    match = re.search(field_name + rb"\s+(\d+)\s+(\d+)\s+R", obj_body)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _extract_refs_from_kids(obj_body: bytes) -> list[tuple[int, int]]:
    match = re.search(rb"/Kids\s*\[(.*?)\]", obj_body, re.S)
    if not match:
        return []
    return [(int(a), int(b)) for a, b in re.findall(rb"(\d+)\s+(\d+)\s+R", match.group(1))]


def _extract_count(obj_body: bytes) -> int:
    match = re.search(rb"/Count\s+(\d+)", obj_body)
    if not match:
        return 0
    return int(match.group(1))


def _is_pages_node(obj: PdfObject) -> bool:
    return b"/Type /Pages" in obj.body or b"/Type/Pages" in obj.body


def _is_page_node(obj: PdfObject) -> bool:
    return (
        (b"/Type /Page" in obj.body or b"/Type/Page" in obj.body)
        and b"/Type /Pages" not in obj.body
        and b"/Type/Pages" not in obj.body
    )


def build_page_tree(
    objects: dict[tuple[int, int], PdfObject], root_pages_ref: tuple[int, int]
) -> tuple[list[dict], dict[tuple[int, int], dict], list[tuple[int, int]]]:
    pages_order: list[dict] = []
    tree_info: dict[tuple[int, int], dict] = {}

    def walk_pages_node(ref: tuple[int, int], ancestors: list[tuple[int, int]]) -> int:
        obj = objects[ref]
        kids = _extract_refs_from_kids(obj.body)
        child_refs: list[tuple[int, int]] = []
        total = 0
        for kid in kids:
            kid_obj = objects.get(kid)
            if kid_obj is None:
                continue
            if _is_pages_node(kid_obj):
                count = walk_pages_node(kid, ancestors + [ref])
                if count > 0:
                    child_refs.append(kid)
                total += count
            elif _is_page_node(kid_obj):
                contents_ref = _extract_ref(kid_obj.body, rb"/Contents")
                contents_refs: list[tuple[int, int]] = []
                if contents_ref is not None:
                    contents_refs = [contents_ref]
                else:
                    match = re.search(rb"/Contents\s*\[(.*?)\]", kid_obj.body, re.S)
                    if match:
                        contents_refs = [
                            (int(a), int(b))
                            for a, b in re.findall(rb"(\d+)\s+(\d+)\s+R", match.group(1))
                        ]
                pages_order.append(
                    {
                        "ref": kid,
                        "parent": ref,
                        "ancestors": ancestors + [ref],
                        "contents": contents_refs,
                    }
                )
                child_refs.append(kid)
                total += 1
        tree_info[ref] = {
            "kids": child_refs,
            "count": total,
            "obj": obj,
        }
        return total

    walk_pages_node(root_pages_ref, [])
    return pages_order, tree_info, [root_pages_ref]


def extract_page_lines(objects: dict[tuple[int, int], PdfObject], page_info: dict) -> list[str]:
    lines: list[str] = []
    for ref in page_info["contents"]:
        obj = objects.get(ref)
        if not obj:
            continue
        raw = extract_stream_bytes(obj)
        if raw:
            lines.extend(extract_text_from_stream(raw))
    return normalize_text_lines("\n".join(lines))


def detect_pages_to_delete(page_lines: list[list[str]]) -> list[int]:
    to_delete: list[int] = []
    for i in range(len(page_lines) - 1):
        current_lines = page_lines[i]
        next_lines = page_lines[i + 1]
        if current_lines and _next_page_has_more_content(current_lines, next_lines) and is_subset_fuzzy(
            current_lines, next_lines
        ):
            to_delete.append(i)
    return to_delete


def _next_page_has_more_content(current_lines: list[str], next_lines: list[str]) -> bool:
    """Compare pages by total extracted text length, then by line count."""
    return (
        sum(len(s) for s in next_lines),
        len(next_lines),
    ) > (
        sum(len(s) for s in current_lines),
        len(current_lines),
    )


def _replace_count_and_kids(obj_body: bytes, count: int, kids: list[tuple[int, int]]) -> bytes:
    updated = re.sub(rb"/Count\s+\d+", f"/Count {count}".encode("ascii"), obj_body, count=1)
    kids_text = " ".join(_ref_text(ref) for ref in kids)
    if re.search(rb"/Kids\s*\[.*?\]", updated, re.S):
        updated = re.sub(rb"/Kids\s*\[.*?\]", f"/Kids [{kids_text}]".encode("ascii"), updated, count=1)
    return updated


def _collect_updated_nodes(
    root_ref: tuple[int, int],
    tree_info: dict[tuple[int, int], dict],
    removed_page_refs: set[tuple[int, int]],
) -> dict[tuple[int, int], bytes]:
    updated: dict[tuple[int, int], bytes] = {}

    def walk(ref: tuple[int, int]) -> int:
        info = tree_info[ref]
        new_kids: list[tuple[int, int]] = []
        new_count = 0
        for kid in info["kids"]:
            if kid in tree_info:
                count = walk(kid)
                if count > 0:
                    new_kids.append(kid)
                new_count += count
            else:
                if kid not in removed_page_refs:
                    new_kids.append(kid)
                    new_count += 1
        if new_kids != info["kids"] or new_count != info["count"]:
            updated[ref] = _replace_count_and_kids(info["obj"].body, new_count, new_kids)
        return new_count

    walk(root_ref)
    return updated


def _format_obj_bytes(ref: tuple[int, int], body: bytes) -> bytes:
    return f"{ref[0]} {ref[1]} obj\n".encode("ascii") + body.strip(b"\r\n") + b"\nendobj\n"


def _parse_trailer(data: bytes) -> tuple[int, bytes, bytes]:
    startxref_matches = list(re.finditer(rb"startxref\s+(\d+)\s*%%EOF", data, re.S))
    if not startxref_matches:
        raise ValueError("Could not locate startxref")
    startxref_match = startxref_matches[-1]
    prev_xref = int(startxref_match.group(1))
    trailer_matches = list(re.finditer(rb"trailer\s*<<(.*?)>>\s*startxref", data, re.S))
    if not trailer_matches:
        raise ValueError("Could not locate trailer")
    trailer_match = trailer_matches[-1]
    trailer_body = trailer_match.group(1)
    return prev_xref, trailer_body, data[startxref_match.start() :]


def _build_incremental_update(
    original: bytes,
    objects: dict[tuple[int, int], PdfObject],
    catalog_ref: tuple[int, int],
    updated_nodes: dict[tuple[int, int], bytes],
) -> bytes:
    if not updated_nodes:
        return original

    prev_xref, trailer_body, _ = _parse_trailer(original)
    trailer_text = trailer_body.decode("latin1", errors="replace")
    size_match = re.search(r"/Size\s+(\d+)", trailer_text)
    size = int(size_match.group(1)) if size_match else (max(num for num, _ in objects) + 1)

    patch = bytearray()
    offsets: list[tuple[int, int]] = []
    for ref, body in sorted(updated_nodes.items()):
        offsets.append((ref[0], len(original) + len(patch)))
        patch.extend(_format_obj_bytes(ref, body))

    xref_offset = len(original) + len(patch)
    xref = bytearray()
    xref.extend(b"xref\n")
    for obj_num, offset in offsets:
        xref.extend(f"{obj_num} 1\n{offset:010d} 00000 n \n".encode("ascii"))

    trailer_parts = [f"/Size {size}", f"/Root {_ref_text(catalog_ref)}"]
    trailer_parts.append(f"/Prev {prev_xref}")
    trailer = f"trailer\n<<{' '.join(trailer_parts)}>>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin1")
    return original + patch + xref + trailer


def slim_pdf(input_path: str, output_path: str, texts: dict[str, str]) -> None:
    with open(input_path, "rb") as fh:
        original = fh.read()

    objects = parse_objects(original)
    catalog_ref = _find_catalog(objects)
    root_pages_ref = _extract_ref(objects[catalog_ref].body, rb"/Pages")
    if root_pages_ref is None:
        raise ValueError("Root pages tree not found")

    pages_order, tree_info, _ = build_page_tree(objects, root_pages_ref)
    if len(pages_order) <= 1:
        print(texts["single_page"])
        shutil.copyfile(input_path, output_path)
        return

    page_lines = [extract_page_lines(objects, page_info) for page_info in pages_order]
    pages_to_delete = detect_pages_to_delete(page_lines)
    removed_refs = {pages_order[i]["ref"] for i in pages_to_delete}

    if not removed_refs:
        print(texts["no_redundancy"])
        shutil.copyfile(input_path, output_path)
        return

    updated_nodes = _collect_updated_nodes(root_pages_ref, tree_info, removed_refs)
    slimmed = _build_incremental_update(original, objects, catalog_ref, updated_nodes)
    with open(output_path, "wb") as fh:
        fh.write(slimmed)

    final_pages = len(pages_order) - len(removed_refs)
    print(
        texts["process_success"].format(
            original=len(pages_order),
            final=final_pages,
            output_path=os.path.basename(output_path),
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Slim PDF files by removing redundant pages.")
    parser.add_argument("files", nargs="*", help="Paths to PDF files.")
    parser.add_argument("--lang", type=str, default="en", choices=["zh", "en"], help=argparse.SUPPRESS)  # GUI-only
    parser.add_argument("--gui-mode", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    texts = SCRIPT_TEXTS.get(args.lang, SCRIPT_TEXTS["en"])
    print(texts["init"])

    if not args.files:
        print(texts["no_files"])
        return 1

    print(texts["start_processing"])
    for file_path in args.files:
        if not os.path.exists(file_path):
            print(texts["missing_file"].format(path=file_path))
            continue

        print(texts["processing_file"].format(filename=os.path.basename(file_path)))
        try:
            if not file_path.lower().endswith(".pdf"):
                print(texts["skip_unsupported"])
                continue

            directory, filename = os.path.split(file_path)
            stem, _ = os.path.splitext(filename)
            output_path = os.path.join(directory, f"{stem}_slimmer.pdf")

            print(texts["analyzing"])
            slim_pdf(file_path, output_path, texts)
        except (OSError, ValueError, zlib.error, binascii.Error) as exc:
            print(texts["process_fail"].format(error=f"{type(exc).__name__}: {exc}"))

    print(texts["all_done"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
