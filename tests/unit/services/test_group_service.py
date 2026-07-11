"""测试：GroupService。"""

import pytest
from infrastructure.storage.memory_storage import MemoryStorage
from infrastructure.event.event_bus import EventBus
from infrastructure.command.command_bus import CommandBus
from infrastructure.repository.group_repository import GroupRepository
from services.node_group.group_service import GroupService


@pytest.fixture
def service():
    storage = MemoryStorage()
    event_bus = EventBus()
    command_bus = CommandBus()
    repository = GroupRepository(storage)
    return GroupService(repository, event_bus, command_bus)


class TestGroupService:
    """GroupService 单元测试。"""

    def test_create_group(self, service):
        """应成功创建 Group。"""
        group = service.create_group(name="My Group", color="#FF0000")
        assert group.id
        assert group.name == "My Group"
        assert group.color == "#FF0000"

    def test_create_group_with_parent(self, service):
        """创建子 Group 时应自动关联。"""
        parent = service.create_group(name="Parent")
        child = service.create_group(name="Child", parent=parent.id)

        fetched_parent = service.get_group(parent.id)
        assert child.id in fetched_parent.children

    def test_delete_group(self, service):
        """应能删除 Group。"""
        group = service.create_group(name="Test")
        assert service.delete_group(group.id) is True
        assert service.get_group(group.id) is None

    def test_get_tree(self, service):
        """应返回根级 Group。"""
        root1 = service.create_group(name="Root1")
        root2 = service.create_group(name="Root2")
        child = service.create_group(name="Child", parent=root1.id)

        roots = service.get_tree()
        assert len(roots) == 2
        assert root1.id in [r.id for r in roots]
        assert root2.id in [r.id for r in roots]

    def test_move_group(self, service):
        """应能移动 Group 到新父节点。"""
        parent1 = service.create_group(name="Parent1")
        parent2 = service.create_group(name="Parent2")
        child = service.create_group(name="Child", parent=parent1.id)

        service.move_group(child.id, parent2.id)

        fetched_child = service.get_group(child.id)
        assert fetched_child.parent == parent2.id

        fetched_p1 = service.get_group(parent1.id)
        assert child.id not in fetched_p1.children

    def test_toggle_collapse(self, service):
        """应能切换折叠状态。"""
        group = service.create_group(name="Test")
        assert group.collapsed is False

        service.toggle_collapse(group.id)
        assert service.get_group(group.id).collapsed is True

    def test_add_and_remove_nodes(self, service):
        """应能添加和移除节点。"""
        group = service.create_group(name="Test")
        service.add_nodes_to_group(group.id, ["node1", "node2"])
        assert len(service.get_group(group.id).node_ids) == 2

        service.remove_nodes_from_group(group.id, ["node1"])
        assert len(service.get_group(group.id).node_ids) == 1

    def test_locate_group(self, service):
        """定位应返回包含的所有节点 ID。"""
        group = service.create_group(name="Test")
        service.add_nodes_to_group(group.id, ["n1", "n2"])

        child = service.create_group(name="Child", parent=group.id)
        service.add_nodes_to_group(child.id, ["n3"])

        node_ids = service.locate_group(group.id)
        assert "n1" in node_ids
        assert "n3" in node_ids

    def test_get_statistics(self, service):
        """应返回正确的统计信息。"""
        group = service.create_group(name="Test")
        service.add_nodes_to_group(group.id, ["n1", "n2"])

        stats = service.get_group_statistics(group.id)
        assert stats["direct_node_count"] == 2
        assert stats["direct_child_count"] == 0
