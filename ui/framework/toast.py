"""Toast — 短暂消息提示。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ToastMessage:
    """Toast 消息。"""
    message: str
    type: str = "info"  # info, success, warning, error
    duration: int = 3000  # 毫秒


class Toast:
    """Toast 消息管理器。

    显示短暂的消息提示，自动消失。
    """

    def __init__(self) -> None:
        self._messages: list[ToastMessage] = []
        self._max_messages = 5

    def info(self, message: str, duration: int = 3000) -> None:
        """显示信息提示。"""
        self._add(ToastMessage(message, "info", duration))

    def success(self, message: str, duration: int = 3000) -> None:
        """显示成功提示。"""
        self._add(ToastMessage(message, "success", duration))

    def warning(self, message: str, duration: int = 4000) -> None:
        """显示警告提示。"""
        self._add(ToastMessage(message, "warning", duration))

    def error(self, message: str, duration: int = 5000) -> None:
        """显示错误提示。"""
        self._add(ToastMessage(message, "error", duration))

    def _add(self, msg: ToastMessage) -> None:
        """添加消息。"""
        self._messages.append(msg)
        if len(self._messages) > self._max_messages:
            self._messages.pop(0)

    def clear(self) -> None:
        """清空所有消息。"""
        self._messages.clear()

    @property
    def messages(self) -> list[ToastMessage]:
        """当前消息列表。"""
        return list(self._messages)
