"""ModuleRegistry — 模块注册表。

维护所有已注册的 PluginModule 实例，支持按名称查找和遍历。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .module import PluginModule


class RegistryError(RuntimeError):
    """注册表操作异常。"""
    pass


class ModuleRegistry:
    """模块注册表。

    职责：
    - 注册/注销模块
    - 按名称查找模块
    - 遍历所有模块
    """

    def __init__(self) -> None:
        self._modules: dict[str, PluginModule] = {}

    def register(self, module: PluginModule) -> None:
        """注册一个模块。

        Args:
            module: PluginModule 实例

        Raises:
            RegistryError: 当模块名重复时
        """
        name = module.name
        if name in self._modules:
            raise RegistryError(f"Module '{name}' is already registered.")
        self._modules[name] = module

    def unregister(self, name: str) -> None:
        """注销一个模块。

        Args:
            name: 模块名称

        Raises:
            RegistryError: 当模块不存在时
        """
        if name not in self._modules:
            raise RegistryError(f"Module '{name}' is not registered.")
        del self._modules[name]

    def get(self, name: str) -> PluginModule | None:
        """按名称获取模块。

        Args:
            name: 模块名称

        Returns:
            PluginModule 实例，不存在时返回 None
        """
        return self._modules.get(name)

    def get_all(self) -> list[PluginModule]:
        """获取所有已注册的模块列表。

        Returns:
            按注册顺序排列的模块列表
        """
        return list(self._modules.values())

    def has(self, name: str) -> bool:
        """判断模块是否已注册。

        Args:
            name: 模块名称

        Returns:
            是否存在
        """
        return name in self._modules

    @property
    def count(self) -> int:
        """已注册模块数量。"""
        return len(self._modules)
