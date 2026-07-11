"""Inspector — 属性检查器。"""

from __future__ import annotations

from typing import Any


class Inspector:
    """属性检查器。

    显示选中节点/分组的属性信息。
    """

    def __init__(self) -> None:
        self._current: dict[str, Any] = {}
        self._visible: bool = False

    def show(self, data: dict[str, Any]) -> None:
        """显示属性。"""
        self._current = dict(data)
        self._visible = True

    def hide(self) -> None:
        """隐藏属性。"""
        self._current.clear()
        self._visible = False

    def update(self, data: dict[str, Any]) -> None:
        """更新属性。"""
        self._current.update(data)

    @property
    def visible(self) -> bool:
        """是否可见。"""
        return self._visible

    @property
    def current(self) -> dict[str, Any]:
        """当前显示的属性数据。"""
        return dict(self._current)
