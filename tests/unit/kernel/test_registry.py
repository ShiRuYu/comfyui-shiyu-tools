"""测试：模块注册表。"""

import pytest
from kernel.registry import ModuleRegistry, RegistryError


class TestModuleRegistry:
    """ModuleRegistry 单元测试。"""

    def test_register_and_get(self):
        """注册后应能获取。"""
        registry = ModuleRegistry()
        mock_module = _create_mock_module("test")
        registry.register(mock_module)
        assert registry.get("test") is mock_module

    def test_register_duplicate_raises(self):
        """重复注册应抛出异常。"""
        registry = ModuleRegistry()
        registry.register(_create_mock_module("test"))
        with pytest.raises(RegistryError):
            registry.register(_create_mock_module("test"))

    def test_unregister(self):
        """注销后不应再获取到。"""
        registry = ModuleRegistry()
        registry.register(_create_mock_module("test"))
        registry.unregister("test")
        assert registry.get("test") is None

    def test_unregister_nonexistent_raises(self):
        """注销不存在的模块应抛出异常。"""
        registry = ModuleRegistry()
        with pytest.raises(RegistryError):
            registry.unregister("nonexistent")

    def test_get_all(self):
        """应返回所有已注册模块。"""
        registry = ModuleRegistry()
        registry.register(_create_mock_module("a"))
        registry.register(_create_mock_module("b"))
        assert len(registry.get_all()) == 2

    def test_has(self):
        """应正确判断是否存在。"""
        registry = ModuleRegistry()
        registry.register(_create_mock_module("test"))
        assert registry.has("test") is True
        assert registry.has("nonexistent") is False

    def test_count(self):
        """应返回正确的模块数量。"""
        registry = ModuleRegistry()
        assert registry.count == 0
        registry.register(_create_mock_module("a"))
        assert registry.count == 1
        registry.register(_create_mock_module("b"))
        assert registry.count == 2


class MockModule:
    """模拟模块。"""
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name


def _create_mock_module(name):
    return MockModule(name)
