"""Toolbar — 工具栏。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ToolbarAction:
    """工具栏动作。"""
    id: str
    label: str
    icon: str = ""
    tooltip: str = ""
    shortcut: str = ""
    callback: Callable | None = None
    enabled: bool = True
    visible: bool = True


class Toolbar:
    """工具栏管理器。

    管理工具栏按钮和动作。
    """

    def __init__(self) -> None:
        self._actions: dict[str, ToolbarAction] = {}
        self._groups: dict[str, list[str]] = {}

    def add_action(self, action: ToolbarAction, group: str = "default") -> None:
        """添加工具栏动作。"""
        self._actions[action.id] = action
        if group not in self._groups:
            self._groups[group] = []
        if action.id not in self._groups[group]:
            self._groups[group].append(action.id)

    def remove_action(self, action_id: str) -> None:
        """移除工具栏动作。"""
        self._actions.pop(action_id, None)
        for group in self._groups.values():
            if action_id in group:
                group.remove(action_id)

    def get_action(self, action_id: str) -> ToolbarAction | None:
        """获取工具栏动作。"""
        return self._actions.get(action_id)

    def get_actions(self, group: str | None = None) -> list[ToolbarAction]:
        """获取指定分组或所有动作。"""
        if group:
            return [
                self._actions[aid] for aid in self._groups.get(group, [])
                if aid in self._actions
            ]
        return list(self._actions.values())

    def enable_action(self, action_id: str, enabled: bool = True) -> None:
        """启用/禁用动作。"""
        action = self._actions.get(action_id)
        if action:
            action.enabled = enabled

    def clear(self) -> None:
        """清空所有动作。"""
        self._actions.clear()
        self._groups.clear()
