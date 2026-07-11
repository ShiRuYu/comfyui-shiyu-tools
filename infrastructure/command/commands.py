"""命令定义。

所有修改操作通过命令对象封装。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Command:
    """命令基类。

    所有命令必须继承此类。
    """
    executed: bool = False
    timestamp: str = ""

    def __post_init__(self) -> None:
        import datetime
        if not self.timestamp:
            self.timestamp = datetime.datetime.now().isoformat()

    def undo(self) -> None:
        """撤销此命令。子类可覆盖。"""
        pass


# ──────────────────────────────────────────
# Prompt 命令
# ──────────────────────────────────────────

@dataclass
class PromptCommand(Command):
    """Prompt 操作命令基类。"""

@dataclass
class CreatePromptCommand(PromptCommand):
    """创建 Prompt。"""
    name: str = ""
    positive: str = ""
    negative: str = ""
    tags: list[str] = field(default_factory=list)

@dataclass
class UpdatePromptCommand(PromptCommand):
    """更新 Prompt。"""
    prompt_id: str = ""
    changes: dict[str, Any] = field(default_factory=dict)

@dataclass
class DeletePromptCommand(PromptCommand):
    """删除 Prompt。"""
    prompt_id: str = ""

@dataclass
class FavoritePromptCommand(PromptCommand):
    """收藏/取消收藏 Prompt。"""
    prompt_id: str = ""
    favorite: bool = True

@dataclass
class SearchPromptCommand(PromptCommand):
    """搜索 Prompt。"""
    query: str = ""
    tags: list[str] = field(default_factory=list)


# ──────────────────────────────────────────
# Node Group 命令
# ──────────────────────────────────────────

@dataclass
class GroupCommand(Command):
    """Node Group 操作命令基类。"""

@dataclass
class CreateGroupCommand(GroupCommand):
    """创建 Group。"""
    name: str = ""
    color: str = "#4A90D9"
    parent: str | None = None

@dataclass
class UpdateGroupCommand(GroupCommand):
    """更新 Group。"""
    group_id: str = ""
    changes: dict[str, Any] = field(default_factory=dict)

@dataclass
class DeleteGroupCommand(GroupCommand):
    """删除 Group。"""
    group_id: str = ""

@dataclass
class MoveGroupCommand(GroupCommand):
    """移动 Group。"""
    group_id: str = ""
    target_parent: str | None = None
    target_index: int = -1

@dataclass
class CollapseGroupCommand(GroupCommand):
    """折叠/展开 Group。"""
    group_id: str = ""
    collapsed: bool = True

@dataclass
class AddNodeToGroupCommand(GroupCommand):
    """添加节点到 Group。"""
    group_id: str = ""
    node_ids: list[str] = field(default_factory=list)

@dataclass
class RemoveNodeFromGroupCommand(GroupCommand):
    """从 Group 移除节点。"""
    group_id: str = ""
    node_ids: list[str] = field(default_factory=list)

@dataclass
class LocateGroupCommand(GroupCommand):
    """定位 Group（选中该 Group 包含的所有节点）。"""
    group_id: str = ""
