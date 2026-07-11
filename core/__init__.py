"""Core 层 — 唯一允许调用 ComfyUI API 的层。

Core 层封装了所有 ComfyUI Runtime 的直接交互：
- ComfyUIBridge: 统一入口
- GraphAdapter: Graph 操作封装
- ExtensionAdapter: Extension 注册封装

当 ComfyUI 版本升级导致 API 变化时，只需修改 Core 层。
"""

from .comfyui_bridge import ComfyUIBridge
from .graph_adapter import GraphAdapter
from .extension_adapter import ExtensionAdapter

__all__ = [
    "ComfyUIBridge",
    "GraphAdapter",
    "ExtensionAdapter",
]
