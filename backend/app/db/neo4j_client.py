"""
Neo4j 图数据库客户端 (带优雅降级)
- 本地开发无 Neo4j 服务时, 自动降级为 NoOp, 不影响主流程
- 部署环境配置 NEO4J_URL 后启用真实连接
"""
from typing import Any

from loguru import logger

from app.core.config import settings


class Neo4jClient:
    """Neo4j 客户端 (单例, 带降级)"""

    def __init__(self) -> None:
        self._driver = None
        self._available = False
        self._init_driver()

    def _init_driver(self) -> None:
        """初始化驱动, 失败则降级"""
        try:
            from neo4j import GraphDatabase

            self._driver = GraphDatabase.driver(
                settings.NEO4J_URL,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
            # 测试连接
            self._driver.verify_connectivity()
            self._available = True
            logger.info(f"✅ Neo4j 连接成功: {settings.NEO4J_URL}")
        except ImportError:
            logger.warning("⚠️ neo4j 驱动未安装, 知识图谱功能降级 (pip install neo4j)")
            self._available = False
        except Exception as e:
            logger.warning(f"⚠️ Neo4j 连接失败, 知识图谱功能降级: {e}")
            self._available = False

    @property
    def available(self) -> bool:
        """Neo4j 是否可用"""
        return self._available

    def run(self, cypher: str, params: dict | None = None) -> list[dict]:
        """执行 Cypher 查询, 返回结果列表 (降级时返回空)"""
        if not self._available or self._driver is None:
            logger.debug(f"Neo4j 降级, 跳过 Cypher: {cypher[:80]}")
            return []
        try:
            with self._driver.session() as session:
                result = session.run(cypher, parameters=params or {})
                return [r.data() for r in result]
        except Exception as e:
            logger.error(f"Neo4j 查询失败: {e}")
            return []

    def close(self) -> None:
        """关闭连接"""
        if self._driver:
            self._driver.close()


# 全局单例
neo4j_client = Neo4jClient()
