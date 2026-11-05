"""Markdown 文本处理 — 标题降级、表格降级、图片 key 剥离、长文本分块."""

from __future__ import annotations

import logging
import re

_logger = logging.getLogger("hermes_lark_cards")

_MAX_CARD_TABLES = 5
_MAX_CHUNK_CHARS = 2400
_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")

__all__ = [
    "_downgrade_tables",
    "_find_tables_outside_code_blocks",
    "_open_fence_at",
    "_split_long_text",
    "_strip_invalid_image_keys",
    "optimize_markdown_style",
    "truncate_markdown",
]


def _find_tables_outside_code_blocks(text: str) -> list[tuple[int, int, str]]:
    """查找代码块外的 markdown 表格，返回 [(start, end, raw), ...]."""
    code_ranges: list[tuple[int, int]] = []
    for m in re.finditer(r"```[\s\S]*?```", text):
        code_ranges.append((m.start(), m.end()))

    def _in_code(idx: int) -> bool:
        return any(s <= idx < e for s, e in code_ranges)

    results: list[tuple[int, int, str]] = []
    for m in re.finditer(r"\|.+\|\n\|[-:| ]+\|[\s\S]*?(?=\n\n|\n(?!\|)|$)", text):
        if not _in_code(m.start()):
            results.append((m.start(), m.end(), m.group(0)))
    return results


def _downgrade_tables(text: str, limit: int = _MAX_CARD_TABLES) -> str:
    """超限表格降级为代码块（保留内容可见但飞书不渲染为表格元素）."""
    matches = _find_tables_outside_code_blocks(text)
    if len(matches) <= limit:
        return text
    result = text
    for start, end, raw in reversed(matches[limit:]):
        replacement = f"```\n{raw}\n```"
        result = result[:start] + replacement + result[end:]
    return result


def _strip_invalid_image_keys(text: str) -> str:
    """移除非 img_ 前缀的图片引用."""
    if "![" not in text:
        return text

    def _replace(m: re.Match) -> str:
        return m.group(0) if m.group(2).startswith("img_") else ""

    return re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", _replace, text)


def optimize_markdown_style(text: str) -> str:
    """优化流式 Markdown 以适配飞书 CardKit 渲染.

    1. 提取代码块用占位符保护
    2. 标题降级: H1 -> H4, H2-H6 -> H5
    3. 还原代码块
    4. 压缩多余空行
    5. 剥离无效图片 key（非 img_xxx 格式）
    """
    try:
        # 1. 提取代码块
        mark = "___CB_"
        code_blocks: list[str] = []

        def _extract(m: re.Match) -> str:
            prefix = m.group(1) or ""
            block = m.group(0)[len(prefix) :]
            idx = len(code_blocks)
            code_blocks.append(block)
            return f"{prefix}{mark}{idx}___"

        r = re.sub(r"(^|\n)(`{3,})([^\n]*)\n[\s\S]*?\n\2(?=\n|$)", _extract, text)

        # 2. 标题降级（仅当存在 H1-H3 时）；跳过仍在围栏内的行，避免把注释改成标题
        if re.search(r"^#{1,3} ", text, re.MULTILINE):
            lines = r.split("\n")
            in_fence: str | None = None
            for i, line in enumerate(lines):
                fence_match = _FENCE_RE.match(line)
                if fence_match:
                    marker = fence_match.group(1)
                    if in_fence is None:
                        in_fence = marker
                    elif marker[0] == in_fence[0] and len(marker) >= len(in_fence):
                        in_fence = None
                    continue
                if in_fence is not None:
                    continue
                if re.match(r"^#{2,6} ", line):
                    lines[i] = "##### " + line.lstrip("#").lstrip(" ")
                elif re.match(r"^# ", line):
                    lines[i] = "#### " + line[2:]
            r = "\n".join(lines)

        # 3. 还原代码块
        for i, block in enumerate(code_blocks):
            r = r.replace(f"{mark}{i}___", block)

        # 4. 压缩多余空行
        r = re.sub(r"\n{3,}", "\n\n", r)

        # 5. 剥离无效图片 key
        r = _strip_invalid_image_keys(r)

        return r
    except Exception:
        _logger.debug("optimize_markdown_style failed", exc_info=True)
        return text


def _open_fence_at(text: str, index: int) -> tuple[str, str] | None:
    """返回 index 处仍未闭合的围栏 (fence_marker, info_string)。"""
    open_fence: tuple[str, str] | None = None
    for line in text[:index].splitlines():
        m = _FENCE_RE.match(line)
        if not m:
            continue
        marker = m.group(1)
        if open_fence is None:
            open_fence = (marker, m.group(2).strip())
        elif marker[0] == open_fence[0][0] and len(marker) >= len(open_fence[0]):
            open_fence = None
    return open_fence


def truncate_markdown(text: str, keep_chars: int) -> tuple[str, int]:
    """截断 markdown 但保持围栏闭合；返回 (文本, 被丢弃的字符数)."""
    if keep_chars >= len(text):
        return text, 0
    keep = max(keep_chars, 0)
    head = text[:keep]
    tail = text[keep:]
    # 尽量在行边界截断，避免切坏行内语法
    line_cut = head.rfind("\n")
    if line_cut >= keep * 0.8:
        head = head[: line_cut + 1]
        tail = text[len(head):]
    fence = _open_fence_at(text, len(head))
    if fence is not None:
        marker, _info = fence
        head = head + ("" if head.endswith("\n") else "\n") + marker + "\n"
    return head, len(tail)


def _split_long_text(text: str, limit: int = _MAX_CHUNK_CHARS) -> list[str]:
    """将超长文本按段落/换行拆分为多个不超过 limit 字符的块。

    围栏代码块必须保持闭合：切点落在 ``` 内时，本块补上收尾围栏，下一块重开
    同语言围栏，避免飞书把代码渲染成普通段落。
    """
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        cut = text.rfind("\n\n", 0, limit)
        if cut < limit // 2:
            cut = text.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = limit
        head = text[:cut]
        tail = text[cut:].lstrip("\n")
        fence = _open_fence_at(text, cut)
        if fence is not None:
            marker, info = fence
            closing = f"\n{marker}\n" if not head.endswith("\n") else f"{marker}\n"
            head = head + closing
            tail = f"{marker}{info}\n" + tail
        chunks.append(head)
        text = tail
    return chunks
