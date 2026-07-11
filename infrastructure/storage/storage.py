"""Storage — 存储抽象基类（SPI）。

所有存储实现必须继承此类。
业务模块通过 Storage 接口访问数据，不知道底层使用什么存储。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class StorageError(RuntimeError):
    """存储操作异常。"""
    pass


class EntityNotFoundError(StorageError):
    """实体不存在异常。"""
    def __init__(self, collection: str, entity_id: str) -> None:
        super().__init__(f"Entity '{entity_id}' not found in collection '{collection}'")
        self.collection = collection
        self.entity_id = entity_id


class Storage(ABC):
    """存储抽象基类。

    定义存储层的 SPI：
    - CRUD 操作
    - 查询
    - 序列化

    所有业务模块通过此接口访问数据。
    """

    @abstractmethod
    def load(self) -> None:
        """从持久化介质加载数据。"""
        ...

    @abstractmethod
    def save(self) -> None:
        """持久化数据到介质。"""
        ...

    # ──────────────────────────────────────────
    # CRUD
    # ──────────────────────────────────────────

    @abstractmethod
    def get(self, collection: str, entity_id: str) -> dict | None:
        """根据 ID 获取实体。"""
        ...

    @abstractmethod
    def get_all(self, collection: str) -> list[dict]:
        """获取集合中所有实体。"""
        ...

    @abstractmethod
    def create(self, collection: str, entity_id: str, data: dict) -> dict:
        """创建实体。"""
        ...

    @abstractmethod
    def update(self, collection: str, entity_id: str, data: dict) -> dict:
        """更新实体。"""
        ...

    @abstractmethod
    def delete(self, collection: str, entity_id: str) -> bool:
        """删除实体。"""
        ...

    @abstractmethod
    def exists(self, collection: str, entity_id: str) -> bool:
        """判断实体是否存在。"""
        ...

    @abstractmethod
    def count(self, collection: str) -> int:
        """获取集合中实体数量。"""
        ...

    # ──────────────────────────────────────────
    # 集合管理
    # ──────────────────────────────────────────

    @abstractmethod
    def list_collections(self) -> list[str]:
        """列出所有集合名称。"""
        ...

    @abstractmethod
    def clear_collection(self, collection: str) -> None:
        """清空集合。"""
        ...
