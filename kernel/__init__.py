"""ComfyUI Shiyu Tools — Plugin Kernel.

Plugin Kernel 是插件的核心中枢，所有模块都注册在 Kernel 上。
Kernel 是唯一直接依赖 ComfyUI Runtime 的层。
"""

from .kernel import PluginKernel
from .module import PluginModule
from .lifecycle import LifecycleState, LifecycleManager
from .registry import ModuleRegistry

__all__ = [
    "PluginKernel",
    "PluginModule",
    "LifecycleState",
    "LifecycleManager",
    "ModuleRegistry",
]
