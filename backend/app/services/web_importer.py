# -*- coding: utf-8 -*-
"""
网页导入服务 — 复用桌面版 WebImporter/BilibiliFetcher/XiaohongshuFetcher/GenericWebFetcher
去掉 PyQt 依赖，改为异步兼容
"""

import hashlib
import json
import re
import time
import traceback
from functools import reduce
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs, quote

import requests

from app.config import settings
from app.utils.text import clean_text
from app.utils.file_storage import get_web_cache_dir


# ---- 可选依赖检测 ----
_BS4_AVAILABLE = False
_TRAFILATURA_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    _BS4_AVAILABLE = True
except ImportError:
    pass

try:
    import trafilatura
    _TRAFILATURA_AVAILABLE = True
except ImportError:
    pass


# ---- HTTP 请求工具 ----

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com/",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def safe_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict] = None,
    cookies: Optional[Dict] = None,
    params: Optional[Dict] = None,
    json_data: Optional[Dict] = None,
    timeout: int = 15,
    max_retries: int = 3,
    session: Optional[requests.Session] = None,
) -> Optional[requests.Response]:
    """带重试的 HTTP 请求"""
    s = session or requests.Session()
    merged_headers = {**DEFAULT_HEADERS, **(headers or {})}

    for attempt in range(max_retries):
        try:
            if method.upper() == "GET":
                resp = s.get(url, headers=merged_headers, cookies=cookies,
                             params=params, timeout=timeout)
            else:
                resp = s.post(url, headers=merged_headers, cookies=cookies,
                              params=params, json=json_data, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(1 * (attempt + 1))
        except requests.exceptions.HTTPError:
            if resp is not None and resp.status_code == 412:
                time.sleep(2 * (attempt + 1))
            elif resp is not None and resp.status_code in (401, 403):
                raise
            elif attempt < max_retries - 1:
                time.sleep(1 * (attempt + 1))
            else:
                raise
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
    return None


def parse_cookie_string(cookie_str: str) -> Dict[str, str]:
    """将浏览器复制的 Cookie 字符串解析为 dict"""
    cookies = {}
    for item in cookie_str.split(";"):
        item = item.strip()
        if "=" in item:
            key, _, value = item.partition("=")
            if key.strip():
                cookies[key.strip()] = value.strip()
    return cookies


# ---- B站 WBI 签名 ----

MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52,
]


def _get_mixin_key(raw_key: str) -> str:
    return reduce(lambda s, i: s + raw_key[i], MIXIN_KEY_ENC_TAB, "")[:32]


def sign_wbi_params(params: Dict[str, Any], img_key: str, sub_key: str) -> Dict[str, Any]:
    """为 B 站 WBI 接口参数添加签名"""
    signed = dict(params)
    signed["wts"] = int(time.time())
    sorted_params = dict(sorted(signed.items()))
    filtered = {
        k: "".join(ch for ch in str(v) if ch not in "!'()*")
        for k, v in sorted_params.items()
    }
    query = "&".join(
        f"{quote(str(k), safe='')}={quote(str(v), safe='')}"
        for k, v in filtered.items()
    )
    mixin_key = _get_mixin_key(img_key + sub_key)
    filtered["w_rid"] = hashlib.md5((query + mixin_key).encode()).hexdigest()
    return filtered


def extract_wbi_keys_from_nav(data: Dict[str, Any]) -> Tuple[str, str]:
    """从 nav 接口返回数据中提取 WBI 签名密钥"""
    wbi_img = data.get("data", {}).get("wbi_img", {}) or {}
    img_url = wbi_img.get("img_url", "") or ""
    sub_url = wbi_img.get("sub_url", "") or ""
    img_key = img_url.rsplit("/", 1)[-1].split(".")[0]
    sub_key = sub_url.rsplit("/", 1)[-1].split(".")[0]
    if not img_key or not sub_key:
        raise RuntimeError("nav 接口未返回 wbi_img 密钥")
    return img_key, sub_key


# ---- 通用网页抓取器 ----

