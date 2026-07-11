"""UI 层 — 所有 UI 组件统一管理。

模块不能自己创建窗口，必须通过 UI Framework 注册。
"""

from .framework.sidebar import SidebarPanel, UIService

__all__ = ["SidebarPanel", "UIService"]
