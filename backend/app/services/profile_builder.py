# -*- coding: utf-8 -*-
"""
知识画像服务 — 复用桌面版 build_rule_based_knowledge_profile + call_llm_profile_api 逻辑
"""

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import httpx

from app.config import settings
from app.utils.text import clean_text, extract_json_from_text
from app.services.llm_organizer import get_api_config


# ---- 主题聚类规则 ----
PROFILE_CLUSTER_RULES = {
    "人工智能与深度学习": ["人工智能", "AI", "深度学习", "机器学习", "神经网络", "卷积", "CNN", "Transformer", "YOLO", "模型", "训练"],
    "数字电路与硬件设计": ["数字电路", "逻辑代数", "布尔代数", "组合逻辑", "时序逻辑", "Verilog", "HDL", "FPGA", "门电路"],
    "个人知识管理与检索系统": ["知识管理", "知识画像", "语义检索", "向量检索", "RAG", "FAISS", "Embedding", "标签", "摘要"],
    "机器人与智能系统": ["机器人", "运动学", "动力学", "控制", "路径规划", "SLAM", "自动驾驶", "智能车辆"],
    "科研项目与医学影像": ["纺锤体", "卵母细胞", "ICSI", "医学影像", "显微", "Hoffman", "PolScope", "检测"],
    "课程学习与考试复习": ["课程", "考试", "复习", "作业", "教材", "课堂", "学习", "报告", "PPT"],
    "思政与汇报材料": ["马克思主义", "毛泽东思想", "中国特色社会主义", "学校", "汇报", "党建", "思政"],
    "编程开发与工程实践": ["Python", "代码", "API", "PyQt", "前端", "部署", "CUDA", "GPU", "系统", "项目"],
}


def _item_text_for_profile(item: Dict[str, Any]) -> str:
    """拼接文档的所有文本用于画像分析"""
    doc = item.get("document", {})
    org = item.get("organized", {})
    parts = [
        str(doc.get("title", "")),
        str(org.get("title_suggestion", "")),
        str(org.get("category", "")),
        " ".join([str(x) for x in org.get("tags", [])]),
        str(org.get("summary", "")),
        str(org.get("search_text", ""))[:1000],
    ]
    for sec in org.get("sections", []) or []:
        if isinstance(sec, dict):
            parts.extend([
                str(sec.get("section_title", "")),
                " ".join([str(x) for x in sec.get("keywords", []) or []]),
                str(sec.get("summary", "")),
            ])
    return clean_text("\n".join(parts))


def _guess_item_time(item: Dict[str, Any]) -> str:
    """从文件路径或标题中猜测文档时间"""
    doc = item.get("document", {})
    path = doc.get("path", "")
    if path and Path(path).exists():
        try:
            ts = Path(path).stat().st_mtime
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
        except Exception:
            pass

    raw = f"{doc.get('title', '')} {path} {doc.get('url', '')}"
    m = re.search(r"(20\d{2})[-_年]?(\d{1,2})[-_月]?(\d{1,2})", raw)
    if m:
        y, mo, d = m.groups()
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    return "未知时间"


