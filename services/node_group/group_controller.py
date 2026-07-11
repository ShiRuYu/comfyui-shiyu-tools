"""GroupController — Node Group API/命令入口。

接收来自 UI、快捷键、右键菜单的命令，转发给 GroupService。
"""

from __future__ import annotations

from typing import Any

from infrastructure.command.command_bus import CommandBus
from infrastructure.command.commands import (
    CreateGroupCommand,
    UpdateGroupCommand,
    DeleteGroupCommand,
    MoveGroupCommand,
    CollapseGroupCommand,
    AddNodeToGroupCommand,
    RemoveNodeFromGroupCommand,
    LocateGroupCommand,
)

from .group_service import GroupService


class GroupController:
    """Node Group 控制器。

    职责：
    - 注册命令处理器
    - 接收命令并调用 Service
    - 返回执行结果
    - 对需要调用 Core/Graph 的操作进行桥接

    禁止：
    - ❌ 包含业务逻辑
    - ❌ 直接访问 Repository
    - ❌ 直接操作 ComfyUI Graph
    """

    def __init__(
        self,
        service: GroupService,
        command_bus: CommandBus,
    ) -> None:
        self._service = service
        self._command_bus = command_bus

        # 注册命令处理器
        self._register_commands()

    def _register_commands(self) -> None:
        """注册所有命令处理器。"""
        self._command_bus.register(CreateGroupCommand, self._handle_create)
        self._command_bus.register(UpdateGroupCommand, self._handle_update)
        self._command_bus.register(DeleteGroupCommand, self._handle_delete)
        self._command_bus.register(MoveGroupCommand, self._handle_move)
        self._command_bus.register(CollapseGroupCommand, self._handle_collapse)
        self._command_bus.register(AddNodeToGroupCommand, self._handle_add_nodes)
        self._command_bus.register(RemoveNodeFromGroupCommand, self._handle_remove_nodes)
        self._command_bus.register(LocateGroupCommand, self._handle_locate)

    # ──────────────────────────────────────────
    # 命令处理器
    # ──────────────────────────────────────────

    def _handle_create(self, command: CreateGroupCommand) -> dict[str, Any]:
        """处理创建 Group 命令。"""
        group = self._service.create_group(
            name=command.name,
            color=command.color,
            parent=command.parent,
        )
        return {"success": True, "data": self._get_group_data(group.id)}

    def _handle_update(self, command: UpdateGroupCommand) -> dict[str, Any]:
        """处理更新 Group 命令。"""
        group = self._service.update_group(command.group_id, command.changes)
        if group is None:
            return {"success": False, "error": "Group not found"}
        return {"success": True, "data": self._get_group_data(group.id)}

    def _handle_delete(self, command: DeleteGroupCommand) -> dict[str, Any]:
        """处理删除 Group 命令。"""
        result = self._service.delete_group(command.group_id)
        return {"success": result}

    def _handle_move(self, command: MoveGroupCommand) -> dict[str, Any]:
        """处理移动 Group 命令。"""
        group = self._service.move_group(
            command.group_id,
            command.target_parent,
            command.target_index,
        )
        if group is None:
            return {"success": False, "error": "Group not found"}
        return {"success": True, "data": self._get_group_data(group.id)}

    def _handle_collapse(self, command: CollapseGroupCommand) -> dict[str, Any]:
        """处理折叠/展开命令。"""
        group = self._service.toggle_collapse(command.group_id)
        if group is None:
            return {"success": False, "error": "Group not found"}
        return {"success": True, "collapsed": group.collapsed}

    def _handle_add_nodes(self, command: AddNodeToGroupCommand) -> dict[str, Any]:
        """处理添加节点到 Group 的命令。"""
        group = self._service.add_nodes_to_group(command.group_id, command.node_ids)
        if group is None:
            return {"success": False, "error": "Group not found"}
        return {"success": True, "node_count": len(group.node_ids)}

    def _handle_remove_nodes(self, command: RemoveNodeFromGroupCommand) -> dict[str, Any]:
        """处理从 Group 移除节点的命令。"""
        group = self._service.remove_nodes_from_group(command.group_id, command.node_ids)
        if group is None:
            return {"success": False, "error": "Group not found"}
        return {"success": True, "node_count": len(group.node_ids)}

    def _handle_locate(self, command: LocateGroupCommand) -> dict[str, Any]:
        """处理定位 Group 的命令。"""
        node_ids = self._service.locate_group(command.group_id)
        if node_ids is None:
            return {"success": False, "error": "Group not found"}
        return {"success": True, "node_ids": node_ids}

    # ──────────────────────────────────────────
    # 工具
    # ──────────────────────────────────────────

    def _get_group_data(self, group_id: str) -> dict[str, Any] | None:
        """获取 Group 的可序列化数据。"""
        group = self._service.get_group(group_id)
        if group is None:
            return None
        from infrastructure.repository.base_repository import BaseRepository
        # 使用 repo 的序列化方法
        return self._service._repo._to_dict(group)
