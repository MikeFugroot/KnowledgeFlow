# -*- coding: utf-8 -*-
"""
语义检索服务 — 复用桌面版 SearchIndexWorker + hybrid_rerank + expand_query 逻辑
将 QThread 替换为异步操作
"""

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from app.config import settings
from app.utils.text import clean_text
from app.utils.file_storage import get_vector_index_dir


# ---- 查询扩展词典 ----
QUERY_EXPANSION = {
    "卷积神经网络": ["CNN", "卷积", "卷积层", "卷积核", "特征图", "池化", "图像识别", "神经网络"],
    "卷积网络": ["卷积神经网络", "CNN", "卷积层", "卷积核", "特征图", "池化"],
    "神经网络": ["神经元", "激活函数", "层级结构", "权重", "反向传播", "深度学习"],
    "语义检索": ["向量检索", "embedding", "FAISS", "相似度搜索", "RAG", "知识库"],
    "知识画像": ["主题分布", "标签统计", "高频标签", "学习结构", "个人知识管理", "成长建议"],
    "虚短虚断": ["运算放大器", "虚短", "虚断", "负反馈", "输入电流", "输入电压"],
    "稳压管": ["二极管", "反向击穿", "稳压电路", "齐纳二极管", "稳压值"],
    "数字电路": ["逻辑代数", "布尔代数", "组合逻辑", "时序逻辑", "Verilog", "FPGA"],
    "机器人": ["运动学", "动力学", "控制", "路径规划", "感知", "SLAM"],
}


def expand_query(query: str) -> str:
    """把 5~15 字短问题补成更稳定的检索表达，避免纯向量匹配漂移"""
    q = clean_text(query)
    extra = []

    for key, words in QUERY_EXPANSION.items():
        if key.lower() in q.lower():
            extra.extend(words)

    if "卷积" in q and ("神经" in q or "网络" in q):
        extra.extend(["卷积神经网络", "CNN", "卷积层", "卷积核", "特征图", "池化"])
    if "CNN" in q.upper():
        extra.extend(["卷积神经网络", "卷积层", "卷积核", "特征图", "图像识别"])

    seen = set()
    extra_unique = []
    for x in extra:
        if x not in seen:
            seen.add(x)
            extra_unique.append(x)

    return (q + " " + " ".join(extra_unique)).strip() if extra_unique else q


def extract_query_terms(query: str) -> List[str]:
    """中文短查询不能只靠空格切词：保留原句，并加入 2~4 字 ngram 和扩展词"""
    q = clean_text(query)
    terms = []

    if q:
        terms.append(q)

    expanded = expand_query(q)
    parts = re.findall(r"[A-Za-z0-9_+\-#]+|[\u4e00-\u9fa5]+", expanded)

    for p in parts:
        if len(p) >= 2:
            terms.append(p)
        if re.fullmatch(r"[\u4e00-\u9fa5]+", p):
            for n in (2, 3, 4):
                if len(p) >= n:
                    for i in range(len(p) - n + 1):
                        terms.append(p[i:i + n])

    stop_terms = {
        "什么", "怎么", "如何", "这个", "那个", "一下", "为什么", "是不是",
        "可以", "不能", "以及", "进行", "相关", "资料", "内容", "一个",
    }

    cleaned = []
    seen = set()
    for t in terms:
        t = t.strip()
        if len(t) < 2 or t in stop_terms:
            continue
        if t not in seen:
            seen.add(t)
            cleaned.append(t)

    return cleaned[:40]


