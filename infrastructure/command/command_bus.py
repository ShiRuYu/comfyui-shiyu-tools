"""CommandBus — 命令总线。

命令模式实现：
- 所有修改操作通过 Command 对象提交
- 支持命令注册、执行、撤销
- 天然支持 Undo/Redo 历史
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Type

from .commands import Command

logger = logging.getLogger("shiyu-tools.command")

# 命令处理器类型
CommandHandler = Callable[[Command], Any]


class CommandBus:
    """命令总线。

    职责：
    - 注册命令类型及其处理器
    - 执行命令
    - 维护命令历史（支持 Undo/Redo）
    - 权限校验
    """

    def __init__(self) -> None:
        self._handlers: dict[type, CommandHandler] = {}
        self._history: list[Command] = []
        self._history_index: int = -1
        self._max_history: int = 100

    # ──────────────────────────────────────────
    # 注册
    # ──────────────────────────────────────────

    def register(self, command_type: type[Command], handler: CommandHandler) -> None:
        """注册命令处理器。

        Args:
            command_type: 命令类
            handler: 处理函数
        """
        self._handlers[command_type] = handler

    def unregister(self, command_type: type[Command]) -> None:
        """注销命令处理器。"""
        self._handlers.pop(command_type, None)

    # ──────────────────────────────────────────
    # 执行
    # ──────────────────────────────────────────

    def execute(self, command: Command) -> Any:
        """执行命令。

        Args:
            command: 命令实例

        Returns:
            命令执行结果

        Raises:
            RuntimeError: 没有注册对应处理器
        """
        command_type = type(command)
        handler = self._handlers.get(command_type)

        if handler is None:
            raise RuntimeError(f"No handler registered for command: {command_type.__name__}")

        # 执行
        result = handler(command)

        # 记录历史
        command.executed = True
        self._history = self._history[:self._history_index + 1]
        self._history.append(command)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        self._history_index = len(self._history) - 1

        logger.debug(f"Command executed: {command_type.__name__}")
        return result

    # ──────────────────────────────────────────
    # Undo / Redo
    # ──────────────────────────────────────────

    def undo(self) -> bool:
        """撤销上一条命令。

        Returns:
            是否成功撤销
        """
        if self._history_index < 0:
            return False

        command = self._history[self._history_index]
        if hasattr(command, 'undo') and callable(command.undo):
            try:
                command.undo()
                self._history_index -= 1
                logger.debug(f"Undo: {type(command).__name__}")
                return True
            except Exception as e:
                logger.error(f"Undo failed for {type(command).__name__}: {e}")
                return False

        return False

    def redo(self) -> bool:
        """重做下一条命令。

        Returns:
            是否成功重做
        """
        if self._history_index >= len(self._history) - 1:
            return False

        self._history_index += 1
        command = self._history[self._history_index]

        try:
            self.execute(command)
            logger.debug(f"Redo: {type(command).__name__}")
            return True
        except Exception as e:
            logger.error(f"Redo failed for {type(command).__name__}: {e}")
            self._history_index -= 1
            return False

    # ──────────────────────────────────────────
    # 工具
    # ──────────────────────────────────────────

    def clear_history(self) -> None:
        """清空命令历史。"""
        self._history.clear()
        self._history_index = -1

    @property
    def can_undo(self) -> bool:
        """是否可以撤销。"""
        return self._history_index >= 0

    @property
    def can_redo(self) -> bool:
        """是否可以重做。"""
        return self._history_index < len(self._history) - 1

    @property
    def history_count(self) -> int:
        """历史命令数量。"""
        return len(self._history)
