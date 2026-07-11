"""GroupRepository — Node Group 数据访问层。

Node Group 是业务对象，不是 UI 上的矩形。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from infrastructure.storage.storage import Storage
from .base_repository import BaseRepository


@dataclass
class GroupMetadata:
    """Group 元数据。

    支持：
    - 所有者
    - 描述
    - 创建/更新时间
    - 图标、颜色、快捷键
    - 收藏标记
    """
    owner: str = ""
    description: str = ""
    create_time: str = ""
    update_time: str = ""
    icon: str = ""
    color: str = ""
    shortcut: str = ""
    favorite: bool = False


@dataclass
class NodeGroup:
    """Node Group — 企业级分组业务对象。

    不是 UI 上的 Rectangle，而是包含完整业务属性的实体。
    """
    id: str = ""
    name: str = ""
    color: str = "#4A90D9"
    parent: Optional[str] = None
    children: list[str] = field(default_factory=list)
    node_ids: list[str] = field(default_factory=list)
    collapsed: bool = False
    enabled: bool = True
    locked: bool = False
    visible: bool = True
    metadata: GroupMetadata = field(default_factory=GroupMetadata)
    tags: list[str] = field(default_factory=list)


class GroupRepository(BaseRepository[NodeGroup]):
    """Node Group 数据访问。

    职责：
    - Group 实体的 CRUD
    - 树结构维护
    - 节点映射维护

    禁止：
    - ❌ 包含业务逻辑（如树遍历算法、折叠逻辑）
    - ❌ 直接操作 ComfyUI Graph
    """

    def __init__(self, storage: Storage) -> None:
        super().__init__(storage, "node_groups", NodeGroup)

    # ──────────────────────────────────────────
    # 树结构查询
    # ──────────────────────────────────────────

    def get_roots(self) -> list[NodeGroup]:
        """获取所有根节点（没有父节点的 Group）。"""
        return [g for g in self.get_all() if g.parent is None]

    def get_children(self, group_id: str) -> list[NodeGroup]:
        """获取指定 Group 的直接子节点。"""
        parent = self.get_by_id(group_id)
        if parent is None:
            return []
        return [self.get_by_id(cid) for cid in parent.children if self.get_by_id(cid) is not None]

    def get_descendants(self, group_id: str) -> list[NodeGroup]:
        """获取指定 Group 的所有后代节点（递归）。"""
        result: list[NodeGroup] = []
        children = self.get_children(group_id)
        for child in children:
            result.append(child)
            result.extend(self.get_descendants(child.id))
        return result

    def get_ancestors(self, group_id: str) -> list[NodeGroup]:
        """获取指定 Group 的所有祖先节点（从根到父节点）。"""
        result: list[NodeGroup] = []
        current = self.get_by_id(group_id)
        while current and current.parent:
            parent = self.get_by_id(current.parent)
            if parent:
                result.insert(0, parent)
                current = parent
            else:
                break
        return result

    def get_siblings(self, group_id: str) -> list[NodeGroup]:
        """获取同级节点。"""
        group = self.get_by_id(group_id)
        if group is None or group.parent is None:
            return [g for g in self.get_roots() if g.id != group_id]
        parent = self.get_by_id(group.parent)
        if parent is None:
            return []
        return [
            self.get_by_id(cid) for cid in parent.children
            if cid != group_id and self.get_by_id(cid) is not None
        ]

    # ──────────────────────────────────────────
    # 节点映射
    # ──────────────────────────────────────────

    def find_groups_by_node(self, node_id: str) -> list[NodeGroup]:
        """查找包含指定节点的所有 Group。"""
        return [g for g in self.get_all() if node_id in g.node_ids]

    def find_groups_by_nodes(self, node_ids: list[str]) -> list[NodeGroup]:
        """查找包含指定节点列表的 Group。"""
        node_set = set(node_ids)
        return [
            g for g in self.get_all()
            if node_set.intersection(g.node_ids)
        ]
