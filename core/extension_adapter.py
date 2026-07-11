"""ExtensionAdapter — Extension 注册适配器。

封装 ComfyUI 扩展（extension）的注册和管理操作。
"""

from __future__ import annotations

import logging
from typing import Any

from .comfyui_bridge import ComfyUIBridge

logger = logging.getLogger("shiyu-tools.core.extension")


class ExtensionAdapter:
    """Extension 注册适配器。

    封装对 ComfyUI Extension API 的调用。
    """

    def __init__(self, bridge: ComfyUIBridge) -> None:
        self._bridge = bridge
        self._extensions: dict[str, Any] = {}

    def register_extension(self, name: str, extension: Any) -> bool:
        """注册扩展。

        Args:
            name: 扩展名称
            extension: 扩展实例

        Returns:
            是否注册成功
        """
        if name in self._extensions:
            logger.warning(f"Extension '{name}' already registered, replacing")
        self._extensions[name] = extension
        logger.info(f"Extension registered: {name}")
        return True

    def unregister_extension(self, name: str) -> bool:
        """注销扩展。"""
        if name in self._extensions:
            del self._extensions[name]
            logger.info(f"Extension unregistered: {name}")
            return True
        logger.warning(f"Extension '{name}' not found")
        return False

    def get_extension(self, name: str) -> Any | None:
        """获取已注册的扩展。"""
        return self._extensions.get(name)

    def get_all_extensions(self) -> dict[str, Any]:
        """获取所有已注册扩展。"""
        return dict(self._extensions)

    @property
    def count(self) -> int:
        """已注册扩展数量。"""
        return len(self._extensions)
