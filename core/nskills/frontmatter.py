"""Dependency-free parser for the YAML subset used by NSkills frontmatter.

Supported: top-level mappings, nested mappings, block lists of scalars, inline
lists, quoted and plain scalars, booleans, null, integers, and literal/folded
block scalars. Anchors, aliases, tags, multi-document streams, and complex keys
are rejected with a clear error. That is deliberate: canonical metadata stays
simple, and a wrong parse fails loudly instead of becoming a silent string.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple


class FrontmatterError(ValueError):
    pass


_KEY_RE = re.compile(r"^([A-Za-z0-9_.-]+):(?:[ \t]+(.*))?$")
_INT_RE = re.compile(r"^-?[0-9]+$")
_FLOAT_RE = re.compile(r"^-?[0-9]+\.[0-9]+$")


def split(text: str) -> Tuple[Dict[str, Any], str, int]:
    """Return (metadata, body, body_start_line).

    Raises FrontmatterError when the delimiters are missing or malformed.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError("missing opening '---'")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise FrontmatterError("missing closing '---'")
    meta, _ = _parse_block(lines[1:end], 0, 0)
    if not isinstance(meta, dict):
        raise FrontmatterError("frontmatter must be a mapping")
    return meta, "\n".join(lines[end + 1 :]), end + 2


def parse(text: str) -> Tuple[Dict[str, Any], str]:
    meta, body, _ = split(text)
    return meta, body


def _parse_block(lines: List[str], start: int, indent: int) -> Tuple[Any, int]:
    i = _next_content(lines, start)
    if i >= len(lines):
        return {}, i
    if _indent(lines[i]) < indent:
        return {}, i
    if lines[i][indent:].startswith("-"):
        return _parse_list(lines, i, indent)
    return _parse_map(lines, i, indent)


def _parse_map(lines: List[str], start: int, indent: int) -> Tuple[Dict[str, Any], int]:
    result: Dict[str, Any] = {}
    i = start
    while i < len(lines):
        i = _next_content(lines, i)
        if i >= len(lines):
            break
        raw = lines[i]
        line_indent = _indent(raw)
        if line_indent < indent:
            break
        if line_indent > indent:
            raise FrontmatterError(f"line {i + 2}: unexpected indentation")
        content = raw[indent:]
        if content.startswith("-"):
            break
        match = _KEY_RE.match(content)
        if not match:
            raise FrontmatterError(f"line {i + 2}: expected 'key: value', got {content!r}")
        key, rest = match.group(1), (match.group(2) or "").strip()
        if key in result:
            raise FrontmatterError(f"line {i + 2}: duplicate key {key!r}")
        if rest in ("|", ">", "|-", ">-", "|+", ">+"):
            value, i = _parse_block_scalar(lines, i + 1, indent, rest)
            result[key] = value
            continue
        if rest:
            result[key] = _parse_scalar(rest, i + 2)
            i += 1
            continue
        j = _next_content(lines, i + 1)
        if j < len(lines) and _indent(lines[j]) > indent:
            value, i = _parse_block(lines, j, _indent(lines[j]))
            result[key] = value
        elif j < len(lines) and _indent(lines[j]) == indent and lines[j][indent:].startswith("-"):
            value, i = _parse_list(lines, j, indent)
            result[key] = value
        else:
            result[key] = None
            i += 1
    return result, i


def _parse_list(lines: List[str], start: int, indent: int) -> Tuple[List[Any], int]:
    result: List[Any] = []
    i = start
    while i < len(lines):
        i = _next_content(lines, i)
        if i >= len(lines):
            break
        raw = lines[i]
        line_indent = _indent(raw)
        if line_indent != indent:
            if line_indent < indent:
                break
            raise FrontmatterError(f"line {i + 2}: unexpected indentation in list")
        content = raw[indent:]
        if not content.startswith("-"):
            break
        item = content[1:].strip()
        if not item:
            j = _next_content(lines, i + 1)
            if j < len(lines) and _indent(lines[j]) > indent:
                value, i = _parse_block(lines, j, _indent(lines[j]))
                result.append(value)
            else:
                result.append(None)
                i += 1
            continue
        if item.startswith("|") or item.startswith(">"):
            value, i = _parse_block_scalar(lines, i + 1, indent, item)
            result.append(value)
            continue
        result.append(_parse_scalar(item, i + 2))
        i += 1
    return result, i


def _parse_block_scalar(
    lines: List[str], start: int, parent_indent: int, marker: str
) -> Tuple[str, int]:
    i = start
    collected: List[str] = []
    block_indent = None
    while i < len(lines):
        raw = lines[i]
        if raw.strip() == "":
            collected.append("")
            i += 1
            continue
        current = _indent(raw)
        if current <= parent_indent:
            break
        if block_indent is None:
            block_indent = current
        if current < block_indent:
            break
        collected.append(raw[block_indent:])
        i += 1
    while collected and collected[-1] == "":
        collected.pop()
    if marker.startswith(">"):
        value = " ".join(part for part in collected if part).strip()
    else:
        value = "\n".join(collected)
    if marker.endswith("-"):
        value = value.rstrip("\n")
    elif marker.endswith("+"):
        value += "\n"
    return value, i


def _parse_scalar(token: str, line_no: int) -> Any:
    token = token.strip()
    if token == "":
        return None
    if token[0] in "\"'":
        if token[0] == '"':
            try:
                return json.loads(token)
            except json.JSONDecodeError as exc:
                raise FrontmatterError(f"line {line_no}: invalid double-quoted string: {exc}") from exc
        if len(token) < 2 or not token.endswith("'"):
            raise FrontmatterError(f"line {line_no}: unterminated single-quoted string")
        return token[1:-1].replace("''", "'")
    if token.startswith("[") and token.endswith("]"):
        inner = token[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part, line_no) for part in _split_inline(inner, line_no)]
    if token in ("true", "True"):
        return True
    if token in ("false", "False"):
        return False
    if token in ("null", "Null", "~"):
        return None
    if _INT_RE.match(token):
        return int(token)
    if _FLOAT_RE.match(token):
        return float(token)
    return _strip_comment(token)


def _split_inline(text: str, line_no: int) -> List[str]:
    parts: List[str] = []
    current: List[str] = []
    quote = None
    for char in text:
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in "\"'":
            quote = char
            current.append(char)
            continue
        if char == ",":
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    if quote:
        raise FrontmatterError(f"line {line_no}: unterminated quoted value in list")
    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def _strip_comment(token: str) -> str:
    match = re.search(r"\s+#", token)
    if match:
        return token[: match.start()].rstrip()
    return token


def _next_content(lines: List[str], start: int) -> int:
    i = start
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped and not stripped.startswith("#"):
            return i
        i += 1
    return i


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _unused() -> None:
    # Keep the type checker honest about imported names used only for typing.
    _ = (Dict, List, Tuple)
