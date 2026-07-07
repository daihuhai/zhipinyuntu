"""测试 embedding 模型 - 测试多个模型名"""
from app.ai.ark_client import ark_client
from app.core.config import settings

candidates = [
    "doubao-embedding-large-text-240915",
    "doubao-embedding-text-240515",
    "doubao-embedding-text-240715",
]
for m in candidates:
    try:
        vecs = ark_client.embed(["测试向量化"], model=m)
        print(f"✅ {m}: 维度 {len(vecs[0]) if vecs else 0}")
        break
    except Exception as e:
        print(f"❌ {m}: {str(e)[:120]}")
print(f"当前配置: {settings.ARK_EMBEDDING_MODEL}")
