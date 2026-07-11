"""
ComfyUI Shiyu Tools — Enterprise Plugin Framework

一个运行于 ComfyUI 内部的企业级插件平台。
目标不是生成图片，而是增强 Workflow 开发效率。

架构类似 VSCode Plugin / JetBrains Plugin / Chrome Extension，
而非普通 ComfyUI Custom Node。
"""

from __future__ import annotations

import logging

__version__ = "0.1.0"
__author__ = "ShiRuYu"
__license__ = "MIT"
__description__ = "ComfyUI Enterprise Plugin Framework"

EXTENSION_NAME = "Shiyu Tools"
EXTENSION_DESCRIPTION = "Enterprise Plugin Framework for ComfyUI"

WEB_DIRECTORY = "./web"

logger = logging.getLogger("shiyu-tools")


def _bootstrap_plugin() -> None:
    """安全引导插件。"""
    try:
        from .shiyu_tools import bootstrap
        bootstrap()
    except Exception as e:
        print(f"[Shiyu Tools] Bootstrap failed: {e}")
        import traceback
        traceback.print_exc()


def _register_api_routes(server_module) -> None:
    """注册 API 路由。"""
    try:
        from .routes import register_routes
        register_routes(server_module)
    except Exception as e:
        print(f"[Shiyu Tools] Route registration failed: {e}")
        import traceback
        traceback.print_exc()


# ════════════════════════════════════════════
# ComfyUI 自定义节点注册
# ════════════════════════════════════════════

class ShiyuToolsBootstrap:
    """Shiyu Tools 启动节点。

    此节点不是生成图片的 Node，而是插件的引导触发器。
    """
    CLASS_NAME = "ShiyuToolsBootstrap"
    CATEGORY = "shiyu-tools"
    FUNCTION = "bootstrap"
    RETURN_TYPES = ()

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {"required": {}}

    def bootstrap(self) -> tuple:
        _bootstrap_plugin()
        return ()


NODE_CLASS_MAPPINGS = {"ShiyuToolsBootstrap": ShiyuToolsBootstrap}
NODE_DISPLAY_NAME_MAPPINGS = {"ShiyuToolsBootstrap": "Shiyu Tools Bootstrap"}

# ════════════════════════════════════════════
# ComfyUI Server 扩展注册
# ════════════════════════════════════════════

try:
    import comfy.server as server
    _register_api_routes(server)
except ImportError:
    pass
except Exception as e:
    print(f"[Shiyu Tools] Failed to register API routes: {e}")

# ════════════════════════════════════════════
# 自动启动
# ════════════════════════════════════════════

_bootstrap_plugin()
