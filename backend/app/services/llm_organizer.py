# -*- coding: utf-8 -*-
"""
LLM 整理服务 — 复用桌面版 organize_doc/call_llm_api/rule_fallback 逻辑
将 requests 替换为 httpx 异步调用，去掉 PyQt 依赖
"""

import re
import time
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import httpx

from app.config import settings
from app.utils.text import clean_text, extract_json_from_text


# ---- 关键词银行（规则兜底用）----
KEYWORD_BANK = {
    "技术": ["AI", "人工智能", "模型", "算法", "Python", "代码", "深度学习", "机器学习", "数据库", "系统", "API", "向量", "检索", "RAG", "YOLO", "Transformer", "神经网络", "部署", "GPU", "CUDA"],
    "学习": ["学院", "学校", "课程", "考试", "学习", "学生", "教师", "毕业", "就业", "通知", "招募", "团委", "学生会", "培养", "专业", "课堂", "汇报", "论文", "教育"],
    "生活": ["生活", "旅行", "美食", "运动", "娱乐", "电影", "音乐", "健康", "家庭", "购物", "日常"],
}


def get_api_config(provider: Optional[str] = None) -> tuple:
    """
    获取 LLM API 配置

    Returns:
        (api_key, base_url, model_name) 元组
    """
    provider = provider or settings.API_PROVIDER
    if provider == "qwen":
        return settings.DASHSCOPE_API_KEY, settings.QWEN_BASE_URL, settings.QWEN_MODEL_NAME
    if provider == "deepseek":
        return settings.DEEPSEEK_API_KEY, settings.DEEPSEEK_BASE_URL, settings.DEEPSEEK_MODEL_NAME
    raise ValueError(f"未知 API_PROVIDER：{provider}")


def build_prompt(doc: Dict[str, Any]) -> str:
    """构建 LLM 整理提示词"""
    text = doc.get("text", "")[:settings.MAX_TEXT_CHARS_FOR_LLM]
    return f"""
你是一个"个人知识库自动整理助手"。请根据下面资料内容，完成自动整理。

要求：
1. category 必须从这四个里面选一个：学习、技术、生活、其他。
2. tags 输出 3 到 5 个关键词，尽量短。
3. summary 用 80 到 180 字概括资料整体内容。
4. overall_evaluation 用 80 到 150 字评价这份资料的知识价值、适合谁学习、适合怎样复习或使用。
5. title_suggestion 给出一个更适合作为知识库标题的名称。
6. reason 用一句话说明为什么这样分类。
7. sections 输出 3 到 8 个"章节级总结"。不要机械按页切分，而是按连续主题/知识点分段。每个 section 包含：
   - section_title：章节/主题名称
   - location_hint：位置提示；如果能判断页码、章节名、时间段就写出来，不能判断就写"文档中部/相关部分/全文相关"
   - summary：80 到 160 字总结该章节讲了什么
   - keywords：2 到 5 个关键词
   - search_text：150 到 350 字适合语义检索的内容，包含关键概念、公式、术语、结论
8. search_text 输出 500 到 1500 字，整理出适合全文语义检索的核心内容。
9. 只输出 JSON，不要输出任何解释，不要使用 Markdown 代码块。

输出 JSON 格式：
{{
  "category": "学习",
  "tags": ["标签1", "标签2", "标签3"],
  "summary": "这里是整体摘要。",
  "overall_evaluation": "这里是整体评价。",
  "title_suggestion": "这里是建议标题。",
  "reason": "这里是一句话分类理由。",
  "sections": [
    {{
      "section_title": "章节主题1",
      "location_hint": "第1-3页/第一部分/全文相关",
      "summary": "这里是章节级总结。",
      "keywords": ["关键词1", "关键词2"],
      "search_text": "这里是用于语义检索的章节内容。"
    }}
  ],
  "search_text": "这里是适合全文语义检索的核心内容。"
}}

资料信息：
- 原始标题：{doc.get('title', '')}
- 资料类型：{doc.get('type', '')}
- 来源链接：{doc.get('url', '') or '无'}
- 字符数：{len(doc.get('text', ''))}

资料正文：
{text}
""".strip()


