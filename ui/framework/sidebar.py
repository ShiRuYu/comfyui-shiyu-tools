"""Sidebar — 侧边栏 UI 框架。

提供侧边栏容器，所有面板必须通过 UIService 注册。
"""

from __future__ import annotations

from typing import Any


class SidebarPanel:
    """侧边栏面板基类。

    所有侧边栏面板必须继承此类。
    """

    def __init__(self) -> None:
        self._title: str = ""
        self._icon: str = ""
        self._visible: bool = False
        self._data: dict[str, Any] = {}

    @property
    def title(self) -> str:
        """面板标题。"""
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self._title = value

    @property
    def icon(self) -> str:
        """面板图标。"""
        return self._icon

    @property
    def visible(self) -> bool:
        """面板是否可见。"""
        return self._visible

    def show(self) -> None:
        """显示面板。"""
        self._visible = True

    def hide(self) -> None:
        """隐藏面板。"""
        self._visible = False

    def update(self, data: dict[str, Any]) -> None:
        """更新面板数据。"""
        self._data.update(data)

    def get_data(self) -> dict[str, Any]:
        """获取面板数据。"""
        return dict(self._data)


class UIService:
    """UI 服务 — 统一管理所有 UI 组件。

    职责：
    - 管理侧边栏面板注册
    - 管理工具栏
    - 管理属性检查器
    - 管理对话框
    - 管理 Toast 消息

    模块不能自己创建窗口，必须通过 UIService 注册。
    """

    def __init__(self) -> None:
        self._panels: dict[str, SidebarPanel] = {}
        self._active_panel: str | None = None
        self._visible_panels: list[str] = []

    # ──────────────────────────────────────────
    # 面板管理
    # ──────────────────────────────────────────

    def register_panel(self, name: str, panel: SidebarPanel) -> None:
        """注册侧边栏面板。

        Args:
            name: 面板名称（唯一标识）
            panel: 面板实例
        """
        self._panels[name] = panel

    def unregister_panel(self, name: str) -> None:
        """注销面板。"""
        self._panels.pop(name, None)

    def get_panel(self, name: str) -> SidebarPanel | None:
        """获取指定面板。"""
        return self._panels.get(name)

    def get_all_panels(self) -> dict[str, SidebarPanel]:
        """获取所有已注册的面板。"""
        return dict(self._panels)

    # ──────────────────────────────────────────
    # 面板可见性
    # ──────────────────────────────────────────

    def show_panel(self, name: str) -> None:
        """显示指定面板。"""
        panel = self._panels.get(name)
        if panel:
            panel.show()
            if name not in self._visible_panels:
                self._visible_panels.append(name)
            self._active_panel = name

    def hide_panel(self, name: str) -> None:
        """隐藏指定面板。"""
        panel = self._panels.get(name)
        if panel:
            panel.hide()
            if name in self._visible_panels:
                self._visible_panels.remove(name)
            if self._active_panel == name:
                self._active_panel = self._visible_panels[-1] if self._visible_panels else None

    def hide_all_panels(self) -> None:
        """隐藏所有面板。"""
        for name, panel in self._panels.items():
            panel.hide()
        self._visible_panels.clear()
        self._active_panel = None

    # ──────────────────────────────────────────
    # 活动面板
    # ──────────────────────────────────────────

    def set_active_panel(self, name: str) -> None:
        """设置活动面板。"""
        if name in self._panels:
            self._active_panel = name
            self.show_panel(name)

    @property
    def active_panel(self) -> str | None:
        """当前活动面板名称。"""
        return self._active_panel

    @property
    def visible_panels(self) -> list[str]:
        """当前可见面板列表。"""
        return list(self._visible_panels)
