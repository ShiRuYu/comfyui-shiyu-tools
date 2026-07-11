"""GroupService — Node Group 业务逻辑。

职责：
- Group 树结构管理
- 分组/取消分组
- 折叠/展开
- 锁定/解锁
- 节点定位
- 统计
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any, Optional

from infrastructure.event.event_bus import EventBus
from infrastructure.command.command_bus import CommandBus
from infrastructure.event.events import GroupEvent
from infrastructure.repository.group_repository import (
    GroupMetadata,
    NodeGroup,
    GroupRepository,
)


class GroupService:
    """Node Group 业务逻辑层。

    职责：
    - Group 的 CRUD 业务逻辑
    - 树结构管理
    - 折叠/展开
    - 锁定/解锁
    - 节点管理
    - 统计信息

    禁止：
    - ❌ 直接操作存储（通过 Repository）
    - ❌ 直接操作 UI
    - ❌ 直接操作 ComfyUI Graph（应通过 Core 调用）
    """

    def __init__(
        self,
        repository: GroupRepository,
        event_bus: EventBus,
        command_bus: CommandBus,
    ) -> None:
        self._repo = repository
        self._event_bus = event_bus
        self._command_bus = command_bus

    # ──────────────────────────────────────────
    # CRUD
    # ──────────────────────────────────────────

    def create_group(
        self,
        name: str,
        color: str = "#4A90D9",
        parent: str | None = None,
        tags: list[str] | None = None,
    ) -> NodeGroup:
        """创建新的 Group。

        Args:
            name: 组名
            color: 颜色
            parent: 父组 ID（可选）
            tags: 标签

        Returns:
            创建的 NodeGroup

        Raises:
            ValueError: 名称为空或父组不存在
        """
        if not name or not name.strip():
            raise ValueError("Group name must not be empty")

        now = datetime.datetime.now().isoformat()

        group = NodeGroup(
            id=str(uuid.uuid4()),
            name=name.strip(),
            color=color,
            parent=parent,
            metadata=GroupMetadata(
                create_time=now,
                update_time=now,
            ),
            tags=tags or [],
        )

        self._repo.create(group)

        # 更新父节点的 children 列表
        if parent:
            parent_group = self._repo.get_by_id(parent)
            if parent_group is None:
                raise ValueError(f"Parent group '{parent}' not found")
            parent_group.children.append(group.id)
            self._repo.update(parent, parent_group)

        self._event_bus.emit(GroupEvent.CREATED, {
            "group_id": group.id,
            "parent": parent,
        })

        return group

    def update_group(self, group_id: str, changes: dict[str, Any]) -> NodeGroup | None:
        """更新 Group。"""
        group = self._repo.get_by_id(group_id)
        if group is None:
            return None

        for key, value in changes.items():
            if hasattr(group, key) and key != "id":
                setattr(group, key, value)

        group.metadata.update_time = datetime.datetime.now().isoformat()
        self._repo.update(group_id, group)

        self._event_bus.emit(GroupEvent.UPDATED, {
            "group_id": group_id,
            "changes": changes,
        })

        return group

    def delete_group(self, group_id: str) -> bool:
        """删除 Group。

        删除时：
        - 子节点上移一层（连接到父节点）
        - 从父节点的 children 列表中移除
        - 释放包含的节点引用
        """
        group = self._repo.get_by_id(group_id)
        if group is None:
            return False

        # 子节点上移
        if group.parent:
            parent = self._repo.get_by_id(group.parent)
            if parent:
                parent.children.remove(group_id)
                parent.children.extend(group.children)
                # 更新子节点的 parent
                for child_id in group.children:
                    child = self._repo.get_by_id(child_id)
                    if child:
                        child.parent = group.parent
                        self._repo.update(child_id, child)
                self._repo.update(group.parent, parent)

        self._repo.delete(group_id)

        self._event_bus.emit(GroupEvent.DELETED, {
            "group_id": group_id,
        })

        return True

    def get_group(self, group_id: str) -> NodeGroup | None:
        """获取指定 Group。"""
        return self._repo.get_by_id(group_id)

    def get_all_groups(self) -> list[NodeGroup]:
        """获取所有 Group。"""
        return self._repo.get_all()

    # ──────────────────────────────────────────
    # 树结构管理
    # ──────────────────────────────────────────

    def get_tree(self) -> list[NodeGroup]:
        """获取根级 Group 列表（树结构的入口）。"""
        return self._repo.get_roots()

    def move_group(
        self,
        group_id: str,
        target_parent: str | None,
        target_index: int = -1,
    ) -> NodeGroup | None:
        """移动 Group 到新的父节点下。"""
        group = self._repo.get_by_id(group_id)
        if group is None:
            return None

        old_parent = group.parent

        # 从原父节点移除
        if old_parent:
            old_parent_group = self._repo.get_by_id(old_parent)
            if old_parent_group and group_id in old_parent_group.children:
                old_parent_group.children.remove(group_id)
                self._repo.update(old_parent, old_parent_group)

        # 添加到新父节点
        group.parent = target_parent
        if target_parent:
            new_parent_group = self._repo.get_by_id(target_parent)
            if new_parent_group:
                if target_index >= 0:
                    new_parent_group.children.insert(target_index, group_id)
                else:
                    new_parent_group.children.append(group_id)
                self._repo.update(target_parent, new_parent_group)

        group.metadata.update_time = datetime.datetime.now().isoformat()
        self._repo.update(group_id, group)

        self._event_bus.emit(GroupEvent.MOVED, {
            "group_id": group_id,
            "from": old_parent,
            "to": target_parent,
        })

        return group

    # ──────────────────────────────────────────
    # 折叠/展开
    # ──────────────────────────────────────────

    def toggle_collapse(self, group_id: str) -> NodeGroup | None:
        """切换折叠状态。"""
        group = self._repo.get_by_id(group_id)
        if group is None:
            return None
        group.collapsed = not group.collapsed
        self._repo.update(group_id, group)

        self._event_bus.emit(GroupEvent.COLLAPSED, {
            "group_id": group_id,
            "collapsed": group.collapsed,
        })

        return group

    # ──────────────────────────────────────────
    # 锁定/解锁
    # ──────────────────────────────────────────

    def toggle_lock(self, group_id: str) -> NodeGroup | None:
        """切换锁定状态。"""
        group = self._repo.get_by_id(group_id)
        if group is None:
            return None
        group.locked = not group.locked

        # Also lock/unlock all children
        for child in self._repo.get_descendants(group_id):
            child.locked = group.locked
            self._repo.update(child.id, child)

        self._repo.update(group_id, group)

        event = GroupEvent.LOCKED if group.locked else GroupEvent.UNLOCKED
        self._event_bus.emit(event, {
            "group_id": group_id,
        })

        return group

    # ──────────────────────────────────────────
    # 节点管理
    # ──────────────────────────────────────────

    def add_nodes_to_group(self, group_id: str, node_ids: list[str]) -> NodeGroup | None:
        """添加节点到 Group。"""
        group = self._repo.get_by_id(group_id)
        if group is None:
            return None

        for nid in node_ids:
            if nid not in group.node_ids:
                group.node_ids.append(nid)

        self._repo.update(group_id, group)

        self._event_bus.emit(GroupEvent.NODE_ADDED, {
            "group_id": group_id,
            "node_ids": node_ids,
        })

        return group

    def remove_nodes_from_group(self, group_id: str, node_ids: list[str]) -> NodeGroup | None:
        """从 Group 移除节点。"""
        group = self._repo.get_by_id(group_id)
        if group is None:
            return None

        node_set = set(node_ids)
        group.node_ids = [nid for nid in group.node_ids if nid not in node_set]

        self._repo.update(group_id, group)

        self._event_bus.emit(GroupEvent.NODE_REMOVED, {
            "group_id": group_id,
            "node_ids": node_ids,
        })

        return group

    def locate_group(self, group_id: str) -> list[str] | None:
        """定位 Group，返回其包含的所有节点 ID。"""
        group = self._repo.get_by_id(group_id)
        if group is None:
            return None

        # 收集所有子节点的 node_ids
        all_node_ids = list(group.node_ids)
        for descendant in self._repo.get_descendants(group_id):
            all_node_ids.extend(descendant.node_ids)

        self._event_bus.emit(GroupEvent.NODE_LOCATED, {
            "group_id": group_id,
            "node_ids": all_node_ids,
        })

        return all_node_ids

    # ──────────────────────────────────────────
    # 可见性
    # ──────────────────────────────────────────

    def toggle_visibility(self, group_id: str) -> NodeGroup | None:
        """切换 Group 可见性。"""
        group = self._repo.get_by_id(group_id)
        if group is None:
            return None
        group.visible = not group.visible
        self._repo.update(group_id, group)

        self._event_bus.emit(GroupEvent.VISIBILITY_CHANGED, {
            "group_id": group_id,
            "visible": group.visible,
        })

        return group

    # ──────────────────────────────────────────
    # 统计
    # ──────────────────────────────────────────

    def get_group_statistics(self, group_id: str) -> dict[str, Any]:
        """获取 Group 统计信息。"""
        group = self._repo.get_by_id(group_id)
        if group is None:
            return {}

        descendants = self._repo.get_descendants(group_id)
        all_node_ids = set(group.node_ids)
        for desc in descendants:
            all_node_ids.update(desc.node_ids)

        return {
            "group_id": group_id,
            "name": group.name,
            "direct_node_count": len(group.node_ids),
            "total_node_count": len(all_node_ids),
            "direct_child_count": len(group.children),
            "descendant_count": len(descendants),
            "depth": len(self._repo.get_ancestors(group_id)),
            "locked": group.locked,
            "collapsed": group.collapsed,
            "visible": group.visible,
        }
