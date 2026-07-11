"""EventBus — 事件总线。

发布/订阅模式实现，支持：
- 同步/异步事件
- 通配符监听（如 "prompt.*" 匹配所有 prompt 事件）
- 一次性监听器
- 监听器优先级
"""

from __future__ import annotations

import fnmatch
import logging
from typing import Any, Callable

logger = logging.getLogger("shiyu-tools.event")

# 事件监听器类型
EventHandler = Callable[[str, dict[str, Any]], None]


class EventBus:
    """事件总线 — 发布/订阅模式。

    模块间通信通过 EventBus 解耦：
    - 发布者不关心谁在监听
    - 监听者不关心谁在发布
    - 模块之间禁止直接调用
    """

    def __init__(self) -> None:
        # {event_name: [(handler, priority, once), ...]}
        self._handlers: dict[str, list[tuple[EventHandler, int, bool]]] = {}
        self._patterns: list[tuple[str, EventHandler, int, bool]] = []
        self._history: list[dict[str, Any]] = []
        self._max_history = 100

    # ──────────────────────────────────────────
    # 监听
    # ──────────────────────────────────────────

    def on(
        self,
        event: str,
        handler: EventHandler,
        priority: int = 0,
    ) -> None:
        """注册事件监听器。

        Args:
            event: 事件名称，支持通配符（如 "prompt.*"）
            handler: 处理函数
            priority: 优先级，数值越大越先执行
        """
        if "*" in event or "?" in event:
            # 通配符模式
            self._patterns.append((event, handler, priority, False))
            self._patterns.sort(key=lambda x: -x[2])
        else:
            # 精确匹配
            if event not in self._handlers:
                self._handlers[event] = []
            self._handlers[event].append((handler, priority, False))
            self._handlers[event].sort(key=lambda x: -x[1])

    def once(
        self,
        event: str,
        handler: EventHandler,
        priority: int = 0,
    ) -> None:
        """注册一次性事件监听器（执行一次后自动移除）。"""
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append((handler, priority, True))

    def off(self, event: str, handler: EventHandler | None = None) -> None:
        """移除事件监听器。

        Args:
            event: 事件名称
            handler: 要移除的处理器，为 None 时移除所有处理器
        """
        if handler is None:
            self._handlers.pop(event, None)
            self._patterns = [(p, h, pr, o) for p, h, pr, o in self._patterns if p != event]
        else:
            if event in self._handlers:
                self._handlers[event] = [
                    (h, p, o) for h, p, o in self._handlers[event] if h != handler
                ]
            self._patterns = [(p, h, pr, o) for p, h, pr, o in self._patterns if h != handler]

    # ──────────────────────────────────────────
    # 发布
    # ──────────────────────────────────────────

    def emit(self, event: str, data: dict[str, Any] | None = None) -> None:
        """发布事件。

        Args:
            event: 事件名称
            data: 事件数据
        """
        data = data or {}
        event_data = {"event": event, "data": data}

        # 记录历史
        self._history.append(event_data)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        # 精确匹配
        if event in self._handlers:
            self._run_handlers(event, self._handlers[event], data)

        # 通配符匹配
        for pattern, handler, priority, once in self._patterns:
            if fnmatch.fnmatch(event, pattern):
                try:
                    handler(event, data)
                except Exception as e:
                    logger.error(f"Event handler error for '{event}': {e}")

        logger.debug(f"Event emitted: {event}")

    def _run_handlers(
        self,
        event: str,
        handlers: list[tuple[EventHandler, int, bool]],
        data: dict[str, Any],
    ) -> None:
        """执行一组处理器。"""
        remove_list: list[EventHandler] = []
        for handler, priority, once in handlers:
            try:
                handler(event, data)
                if once:
                    remove_list.append(handler)
            except Exception as e:
                logger.error(f"Event handler error for '{event}': {e}")

        # 清理一次性处理器
        if remove_list:
            self._handlers[event] = [
                (h, p, o) for h, p, o in self._handlers[event]
                if h not in remove_list
            ]

    # ──────────────────────────────────────────
    # 工具方法
    # ──────────────────────────────────────────

    def clear(self) -> None:
        """清除所有监听器和历史。"""
        self._handlers.clear()
        self._patterns.clear()
        self._history.clear()

    def get_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取最近的事件历史。"""
        return self._history[-limit:]

    @property
    def listener_count(self) -> int:
        """当前注册的监听器数量。"""
        count = sum(len(h) for h in self._handlers.values())
        count += len(self._patterns)
        return count
