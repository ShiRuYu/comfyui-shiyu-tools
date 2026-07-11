"""PluginKernel — 全局插件内核单例。

PluginKernel 是插件的核心中枢：
- 管理模块注册与生命周期
- 持有基础设施实例（EventBus, CommandBus, Storage, Config, Logger）
- 提供 UI Service 注册
- 提供 ComfyUI Bridge 访问
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .lifecycle import LifecycleManager, LifecycleState
from .registry import ModuleRegistry

if TYPE_CHECKING:
    from .module import PluginModule
    from core.comfyui_bridge import ComfyUIBridge
    from infrastructure.storage.storage import Storage
    from infrastructure.event.event_bus import EventBus
    from infrastructure.command.command_bus import CommandBus
    from infrastructure.config.config import ConfigManager
    from infrastructure.logger.logger import LoggerService
    from ui.framework.sidebar import UIService


class PluginKernel:
    """插件内核 — 全局单例。"""

    _instance: PluginKernel | None = None

    def __init__(self) -> None:
        """初始化内核（仅允许通过 create() 调用）。"""
        if PluginKernel._instance is not None:
            raise RuntimeError("PluginKernel is a singleton. Use PluginKernel.create() instead.")

        PluginKernel._instance = self

        # 基础设施
        self._storage: Storage | None = None
        self._event_bus: EventBus | None = None
        self._command_bus: CommandBus | None = None
        self._config: ConfigManager | None = None
        self._logger: LoggerService | None = None
        self._ui_service: Any | None = None  # UIService type

        # ComfyUI Bridge
        self._comfyui_bridge: ComfyUIBridge | None = None

        # 模块系统
        self._registry = ModuleRegistry()
        self._lifecycle = LifecycleManager()

        # 元数据
        self._version: str = "0.1.0"
        self._comfyui_version: str = ""

    # ──────────────────────────────────────────
    # 工厂方法
    # ──────────────────────────────────────────

    @classmethod
    def create(cls) -> PluginKernel:
        """创建或获取 PluginKernel 实例。"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def get_instance(cls) -> PluginKernel | None:
        """获取现有 PluginKernel 实例，未创建时返回 None。"""
        return cls._instance

    @classmethod
    def destroy_instance(cls) -> None:
        """销毁全局实例。"""
        if cls._instance is not None:
            cls._instance = None

    # ──────────────────────────────────────────
    # 基础设施注入
    # ──────────────────────────────────────────

    def set_storage(self, storage: Storage) -> None:
        """设置存储服务。"""
        self._storage = storage

    def set_event_bus(self, event_bus: EventBus) -> None:
        """设置事件总线。"""
        self._event_bus = event_bus

    def set_command_bus(self, command_bus: CommandBus) -> None:
        """设置命令总线。"""
        self._command_bus = command_bus

    def set_config(self, config: ConfigManager) -> None:
        """设置配置管理器。"""
        self._config = config

    def set_logger(self, logger: LoggerService) -> None:
        """设置日志服务。"""
        self._logger = logger

    def set_ui_service(self, ui_service: Any) -> None:
        """设置 UI 服务。"""
        self._ui_service = ui_service

    def set_comfyui_bridge(self, bridge: ComfyUIBridge) -> None:
        """设置 ComfyUI Bridge。"""
        self._comfyui_bridge = bridge

    # ──────────────────────────────────────────
    # 基础设施获取
    # ──────────────────────────────────────────

    def get_storage(self) -> Storage:
        """获取存储服务。"""
        if self._storage is None:
            raise RuntimeError("Storage not initialized")
        return self._storage

    def get_event_bus(self) -> EventBus:
        """获取事件总线。"""
        if self._event_bus is None:
            raise RuntimeError("EventBus not initialized")
        return self._event_bus

    def get_command_bus(self) -> CommandBus:
        """获取命令总线。"""
        if self._command_bus is None:
            raise RuntimeError("CommandBus not initialized")
        return self._command_bus

    def get_config(self) -> ConfigManager:
        """获取配置管理器。"""
        if self._config is None:
            raise RuntimeError("Config not initialized")
        return self._config

    def get_logger(self) -> LoggerService:
        """获取日志服务。"""
        if self._logger is None:
            raise RuntimeError("Logger not initialized")
        return self._logger

    def get_ui_service(self) -> Any:
        """获取 UI 服务。"""
        if self._ui_service is None:
            raise RuntimeError("UIService not initialized")
        return self._ui_service

    def get_comfyui_bridge(self) -> ComfyUIBridge:
        """获取 ComfyUI Bridge。"""
        if self._comfyui_bridge is None:
            raise RuntimeError("ComfyUIBridge not initialized")
        return self._comfyui_bridge

    # ──────────────────────────────────────────
    # 模块管理
    # ──────────────────────────────────────────

    def register_module(self, module: PluginModule) -> None:
        """注册一个业务模块。"""
        self._registry.register(module)

    def get_module(self, name: str) -> PluginModule | None:
        """按名称获取已注册的模块。"""
        return self._registry.get(name)

    def get_all_modules(self) -> list[PluginModule]:
        """获取所有已注册的模块。"""
        return self._registry.get_all()

    # ──────────────────────────────────────────
    # 生命周期
    # ──────────────────────────────────────────

    @property
    def state(self) -> LifecycleState:
        """当前生命周期状态。"""
        return self._lifecycle.state

    def initialize(self) -> None:
        """初始化插件（Install → Initialize 阶段）。"""
        logger = self._logger
        if logger:
            logger.info(f"PluginKernel initializing (v{self._version})...")

        self._lifecycle.transition_to(LifecycleState.INITIALIZING)

        # 初始化所有已注册模块
        for module in self._registry.get_all():
            if logger:
                logger.info(f"  Initializing module: {module.name}")
            module.initialize()

        self._lifecycle.transition_to(LifecycleState.INITIALIZED)

        if logger:
            logger.info("PluginKernel initialized.")

    def load(self) -> None:
        """加载数据（Load 阶段）。"""
        logger = self._logger
        if logger:
            logger.info("PluginKernel loading data...")

        self._lifecycle.transition_to(LifecycleState.LOADING)

        for module in self._registry.get_all():
            if logger:
                logger.info(f"  Loading module: {module.name}")
            module.load()

        self._lifecycle.transition_to(LifecycleState.LOADED)

        if logger:
            logger.info("PluginKernel data loaded.")

    def start(self) -> None:
        """启动插件（Ready 阶段）。"""
        logger = self._logger
        if logger:
            logger.info("PluginKernel starting...")

        self._lifecycle.transition_to(LifecycleState.STARTING)

        for module in self._registry.get_all():
            if logger:
                logger.info(f"  Starting module: {module.name}")
            module.start()

        self._lifecycle.transition_to(LifecycleState.READY)

        if logger:
            logger.info("PluginKernel is READY.")

        # 发布插件启动事件
        if self._event_bus:
            self._event_bus.emit("plugin.initialized", {
                "version": self._version,
            })

    def shutdown(self) -> None:
        """关闭插件（Dispose 阶段）。"""
        logger = self._logger
        if logger:
            logger.info("PluginKernel shutting down...")

        # 发布关闭前事件
        if self._event_bus:
            self._event_bus.emit("plugin.before_shutdown", {})

        self._lifecycle.transition_to(LifecycleState.STOPPING)

        # 逆序停止模块
        for module in reversed(self._registry.get_all()):
            if logger:
                logger.info(f"  Stopping module: {module.name}")
            module.stop()
            module.destroy()

        self._lifecycle.transition_to(LifecycleState.DISPOSED)

        if logger:
            logger.info("PluginKernel shut down.")

    # ──────────────────────────────────────────
    # 属性
    # ──────────────────────────────────────────

    @property
    def version(self) -> str:
        """插件版本。"""
        return self._version

    @version.setter
    def version(self, value: str) -> None:
        self._version = value

    @property
    def comfyui_version(self) -> str:
        """ComfyUI 版本。"""
        return self._comfyui_version

    @comfyui_version.setter
    def comfyui_version(self, value: str) -> None:
        self._comfyui_version = value
