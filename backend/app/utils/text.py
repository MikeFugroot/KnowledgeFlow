# -*- coding: utf-8 -*-
"""
文本处理工具函数 — 复用桌面版逻辑
"""

import json
import re
from typing import Any, Dict


def clean_text(text: str) -> str:
    """清洗文本：统一换行、合并空格、去除首尾空白"""
    if not text:
        return ""
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = "\n".join(line.strip() for line in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def safe_filename(name: str, max_len: int = 80) -> str:
    """生成安全的文件名"""
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    name = re.sub(r"\s+", "_", name)
    return name[:max_len].strip("_") or "untitled"


def _repair_json_text(text: str) -> str:
    """修正常见 LLM JSON 输出问题：尾逗号、截断等"""
    text = re.sub(r",\s*([}\]])", r"\1", text)
    if text.count("{") > text.count("}"):
        text += "}" * (text.count("{") - text.count("}"))
    if text.count("[") > text.count("]"):
        text += "]" * (text.count("[") - text.count("]"))
    return text


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    从 LLM 返回的文本中提取 JSON 对象。
    支持带 ```json``` 包裹、尾逗号、截断等常见问题。
    """
    text = (text or "").strip()
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    candidates = [text]
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(text[start:end + 1])
        candidates.append(_repair_json_text(text[start:end + 1]))

    last_err = None
    for candidate in candidates:
        for attempt in (candidate, _repair_json_text(candidate)):
            try:
                return json.loads(attempt)
            except json.JSONDecodeError as e:
                last_err = e
            except Exception as e:
                last_err = e

    preview = text[:500] + ("..." if len(text) > 500 else "")
    raise ValueError(
        f"模型返回的内容不是合法 JSON（{last_err}）。"
        f"常见原因：输出过长被截断、字符串含未转义引号。"
        f"返回预览：\n{preview}"
    )
