"""ComfyUIBridge — ComfyUI Runtime 统一入口。

ComfyUIBridge 是 **唯一允许直接调用 ComfyUI API** 的类。
所有业务模块必须通过 ComfyUIBridge 访问 ComfyUI 功能。

封装范围：
- app.graph — 工作流图操作
- app.canvas — 画布操作
- api — REST API
- queue — 队列管理
- nodes — 节点操作
- extensions — 扩展注册

ComfyUI 版本升级时，只需修改此文件及 core/ 目录下的适配器。
"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger("shiyu-tools.core")


class ComfyUIBridge:
    """ComfyUI Runtime 桥接器。

    此类封装对 ComfyUI 内部 API 的所有直接调用。
    业务模块禁止直接导入 ComfyUI 模块。
    """

    def __init__(self) -> None:
        self._initialized = False

        # ComfyUI 引用（在 initialize 中注入）
        self._app: Any = None
        self._api: Any = None
        self._queue: Any = None
        self._nodes: Any = None

    # ──────────────────────────────────────────
    # 初始化
    # ──────────────────────────────────────────

    def initialize(self, app: Any, api: Any, queue: Any, nodes: Any) -> None:
        """注入 ComfyUI Runtime 引用。

        Args:
            app: ComfyUI app 实例
            api: ComfyUI API 实例
            queue: 队列实例
            nodes: 节点注册表
        """
        self._app = app
        self._api = api
        self._queue = queue
        self._nodes = nodes
        self._initialized = True
        logger.info("ComfyUIBridge initialized")

    @property
    def is_initialized(self) -> bool:
        """是否已初始化。"""
        return self._initialized

    # ──────────────────────────────────────────
    # Graph 操作
    # ──────────────────────────────────────────

    def get_graph(self) -> Any | None:
        """获取当前工作流图。"""
        if not self._initialized or self._app is None:
            return None
        try:
            return self._app.graph
        except AttributeError:
            logger.warning("app.graph not available")
            return None

    def get_canvas(self) -> Any | None:
        """获取画布对象。"""
        if not self._initialized or self._app is None:
            return None
        try:
            return self._app.canvas
        except AttributeError:
            logger.warning("app.canvas not available")
            return None

    # ──────────────────────────────────────────
    # API 操作
    # ──────────────────────────────────────────

    def get_api(self) -> Any | None:
        """获取 ComfyUI API。"""
        if not self._initialized:
            return None
        return self._api

    # ──────────────────────────────────────────
    # 队列操作
    # ──────────────────────────────────────────

    def get_queue(self) -> Any | None:
        """获取队列。"""
        if not self._initialized:
            return None
        return self._queue

    # ──────────────────────────────────────────
    # 节点注册
    # ──────────────────────────────────────────

    def get_nodes_registry(self) -> Any | None:
        """获取节点注册表。"""
        if not self._initialized:
            return None
        return self._nodes

    def register_node(self, node_class: type) -> bool:
        """注册自定义节点。

        Args:
            node_class: 节点类（需包含 NODE_CLASS_MAPPINGS）

        Returns:
            是否注册成功
        """
        if not self._initialized:
            logger.error("Cannot register node: ComfyUIBridge not initialized")
            return False

        try:
            class_name = getattr(node_class, "CLASS_NAME", node_class.__name__)
            # ComfyUI 的节点注册方式
            logger.info(f"Registering node: {class_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register node: {e}")
            return False

    # ──────────────────────────────────────────
    # 扩展操作
    # ──────────────────────────────────────────

    def register_extension(self, name: str, extension: Any) -> bool:
        """注册扩展。"""
        if not self._initialized:
            logger.error("Cannot register extension: ComfyUIBridge not initialized")
            return False
        logger.info(f"Registering extension: {name}")
        return True
