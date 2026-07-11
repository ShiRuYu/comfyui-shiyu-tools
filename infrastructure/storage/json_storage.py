"""JsonStorage — JSON 文件存储实现。

数据以 JSON 格式存储在本地文件系统中。
每个集合对应一个 JSON 文件。

路径格式: {base_path}/{collection}.json
"""

from __future__ import annotations

import json
import os
from typing import Any

from .storage import Storage, EntityNotFoundError


class JsonStorage(Storage):
    """JSON 文件存储实现。

    每个集合对应一个 JSON 文件，文件名 = 集合名 + .json。
    文件存储在指定的 base_path 下。
    """

    def __init__(self, base_path: str = "") -> None:
        super().__init__()
        self._base_path = base_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", "data"
        )
        self._data: dict[str, dict[str, dict]] = {}
        self._dirty = False

    # ──────────────────────────────────────────
    # 路径工具
    # ──────────────────────────────────────────

    def _collection_path(self, collection: str) -> str:
        """获取集合对应的文件路径。"""
        return os.path.join(self._base_path, f"{collection}.json")

    def _ensure_base_path(self) -> None:
        """确保基础路径存在。"""
        os.makedirs(self._base_path, exist_ok=True)

    # ──────────────────────────────────────────
    # Storage SPI 实现
    # ──────────────────────────────────────────

    def load(self) -> None:
        """从文件系统加载所有集合数据。"""
        self._ensure_base_path()
        self._data.clear()

        if not os.path.isdir(self._base_path):
            return

        for filename in os.listdir(self._base_path):
            if not filename.endswith(".json"):
                continue

            collection = filename[:-5]  # 去掉 .json
            filepath = os.path.join(self._base_path, filename)

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    # 支持数组格式: [{"id": "xxx", ...}, ...]
                    if isinstance(raw, list):
                        self._data[collection] = {
                            item["id"]: item
                            for item in raw
                            if isinstance(item, dict) and "id" in item
                        }
                    # 支持字典格式: {"id1": {...}, "id2": {...}}
                    elif isinstance(raw, dict):
                        self._data[collection] = raw
                    else:
                        self._data[collection] = {}
            except (json.JSONDecodeError, OSError) as e:
                print(f"[JsonStorage] Failed to load {filename}: {e}")
                self._data[collection] = {}

        self._dirty = False

    def save(self) -> None:
        """将所有数据持久化到文件系统。"""
        if not self._dirty:
            return

        self._ensure_base_path()

        for collection, items in self._data.items():
            filepath = self._collection_path(collection)
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(
                        list(items.values()),
                        f,
                        ensure_ascii=False,
                        indent=2,
                    )
            except OSError as e:
                print(f"[JsonStorage] Failed to save {collection}: {e}")

        self._dirty = False

    # ──────────────────────────────────────────
    # CRUD
    # ──────────────────────────────────────────

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
        self._dirty = True
        return self._data[collection][entity_id]

    def update(self, collection: str, entity_id: str, data: dict) -> dict:
        if collection not in self._data or entity_id not in self._data[collection]:
            raise EntityNotFoundError(collection, entity_id)
        self._data[collection][entity_id].update(data)
        self._dirty = True
        return self._data[collection][entity_id]

    def delete(self, collection: str, entity_id: str) -> bool:
        if collection not in self._data or entity_id not in self._data[collection]:
            return False
        del self._data[collection][entity_id]
        self._dirty = True
        return True

    def exists(self, collection: str, entity_id: str) -> bool:
        if collection not in self._data:
            return False
        return entity_id in self._data[collection]

    def count(self, collection: str) -> int:
        if collection not in self._data:
            return 0
        return len(self._data[collection])

    # ──────────────────────────────────────────
    # 集合管理
    # ──────────────────────────────────────────

    def list_collections(self) -> list[str]:
        return list(self._data.keys())

    def clear_collection(self, collection: str) -> None:
        if collection in self._data:
            self._data[collection].clear()
            self._dirty = True
