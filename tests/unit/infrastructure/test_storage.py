"""测试：存储系统。"""

import pytest
from infrastructure.storage.memory_storage import MemoryStorage
from infrastructure.storage.storage import EntityNotFoundError


class TestMemoryStorage:
    """MemoryStorage 单元测试。"""

    @pytest.fixture
    def storage(self):
        return MemoryStorage()

    def test_create_and_get(self, storage):
        """创建后应能获取。"""
        storage.create("test_col", "1", {"name": "Alice"})
        result = storage.get("test_col", "1")
        assert result is not None
        assert result["name"] == "Alice"

    def test_get_nonexistent(self, storage):
        """获取不存在的实体应返回 None。"""
        assert storage.get("test_col", "nonexistent") is None

    def test_get_all(self, storage):
        """应返回所有实体。"""
        storage.create("test_col", "1", {"name": "Alice"})
        storage.create("test_col", "2", {"name": "Bob"})
        results = storage.get_all("test_col")
        assert len(results) == 2

    def test_update(self, storage):
        """更新实体。"""
        storage.create("test_col", "1", {"name": "Alice"})
        storage.update("test_col", "1", {"name": "Alice Updated"})
        result = storage.get("test_col", "1")
        assert result["name"] == "Alice Updated"

    def test_delete(self, storage):
        """删除实体。"""
        storage.create("test_col", "1", {"name": "Alice"})
        assert storage.delete("test_col", "1") is True
        assert storage.get("test_col", "1") is None

    def test_delete_nonexistent(self, storage):
        """删除不存在的实体应返回 False。"""
        assert storage.delete("test_col", "nonexistent") is False

    def test_exists(self, storage):
        """存在性判断。"""
        storage.create("test_col", "1", {"name": "Alice"})
        assert storage.exists("test_col", "1") is True
        assert storage.exists("test_col", "nonexistent") is False

    def test_count(self, storage):
        """计数。"""
        assert storage.count("test_col") == 0
        storage.create("test_col", "1", {"name": "Alice"})
        assert storage.count("test_col") == 1

    def test_list_collections(self, storage):
        """列出集合。"""
        storage.create("col1", "1", {"name": "Alice"})
        storage.create("col2", "1", {"name": "Bob"})
        collections = storage.list_collections()
        assert "col1" in collections
        assert "col2" in collections

    def test_clear_collection(self, storage):
        """清空集合。"""
        storage.create("test_col", "1", {"name": "Alice"})
        storage.create("test_col", "2", {"name": "Bob"})
        storage.clear_collection("test_col")
        assert storage.count("test_col") == 0
