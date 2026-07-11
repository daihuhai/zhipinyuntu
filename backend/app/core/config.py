"""智聘云图全局配置 - 基于 pydantic-settings 管理"""
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置 (从 .env 文件加载)"""

    model_config = SettingsConfigDict(
        env_file=".env.dev",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===== 应用 =====
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_NAME: str = "智聘云图"
    APP_VERSION: str = "1.0.0"
    SECRET_KEY: str = "change-me"

    # ===== 后端服务 =====
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # ===== 数据库 =====
    DATABASE_URL: str = "sqlite:///./zhipin.db"

    # ===== Redis =====
    REDIS_URL: str = "redis://localhost:6379/0"

    # ===== Neo4j =====
    NEO4J_URL: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "zhipin123"

    # ===== 文件存储 =====
    STORAGE_TYPE: str = "local"
    STORAGE_PATH: str = "./uploads"

    # ===== 豆包 ARK API =====
    ARK_API_KEY: str = ""
    ARK_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    ARK_CHAT_MODEL: str = "doubao-seed-2-1-pro-260628"
    ARK_EMBEDDING_MODEL: str = "doubao-embedding-vision-251215"

    # ===== Celery =====
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ===== JWT =====
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # ===== CORS =====
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8080"

    @field_validator("CORS_ORIGINS")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        """CORS 配置允许逗号分隔字符串"""
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        """解析 CORS 来源列表"""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


# 全局单例
settings = Settings()
