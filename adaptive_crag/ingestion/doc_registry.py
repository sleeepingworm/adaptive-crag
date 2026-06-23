"""文档哈希注册表 — 检测重复上传的文档，避免重复 embedding"""

import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DocRegistry:
    """
    基于 JSON 文件的文档哈希注册表。

    持久化位置: {index_dir}/doc_registry.json
    映射: file_hash → {doc_id, filename, chunk_count, indexed_at}

    拆一个模块，写一个断言：
    >>> reg = DocRegistry("/tmp/test_registry")
    >>> reg.register("abc", "doc_1", "test.pdf", 10)
    >>> assert reg.lookup("abc") is not None
    >>> assert reg.lookup("def") is None
    >>> assert reg.count == 1
    """

    def __init__(self, index_dir: str):
        self._path = os.path.join(index_dir, "doc_registry.json")
        self._registry: dict[str, dict] = {}
        self._load()

    def _load(self):
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    self._registry = json.load(f)
            except Exception as e:
                logger.warning(f"文档注册表加载失败，将重新创建: {e}")
                self._registry = {}

    def _save(self):
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._registry, f, ensure_ascii=False, indent=2)

    def lookup(self, file_hash: str) -> dict | None:
        """查询文件 hash 是否已索引过。命中返回注册信息，未命中返回 None。"""
        return self._registry.get(file_hash)

    def register(self, file_hash: str, doc_id: str, filename: str, chunk_count: int):
        """注册一个新索引的文档。"""
        self._registry[file_hash] = {
            "doc_id": doc_id,
            "filename": filename,
            "chunk_count": chunk_count,
            "indexed_at": datetime.now().isoformat(),
        }
        self._save()
        logger.info(f"注册文档缓存: {filename} (hash={file_hash[:12]}..., chunks={chunk_count})")

    @property
    def count(self) -> int:
        return len(self._registry)