def build_qwen_doc_prompt(doc: Dict[str, Any]) -> str:
    """构建 Qwen-Doc-Turbo 文件直读提示词"""
    return f"""
你是一个"个人知识库自动整理助手"。请直接阅读我上传的原始文件，完成自动整理。

重要原则：
- 不要机械地逐页总结。很多资料连续好几页讲同一个主题，请按"连续主题 / 知识模块 / 章节逻辑"合并总结。
- 章节级总结要服务于后续模糊搜索定位：用户搜索某个知识点时，应该能命中对应章节，而不是只命中整篇文件。
- 如果文件是课件、教材、扫描 PDF 或图文混排资料，也要尽量根据可见内容判断章节主题。

要求：
1. category 必须从这四个里面选一个：学习、技术、生活、其他。
2. tags 输出 3 到 5 个关键词，尽量短。
3. summary 用 120 到 220 字概括整份资料内容。
4. overall_evaluation 用 80 到 150 字评价这份资料的知识价值、适合谁学习、适合怎样复习或使用。
5. title_suggestion 给出一个更适合作为知识库标题的名称。
6. reason 用一句话说明为什么这样分类。
7. sections 输出 3 到 8 个章节级总结。每个 section 包含：
   - section_title：章节/主题名称。
   - location_hint：位置提示。能判断页码就写"第x-y页"，不能准确判断就写"前半部分/中部/后半部分/相关章节"。
   - summary：80 到 160 字，总结这个章节讲了什么。
   - keywords：2 到 5 个关键词。
   - search_text：150 到 350 字，专门用于语义检索。
8. search_text 输出 600 到 1800 字，整理出适合全文语义检索的核心内容。
9. 只输出 JSON，不要输出任何解释，不要使用 Markdown 代码块。

输出 JSON 格式：
{{
  "category": "学习",
  "tags": ["标签1", "标签2", "标签3"],
  "summary": "这里是整份资料的总体摘要。",
  "overall_evaluation": "这里是对资料质量、用途和学习价值的整体评价。",
  "title_suggestion": "这里是建议标题。",
  "reason": "这里是一句话分类理由。",
  "sections": [
    {{
      "section_title": "章节主题1",
      "location_hint": "第1-4页/前半部分/相关章节",
      "summary": "这里是章节级总结。",
      "keywords": ["关键词1", "关键词2"],
      "search_text": "这里是该章节用于语义检索的内容。"
    }}
  ],
  "search_text": "这里是适合全文语义检索的核心内容。"
}}

文件信息：
- 原始标题：{doc.get('title', '')}
- 文件类型：{Path(doc.get('path', '')).suffix.lower()}
""".strip()


def normalize_organized_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """标准化 LLM 返回的整理结果"""
    category = result.get("category", "其他")
    if category not in settings.CATEGORIES:
        category = "其他"

    tags = result.get("tags", [])
    if isinstance(tags, str):
        tags = [x.strip() for x in re.split(r"[，,、/|]", tags) if x.strip()]
    if not isinstance(tags, list):
        tags = []
    tags = [str(x).strip() for x in tags if str(x).strip()][:5]

    normalized = {
        "category": category,
        "tags": tags or [category],
        "summary": str(result.get("summary", "")).strip(),
        "overall_evaluation": str(result.get("overall_evaluation", result.get("evaluation", ""))).strip(),
        "title_suggestion": str(result.get("title_suggestion", "")).strip(),
        "reason": str(result.get("reason", "")).strip(),
        "method": result.get("method", "llm_api"),
        "model": result.get("model", "unknown"),
    }

    if result.get("search_text"):
        normalized["search_text"] = clean_text(str(result.get("search_text", "")))[:6000]
    if result.get("outline"):
        normalized["outline"] = str(result.get("outline", "")).strip()

    raw_sections = result.get("sections", result.get("section_summaries", []))
    sections = []
    if isinstance(raw_sections, dict):
        raw_sections = list(raw_sections.values())
    if isinstance(raw_sections, list):
        for idx, sec in enumerate(raw_sections, start=1):
            if isinstance(sec, str):
                sec = {"section_title": f"主题 {idx}", "summary": sec}
            if not isinstance(sec, dict):
                continue
            title = str(sec.get("section_title", sec.get("title", f"主题 {idx}"))).strip() or f"主题 {idx}"
            location = str(sec.get("location_hint", sec.get("location", sec.get("page_range", "全文相关")))).strip() or "全文相关"
            summary = clean_text(str(sec.get("summary", sec.get("content", ""))))[:800]
            search_text = clean_text(str(sec.get("search_text", summary)))[:1000]
            keywords = sec.get("keywords", [])
            if isinstance(keywords, str):
                keywords = [x.strip() for x in re.split(r"[，,、/|]", keywords) if x.strip()]
            if not isinstance(keywords, list):
                keywords = []
            keywords = [str(x).strip() for x in keywords if str(x).strip()][:6]
            if not summary and not search_text:
                continue
            sections.append({
                "section_title": title,
                "location_hint": location,
                "summary": summary,
                "keywords": keywords,
                "search_text": search_text or summary,
            })
    if sections:
        normalized["sections"] = sections[:10]

    return normalized


