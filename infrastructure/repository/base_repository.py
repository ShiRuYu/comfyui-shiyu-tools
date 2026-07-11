"""BaseRepository — Repository 基类。

所有业务 Repository 必须继承此类。
提供通用的 CRUD 和序列化支持。
"""

import typing
from dataclasses import fields, is_dataclass
from typing import Any, Generic, TypeVar

from infrastructure.storage.storage import Storage

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Repository 基类。

    职责：
    - 封装 Storage 的 CRUD 操作
    - 数据模型序列化/反序列化
    - 类型安全

    Args:
        storage: Storage 实例
        collection: 集合名称
        entity_class: 实体类（dataclass）
    """

    def __init__(
        self,
        storage: Storage,
        collection: str,
        entity_class: type,
    ) -> None:
        self._storage = storage
        self._collection = collection
        self._entity_class = entity_class
        # 缓存解析后的类型提示
        self._type_hints: dict[str, type] | None = None

    def _get_type_hints(self) -> dict[str, type]:
        """获取实体类的类型提示（缓存）。"""
        if self._type_hints is None:
            self._type_hints = typing.get_type_hints(self._entity_class)
        return self._type_hints

    @property
    def collection(self) -> str:
        """集合名称。"""
        return self._collection

    @property
    def storage(self) -> Storage:
        """底层 Storage 实例。"""
        return self._storage

    # ──────────────────────────────────────────
    # 序列化/反序列化
    # ──────────────────────────────────────────

    def _to_dict(self, entity: Any) -> dict[str, Any]:
        """将 dataclass 实体转换为字典。"""
        if is_dataclass(entity):
            result = {}
            for f in fields(entity):
                value = getattr(entity, f.name)
                if is_dataclass(value):
                    result[f.name] = self._to_dict(value)
                elif isinstance(value, list):
                    result[f.name] = [
                        self._to_dict(item) if is_dataclass(item) else item
                        for item in value
                    ]
                elif isinstance(value, dict):
                    result[f.name] = {
                        k: self._to_dict(v) if is_dataclass(v) else v
                        for k, v in value.items()
                    }
                else:
                    result[f.name] = value
            return result
        return dict(entity)

    def _from_dict(self, data: dict[str, Any]) -> Any | None:
        """将字典转换为 dataclass 实体。

        递归处理嵌套的 dataclass 字段。
        """
        if not data:
            return None
        try:
            cls = self._entity_class
            if is_dataclass(cls):
                processed = {}
                type_hints = self._get_type_hints()

                for f in fields(cls):
                    raw = data.get(f.name, _SENTINEL)
                    if raw is _SENTINEL:
                        continue

                    type_hint = type_hints.get(f.name)

                    if type_hint and is_dataclass(type_hint) and isinstance(raw, dict):
                        # 嵌套 dataclass: 递归构造
                        processed[f.name] = type_hint(**raw)
                    elif (
                        type_hint
                        and hasattr(type_hint, "__origin__")
                        and type_hint.__origin__ is list
                        and isinstance(raw, list)
                    ):
                        # 列表类型
                        args = getattr(type_hint, "__args__", [])
                        if args and is_dataclass(args[0]):
                            processed[f.name] = [
                                args[0](**item) if isinstance(item, dict) else item
                                for item in raw
                            ]
                        else:
                            processed[f.name] = raw
                    else:
                        processed[f.name] = raw

                return cls(**processed)

            return cls(**data)
        except (TypeError, ValueError) as e:
            print(f"[BaseRepository] Failed to deserialize {self._entity_class.__name__}: {e}")
            return None

    # ──────────────────────────────────────────
    # CRUD
    # ──────────────────────────────────────────

    def get_by_id(self, entity_id: str) -> Any | None:
        """根据 ID 获取实体。"""
        data = self._storage.get(self._collection, entity_id)
        return self._from_dict(data) if data else None

    def get_all(self) -> list[Any]:
        """获取所有实体。"""
        data_list = self._storage.get_all(self._collection)
        return [self._from_dict(d) for d in data_list if d is not None]

    def create(self, entity: Any) -> Any:
        """创建实体。"""
        entity_id = getattr(entity, "id", "")
        data = self._to_dict(entity)
        self._storage.create(self._collection, entity_id, data)
        return entity

    def update(self, entity_id: str, entity: Any) -> Any:
        """更新实体。"""
        data = self._to_dict(entity)
        self._storage.update(self._collection, entity_id, data)
        return entity

    def delete(self, entity_id: str) -> bool:
        """删除实体。"""
        return self._storage.delete(self._collection, entity_id)

    def exists(self, entity_id: str) -> bool:
        """判断实体是否存在。"""
        return self._storage.exists(self._collection, entity_id)

    def count(self) -> int:
        """获取实体数量。"""
        return self._storage.count(self._collection)

    # ──────────────────────────────────────────
    # 批量操作
    # ──────────────────────────────────────────

    def create_many(self, entities: list[Any]) -> list[Any]:
        """批量创建。"""
        return [self.create(entity) for entity in entities]

    def delete_many(self, entity_ids: list[str]) -> int:
        """批量删除。"""
        count = 0
        for eid in entity_ids:
            if self.delete(eid):
                count += 1
        return count

    def update_many(self, updates: dict[str, dict[str, Any]]) -> int:
        """批量更新。"""
        count = 0
        for entity_id, data in updates.items():
            entity = self.get_by_id(entity_id)
            if entity:
                for key, value in data.items():
                    setattr(entity, key, value)
                self.update(entity_id, entity)
                count += 1
        return count

    # ──────────────────────────────────────────
    # 持久化
    # ──────────────────────────────────────────

    def load(self) -> None:
        """从存储加载数据。"""
        self._storage.load()

    def save(self) -> None:
        """持久化数据到存储。"""
        self._storage.save()


# 哨兵值
class _SENTINEL:
    pass
