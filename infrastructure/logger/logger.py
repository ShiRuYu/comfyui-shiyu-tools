"""LoggerService — 日志服务。"""

from __future__ import annotations

import logging
import sys
from typing import TextIO


_LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


class LoggerService:
    """日志服务。

    封装 Python logging 模块，提供统一的日志接口。
    后续可扩展为文件日志、轮转日志等。
    """

    def __init__(
        self,
        name: str = "shiyu-tools",
        level: str = "info",
        output: TextIO | None = None,
    ) -> None:
        self._logger = logging.getLogger(name)
        self._logger.setLevel(_LOG_LEVELS.get(level, logging.INFO))

        # 避免重复添加 Handler
        if not self._logger.handlers:
            handler = logging.StreamHandler(output or sys.stdout)
            handler.setFormatter(logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            ))
            self._logger.addHandler(handler)

    # ──────────────────────────────────────────
    # 日志方法
    # ──────────────────────────────────────────

    def debug(self, message: str) -> None:
        self._logger.debug(message)

    def info(self, message: str) -> None:
        self._logger.info(message)

    def warning(self, message: str) -> None:
        self._logger.warning(message)

    def error(self, message: str) -> None:
        self._logger.error(message)

    def critical(self, message: str) -> None:
        self._logger.critical(message)

    # ──────────────────────────────────────────
    # 快捷方法
    # ──────────────────────────────────────────

    def set_level(self, level: str) -> None:
        """设置日志级别。"""
        log_level = _LOG_LEVELS.get(level, logging.INFO)
        self._logger.setLevel(log_level)

    def get_logger(self) -> logging.Logger:
        """获取底层 Logger 实例。"""
        return self._logger
