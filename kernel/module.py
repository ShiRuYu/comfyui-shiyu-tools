"""PluginModule — 业务模块抽象基类。

所有业务模块（Prompt Center、Node Group Center 等）必须继承此类。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .kernel import PluginKernel


class PluginModule(ABC):
    """插件模块抽象基类。

    所有业务模块必须实现以下生命周期方法：

    - initialize(): 初始化（创建 Repository、Service、Controller、Panel 实例）
    - load():       加载数据（从存储恢复状态）
    - start():      启动（注册 UI、注册事件监听）
    - stop():       停止（注销 UI、注销事件监听）
    - destroy():    销毁（释放资源、持久化状态）

    模块之间禁止直接调用，必须通过 EventBus / CommandBus 通信。
    """

    def __init__(self, name: str, kernel: PluginKernel) -> None:
        """初始化模块。

        Args:
            name: 模块名称（唯一标识，如 "prompt", "node_group"）
            kernel: PluginKernel 实例
        """
        self._name = name
        self._kernel = kernel

    # ──────────────────────────────────────────
    # 属性
    # ──────────────────────────────────────────

    @property
    def name(self) -> str:
        """模块名称。"""
        return self._name

    @property
    def kernel(self) -> PluginKernel:
        """PluginKernel 引用。"""
        return self._kernel

    # ──────────────────────────────────────────
    # 生命周期方法（必须实现）
    # ──────────────────────────────────────────

    @abstractmethod
    def initialize(self) -> None:
        """初始化模块。

        在此方法中：
        - 创建 Repository 实例
        - 创建 Service 实例
        - 创建 Controller 实例
        - 创建 Panel 实例
        - 注册到 Kernel
        """
        ...

    @abstractmethod
    def load(self) -> None:
        """加载模块数据。

        在此方法中：
        - 从 Storage 加载数据到 Repository
        - 重建索引
        """
        ...

    @abstractmethod
    def start(self) -> None:
        """启动模块。

        在此方法中：
        - 注册 UI 到 UI Framework
        - 注册事件监听器
        - 注册命令处理器
        """
        ...

    @abstractmethod
    def stop(self) -> None:
        """停止模块。

        在此方法中：
        - 注销 UI
        - 注销事件监听器
        - 注销命令处理器
        """
        ...

    @abstractmethod
    def destroy(self) -> None:
        """销毁模块。

        在此方法中：
        - 持久化未保存的数据
        - 释放资源
        - 清理临时文件
        """
        ...
