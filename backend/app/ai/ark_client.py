"""
豆包大模型客户端 (基于火山引擎 ARK API, 兼容 OpenAI SDK)
- chat: 对话补全 (支持 JSON 模式)
- embed: 文本向量化 (自动适配多模态 embedding 模型, 如 doubao-embedding-vision-*)
"""
import json
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from openai import OpenAI
from loguru import logger

from app.core.config import settings

# 多模态 embedding 并发数 (同时发起多个 HTTP 请求)
_EMBED_MAX_WORKERS = 8


class ArkClient:
    """豆包 ARK API 客户端 (OpenAI 兼容)"""

    def __init__(self) -> None:
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        """懒加载 OpenAI 客户端"""
        if self._client is None:
            self._client = OpenAI(
                api_key=settings.ARK_API_KEY,
                base_url=settings.ARK_BASE_URL,
            )
        return self._client

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        """对话补全, 返回文本内容"""
        try:
            resp = self.client.chat.completions.create(
                model=model or settings.ARK_CHAT_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = resp.choices[0].message.content or ""
            logger.debug(f"ARK chat 调用成功, 返回 {len(content)} 字符")
            return content
        except Exception as e:
            logger.error(f"ARK chat 调用失败: {e}")
            raise

    def chat_json(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """对话补全并解析为 JSON (带容错处理)"""
        raw = self.chat(messages, model=model, temperature=temperature, max_tokens=max_tokens)
        return _safe_parse_json(raw)

    def chat_json_array(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> list[dict[str, Any]]:
        """对话补全并解析为 JSON 数组 (带容错处理)"""
        raw = self.chat(messages, model=model, temperature=temperature, max_tokens=max_tokens)
        return _safe_parse_json_array(raw)

    def embed(self, texts: list[str] | str, model: str | None = None) -> list[list[float]]:
        """文本向量化, 返回向量列表
        - 普通模型: 走 OpenAI SDK embeddings.create (支持批量)
        - 多模态模型 (doubao-embedding-vision-*): 走 /embeddings/multimodal HTTP 接口 (仅支持单条)
        """
        if isinstance(texts, str):
            texts = [texts]
        use_model = model or settings.ARK_EMBEDDING_MODEL
        # 多模态 embedding 模型走专用接口 (不支持批量, 逐条调用)
        if "vision" in use_model or "multimodal" in use_model:
            return self._embed_multimodal(texts, use_model)
        # 普通 embedding 走 OpenAI SDK
        try:
            resp = self.client.embeddings.create(
                model=use_model,
                input=texts,
            )
            vectors = [item.embedding for item in resp.data]
            logger.debug(f"ARK embed 调用成功, 生成 {len(vectors)} 个向量, 维度 {len(vectors[0]) if vectors else 0}")
            return vectors
        except Exception as e:
            logger.error(f"ARK embed 调用失败: {e}")
            raise

    def _embed_multimodal(self, texts: list[str], model: str) -> list[list[float]]:
        """多模态 embedding (HTTP 调用, 并发生成)
        接口: POST {base_url}/embeddings/multimodal
        payload: {"model": ..., "input": [{"type":"text","text":"..."}]}
        响应: {"data": {"embedding": [...]}}
        注意: 该接口不支持批量, 使用 ThreadPoolExecutor 并发调用以加速
        """
        url = f"{settings.ARK_BASE_URL.rstrip('/')}/embeddings/multimodal"
        headers = {
            "Authorization": f"Bearer {settings.ARK_API_KEY}",
            "Content-Type": "application/json",
        }

        def _embed_one(idx: int, txt: str) -> tuple[int, list[float]]:
            payload = {
                "model": model,
                "input": [{"type": "text", "text": txt[:8000]}],
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                emb = data.get("data", {}).get("embedding", [])
                if not emb:
                    raise ValueError("响应中未找到 embedding 字段")
                return (idx, emb)
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8")[:200]
                logger.error(f"ARK multimodal embed HTTP {e.code} 失败: {body}")
                raise

        # 并发调用, 按原始顺序返回
        vectors: list[list[float] | None] = [None] * len(texts)
        with ThreadPoolExecutor(max_workers=_EMBED_MAX_WORKERS) as pool:
            futures = {pool.submit(_embed_one, i, txt): i for i, txt in enumerate(texts)}
            for future in as_completed(futures):
                idx, emb = future.result()
                vectors[idx] = emb
        logger.debug(
            f"ARK multimodal embed 调用成功, 生成 {len(vectors)} 个向量, "
            f"维度 {len(vectors[0]) if vectors else 0}"
        )
        return vectors  # type: ignore[return-value]


def _safe_parse_json(text: str) -> dict[str, Any]:
    """容错 JSON 解析: 去除 markdown 代码块标记、提取首个 JSON 对象"""
    text = text.strip()
    # 去除 markdown 代码块
    if text.startswith("```"):
        text = text.split("```", 2)
        # 取第二个元素 (代码块内容)
        text = text[1] if len(text) > 1 else text[0]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
        if text.endswith("```"):
            text = text[:-3]
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 提取首个 { ... } 块
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    logger.warning(f"JSON 解析失败, 返回原始文本: {text[:200]}")
    return {"_raw": text}


def _safe_parse_json_array(text: str) -> list[dict[str, Any]]:
    """容错 JSON 数组解析: 去除 markdown 标记、提取首个 JSON 数组"""
    text = text.strip()
    # 去除 markdown 代码块
    if text.startswith("```"):
        text = text.split("```", 2)
        text = text[1] if len(text) > 1 else text[0]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
        if text.endswith("```"):
            text = text[:-3]
    # 尝试直接解析
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    # 提取首个 [ ... ] 块
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
    logger.warning(f"JSON 数组解析失败, 返回空列表: {text[:200]}")
    return []


# 全局单例
ark_client = ArkClient()
