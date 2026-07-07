"""
文档解析服务
- 从 DOC/DOCX/PDF 提取纯文本
- 调用豆包大模型结构化为 JSON
- 支持简历与职位两种解析模式
"""
import json
from typing import Any

from loguru import logger

from app.ai.ark_client import ark_client
from app.ai.prompts import build_job_messages, build_resume_messages


class DocParser:
    """文档解析器 (文本提取 + AI 结构化)"""

    def extract_text(self, file_path: str) -> str:
        """从文件提取纯文本"""
        lower = file_path.lower()
        if lower.endswith(".docx"):
            return self._extract_docx(file_path)
        if lower.endswith(".pdf"):
            return self._extract_pdf(file_path)
        if lower.endswith(".doc"):
            # 旧版 .doc 格式, 尝试用 pdfplumber 或提示转换
            logger.warning(f"旧版 .doc 格式支持有限: {file_path}, 尝试用 pdfplumber 解析")
            return self._extract_pdf(file_path)
        raise ValueError(f"不支持的文件格式: {file_path}")

    def _extract_docx(self, file_path: str) -> str:
        """从 DOCX 提取文本"""
        from docx import Document

        doc = Document(file_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        # 表格内容
        for table in doc.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    paragraphs.append(" | ".join(cells))
        text = "\n".join(paragraphs)
        logger.info(f"DOCX 文本提取完成: {len(text)} 字符")
        return text

    def _extract_pdf(self, file_path: str) -> str:
        """从 PDF 提取文本"""
        import pdfplumber

        texts: list[str] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    texts.append(page_text.strip())
        text = "\n".join(texts)
        logger.info(f"PDF 文本提取完成: {len(text)} 字符, {len(texts)} 页")
        return text

    def parse_resume(self, text: str) -> dict[str, Any]:
        """用豆包模型将简历文本结构化"""
        if not text.strip():
            raise ValueError("简历文本为空")
        # 截断超长文本 (避免 token 超限)
        truncated = text[:8000]
        messages = build_resume_messages(truncated)
        result = ark_client.chat_json(messages, temperature=0.1)
        logger.info(f"简历结构化完成, 字段: {list(result.keys())}")
        return result

    def parse_job(self, text: str) -> dict[str, Any]:
        """用豆包模型将职位描述结构化"""
        if not text.strip():
            raise ValueError("职位文本为空")
        truncated = text[:4000]
        messages = build_job_messages(truncated)
        result = ark_client.chat_json(messages, temperature=0.1)
        logger.info(f"职位结构化完成, 字段: {list(result.keys())}")
        return result


doc_parser = DocParser()
