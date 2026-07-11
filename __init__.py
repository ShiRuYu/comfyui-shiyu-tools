"""
ComfyUI Shiyu Tools — Enterprise Plugin Framework

一个运行于 ComfyUI 内部的企业级插件平台。
目标不是生成图片，而是增强 Workflow 开发效率。

架构类似 VSCode Plugin / JetBrains Plugin / Chrome Extension，
而非普通 ComfyUI Custom Node。

启动流程：
1. ComfyUI 加载 custom_nodes/comfyui-shiyu-tools
2. 执行本文件的 NODE_CLASS_MAPPINGS 初始化
3. NODE_CLASS_MAPPINGS 中的特殊节点触发 shiyu_tools.bootstrap()
4. PluginKernel 创建并启动全部基础设施和业务模块
"""

from __future__ import annotations

import logging

# ──────────────────────────────────────────
# 版本信息
# ──────────────────────────────────────────
__version__ = "0.1.0"
__author__ = "ShiRuYu"
__license__ = "MIT"
__description__ = "ComfyUI Enterprise Plugin Framework"

# ──────────────────────────────────────────
# 插件启动
# ──────────────────────────────────────────

# ComfyUI 扩展 API 检测标志
EXTENSION_NAME = "Shiyu Tools"
EXTENSION_DESCRIPTION = "Enterprise Plugin Framework for ComfyUI"


def _bootstrap_plugin() -> None:
    """安全引导插件。

    在主线程中执行 bootstrap，捕获异常避免影响 ComfyUI 启动。
    """
    try:
        from .shiyu_tools import bootstrap
        bootstrap()
    except Exception as e:
        print(f"[Shiyu Tools] Bootstrap failed: {e}")
        import traceback
        traceback.print_exc()


# ──────────────────────────────────────────
# ComfyUI 自定义节点注册
# ──────────────────────────────────────────

class ShiyuToolsBootstrap:
    """Shiyu Tools 启动节点。

    此节点不是生成图片的 Node，而是插件的引导触发器。
    当 ComfyUI 加载此节点时，触发插件内核启动。

    此节点不会出现在用户的节点菜单中，它对用户透明。
    """

    CLASS_NAME = "ShiyuToolsBootstrap"
    CATEGORY = "shiyu-tools"
    FUNCTION = "bootstrap"
    RETURN_TYPES = ()

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {},
        }

    def bootstrap(self) -> tuple:
        """触发插件启动。"""
        _bootstrap_plugin()
        return ()


# ──────────────────────────────────────────
# 节点映射（ComfyUI 要求）
# ──────────────────────────────────────────

NODE_CLASS_MAPPINGS = {
    "ShiyuToolsBootstrap": ShiyuToolsBootstrap,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ShiyuToolsBootstrap": "Shiyu Tools Bootstrap",
}

# ──────────────────────────────────────────
# Web 扩展注册（ComfyUI 前端支持）
# ──────────────────────────────────────────

WEB_DIRECTORY = "./web"

# ──────────────────────────────────────────
# 自动启动
# ──────────────────────────────────────────

# 当 ComfyUI 加载此模块时，自动启动插件
_bootstrap_plugin()
