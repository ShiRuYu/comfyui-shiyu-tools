"""Dialog — 对话框。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class DialogConfig:
    """对话框配置。"""
    title: str = ""
    message: str = ""
    width: int = 400
    height: int = 300
    modal: bool = True
    buttons: list[str] = field(default_factory=lambda: ["OK", "Cancel"])
    data: dict[str, Any] = field(default_factory=dict)


class Dialog:
    """对话框管理器。

    管理模态/非模态对话框的创建和生命周期。
    """

    def __init__(self) -> None:
        self._active_dialog: DialogConfig | None = None
        self._callbacks: dict[str, Callable] = {}

    def open(self, config: DialogConfig) -> None:
        """打开对话框。"""
        self._active_dialog = config

    def close(self) -> None:
        """关闭当前对话框。"""
        self._active_dialog = None

    def on_button(self, button: str, callback: Callable) -> None:
        """注册按钮回调。"""
        self._callbacks[button] = callback

    def trigger(self, button: str) -> None:
        """触发按钮点击。"""
        if button in self._callbacks:
            self._callbacks[button](self._active_dialog)
        self.close()

    @property
    def is_open(self) -> bool:
        """是否有打开的对话框。"""
        return self._active_dialog is not None

    @property
    def current(self) -> DialogConfig | None:
        """当前对话框配置。"""
        return self._active_dialog