async def call_llm_api(
    doc: Dict[str, Any],
    provider: Optional[str] = None,
    log_func: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """异步调用 LLM API 进行文档整理"""
    api_key, base_url, model_name = get_api_config(provider)
    if not api_key:
        raise RuntimeError(f"没有检测到 API Key。当前 provider={provider or settings.API_PROVIDER}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "你是一个严谨的个人知识库资料整理助手，只输出合法 JSON。"},
            {"role": "user", "content": build_prompt(doc)},
        ],
        "temperature": 0.2,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
        response = await client.post(base_url, headers=headers, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"API 请求失败，状态码={response.status_code}，返回={response.text}")

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        organized = extract_json_from_text(content)
        organized["method"] = "llm_api"
        organized["model"] = model_name
        return normalize_organized_result(organized)


def can_use_qwen_doc_turbo(doc: Dict[str, Any]) -> bool:
    """判断文档是否可以使用 Qwen-Doc-Turbo 文件直读"""
    if settings.API_PROVIDER != "qwen":
        return False
    if not settings.USE_QWEN_DOC_TURBO_FOR_FILES:
        return False
    path_str = doc.get("path", "")
    if not path_str:
        return False
    path = Path(path_str)
    if not path.exists():
        return False
    if path.suffix.lower() not in settings.qwen_doc_supported_exts_set:
        return False
    if path.suffix.lower() in settings.video_exts_set:
        return False
    return True


async def upload_file_to_qwen_doc(
    path: Path,
    log_func: Optional[Callable[[str], None]] = None,
) -> str:
    """上传文件给 Qwen-Doc-Turbo，返回 file_id"""
    if not settings.DASHSCOPE_API_KEY:
        raise RuntimeError("没有检测到 DASHSCOPE_API_KEY，无法上传文件给 Qwen-Doc-Turbo。")
    if log_func:
        log_func(f"上传原文件给 Qwen-Doc-Turbo：{path.name}")

    headers = {"Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}"}
    async with httpx.AsyncClient(timeout=settings.QWEN_DOC_UPLOAD_TIMEOUT) as client:
        with open(path, "rb") as f:
            files = {"file": (path.name, f)}
            data = {"purpose": "file-extract"}
            resp = await client.post(
                settings.QWEN_FILE_UPLOAD_URL,
                headers=headers,
                files=files,
                data=data,
            )
        if resp.status_code != 200:
            raise RuntimeError(f"文件上传失败，状态码={resp.status_code}，返回={resp.text}")

    obj = resp.json()
    file_id = obj.get("id")
    if not file_id:
        raise RuntimeError(f"文件上传成功但没有返回 file-id：{obj}")
    if log_func:
        log_func(f"文件上传成功：{file_id}")
    return file_id


async def call_qwen_doc_turbo_file(
    doc: Dict[str, Any],
    log_func: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """把 PDF/DOCX/PPT 等原文件上传给 qwen-doc-turbo，让模型直接读文件"""
    path = Path(doc.get("path", ""))
    file_id = await upload_file_to_qwen_doc(path, log_func=log_func)

    headers = {
        "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.QWEN_DOC_MODEL_NAME,
        "messages": [
            {"role": "system", "content": "你是一个严谨的个人知识库资料整理助手，只输出合法 JSON。"},
            {"role": "system", "content": f"fileid://{file_id}"},
            {"role": "user", "content": build_qwen_doc_prompt(doc)},
        ],
        "temperature": 0.2,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }

    last_text = ""
    for attempt in range(1, settings.QWEN_DOC_PARSE_RETRY + 1):
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
            resp = await client.post(settings.QWEN_BASE_URL, headers=headers, json=payload)
        last_text = resp.text
        if resp.status_code == 200:
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            organized = extract_json_from_text(content)
            organized["method"] = "qwen_doc_file"
            organized["model"] = settings.QWEN_DOC_MODEL_NAME
            organized["file_id"] = file_id
            return normalize_organized_result(organized)
        # 文件刚上传后可能还在解析，等一下再试
        if "File parsing in progress" in resp.text or "parsing" in resp.text.lower():
            if log_func:
                log_func(f"文件仍在解析，等待后重试 {attempt}/{settings.QWEN_DOC_PARSE_RETRY}...")
            import asyncio
            await asyncio.sleep(2 + attempt)
            continue
        raise RuntimeError(f"Qwen-Doc-Turbo 调用失败，状态码={resp.status_code}，返回={resp.text}")

    raise RuntimeError(f"Qwen-Doc-Turbo 多次重试后仍失败：{last_text}")


def rule_fallback(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    规则兜底整理：当 LLM API 不可用时，根据标题和正文高频关键词进行分类
    """
    text = doc.get("text", "")
    title = doc.get("title", "")
    content = f"{title}\n{text}"
    scores = {cat: sum(content.lower().count(kw.lower()) for kw in kws) for cat, kws in KEYWORD_BANK.items()}
    category = max(scores, key=scores.get) if scores else "其他"
    if scores.get(category, 0) <= 0:
        category = "其他"

    tags = []
    for kw in KEYWORD_BANK.get(category, []):
        if kw.lower() in content.lower() and kw not in tags:
            tags.append(kw)
    terms = re.findall(r"[\u4e00-\u9fa5]{2,8}", content)
    stop_words = {"这个", "一个", "我们", "你们", "他们", "进行", "通过", "可以", "以及", "相关", "内容", "资料", "信息", "系统", "本文", "主要", "包括", "根据", "为了", "实现", "使用"}
    freq = Counter(t for t in terms if t not in stop_words)
    for term, _ in freq.most_common(10):
        if term not in tags:
            tags.append(term)
        if len(tags) >= 5:
            break

    sentences = re.split(r"[。！？!?]\s*", clean_text(text))
    summary = ""
    for s in sentences:
        if s and len(summary) + len(s) <= 160:
            summary += s + "。"
    if not summary:
        summary = clean_text(text)[:160] or "未提取到有效正文。"

    return normalize_organized_result({
        "category": category,
        "tags": tags[:5] or [category],
        "summary": summary,
        "title_suggestion": title,
        "reason": "API 不可用时，根据标题和正文高频关键词进行规则兜底。",
        "method": "rule_fallback",
        "model": "none",
    })


async def organize_doc(
    doc: Dict[str, Any],
    provider: Optional[str] = None,
    log_func: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """
    整理文档：优先 Qwen-Doc-Turbo 文件直读 → 普通 LLM API → 规则兜底

    Args:
        doc: 文档数据，格式与 read_any_file() 返回值兼容
        provider: LLM 提供者，None 则使用默认
        log_func: 日志回调

    Returns:
        标准化整理结果
    """
    try:
        if can_use_qwen_doc_turbo(doc):
            if log_func:
                log_func("启用文件直读模式：原文件 → Qwen-Doc-Turbo → JSON")
            return await call_qwen_doc_turbo_file(doc, log_func=log_func)

        if log_func:
            log_func(f"调用 LLM API：provider={provider or settings.API_PROVIDER}")
        return await call_llm_api(doc, provider=provider, log_func=log_func)
    except Exception as e:
        if log_func:
            log_func(f"API/文件直读整理失败：{e}")

        # 文件直读失败时，再尝试把本地抽取出的文本交给普通 chat 模型
        if can_use_qwen_doc_turbo(doc) and clean_text(doc.get("text", "")):
            try:
                if log_func:
                    log_func("文件直读失败，改用本地抽取文本 + Chat 模型。")
                return await call_llm_api(doc, provider=provider, log_func=log_func)
            except Exception as e2:
                if log_func:
                    log_func(f"文本模式也失败：{e2}")

        if settings.USE_RULE_FALLBACK:
            if log_func:
                log_func("启用规则兜底，保证流程继续。")
            return rule_fallback(doc)
        raise
