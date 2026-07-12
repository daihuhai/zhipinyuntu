"""
文件存储服务
- 保存上传文件 (DOC/DOCX/PDF)
- 计算文件 hash (去重)
- 返回相对访问路径
"""
import hashlib
import os
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile
from loguru import logger

from app.core.config import settings


# 允许的文件类型
ALLOWED_EXTENSIONS = {".doc", ".docx", ".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 文件 magic number 签名 (前 N 字节, 防止伪造扩展名)
FILE_SIGNATURES = {
    ".pdf": [b"%PDF"],              # PDF: %PDF-1.x
    ".docx": [b"PK\x03\x04"],       # DOCX: ZIP 格式
    ".doc": [b"\xd0\xcf\x11\xe0"],  # DOC: OLE2 复合文档
}


class FileService:
    """文件存储服务 (本地磁盘)"""

    def __init__(self) -> None:
        self.storage_path = Path(settings.STORAGE_PATH).resolve()
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _ext(self, filename: str) -> str:
        """获取小写扩展名"""
        return os.path.splitext(filename)[1].lower()

    def validate(self, filename: str, file_size: int, content: bytes | None = None) -> None:
        """校验文件类型与大小 (含 magic number 签名校验)"""
        ext = self._ext(filename)
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"不支持的文件类型: {ext}, 仅支持 {', '.join(ALLOWED_EXTENSIONS)}")
        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"文件过大: {file_size} bytes, 上限 {MAX_FILE_SIZE} bytes")
        # magic number 校验: 防止伪造扩展名上传可执行文件
        if content and ext in FILE_SIGNATURES:
            sigs = FILE_SIGNATURES[ext]
            if not any(content.startswith(sig) for sig in sigs):
                raise ValueError(f"文件内容与扩展名 {ext} 不匹配, 疑似伪造文件")

    async def save(self, upload: UploadFile, sub_dir: str = "") -> dict:
        """保存上传文件, 返回 {url, hash, size, filename}"""
        content = await upload.read()
        ext = self._ext(upload.filename or "unknown.pdf")
        self.validate(upload.filename or "", len(content), content)

        # 按 年/月 分目录存储
        now = datetime.now()
        date_dir = f"{now.strftime('%Y%m')}"
        save_dir = self.storage_path / sub_dir / date_dir
        save_dir.mkdir(parents=True, exist_ok=True)

        # 文件名: 时间戳 + hash 前缀, 避免冲突
        file_hash = hashlib.md5(content).hexdigest()
        filename = f"{now.strftime('%d%H%M%S')}_{file_hash[:8]}{ext}"
        file_path = save_dir / filename

        file_path.write_bytes(content)

        # 相对访问 URL (用于前端下载/展示)
        rel_path = file_path.relative_to(self.storage_path).as_posix()
        url = f"/uploads/{rel_path}"

        logger.info(f"文件已保存: {file_path} ({len(content)} bytes)")
        return {
            "url": url,
            "abs_path": str(file_path),
            "hash": file_hash,
            "size": len(content),
            "filename": upload.filename,
        }

    def absolute_path(self, url: str) -> str:
        """将相对 URL 转为绝对路径"""
        if url.startswith("/uploads/"):
            rel = url[len("/uploads/") :]
            return str(self.storage_path / rel)
        return url


file_service = FileService()
