"""GroupPanel — Node Group 侧边栏面板。"""

from __future__ import annotations

from typing import Any

from ui.framework.sidebar import SidebarPanel


class GroupPanel(SidebarPanel):
    """Node Group 侧边栏面板。

    提供分组树形视图、属性面板、搜索定位等 UI 功能。
    所有用户操作通过 Controller 发送命令，不直接调用 Service。

    职责：
    - 渲染分组树
    - 拖拽排序
    - 折叠/展开
    - 锁定/解锁
    - 节点定位
    - 右键菜单

    禁止：
    - ❌ 直接调用 Service
    - ❌ 包含业务逻辑
    - ❌ 直接操作 ComfyUI Graph
    """

    def __init__(self, controller) -> None:
        super().__init__()
        self._controller = controller
        self._title = "Node Groups"
        self._icon = "group_icon"
        self._expanded_groups: set[str] = set()
        self._selected_group: str | None = None

    # ──────────────────────────────────────────
    # UI 操作
    # ──────────────────────────────────────────

    def select_group(self, group_id: str) -> None:
        """选中 Group。"""
        self._selected_group = group_id

    def toggle_expand(self, group_id: str) -> None:
        """切换展开/折叠状态。"""
        if group_id in self._expanded_groups:
            self._expanded_groups.discard(group_id)
        else:
            self._expanded_groups.add(group_id)

        # 发送命令
        from infrastructure.command.commands import CollapseGroupCommand
        cmd = CollapseGroupCommand(
            group_id=group_id,
            collapsed=group_id not in self._expanded_groups,
        )
        self._controller._command_bus.execute(cmd)

    def add_selected_nodes(self, group_id: str, node_ids: list[str]) -> None:
        """将选中的节点添加到 Group。"""
        from infrastructure.command.commands import AddNodeToGroupCommand
        cmd = AddNodeToGroupCommand(group_id=group_id, node_ids=node_ids)
        self._controller._command_bus.execute(cmd)

    def locate_group(self, group_id: str) -> None:
        """定位 Group（选中该 Group 包含的所有节点）。"""
        from infrastructure.command.commands import LocateGroupCommand
        cmd = LocateGroupCommand(group_id=group_id)
        self._controller._command_bus.execute(cmd)
