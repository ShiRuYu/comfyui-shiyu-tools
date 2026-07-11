"""PromptController — Prompt API/命令入口。

接收来自 UI、快捷键、右键菜单的命令，转发给 PromptService。
"""

from __future__ import annotations

from typing import Any

from infrastructure.command.command_bus import CommandBus
from infrastructure.command.commands import (
    CreatePromptCommand,
    UpdatePromptCommand,
    DeletePromptCommand,
    FavoritePromptCommand,
    SearchPromptCommand,
)

from .prompt_service import PromptService


class PromptController:
    """Prompt 控制器。

    职责：
    - 注册命令处理器
    - 接收命令并调用 Service
    - 返回执行结果

    禁止：
    - ❌ 包含业务逻辑
    - ❌ 直接访问 Repository
    """

    def __init__(
        self,
        service: PromptService,
        command_bus: CommandBus,
    ) -> None:
        self._service = service
        self._command_bus = command_bus

        # 注册命令处理器
        self._register_commands()

    def _register_commands(self) -> None:
        """注册所有命令处理器。"""
        self._command_bus.register(CreatePromptCommand, self._handle_create)
        self._command_bus.register(UpdatePromptCommand, self._handle_update)
        self._command_bus.register(DeletePromptCommand, self._handle_delete)
        self._command_bus.register(FavoritePromptCommand, self._handle_favorite)
        self._command_bus.register(SearchPromptCommand, self._handle_search)

    # ──────────────────────────────────────────
    # 命令处理器
    # ──────────────────────────────────────────

    def _handle_create(self, command: CreatePromptCommand) -> dict[str, Any]:
        """处理创建 Prompt 命令。"""
        prompt = self._service.create_prompt(
            name=command.name,
            positive=command.positive,
            negative=command.negative,
            tags=command.tags,
        )
        return {"success": True, "data": self._service.export_prompt(prompt.id)}

    def _handle_update(self, command: UpdatePromptCommand) -> dict[str, Any]:
        """处理更新 Prompt 命令。"""
        prompt = self._service.update_prompt(command.prompt_id, command.changes)
        if prompt is None:
            return {"success": False, "error": "Prompt not found"}
        return {"success": True, "data": self._service.export_prompt(prompt.id)}

    def _handle_delete(self, command: DeletePromptCommand) -> dict[str, Any]:
        """处理删除 Prompt 命令。"""
        result = self._service.delete_prompt(command.prompt_id)
        return {"success": result}

    def _handle_favorite(self, command: FavoritePromptCommand) -> dict[str, Any]:
        """处理收藏命令。"""
        prompt = self._service.toggle_favorite(command.prompt_id)
        if prompt is None:
            return {"success": False, "error": "Prompt not found"}
        return {"success": True, "favorite": prompt.metadata.favorite}

    def _handle_search(self, command: SearchPromptCommand) -> dict[str, Any]:
        """处理搜索命令。"""
        results = self._service.search_prompts(
            query=command.query,
            tags=command.tags,
        )
        return {
            "success": True,
            "results": [self._service.export_prompt(p.id) for p in results],
            "count": len(results),
        }
