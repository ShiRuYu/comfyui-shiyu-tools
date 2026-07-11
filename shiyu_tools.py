"""shiyu_tools — ComfyUI Shiyu Tools 插件主启动器。

这是插件的主入口，负责：
1. 创建 PluginKernel 实例
2. 注入基础设施（Storage, EventBus, CommandBus, Config, Logger）
3. 创建 Core/ComfyUI Bridge
4. 注册业务模块（Prompt Center, Node Group Center）
5. 执行生命周期 (Initialize → Load → Start)

调用方（__init__.py）在 ComfyUI 加载插件时调用 bootstrap()。
"""

from __future__ import annotations

import logging
import os
import sys

# ──────────────────────────────────────────
# 基础设施
# ──────────────────────────────────────────
from kernel.kernel import PluginKernel
from infrastructure.storage.json_storage import JsonStorage
from infrastructure.event.event_bus import EventBus
from infrastructure.command.command_bus import CommandBus
from infrastructure.config.config import ConfigManager
from infrastructure.logger.logger import LoggerService

# ──────────────────────────────────────────
# Core
# ──────────────────────────────────────────
from core.comfyui_bridge import ComfyUIBridge
from core.graph_adapter import GraphAdapter
from core.extension_adapter import ExtensionAdapter

# ──────────────────────────────────────────
# UI Framework
# ──────────────────────────────────────────
from ui.framework.sidebar import UIService
from ui.framework.toolbar import Toolbar
from ui.framework.inspector import Inspector
from ui.framework.dialog import Dialog
from ui.framework.toast import Toast


# ──────────────────────────────────────────
# 模块注册函数（延迟导入避免循环依赖）
# ──────────────────────────────────────────

def _register_prompt_module(kernel: PluginKernel) -> None:
    """注册 Prompt Center 模块。"""
    from kernel.module import PluginModule
    from infrastructure.repository.prompt_repository import PromptRepository
    from services.prompt.prompt_service import PromptService
    from services.prompt.prompt_controller import PromptController
    from ui.prompt.prompt_panel import PromptPanel

    class PromptModule(PluginModule):
        """Prompt Center 业务模块。"""

        def __init__(self) -> None:
            super().__init__("prompt", kernel)

        def initialize(self) -> None:
            storage = self._kernel.get_storage()
            event_bus = self._kernel.get_event_bus()
            command_bus = self._kernel.get_command_bus()
            ui_service = self._kernel.get_ui_service()

            # 1. Repository
            self._repository = PromptRepository(storage)

            # 2. Service
            self._service = PromptService(self._repository, event_bus, command_bus)

            # 3. Controller
            self._controller = PromptController(self._service, command_bus)

            # 4. UI
            self._panel = PromptPanel(self._controller)
            ui_service.register_panel("prompt", self._panel)

            logger = self._kernel.get_logger()
            logger.info("PromptModule initialized")

        def load(self) -> None:
            self._repository.load()
            logger = self._kernel.get_logger()
            logger.info(f"PromptModule loaded: {self._repository.count()} prompts")

        def start(self) -> None:
            self._panel.show()
            logger = self._kernel.get_logger()
            logger.info("PromptModule started")

        def stop(self) -> None:
            self._panel.hide()

        def destroy(self) -> None:
            self._repository.save()

    module = PromptModule()
    kernel.register_module(module)


def _register_group_module(kernel: PluginKernel) -> None:
    """注册 Node Group Center 模块。"""
    from kernel.module import PluginModule
    from infrastructure.repository.group_repository import GroupRepository
    from services.node_group.group_service import GroupService
    from services.node_group.group_controller import GroupController
    from ui.node_group.group_panel import GroupPanel

    class GroupModule(PluginModule):
        """Node Group Center 业务模块。"""

        def __init__(self) -> None:
            super().__init__("node_group", kernel)

        def initialize(self) -> None:
            storage = self._kernel.get_storage()
            event_bus = self._kernel.get_event_bus()
            command_bus = self._kernel.get_command_bus()
            ui_service = self._kernel.get_ui_service()

            # 1. Repository
            self._repository = GroupRepository(storage)

            # 2. Service
            self._service = GroupService(self._repository, event_bus, command_bus)

            # 3. Controller
            self._controller = GroupController(self._service, command_bus)

            # 4. UI
            self._panel = GroupPanel(self._controller)
            ui_service.register_panel("node_group", self._panel)

            logger = self._kernel.get_logger()
            logger.info("GroupModule initialized")

        def load(self) -> None:
            self._repository.load()
            logger = self._kernel.get_logger()
            logger.info(f"GroupModule loaded: {self._repository.count()} groups")

        def start(self) -> None:
            self._panel.show()
            logger = self._kernel.get_logger()
            logger.info("GroupModule started")

        def stop(self) -> None:
            self._panel.hide()

        def destroy(self) -> None:
            self._repository.save()

    module = GroupModule()
    kernel.register_module(module)


# ──────────────────────────────────────────
# 启动
# ──────────────────────────────────────────

def bootstrap() -> PluginKernel:
    """启动 Shiyu Tools 插件。

    由 __init__.py 在 ComfyUI 加载插件时调用。
    可多次调用，幂等。

    Returns:
        PluginKernel 实例
    """
    # 如果已经初始化，直接返回
    existing = PluginKernel.get_instance()
    if existing is not None:
        return existing

    # 1. 创建插件数据目录
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(plugin_dir, "data")
    config_dir = os.path.join(plugin_dir, "config")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(config_dir, exist_ok=True)

    # 2. 创建内核
    kernel = PluginKernel.create()

    # 3. 注入基础设施
    logger = LoggerService(name="shiyu-tools", level="info")
    kernel.set_logger(logger)

    logger.info("Bootstrap: Shiyu Tools starting...")

    storage = JsonStorage(base_path=data_dir)
    kernel.set_storage(storage)
    logger.info("  Storage: JsonStorage initialized")

    event_bus = EventBus()
    kernel.set_event_bus(event_bus)
    logger.info("  EventBus initialized")

    command_bus = CommandBus()
    kernel.set_command_bus(command_bus)
    logger.info("  CommandBus initialized")

    config = ConfigManager(
        config_path=os.path.join(config_dir, "config.json")
    )
    kernel.set_config(config)
    logger.info("  ConfigManager initialized")

    # 4. 创建 ComfyUI Bridge（由 ComfyUI 加载时注入真实引用）
    bridge = ComfyUIBridge()
    kernel.set_comfyui_bridge(bridge)
    graph_adapter = GraphAdapter(bridge)
    extension_adapter = ExtensionAdapter(bridge)

    kernel.set_ui_service(UIService())
    logger.info("  UIService initialized")

    # 5. 加载数据
    storage.load()
    config.load()

    # 6. 注册业务模块
    _register_prompt_module(kernel)
    _register_group_module(kernel)
    logger.info(f"  Modules registered: {len(kernel.get_all_modules())}")

    # 7. 执行生命周期
    try:
        kernel.initialize()
        kernel.load()
        kernel.start()
        logger.info("Bootstrap: Shiyu Tools READY")
    except Exception as e:
        logger.error(f"Bootstrap failed: {e}")
        raise

    return kernel


def shutdown() -> None:
    """关闭 Shiyu Tools 插件。"""
    kernel = PluginKernel.get_instance()
    if kernel is None:
        return

    logger = kernel._logger
    if logger:
        logger.info("Shutdown: Shiyu Tools stopping...")

    kernel.shutdown()
    PluginKernel.destroy_instance()

    if logger:
        logger.info("Shutdown: Shiyu Tools stopped")
