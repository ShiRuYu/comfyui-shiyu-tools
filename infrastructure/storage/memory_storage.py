"""MemoryStorage — 内存存储实现（用于测试）。

数据仅保存在内存中，不持久化到磁盘。
适用于单元测试和临时场景。
"""

from __future__ import annotations

from typing import Any

from .storage import Storage


class MemoryStorage(Storage):
    """内存存储实现。

    所有数据保存在内存字典中，不写入磁盘。
    主要用于单元测试。
    """

    def __init__(self) -> None:
        super().__init__()
        self._data: dict[str, dict[str, dict]] = {}
        self._load_counter = 0
        self._save_counter = 0

    @property
    def load_count(self) -> int:
        """load() 被调用的次数。"""
        return self._load_counter

    @property
    def save_count(self) -> int:
        """save() 被调用的次数。"""
        return self._save_counter

    # ──────────────────────────────────────────
    # Storage SPI 实现
    # ──────────────────────────────────────────

    def load(self) -> None:
        self._load_counter += 1

    def save(self) -> None:
        self._save_counter += 1

    def get(self, collection: str, entity_id: str) -> dict | None:
        if collection not in self._data:
            return None
        return self._data[collection].get(entity_id)

    def get_all(self, collection: str) -> list[dict]:
        if collection not in self._data:
            return []
        return list(self._data[collection].values())

    def create(self, collection: str, entity_id: str, data: dict) -> dict:
        if collection not in self._data:
            self._data[collection] = {}
        self._data[collection][entity_id] = dict(data)
        return self._data[collection][entity_id]

    def update(self, collection: str, entity_id: str, data: dict) -> dict:
        if collection not in self._data:
            self._data[collection] = {}
        if entity_id not in self._data[collection]:
            self._data[collection][entity_id] = {}
        self._data[collection][entity_id].update(data)
        return self._data[collection][entity_id]

    def delete(self, collection: str, entity_id: str) -> bool:
        if collection not in self._data or entity_id not in self._data[collection]:
            return False
        del self._data[collection][entity_id]
        return True

    def exists(self, collection: str, entity_id: str) -> bool:
        if collection not in self._data:
            return False
        return entity_id in self._data[collection]

    def count(self, collection: str) -> int:
        if collection not in self._data:
            return 0
        return len(self._data[collection])

    def list_collections(self) -> list[str]:
        return list(self._data.keys())

    def clear_collection(self, collection: str) -> None:
        if collection in self._data:
            self._data[collection].clear()