class GenericWebFetcher:
    """通用网页正文提取"""

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()

    def fetch(self, url: str) -> Dict[str, Any]:
        """抓取网页正文"""
        result = {
            "title": "",
            "full_text": "",
            "source_url": url,
            "source_type": "webpage",
            "metadata": {},
        }

        resp = safe_request(url, session=self.session)
        if resp is None:
            result["full_text"] = f"[ERROR] 无法访问网页: {url}"
            return result

        html = resp.text
        result["metadata"]["content_type"] = resp.headers.get("Content-Type", "")

        # trafilatura 优先
        full_text = ""
        if _TRAFILATURA_AVAILABLE:
            extracted = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                include_images=False,
                output_format="markdown",
                url=url,
            )
            if extracted:
                full_text = extracted

        # BeautifulSoup 兜底
        if not full_text and _BS4_AVAILABLE:
            full_text = self._extract_with_bs4(html, url)
        elif not full_text:
            full_text = self._simple_strip_tags(html)

        # 提取标题
        if _BS4_AVAILABLE:
            soup = BeautifulSoup(html, "html.parser")
            if soup.title and soup.title.string:
                result["title"] = soup.title.string.strip()
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                result["title"] = og_title["content"].strip()
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                result["metadata"]["description"] = meta_desc["content"].strip()[:200]

        if not result["title"]:
            result["title"] = url.split("/")[-1][:60]

        result["full_text"] = self._clean_text(full_text)
        return result

    def _extract_with_bs4(self, html: str, url: str = "") -> str:
        """BeautifulSoup 正文提取"""
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(["script", "style", "nav", "footer", "header",
                                   "noscript", "iframe", "form"]):
            tag.decompose()

        content_selectors = [
            "article", "main", '[role="main"]',
            ".article-content", ".post-content", ".entry-content",
            ".content", ".markdown-body", "#content",
            ".note-content", ".note-text",
        ]

        for selector in content_selectors:
            container = soup.select_one(selector)
            if container:
                text = container.get_text(separator="\n", strip=True)
                if len(text) > 100:
                    return text

        body = soup.find("body")
        if body:
            return body.get_text(separator="\n", strip=True)
        return ""

    @staticmethod
    def _simple_strip_tags(html: str) -> str:
        return re.sub(r"<[^>]+>", " ", html)

    @staticmethod
    def _clean_text(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{3,}", "  ", text)
        return text.strip()


# ---- B站抓取器 ----

class BilibiliFetcher:
    """B站内容抓取器"""

    API_BASE = "https://api.bilibili.com"
    FAV_BASE = "https://api.bilibili.com/x/v3/fav"

    def __init__(
        self,
        cookie_str: str = "",
        whisper_fallback: bool = True,
        audio_download_dir: Optional[str] = None,
        whisper_model_size: str = "medium",
        progress_callback: Optional[Callable[[str], None]] = None,
    ):
        self.session = requests.Session()
        self.cookies: Dict[str, str] = {}
        if cookie_str:
            self.cookies = parse_cookie_string(cookie_str)
            self.session.cookies.update(self.cookies)
        self._uid: Optional[int] = None
        self._wbi_keys_cache: Optional[Tuple[str, str, float]] = None

        self.whisper_fallback = whisper_fallback
        self.audio_download_dir = Path(audio_download_dir or get_web_cache_dir() / "bilibili_audio")
        self.audio_download_dir.mkdir(parents=True, exist_ok=True)
        self.whisper_model_size = whisper_model_size
        self._progress = progress_callback

    def _log(self, msg: str) -> None:
        if self._progress:
            self._progress(msg)

    def test_auth(self) -> Tuple[bool, str]:
        """测试 Cookie 是否有效"""
        resp = safe_request(
            f"{self.API_BASE}/x/web-interface/nav",
            cookies=self.cookies,
            session=self.session,
        )
        if resp is None:
            return False, "网络请求失败"
        data = resp.json()
        if data.get("code") == 0 and data.get("data", {}).get("isLogin"):
            self._uid = data["data"]["mid"]
            uname = data["data"].get("uname", "未知")
            return True, f"已登录: {uname} (UID: {self._uid})"
        return False, f"未登录: {data.get('message', '未知错误')}"

    def _get_wbi_keys(self) -> Tuple[str, str]:
        """从 nav 接口获取 WBI 签名密钥"""
        now = time.time()
        if self._wbi_keys_cache and now - self._wbi_keys_cache[2] < 3600:
            return self._wbi_keys_cache[0], self._wbi_keys_cache[1]

        resp = safe_request(
            f"{self.API_BASE}/x/web-interface/nav",
            cookies=self.cookies,
            session=self.session,
        )
        if resp is None:
            raise RuntimeError("无法获取 WBI 密钥：nav 请求失败")
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"无法获取 WBI 密钥：{data.get('message')}")
        img_key, sub_key = extract_wbi_keys_from_nav(data)
        self._wbi_keys_cache = (img_key, sub_key, now)
        return img_key, sub_key

    def get_video_info(self, bvid: str) -> Dict[str, Any]:
        """获取单个视频信息"""
        resp = safe_request(
            f"{self.API_BASE}/x/web-interface/view",
            params={"bvid": bvid},
            cookies=self.cookies,
            session=self.session,
        )
        if resp is None:
            return {"error": f"无法获取视频信息: {bvid}"}

        data = resp.json()
        if data.get("code") != 0:
            return {"error": f"B站 API 错误: {data.get('message')}"}

        vdata = data["data"]
        return {
            "bvid": vdata.get("bvid", bvid),
            "aid": vdata.get("aid"),
            "title": vdata.get("title", ""),
            "description": vdata.get("desc", ""),
            "author": vdata.get("owner", {}).get("name", ""),
            "duration": vdata.get("duration", 0),
            "tags": [t.get("tag_name", "") for t in vdata.get("tags", [])],
            "pages": [
                {"cid": p.get("cid"), "title": p.get("part", ""),
                 "duration": p.get("duration", 0)}
                for p in vdata.get("pages", [])
            ],
            "thumbnail": vdata.get("pic", ""),
        }

    def _get_subtitle_meta_list(self, bvid: str, cid: int, aid: Optional[int] = None) -> List[Dict[str, Any]]:
        """从 player 接口获取字幕元数据"""
        if not self.cookies.get("SESSDATA"):
            self._log("未检测到 SESSDATA：B 站字幕接口通常需要登录 Cookie")

        base_params: Dict[str, Any] = {"cid": int(cid), "web_location": "1315873", "isGaiaAvoided": "false"}
        if aid:
            base_params["aid"] = int(aid)
        if bvid:
            base_params["bvid"] = bvid

        # 尝试 WBI 签名
        try:
            img_key, sub_key = self._get_wbi_keys()
            signed_params = sign_wbi_params(base_params, img_key, sub_key)
            resp = safe_request(
                f"{self.API_BASE}/x/player/wbi/v2",
                params=signed_params,
                cookies=self.cookies,
                session=self.session,
            )
            if resp is not None:
                data = resp.json()
                if data.get("code") == 0:
                    subtitle_obj = data.get("data", {}).get("subtitle", {}) or {}
                    subs = subtitle_obj.get("subtitles") or subtitle_obj.get("list") or []
                    if subs:
                        return subs
        except Exception:
            pass

        # 无签名尝试
        resp = safe_request(
            f"{self.API_BASE}/x/player/v2",
            params=base_params,
            cookies=self.cookies,
            session=self.session,
        )
        if resp is not None:
            data = resp.json()
            if data.get("code") == 0:
                subtitle_obj = data.get("data", {}).get("subtitle", {}) or {}
                return subtitle_obj.get("subtitles") or subtitle_obj.get("list") or []
        return []

    def extract_subtitle(self, bvid: str, cid: int, aid: Optional[int] = None) -> str:
        """提取 B 站视频字幕"""
        subtitle_info = self._get_subtitle_meta_list(bvid, cid, aid=aid)
        if not subtitle_info:
            self._log(f"未获取到字幕元数据：bvid={bvid} cid={cid}")
            return ""

        all_texts = []
        for sub in subtitle_info:
            lang = sub.get("lan_doc", sub.get("lan", "未知"))
            sub_url = sub.get("subtitle_url") or sub.get("subtitle_url_v2") or ""
            if not sub_url:
                continue
            if sub_url.startswith("//"):
                sub_url = "https:" + sub_url
            elif not sub_url.startswith("http"):
                sub_url = "https://" + sub_url.lstrip("/")

            headers = {"Referer": f"https://www.bilibili.com/video/{bvid}"}
            sub_resp = safe_request(sub_url, session=self.session, headers=headers, cookies=self.cookies)
            if sub_resp is None:
                continue

            try:
                sub_data = sub_resp.json()
            except json.JSONDecodeError:
                continue

            lines = []
            for item in sub_data.get("body", []):
                content = (item.get("content") or "").strip()
                if content:
                    lines.append(content)

            if lines:
                all_texts.append(f"[字幕·{lang}]\n" + "\n".join(lines))
                # 优先使用中文字幕
                if "中文" in lang or (sub.get("lan") or "").startswith("ai-zh"):
                    break

        return "\n\n".join(all_texts)

    def download_audio(self, bvid: str, cid: int = 0) -> Optional[Path]:
        """用 yt-dlp 下载 B 站视频纯音频"""
        import shutil
        import subprocess

        if not shutil.which("yt-dlp"):
            self._log("yt-dlp 未安装。安装: pip install yt-dlp")
            return None

        url = f"https://www.bilibili.com/video/{bvid}"
        if cid:
            url = f"https://www.bilibili.com/video/{bvid}/?p={cid}"

        file_hash = hashlib.md5(f"{bvid}_{cid}".encode()).hexdigest()[:10]
        output_template = str(self.audio_download_dir / f"bili_{bvid}_{file_hash}")

        cmd = [
            "yt-dlp", url,
            "--extract-audio", "--audio-format", "wav",
            "--audio-quality", "0",
            "--output", f"{output_template}.%(ext)s",
            "--no-playlist", "--no-overwrites",
            "--socket-timeout", "30", "--retries", "3", "--quiet",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                self._log(f"yt-dlp 下载失败: {result.stderr[-200:]}")
                return None

            output_path = self.audio_download_dir / f"bili_{bvid}_{file_hash}.wav"
            if output_path.exists():
                return output_path
            for ext in [".m4a", ".opus", ".aac", ".mp3"]:
                alt_path = Path(str(output_path).replace(".wav", ext))
                if alt_path.exists():
                    return alt_path
            return None
        except Exception as e:
            self._log(f"yt-dlp 异常: {e}")
            return None

    def transcribe_audio(self, audio_path: Path, model_size: Optional[str] = None) -> str:
        """Whisper 音频转写"""
        if not audio_path.exists():
            return ""

        model_size = model_size or self.whisper_model_size
        self._log(f"Whisper 转写中（模型: {model_size}）...")

        # faster-whisper 优先
        try:
            from faster_whisper import WhisperModel
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type = "int8_float16" if device == "cuda" else "int8"
            model = WhisperModel(model_size, device=device, compute_type=compute_type)
            segments, info = model.transcribe(
                str(audio_path), beam_size=5, vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
            )

            lines = []
            for seg in segments:
                if seg.text.strip():
                    start_m = int(seg.start // 60)
                    start_s = int(seg.start % 60)
                    lines.append(f"[{start_m:02d}:{start_s:02d}] {seg.text.strip()}")

            if lines:
                return "\n".join(lines)
        except Exception as e:
            self._log(f"faster-whisper 失败: {e}")

        # openai-whisper 兜底
        try:
            import whisper
            model = whisper.load_model(model_size)
            result = model.transcribe(str(audio_path), language="zh")
            return result.get("text", "")
        except Exception as e:
            self._log(f"openai-whisper 失败: {e}")

        return ""

    def _build_document(self, bvid: str) -> Dict[str, Any]:
        """构建单个 B 站视频的文档数据"""
        info = self.get_video_info(bvid)
        if "error" in info:
            return {
                "title": bvid,
                "full_text": f"[ERROR] {info['error']}",
                "source_url": f"https://www.bilibili.com/video/{bvid}",
                "source_type": "bilibili",
                "metadata": {"bvid": bvid, "error": info["error"]},
            }

        url = f"https://www.bilibili.com/video/{bvid}"
        parts = [f"【标题】{info['title']}", f"【作者】{info['author']}"]
        if info.get("tags"):
            parts.append(f"【标签】{'、'.join(info['tags'])}")
        if info.get("description"):
            parts.append(f"【简介】\n{info['description']}")

        pages = info.get("pages", [])
        subtitle_text = ""
        video_aid = info.get("aid")

        for p in pages:
            cid = p.get("cid", 0)
            if not cid:
                continue
            sub = self.extract_subtitle(bvid, cid, aid=video_aid)
            if sub:
                if len(pages) > 1:
                    subtitle_text += f"\n--- P: {p.get('title', '')} ---\n"
                subtitle_text += sub
            elif self.whisper_fallback:
                if len(pages) > 1:
                    subtitle_text += f"\n--- P: {p.get('title', '')} ---\n"
                audio_path = self.download_audio(bvid, cid)
                if audio_path:
                    transcribed = self.transcribe_audio(audio_path)
                    if transcribed:
                        subtitle_text += f"[Whisper转写]\n{transcribed}"

        if subtitle_text:
            parts.append(f"\n【视频字幕】\n{subtitle_text}")

        return {
            "title": info["title"],
            "full_text": "\n".join(parts),
            "source_url": url,
            "source_type": "bilibili",
            "metadata": {
                "bvid": bvid,
                "author": info["author"],
                "tags": info["tags"],
                "duration": info["duration"],
                "has_subtitle": bool(subtitle_text),
            },
        }

    @staticmethod
    def _extract_bvid(url: str) -> Optional[str]:
        """从 B 站 URL 提取 BV 号"""
        patterns = [r"BV[a-zA-Z0-9]{10}", r"bvid=([a-zA-Z0-9]+)"]
        for p in patterns:
            m = re.search(p, url)
            if m:
                return m.group(0) if "BV" in m.group(0) else m.group(1)
        if "b23.tv" in url or "bili.link" in url:
            try:
                resp = requests.head(url, allow_redirects=True, timeout=10, headers=DEFAULT_HEADERS)
                return BilibiliFetcher._extract_bvid(resp.url)
            except Exception:
                pass
        return None

    def fetch_by_url(self, url: str) -> Dict[str, Any]:
        """从 B 站 URL 导入单个视频"""
        bvid = self._extract_bvid(url)
        if not bvid:
            return {"title": url, "full_text": f"[ERROR] 无法从 URL 提取 BV 号: {url}",
                    "source_url": url, "source_type": "bilibili", "metadata": {}}
        return self._build_document(bvid)

    def get_favorite_folders(self) -> List[Dict[str, Any]]:
        """获取 B 站收藏夹列表"""
        if self._uid is None:
            ok, msg = self.test_auth()
            if not ok:
                return [{"error": f"需要先设置有效 Cookie: {msg}"}]

        resp = safe_request(
            f"{self.FAV_BASE}/folder/created/list-all",
            params={"up_mid": self._uid, "web_location": "333.1387"},
            cookies=self.cookies,
            session=self.session,
        )
        if resp is None:
            return [{"error": "无法获取收藏夹列表"}]

        data = resp.json()
        if data.get("code") != 0:
            return [{"error": f"API 错误: {data.get('message')}"}]

        folders = []
        for f in data.get("data", {}).get("list") or []:
            folders.append({
                "folder_id": f.get("id"),
                "title": f.get("title", ""),
                "media_count": f.get("media_count", 0),
                "intro": f.get("intro", ""),
            })
        return folders

    def get_favorite_videos(
        self,
        folder_id: int,
        max_videos: int = 50,
        progress_callback: Optional[Callable] = None,
    ) -> List[Dict[str, Any]]:
        """获取收藏夹中所有视频内容"""
        videos_data = []
        page = 1

        while True:
            resp = safe_request(
                f"{self.FAV_BASE}/resource/list",
                params={"media_id": folder_id, "pn": page, "ps": 20},
                cookies=self.cookies,
                session=self.session,
            )
            if resp is None:
                break

            data = resp.json()
            if data.get("code") != 0:
                break

            medias = data.get("data", {}).get("medias", [])
            if not medias:
                break

            for m in medias:
                if max_videos > 0 and len(videos_data) >= max_videos:
                    break
                bvid = m.get("bvid", "")
                title = m.get("title", "")
                if progress_callback:
                    progress_callback(len(videos_data), max_videos, bvid, title)
                doc = self._build_document(bvid)
                if doc:
                    videos_data.append(doc)
                time.sleep(0.6)

            page += 1
            if max_videos > 0 and len(videos_data) >= max_videos:
                break
            if not data.get("data", {}).get("has_more", False):
                break

        return videos_data


# ---- 小红书抓取器 ----

class XiaohongshuFetcher:
    """小红书内容抓取器"""

    MOBILE_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/16.0 Mobile/15E148 Safari/604.1"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    }

    def __init__(self, cookie_str: str = ""):
        self.session = requests.Session()
        self.cookies: Dict[str, str] = {}
        if cookie_str:
            self.cookies = parse_cookie_string(cookie_str)
            self.session.cookies.update(self.cookies)

    def fetch_by_url(self, url: str) -> Dict[str, Any]:
        """从小红书笔记链接抓取内容"""
        result = {"title": "", "full_text": "", "source_url": url, "source_type": "xiaohongshu", "metadata": {}}

        note_id = self._extract_note_id(url)
        if not note_id:
            result["full_text"] = f"[ERROR] 无法从 URL 提取笔记 ID: {url}"
            return result
        result["metadata"]["note_id"] = note_id

        resp = safe_request(url, headers=self.MOBILE_HEADERS, session=self.session)
        if resp is None:
            result["full_text"] = f"[ERROR] 无法访问小红书笔记: {url}"
            return result

        html = resp.text

        # 尝试从 __INITIAL_STATE__ 提取
        json_match = re.search(r"window\.__INITIAL_STATE__\s*=\s*({.*?})\s*</script>", html, re.DOTALL)
        if json_match:
            try:
                raw_json = json_match.group(1).replace("undefined", "null")
                state = json.loads(raw_json)
                note_data = state.get("note", {}).get("noteDetailMap", {}).get(note_id, {})
                note = note_data.get("note", note_data)

                result["title"] = note.get("title", note.get("displayTitle", ""))
                desc = note.get("desc", "")

                parts = []
                if result["title"]:
                    parts.append(f"【标题】{result['title']}")
                if desc:
                    parts.append(f"【正文】\n{desc}")
                if note.get("tagList"):
                    tags = [t.get("name", t.get("tagName", "")) for t in note.get("tagList", [])]
                    parts.append(f"【标签】{'、'.join(filter(None, tags))}")

                result["full_text"] = "\n".join(parts)
                return result
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        # BeautifulSoup 兜底
        if _BS4_AVAILABLE:
            soup = BeautifulSoup(html, "html.parser")
            for sel in [".note-content", ".note-text", "#detail-desc", ".content", ".desc"]:
                container = soup.select_one(sel)
                if container:
                    text = container.get_text(separator="\n", strip=True)
                    if len(text) > 30:
                        result["full_text"] = text
                        break
            if not result["title"]:
                og_title = soup.find("meta", property="og:title")
                if og_title and og_title.get("content"):
                    result["title"] = og_title["content"].strip()

        if not result["full_text"]:
            result["full_text"] = f"[提示] 小红书笔记内容提取失败（可能需 Cookie 或触发反爬）"

        return result

    def import_bookmark_html(self, html_path: str) -> List[Dict[str, Any]]:
        """从书签 HTML 文件中提取链接"""
        if not _BS4_AVAILABLE:
            return [{"error": "需要安装 BeautifulSoup: pip install beautifulsoup4"}]

        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a"):
            href = a.get("href", "")
            title = a.get_text(strip=True)
            if href and ("xiaohongshu.com" in href or "xhslink.com" in href):
                links.append({"url": href, "title": title or href[:80]})
        return links

    @staticmethod
    def _extract_note_id(url: str) -> Optional[str]:
        m = re.search(r"/explore/([a-z0-9]+)", url)
        if m:
            return m.group(1)
        if "xhslink.com" in url:
            try:
                resp = requests.head(url, allow_redirects=True, timeout=10, headers=DEFAULT_HEADERS)
                return XiaohongshuFetcher._extract_note_id(resp.url)
            except Exception:
                pass
        return None


# ---- 统一导入入口 ----

class WebImporter:
    """统一网页内容导入入口"""

    def __init__(
        self,
        bilibili_cookie: str = "",
        xiaohongshu_cookie: str = "",
        whisper_fallback: bool = True,
        whisper_model_size: str = "medium",
        progress_callback: Optional[Callable[[str], None]] = None,
    ):
        self.bilibili = BilibiliFetcher(
            cookie_str=bilibili_cookie,
            whisper_fallback=whisper_fallback,
            whisper_model_size=whisper_model_size,
            progress_callback=progress_callback,
        )
        self.xiaohongshu = XiaohongshuFetcher(cookie_str=xiaohongshu_cookie)
        self.webpage = GenericWebFetcher()

    def detect_platform(self, url: str) -> str:
        """自动检测 URL 所属平台"""
        url_lower = url.lower()
        if "bilibili.com" in url_lower or "b23.tv" in url_lower:
            return "bilibili"
        if "xiaohongshu.com" in url_lower or "xhslink.com" in url_lower:
            return "xiaohongshu"
        return "webpage"

    def import_from_url(self, url: str) -> Dict[str, Any]:
        """导入单个 URL"""
        platform = self.detect_platform(url)
        if platform == "bilibili":
            return self.bilibili.fetch_by_url(url)
        elif platform == "xiaohongshu":
            return self.xiaohongshu.fetch_by_url(url)
        else:
            return self.webpage.fetch(url)

    def import_from_urls(
        self,
        urls: List[str],
        progress_callback: Optional[Callable] = None,
    ) -> List[Dict[str, Any]]:
        """批量导入多个 URL"""
        results = []
        total = len(urls)
        for i, url in enumerate(urls):
            try:
                if progress_callback:
                    platform = self.detect_platform(url)
                    progress_callback(i + 1, total, url, platform)
                doc = self.import_from_url(url)
                results.append(doc)
                time.sleep(0.5)
            except Exception as e:
                results.append({
                    "title": url[:60],
                    "full_text": f"[ERROR] {str(e)}",
                    "source_url": url,
                    "source_type": "error",
                    "metadata": {"error": str(e)},
                })
        return results

    def import_bilibili_favorites(
        self,
        folder_id: int,
        max_videos: int = 50,
        progress_callback: Optional[Callable] = None,
    ) -> List[Dict[str, Any]]:
        """导入 B 站收藏夹"""
        return self.bilibili.get_favorite_videos(
            folder_id=folder_id,
            max_videos=max_videos,
            progress_callback=progress_callback,
        )

    def get_bilibili_folders(self) -> List[Dict[str, Any]]:
        """获取 B 站收藏夹列表"""
        return self.bilibili.get_favorite_folders()

    def import_from_bookmarks(
        self,
        html_path: str,
        max_links: int = 100,
        progress_callback: Optional[Callable] = None,
    ) -> List[Dict[str, Any]]:
        """从书签 HTML 批量导入"""
        links = self.xiaohongshu.import_bookmark_html(html_path)
        if max_links > 0:
            links = links[:max_links]
        urls = [l["url"] for l in links if "error" not in l]
        return self.import_from_urls(urls, progress_callback=progress_callback)


def web_doc_to_pipeline_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """将 web_importer 输出转为与 read_any_file() 兼容的格式"""
    text = clean_text(doc.get("full_text", ""))
    source_type = doc.get("source_type", "webpage")
    url = doc.get("source_url", "")
    is_error = (not text) or text.startswith("[ERROR]")

    result: Dict[str, Any] = {
        "type": source_type,
        "path": "",
        "url": url,
        "success": not is_error,
        "title": doc.get("title") or (url[:60] if url else "untitled"),
        "text": text,
        "error": "" if not is_error else (text[:300] if text else "未提取到有效内容"),
        "metadata": doc.get("metadata", {}),
    }

    if source_type == "bilibili" and text and not is_error:
        segments = []
        for m in re.finditer(r"\[(\d+):(\d+)\]\s*(.+)", text):
            start_sec = int(m.group(1)) * 60 + int(m.group(2))
            seg_text = m.group(3).strip()
            if seg_text:
                segments.append({"start": float(start_sec), "end": float(start_sec), "text": seg_text})
        if segments:
            result["segments"] = segments

    return result