def build_rule_based_knowledge_profile(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    基于规则的画像生成：不用等 API，也能立刻生成的基础画像

    Args:
        items: 文档整理结果列表，每项包含 document 和 organized 字段

    Returns:
        画像字典
    """
    cat_counter = Counter()
    tag_counter = Counter()
    type_counter = Counter()
    method_counter = Counter()
    cluster_counter = Counter()
    cluster_items: Dict[str, List[str]] = {k: [] for k in PROFILE_CLUSTER_RULES}

    recent_items = []
    section_total = 0
    total_chars = 0

    for item in items:
        doc = item.get("document", {})
        org = item.get("organized", {})
        title = org.get("title_suggestion") or doc.get("title", "未命名资料")

        cat_counter[org.get("category", "其他")] += 1
        type_counter[doc.get("type", "unknown")] += 1
        method_counter[org.get("method", "unknown")] += 1
        total_chars += int(doc.get("char_count", 0) or 0)
        section_total += len(org.get("sections", []) or [])

        for tag in org.get("tags", []) or []:
            tag_counter[str(tag)] += 1

        text_blob = _item_text_for_profile(item)
        matched = False
        for cluster, keywords in PROFILE_CLUSTER_RULES.items():
            score = sum(text_blob.lower().count(k.lower()) for k in keywords)
            if score > 0:
                cluster_counter[cluster] += score
                if len(cluster_items[cluster]) < 5:
                    cluster_items[cluster].append(title)
                matched = True
        if not matched:
            cluster_counter["其他零散知识"] += 1

        recent_items.append({
            "date": _guess_item_time(item),
            "title": title,
            "category": org.get("category", "其他"),
            "tags": org.get("tags", [])[:4],
        })

    top_tags = tag_counter.most_common(15)
    top_clusters = cluster_counter.most_common(8)
    main_focus = top_clusters[0][0] if top_clusters else (cat_counter.most_common(1)[0][0] if cat_counter else "暂无")

    knowledge_gaps = []
    all_text = "\n".join(_item_text_for_profile(x) for x in items).lower()

    if any(k in all_text for k in ["卷积", "神经网络", "深度学习", "yolo"]):
        if not any(k.lower() in all_text for k in ["部署", "onnx", "tensorrt", "推理加速"]):
            knowledge_gaps.append("AI/深度学习资料较多，但模型部署、ONNX、TensorRT、推理加速相关资料偏少。")
        if not any(k.lower() in all_text for k in ["数据增强", "过拟合", "评估指标"]):
            knowledge_gaps.append("已有模型学习内容，但数据增强、过拟合分析、评估指标体系还可以继续补充。")
    if any(k.lower() in all_text for k in ["数字电路", "逻辑代数", "组合逻辑"]):
        if not any(k.lower() in all_text for k in ["时序逻辑", "verilog", "fpga"]):
            knowledge_gaps.append("数字电路已有基础理论，但时序逻辑、Verilog HDL、FPGA 实践资料不足。")
    if any(k.lower() in all_text for k in ["知识画像", "语义检索", "知识管理", "rag"]):
        if not any(k.lower() in all_text for k in ["前端", "可视化", "交互", "用户反馈"]):
            knowledge_gaps.append("知识管理系统已有检索与整理内容，但前端可视化、交互反馈、用户行为日志仍需完善。")
    if not knowledge_gaps:
        knowledge_gaps.append("当前资料规模还不大，建议继续导入更多课程、项目和阅读资料，以便形成更稳定的知识缺口判断。")

    learning_path = []
    if "数字电路与硬件设计" in cluster_counter:
        learning_path.append("数字电路：逻辑代数 → 组合逻辑 → 时序逻辑 → Verilog HDL → FPGA 小项目。")
    if "人工智能与深度学习" in cluster_counter:
        learning_path.append("AI方向：神经网络基础 → CNN/Transformer → 训练评估 → 项目复现 → 部署优化。")
    if "个人知识管理与检索系统" in cluster_counter:
        learning_path.append("知识管理系统：资料解析 → 摘要标签 → 向量检索 → 混合重排序 → 知识画像 → 个性化推荐。")
    if not learning_path:
        learning_path.append("建议先围绕出现频率最高的 2-3 个标签整理学习路径，再逐步补充实践资料。")

    profile = {
        "generated_by": "rule_based",
        "overview": {
            "total_documents": len(items),
            "knowledge_units": section_total,
            "total_chars": total_chars,
            "main_focus": main_focus,
            "top_tags": [t for t, _ in top_tags[:5]],
            "dominant_type": type_counter.most_common(1)[0][0] if type_counter else "暂无",
        },
        "theme_distribution": dict(cat_counter.most_common()),
        "type_distribution": dict(type_counter.most_common()),
        "method_distribution": dict(method_counter.most_common()),
        "tag_ranking": [{"tag": t, "count": n} for t, n in top_tags],
        "knowledge_clusters": [
            {
                "cluster": c,
                "score": n,
                "related_items": cluster_items.get(c, [])[:5],
            }
            for c, n in top_clusters
        ],
        "learning_timeline": recent_items[-10:][::-1],
        "knowledge_gaps": knowledge_gaps,
        "learning_path": learning_path,
        "growth_suggestions": [
            "把高频主题下的资料补成「理论-例题-项目-复盘」的完整链条。",
            "对长期只出现一次的标签进行复习或归档，避免知识点成为孤岛。",
            "后续可记录打开频率、阅读时长、笔记数量和推荐采纳情况，让画像从静态内容统计升级为动态学习画像。",
        ],
    }
    return profile


def compact_items_for_profile_llm(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """压缩文档列表用于 LLM 画像生成"""
    compact = []
    for item in items[-settings.PROFILE_MAX_ITEMS_FOR_LLM:]:
        doc = item.get("document", {})
        org = item.get("organized", {})
        compact.append({
            "title": org.get("title_suggestion") or doc.get("title", ""),
            "type": doc.get("type", ""),
            "category": org.get("category", ""),
            "tags": org.get("tags", []),
            "summary": org.get("summary", "")[:260],
            "sections": [
                {
                    "title": sec.get("section_title", ""),
                    "keywords": sec.get("keywords", []),
                    "summary": sec.get("summary", "")[:160],
                }
                for sec in (org.get("sections", []) or [])[:5]
                if isinstance(sec, dict)
            ],
        })
    return compact


def build_profile_prompt(items: List[Dict[str, Any]], base_profile: Dict[str, Any]) -> str:
    """构建 LLM 画像生成提示词"""
    compact_items = compact_items_for_profile_llm(items)
    return f"""
你是一个"个人知识画像分析助手"。请基于用户已经整理的资料，生成一个适合前端展示的知识画像。

分析原则：
1. 不要只统计文件数量，要从"内容层、关系层、动态层、建议层"总结。
2. 参考用户画像思路：数据采集 → 特征工程 → 模型构建 → 应用迭代。
3. 当前系统主要有资料内容、AI标签、摘要、章节总结，行为日志还不完整，所以不要编造阅读时长、打开频率、笔记次数。
4. 输出要服务于前端"知识画像"页面：画像总览、主题分布、高频标签、知识聚类、学习动态、知识缺口、学习路径、成长建议。
5. 只输出 JSON，不要输出 Markdown，不要解释。

必须输出 JSON 字段：
{{
  "profile_summary": "150字以内总结用户当前知识画像",
  "main_focus": "当前主攻方向",
  "learning_stage": "入门/进阶/项目实践/综合提升之一，也可加一句解释",
  "theme_insights": ["主题洞察1", "主题洞察2", "主题洞察3"],
  "knowledge_clusters": [
    {{"cluster": "主题簇名称", "description": "这个主题簇说明什么", "related_keywords": ["词1", "词2"], "suggested_next_step": "下一步建议"}}
  ],
  "knowledge_gaps": ["知识缺口1", "知识缺口2", "知识缺口3"],
  "learning_path": ["路径步骤1", "路径步骤2", "路径步骤3"],
  "growth_suggestions": ["建议1", "建议2", "建议3"],
  "dynamic_profile_notes": ["关于近期变化/待激活知识/后续行为日志的说明"]
}}

基础统计画像：
{json.dumps(base_profile, ensure_ascii=False)[:4000]}

资料摘要列表：
{json.dumps(compact_items, ensure_ascii=False)[:9000]}
""".strip()


def normalize_profile_result(result: Dict[str, Any], base_profile: Dict[str, Any]) -> Dict[str, Any]:
    """标准化 LLM 画像结果"""
    normalized = dict(base_profile)
    normalized["generated_by"] = result.get("generated_by", "llm_profile")
    normalized["llm_profile"] = {
        "profile_summary": str(result.get("profile_summary", "")).strip(),
        "main_focus": str(result.get("main_focus", base_profile.get("overview", {}).get("main_focus", ""))).strip(),
        "learning_stage": str(result.get("learning_stage", "")).strip(),
        "theme_insights": [str(x).strip() for x in result.get("theme_insights", []) if str(x).strip()][:6],
        "knowledge_clusters": result.get("knowledge_clusters", []) if isinstance(result.get("knowledge_clusters", []), list) else [],
        "knowledge_gaps": [str(x).strip() for x in result.get("knowledge_gaps", []) if str(x).strip()][:8],
        "learning_path": [str(x).strip() for x in result.get("learning_path", []) if str(x).strip()][:8],
        "growth_suggestions": [str(x).strip() for x in result.get("growth_suggestions", []) if str(x).strip()][:8],
        "dynamic_profile_notes": [str(x).strip() for x in result.get("dynamic_profile_notes", []) if str(x).strip()][:6],
    }
    return normalized


async def call_llm_profile_api(
    items: List[Dict[str, Any]],
    base_profile: Dict[str, Any],
    provider: Optional[str] = None,
    log_func: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """调用 LLM 生成深度知识画像"""
    api_key, base_url, model_name = get_api_config(provider)
    if not api_key:
        raise RuntimeError(f"没有检测到 API Key，无法生成 LLM 深度画像。当前 provider={provider or settings.API_PROVIDER}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "你是一个严谨的个人知识画像分析助手，只输出合法 JSON。"},
            {"role": "user", "content": build_profile_prompt(items, base_profile)},
        ],
        "temperature": 0.2,
        "max_tokens": 3000,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=settings.PROFILE_TIMEOUT) as client:
        response = await client.post(base_url, headers=headers, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"知识画像 API 请求失败，状态码={response.status_code}，返回={response.text}")

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        result = extract_json_from_text(content)
        result["generated_by"] = f"llm_profile:{model_name}"
        return normalize_profile_result(result, base_profile)


def profile_to_text(profile: Dict[str, Any]) -> str:
    """将画像数据转为可读文本"""
    overview = profile.get("overview", {})
    llm = profile.get("llm_profile", {}) if isinstance(profile.get("llm_profile", {}), dict) else {}

    lines = []
    lines.append("# 个人知识画像")
    lines.append("")
    lines.append("## 1. 画像总览")
    lines.append(f"- 总资料数：{overview.get('total_documents', 0)}")
    lines.append(f"- 章节级知识单元：{overview.get('knowledge_units', 0)} 个")
    lines.append(f"- 主攻方向：{llm.get('main_focus') or overview.get('main_focus', '暂无')}")
    if llm.get("learning_stage"):
        lines.append(f"- 学习阶段判断：{llm.get('learning_stage')}")
    lines.append(f"- 高频标签：{'、'.join(overview.get('top_tags', []) or ['暂无'])}")
    lines.append(f"- 主要资料类型：{overview.get('dominant_type', '暂无')}")
    lines.append(f"- 画像生成方式：{profile.get('generated_by', 'rule_based')}")
    if llm.get("profile_summary"):
        lines.append("")
        lines.append("画像摘要：")
        lines.append(llm.get("profile_summary", ""))

    lines.append("")
    lines.append("## 2. 主题分布")
    theme_distribution = profile.get("theme_distribution", {})
    total = max(1, sum(theme_distribution.values()) if isinstance(theme_distribution, dict) else 1)
    for cat, n in theme_distribution.items():
        pct = n / total * 100
        lines.append(f"- {cat}：{n} 篇 ({pct:.1f}%)")

    lines.append("")
    lines.append("## 3. 高频标签 TOP 15")
    for item in profile.get("tag_ranking", [])[:15]:
        lines.append(f"- {item.get('tag')}：{item.get('count')} 次")

    lines.append("")
    lines.append("## 4. 知识关系 / 主题聚类")
    llm_clusters = llm.get("knowledge_clusters", [])
    if llm_clusters:
        for c in llm_clusters[:8]:
            if not isinstance(c, dict):
                continue
            lines.append(f"- {c.get('cluster', '未命名主题簇')}：{c.get('description', '')}")
            kws = c.get("related_keywords", [])
            if kws:
                lines.append(f"  关键词：{'、'.join([str(x) for x in kws[:8]])}")
            if c.get("suggested_next_step"):
                lines.append(f"  下一步：{c.get('suggested_next_step')}")
    else:
        for c in profile.get("knowledge_clusters", [])[:8]:
            related = "、".join(c.get("related_items", [])[:3]) if c.get("related_items") else "暂无代表资料"
            lines.append(f"- {c.get('cluster')}：相关度 {c.get('score')}，代表资料：{related}")

    if llm.get("theme_insights"):
        lines.append("")
        lines.append("## 5. 主题洞察")
        for s in llm.get("theme_insights", []):
            lines.append(f"- {s}")

    lines.append("")
    lines.append("## 6. 知识缺口分析")
    gaps = llm.get("knowledge_gaps") or profile.get("knowledge_gaps", [])
    for g in gaps:
        lines.append(f"- {g}")

    lines.append("")
    lines.append("## 7. 个性化学习路径")
    path_steps = llm.get("learning_path") or profile.get("learning_path", [])
    for i, step in enumerate(path_steps, start=1):
        lines.append(f"{i}. {step}")

    lines.append("")
    lines.append("## 8. 成长建议")
    suggestions = llm.get("growth_suggestions") or profile.get("growth_suggestions", [])
    for s in suggestions:
        lines.append(f"- {s}")

    return "\n".join(lines)