def split_text_with_overlap_for_search(text: str, chunk_size: int = 0, overlap: int = 0) -> List[str]:
    """将文本按 chunk_size 切块，overlap 重叠"""
    chunk_size = chunk_size or settings.SEARCH_CHUNK_SIZE
    overlap = overlap or settings.SEARCH_CHUNK_OVERLAP
    text = clean_text(text)
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def build_search_chunks_for_doc(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    根据文档类型生成搜索块

    PDF 按页切块，视频按时间段切块，其他按固定大小切块
    """
    doc_type = doc.get("type", "unknown")
    text = doc.get("text", "")
    chunks = []

    if doc_type == "pdf":
        page_pattern = re.compile(r"===== 第\s*(\d+)\s*页\s*=====")
        matches = list(page_pattern.finditer(text))
        if matches:
            for page_idx, match in enumerate(matches):
                page_number = int(match.group(1))
                start = match.end()
                end = matches[page_idx + 1].start() if page_idx + 1 < len(matches) else len(text)
                page_text = clean_text(text[start:end])
                for chunk_text in split_text_with_overlap_for_search(page_text):
                    chunks.append({
                        "doc_title": doc.get("title", ""),
                        "doc_type": doc_type,
                        "source": doc.get("path") or doc.get("url") or doc.get("json_path", ""),
                        "location": f"第 {page_number} 页",
                        "document_id": doc.get("document_id"),
                        "chunk_text": chunk_text,
                    })
            return chunks

    if doc_type == "video" and isinstance(doc.get("raw", {}).get("segments"), list):
        current_texts = []
        current_start = None
        current_end = None
        for seg in doc["raw"].get("segments", []):
            seg_text = clean_text(seg.get("text", ""))
            if not seg_text:
                continue
            if current_start is None:
                current_start = seg.get("start")
            current_end = seg.get("end")
            current_texts.append(seg_text)
            merged = clean_text(" ".join(current_texts))
            if len(merged) >= settings.SEARCH_CHUNK_SIZE:
                if current_start is not None and current_end is not None:
                    location = f"{float(current_start):.2f}s - {float(current_end):.2f}s"
                else:
                    location = "视频片段"
                chunks.append({
                    "doc_title": doc.get("title", ""),
                    "doc_type": doc_type,
                    "source": doc.get("path") or doc.get("url") or doc.get("json_path", ""),
                    "location": location,
                    "document_id": doc.get("document_id"),
                    "chunk_text": merged,
                })
                current_texts = []
                current_start = None
                current_end = None
        if current_texts:
            merged = clean_text(" ".join(current_texts))
            if current_start is not None and current_end is not None:
                location = f"{float(current_start):.2f}s - {float(current_end):.2f}s"
            else:
                location = "视频片段"
            chunks.append({
                "doc_title": doc.get("title", ""),
                "doc_type": doc_type,
                "source": doc.get("path") or doc.get("url") or doc.get("json_path", ""),
                "location": location,
                "document_id": doc.get("document_id"),
                "chunk_text": merged,
            })
        return chunks

    if doc_type == "ai_section":
        chunk_text = clean_text(text)
        if chunk_text:
            chunks.append({
                "doc_title": doc.get("title", ""),
                "doc_type": doc_type,
                "source": doc.get("path") or doc.get("url") or doc.get("json_path", ""),
                "location": doc.get("location", "章节级总结"),
                "section_title": doc.get("section_title", ""),
                "document_id": doc.get("document_id"),
                "chunk_text": chunk_text,
            })
        return chunks

    default_location = doc.get("location", "全文")
    for chunk_text in split_text_with_overlap_for_search(text):
        chunks.append({
            "doc_title": doc.get("title", ""),
            "doc_type": doc_type,
            "source": doc.get("path") or doc.get("url") or doc.get("json_path", ""),
            "location": default_location,
            "document_id": doc.get("document_id"),
            "chunk_text": chunk_text,
        })
    return chunks


def build_search_blob(chunk: Dict[str, Any]) -> str:
    """拼接搜索块的所有字段用于关键词匹配"""
    parts = [
        str(chunk.get("doc_title", "")),
        str(chunk.get("section_title", "")),
        str(chunk.get("location", "")),
        str(chunk.get("source", "")),
        str(chunk.get("chunk_text", "")),
    ]
    return clean_text("\n".join(parts))


def calc_lexical_score(query: str, chunk: Dict[str, Any]) -> Dict[str, Any]:
    """关键词、标题、路径、正文命中评分，并返回可解释命中原因"""
    q = clean_text(query)
    q_lower = q.lower()
    terms = extract_query_terms(q)

    title = str(chunk.get("doc_title", ""))
    section_title = str(chunk.get("section_title", ""))
    source = str(chunk.get("source", ""))
    text = str(chunk.get("chunk_text", ""))

    title_lower = title.lower()
    section_lower = section_title.lower()
    source_lower = source.lower()
    text_lower = text.lower()
    blob_lower = build_search_blob(chunk).lower()

    raw = 0.0
    reasons = []

    if q_lower and q_lower in title_lower:
        raw += 3.2
        reasons.append("标题完整命中")
    if q_lower and q_lower in section_lower:
        raw += 3.0
        reasons.append("章节标题完整命中")
    if q_lower and q_lower in source_lower:
        raw += 2.7
        reasons.append("文件名/链接完整命中")
    if q_lower and q_lower in text_lower:
        raw += 2.4
        reasons.append("正文完整命中")

    hit_terms = []
    for t in terms:
        tl = t.lower()
        if tl in blob_lower:
            hit_terms.append(t)
            if tl in title_lower:
                raw += 0.75
            elif tl in section_lower:
                raw += 0.72
            elif tl in source_lower:
                raw += 0.60
            elif tl in text_lower:
                raw += 0.35
            else:
                raw += 0.20

    if terms:
        coverage = len(set(hit_terms)) / max(1, len(set(terms)))
        raw += coverage * 1.5
    else:
        coverage = 0.0

    doc_type = chunk.get("doc_type", "")
    type_boost = 0.0
    if doc_type == "ai_section":
        type_boost = 0.25
        reasons.append("章节级知识单元")
    elif doc_type == "ai_summary":
        type_boost = 0.12
        reasons.append("AI整体摘要")

    lexical_score = min(1.0, raw / 5.0)

    if hit_terms:
        reasons.append("命中词：" + "、".join(hit_terms[:8]))

    return {
        "lexical_score": lexical_score,
        "type_boost": type_boost,
        "hit_terms": hit_terms,
        "reason": "；".join(reasons) if reasons else "语义相关",
        "coverage": coverage,
    }


def hybrid_rerank_results(
    query: str,
    dense_items: List[Dict[str, Any]],
    lexical_items: List[Dict[str, Any]],
    top_k: int = 0,
) -> List[Dict[str, Any]]:
    """合并向量召回和关键词召回，再按短查询友好的综合分排序"""
    top_k = top_k or settings.SEARCH_TOP_K

    merged: Dict[Any, Dict[str, Any]] = {}

    for item in dense_items:
        gid = item.get("global_chunk_id")
        if gid is None:
            gid = f"{item.get('source', '')}_{item.get('location', '')}_{item.get('chunk_text', '')[:40]}"
        merged[gid] = item

    for item in lexical_items:
        gid = item.get("global_chunk_id")
        if gid is None:
            gid = f"{item.get('source', '')}_{item.get('location', '')}_{item.get('chunk_text', '')[:40]}"
        if gid in merged:
            item["dense_score"] = max(float(merged[gid].get("dense_score", 0.0)), float(item.get("dense_score", 0.0)))
        merged[gid] = item

    # 短查询更相信关键词命中，长句描述更相信语义向量
    q_len = len(clean_text(query))
    if q_len <= 15:
        dense_w, lexical_w = 0.35, 0.55
    else:
        dense_w, lexical_w = 0.55, 0.35

    final_items = []
    q_lower = clean_text(query).lower()

    for item in merged.values():
        lex_info = calc_lexical_score(query, item)
        dense_score = float(item.get("dense_score", 0.0))
        lexical_score = float(lex_info["lexical_score"])
        type_boost = float(lex_info["type_boost"])

        final_score = dense_w * dense_score + lexical_w * lexical_score + type_boost

        if q_lower and q_lower in build_search_blob(item).lower():
            final_score += 0.25

        item["score"] = float(final_score)
        item["dense_score"] = dense_score
        item["lexical_score"] = lexical_score
        item["match_reason"] = lex_info["reason"]
        item["hit_terms"] = lex_info["hit_terms"]
        final_items.append(item)

    final_items.sort(key=lambda x: x.get("score", 0.0), reverse=True)

    for rank, item in enumerate(final_items[:top_k], start=1):
        item["rank"] = rank

    return final_items[:top_k]


class SearchEngine:
    """
    语义检索引擎

    管理向量索引的构建、搜索、状态查询
    """

    def __init__(self) -> None:
        self._model = None
        self._index = None
        self._chunks: List[Dict[str, Any]] = []
        self._is_ready: bool = False
        self._last_built_at: Optional[str] = None
        self._embedding_model_name: str = settings.EMBEDDING_MODEL_NAME

    @property
    def is_ready(self) -> bool:
        """索引是否就绪"""
        return self._is_ready

    @property
    def total_chunks(self) -> int:
        """索引中的文本块数"""
        return len(self._chunks)

    @property
    def last_built_at(self) -> Optional[str]:
        """上次构建时间"""
        return self._last_built_at

    async def _load_documents_from_db(self, db) -> List[Dict[str, Any]]:
        """从数据库加载所有文档和章节用于索引构建"""
        from app.models.document import Document, Section
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        documents = []
        stmt = select(Document).options(selectinload(Document.sections))
        result = await db.execute(stmt)
        docs = result.scalars().all()

        for doc in docs:
            # 整体摘要
            whole_parts = []
            if doc.title_suggestion:
                whole_parts.append(f"标题：{doc.title_suggestion}")
            if doc.summary:
                whole_parts.append(f"整体摘要：{doc.summary}")
            if doc.overall_evaluation:
                whole_parts.append(f"整体评价：{doc.overall_evaluation}")
            if doc.tags:
                tag_names = [t.name for t in doc.tags]
                whole_parts.append("标签：" + "、".join(tag_names))
            if doc.search_text:
                whole_parts.append(f"全文核心内容：{doc.search_text}")
            merged = clean_text("\n".join(whole_parts))
            if merged:
                source = doc.source_path or doc.source_url
                documents.append({
                    "type": "ai_summary",
                    "title": doc.title_suggestion or doc.original_title,
                    "path": source,
                    "url": doc.source_url,
                    "text": merged,
                    "location": "整体总结",
                    "document_id": doc.id,
                })

            # 章节级总结
            for sec in doc.sections:
                sec_parts = [f"章节标题：{sec.section_title}", f"位置提示：{sec.location_hint}"]
                if sec.summary:
                    sec_parts.append(f"章节总结：{sec.summary}")
                if sec.search_text:
                    sec_parts.append(f"章节核心内容：{sec.search_text}")
                sec_text = clean_text("\n".join(sec_parts))
                if sec_text:
                    documents.append({
                        "type": "ai_section",
                        "title": f"{doc.title_suggestion or doc.original_title} / {sec.section_title}",
                        "path": source,
                        "url": "",
                        "text": sec_text,
                        "location": sec.location_hint,
                        "section_title": sec.section_title,
                        "document_id": doc.id,
                    })

        return documents

    async def build_index(self, db, log_func: Optional[Callable[[str], None]] = None) -> None:
        """
        构建语义检索索引

        Args:
            db: 数据库会话
            log_func: 日志回调
        """
        import numpy as np
        import faiss
        import torch
        from sentence_transformers import SentenceTransformer

        vector_dir = get_vector_index_dir()

        docs = await self._load_documents_from_db(db)
        if not docs:
            raise RuntimeError("没有可检索的文档。请先导入并处理至少一个文件。")

        chunks = []
        for doc_id_counter, doc in enumerate(docs):
            doc_chunks = build_search_chunks_for_doc(doc)
            for c in doc_chunks:
                c["doc_id"] = doc_id_counter
                c["global_chunk_id"] = len(chunks)
                chunks.append(c)
            if log_func:
                log_func(f"索引资料：{doc.get('title', '')}，切块 {len(doc_chunks)} 个")

        if not chunks:
            raise RuntimeError("没有可用于检索的文本块。")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        if log_func:
            log_func(f"加载 embedding 模型：{self._embedding_model_name}，device={device}")

        model = SentenceTransformer(self._embedding_model_name, device=device)
        texts = [c["chunk_text"] for c in chunks]
        if log_func:
            log_func(f"开始向量化：{len(texts)} 个文本块")

        embeddings = model.encode(
            texts,
            batch_size=settings.SEARCH_BATCH_SIZE,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).astype("float32")

        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)

        # 保存索引到磁盘
        faiss.write_index(index, str(vector_dir / "faiss.index"))
        np.save(vector_dir / "embeddings.npy", embeddings)
        with open(vector_dir / "chunks_metadata.json", "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

        self._model = model
        self._index = index
        self._chunks = chunks
        self._is_ready = True
        self._last_built_at = datetime.now().isoformat()

        if log_func:
            log_func(f"向量索引建立完成：{index.ntotal} 个向量，维度 {embeddings.shape[1]}")

    def _load_documents_from_db_sync(self) -> List[Dict[str, Any]]:
        """从数据库同步加载所有文档和章节用于索引构建"""
        from app.database import SyncSessionLocal
        from app.models.document import Document, Section
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        documents = []
        with SyncSessionLocal() as db:
            stmt = select(Document).options(selectinload(Document.sections), selectinload(Document.tags))
            result = db.execute(stmt)
            docs = result.scalars().all()

            for doc in docs:
                # 整体摘要
                whole_parts = []
                if doc.title_suggestion:
                    whole_parts.append(f"标题：{doc.title_suggestion}")
                if doc.summary:
                    whole_parts.append(f"整体摘要：{doc.summary}")
                if doc.overall_evaluation:
                    whole_parts.append(f"整体评价：{doc.overall_evaluation}")
                if doc.tags:
                    tag_names = [t.name for t in doc.tags]
                    whole_parts.append("标签：" + "、".join(tag_names))
                if doc.search_text:
                    whole_parts.append(f"全文核心内容：{doc.search_text}")
                merged = clean_text("\n".join(whole_parts))
                if merged:
                    source = doc.source_path or doc.source_url
                    documents.append({
                        "type": "ai_summary",
                        "title": doc.title_suggestion or doc.original_title,
                        "path": source,
                        "url": doc.source_url,
                        "text": merged,
                        "location": "整体总结",
                        "document_id": doc.id,
                    })

                # 章节级总结
                for sec in doc.sections:
                    sec_parts = [f"章节标题：{sec.section_title}", f"位置提示：{sec.location_hint}"]
                    if sec.summary:
                        sec_parts.append(f"章节总结：{sec.summary}")
                    if sec.search_text:
                        sec_parts.append(f"章节核心内容：{sec.search_text}")
                    sec_text = clean_text("\n".join(sec_parts))
                    if sec_text:
                        documents.append({
                            "type": "ai_section",
                            "title": f"{doc.title_suggestion or doc.original_title} / {sec.section_title}",
                            "path": source,
                            "url": "",
                            "text": sec_text,
                            "location": sec.location_hint,
                            "section_title": sec.section_title,
                            "document_id": doc.id,
                        })

        return documents

    def build_index_sync(self, log_func: Optional[Callable[[str], None]] = None) -> None:
        """
        同步构建语义检索索引（用于后台 worker 的 asyncio.to_thread 调用）

        使用 SyncSessionLocal 加载数据，避免 aiosqlite greenlet 问题。
        """
        import numpy as np
        import faiss
        import torch
        from sentence_transformers import SentenceTransformer

        vector_dir = get_vector_index_dir()

        docs = self._load_documents_from_db_sync()
        if not docs:
            raise RuntimeError("没有可检索的文档。请先导入并处理至少一个文件。")

        chunks = []
        for doc_id_counter, doc in enumerate(docs):
            doc_chunks = build_search_chunks_for_doc(doc)
            for c in doc_chunks:
                c["doc_id"] = doc_id_counter
                c["global_chunk_id"] = len(chunks)
                chunks.append(c)
            if log_func:
                log_func(f"索引资料：{doc.get('title', '')}，切块 {len(doc_chunks)} 个")

        if not chunks:
            raise RuntimeError("没有可用于检索的文本块。")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        if log_func:
            log_func(f"加载 embedding 模型：{self._embedding_model_name}，device={device}")

        model = SentenceTransformer(self._embedding_model_name, device=device)
        texts = [c["chunk_text"] for c in chunks]
        if log_func:
            log_func(f"开始向量化：{len(texts)} 个文本块")

        embeddings = model.encode(
            texts,
            batch_size=settings.SEARCH_BATCH_SIZE,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).astype("float32")

        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)

        # 保存索引到磁盘
        faiss.write_index(index, str(vector_dir / "faiss.index"))
        np.save(vector_dir / "embeddings.npy", embeddings)
        with open(vector_dir / "chunks_metadata.json", "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

        self._model = model
        self._index = index
        self._chunks = chunks
        self._is_ready = True
        self._last_built_at = datetime.now().isoformat()

        if log_func:
            log_func(f"向量索引建立完成：{index.ntotal} 个向量，维度 {embeddings.shape[1]}")

    async def search(self, query: str, top_k: int = 0) -> List[Dict[str, Any]]:
        """
        执行混合语义检索

        Args:
            query: 查询词
            top_k: 返回结果数

        Returns:
            排序后的检索结果列表
        """
        top_k = top_k or settings.SEARCH_TOP_K
        if not self._is_ready or self._index is None:
            raise RuntimeError("检索索引未就绪，请先构建索引。")

        import numpy as np

        # 向量检索
        expanded_query = expand_query(query)
        query_embedding = self._model.encode(
            [expanded_query],
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).astype("float32")

        candidate_k = min(settings.SEARCH_CANDIDATE_K, len(self._chunks))
        distances, indices = self._index.search(query_embedding, candidate_k)

        dense_items = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < 0 or idx >= len(self._chunks):
                continue
            chunk = dict(self._chunks[idx])
            chunk["dense_score"] = float(dist)
            dense_items.append(chunk)

        # 关键词检索
        terms = extract_query_terms(query)
        lexical_items = []
        for chunk in self._chunks:
            blob = build_search_blob(chunk).lower()
            hit = False
            for t in terms:
                if t.lower() in blob:
                    hit = True
                    break
            if hit:
                lexical_items.append(dict(chunk))

        # 限制关键词候选数
        lexical_items = lexical_items[:settings.LEXICAL_CANDIDATE_K]

        # 混合重排序
        return hybrid_rerank_results(query, dense_items, lexical_items, top_k)

    def load_index_from_disk(self) -> bool:
        """从磁盘加载已有索引"""
        try:
            import numpy as np
            import faiss
            from sentence_transformers import SentenceTransformer

            vector_dir = get_vector_index_dir()
            index_path = vector_dir / "faiss.index"
            chunks_path = vector_dir / "chunks_metadata.json"

            if not index_path.exists() or not chunks_path.exists():
                return False

            self._index = faiss.read_index(str(index_path))

            with open(chunks_path, "r", encoding="utf-8") as f:
                self._chunks = json.load(f)

            # 延迟加载模型（首次搜索时加载）
            self._is_ready = True
            return True
        except Exception:
            return False

    def ensure_model_loaded(self) -> None:
        """确保 embedding 模型已加载"""
        if self._model is not None:
            return
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(self._embedding_model_name)


# 全局搜索引擎实例
search_engine = SearchEngine()
