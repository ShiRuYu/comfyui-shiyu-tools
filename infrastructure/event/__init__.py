"""事件系统。

提供事件发布/订阅机制，用于模块间解耦通信。
"""

from .event_bus import EventBus
from .events import (
    ShiyuEvent,
    PromptEvent,
    GroupEvent,
    PluginEvent,
)

__all__ = [
    "EventBus",
    "ShiyuEvent",
    "PromptEvent",
    "GroupEvent",
    "PluginEvent",
]
