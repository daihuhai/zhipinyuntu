"""
NebulaGraph 图数据库客户端 (带优雅降级)
- 本地开发无 NebulaGraph 服务时, 自动降级为 NoOp, 不影响主流程
- 部署环境配置 NEBULA_HOST 后启用真实连接
- nGQL 查询语言, 与 Neo4j Cypher 语法类似但需适配
"""
from typing import Any

from loguru import logger

from app.core.config import settings


class NebulaClient:
    """NebulaGraph 客户端 (单例, 带降级)"""

    def __init__(self) -> None:
        self._pool = None
        self._available = False
        self._init_pool()

    def _init_pool(self) -> None:
        """初始化连接池, 失败则降级"""
        try:
            from nebula3.gclient.net import ConnectionPool
            from nebula3.Config import Config

            nebula_config = Config()
            nebula_config.max_connection_pool_size = 10
            nebula_config.timeout = 5000

            self._pool = ConnectionPool()
            ok = self._pool.init(
                [(settings.NEBULA_HOST, settings.NEBULA_PORT)], nebula_config
            )
            if not ok:
                logger.warning("⚠️ NebulaGraph 连接池初始化失败")
                self._available = False
                return

            # 测试连接与空间
            session = self._pool.get_session(settings.NEBULA_USER, settings.NEBULA_PASSWORD)
            try:
                resp = session.execute(f"USE {settings.NEBULA_SPACE}")
                if not resp.is_succeeded():
                    logger.warning(
                        f"⚠️ NebulaGraph 空间 '{settings.NEBULA_SPACE}' 不存在, "
                        f"请先创建: CREATE SPACE IF NOT EXISTS {settings.NEBULA_SPACE}(partition_num=1, replica_factor=1, vid_type=FIXED_STRING(64));"
                    )
                    self._available = False
                else:
                    self._available = True
                    logger.info(
                        f"✅ NebulaGraph 连接成功: {settings.NEBULA_HOST}:{settings.NEBULA_PORT}/{settings.NEBULA_SPACE}"
                    )
            finally:
                session.release()
        except ImportError:
            logger.warning("⚠️ nebula3-python 驱动未安装, 知识图谱功能降级 (pip install nebula3-python)")
            self._available = False
        except Exception as e:
            logger.warning(f"⚠️ NebulaGraph 连接失败, 知识图谱功能降级: {e}")
            self._available = False

    @property
    def available(self) -> bool:
        """NebulaGraph 是否可用"""
        return self._available

    def execute(self, ngql: str) -> "NebulaResult":
        """执行 nGQL 语句, 返回封装结果 (降级时返回空结果)"""
        if not self._available or self._pool is None:
            logger.debug(f"NebulaGraph 降级, 跳过 nGQL: {ngql[:80]}")
            return NebulaResult.empty()

        session = self._pool.get_session(settings.NEBULA_USER, settings.NEBULA_PASSWORD)
        try:
            session.execute(f"USE {settings.NEBULA_SPACE}")
            resp = session.execute(ngql)
            if resp.is_succeeded():
                return NebulaResult.from_response(resp)
            else:
                logger.error(f"NebulaGraph nGQL 执行失败: {resp.error_msg()}")
                return NebulaResult.empty()
        except Exception as e:
            logger.error(f"NebulaGraph 查询异常: {e}")
            return NebulaResult.empty()
        finally:
            session.release()

    def close(self) -> None:
        """关闭连接池"""
        if self._pool:
            self._pool.close()


class NebulaResult:
    """封装 NebulaGraph 查询结果, 提供便捷访问"""

    def __init__(self, rows: list[Any], columns: list[str]) -> None:
        self._rows = rows
        self._columns = columns

    @classmethod
    def empty(cls) -> "NebulaResult":
        return cls([], [])

    @classmethod
    def from_response(cls, resp) -> "NebulaResult":
        """从 nebula3 Response 构建结果"""
        rows = resp.rows()
        columns = resp.keys() if hasattr(resp, "keys") else []
        return cls(rows, columns)

    @property
    def rows(self) -> list[Any]:
        return self._rows

    def to_dicts(self) -> list[dict[str, Any]]:
        """将每行转换为 dict, 处理 Vertex/Edge/Path 等类型"""
        result = []
        for row in self._rows:
            row_dict = {}
            for i, col_name in enumerate(self._columns):
                if i < len(row.values):
                    row_dict[col_name] = self._unwrap_value(row.values[i])
            result.append(row_dict)
        return result

    @staticmethod
    def _unwrap_value(val) -> Any:
        """解包 nebula3 Value 对象为 Python 原生类型"""
        try:
            if hasattr(val, "is_vertex") and val.is_vertex():
                return NebulaResult._vertex_to_dict(val)
            elif hasattr(val, "is_edge") and val.is_edge():
                return NebulaResult._edge_to_dict(val)
            elif hasattr(val, "is_path") and val.is_path():
                return {"type": "Path", "nodes": [], "edges": []}
            else:
                return val.get_sVal() if hasattr(val, "get_sVal") else str(val)
        except Exception:
            return str(val)

    @staticmethod
    def _vertex_to_dict(val) -> dict[str, Any]:
        """Vertex → {vid, tags, props}"""
        v = val.get_vVal()
        vid = v.get_vid().get_str()
        tags = list(v.tags)
        props = {}
        for tag in tags:
            tag_props = v.get_props(tag)
            if tag_props:
                props.update({k.decode() if isinstance(k, bytes) else k: str(v)
                              for k, v in tag_props.items()})
        return {
            "vid": vid,
            "tags": tags,
            "props": props,
        }

    @staticmethod
    def _edge_to_dict(val) -> dict[str, Any]:
        """Edge → {src, dst, name, props}"""
        e = val.get_eVal()
        src = e.get_src_id().get_str()
        dst = e.get_dst_id().get_str()
        name = e.get_edge_name()
        props = {}
        if e.props:
            props.update({k.decode() if isinstance(k, bytes) else k: str(v)
                          for k, v in e.props.items()})
        return {
            "src": src,
            "dst": dst,
            "edge_name": name,
            "props": props,
        }


# 全局单例
nebula_client = NebulaClient()