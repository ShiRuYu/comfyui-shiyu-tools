"""测试：PromptService。"""

import pytest
from infrastructure.storage.memory_storage import MemoryStorage
from infrastructure.event.event_bus import EventBus
from infrastructure.command.command_bus import CommandBus
from infrastructure.repository.prompt_repository import PromptRepository
from services.prompt.prompt_service import PromptService


@pytest.fixture
def service():
    storage = MemoryStorage()
    event_bus = EventBus()
    command_bus = CommandBus()
    repository = PromptRepository(storage)
    return PromptService(repository, event_bus, command_bus)


class TestPromptService:
    """PromptService 单元测试。"""

    def test_create_prompt(self, service):
        """应成功创建 Prompt。"""
        prompt = service.create_prompt(
            name="Test Prompt",
            positive="beautiful landscape",
            tags=["landscape", "nature"],
        )
        assert prompt.id
        assert prompt.metadata.name == "Test Prompt"
        assert prompt.positive == "beautiful landscape"
        assert "landscape" in prompt.tags

    def test_create_prompt_with_empty_name_raises(self, service):
        """空名称应抛出异常。"""
        with pytest.raises(ValueError):
            service.create_prompt(name="", positive="test")

    def test_get_prompt(self, service):
        """应能获取已创建的 Prompt。"""
        created = service.create_prompt(name="Test", positive="test")
        fetched = service.get_prompt(created.id)
        assert fetched is not None
        assert fetched.id == created.id

    def test_delete_prompt(self, service):
        """应能删除 Prompt。"""
        prompt = service.create_prompt(name="Test", positive="test")
        assert service.delete_prompt(prompt.id) is True
        assert service.get_prompt(prompt.id) is None

    def test_toggle_favorite(self, service):
        """应能切换收藏状态。"""
        prompt = service.create_prompt(name="Test", positive="test")
        assert prompt.metadata.favorite is False

        service.toggle_favorite(prompt.id)
        fetched = service.get_prompt(prompt.id)
        assert fetched.metadata.favorite is True

        service.toggle_favorite(prompt.id)
        fetched = service.get_prompt(prompt.id)
        assert fetched.metadata.favorite is False

    def test_search_by_name(self, service):
        """应能按名称搜索。"""
        service.create_prompt(name="Cat Image", positive="cat")
        service.create_prompt(name="Dog Image", positive="dog")
        service.create_prompt(name="Sunset", positive="sunset")

        results = service.search_prompts(query="Image")
        assert len(results) == 2

    def test_search_by_tags(self, service):
        """应能按标签搜索。"""
        service.create_prompt(name="A", positive="a", tags=["landscape"])
        service.create_prompt(name="B", positive="b", tags=["portrait"])
        service.create_prompt(name="C", positive="c", tags=["landscape", "nature"])

        results = service.search_prompts(tags=["landscape"])
        assert len(results) == 2

    def test_get_all_tags(self, service):
        """应返回所有标签（去重）。"""
        service.create_prompt(name="A", positive="a", tags=["tag1", "tag2"])
        service.create_prompt(name="B", positive="b", tags=["tag2", "tag3"])

        tags = service.get_all_tags()
        assert "tag1" in tags
        assert "tag2" in tags
        assert "tag3" in tags
        assert len(tags) == 3

    def test_add_and_remove_tag(self, service):
        """应能添加和移除标签。"""
        prompt = service.create_prompt(name="Test", positive="test")
        service.add_tag(prompt.id, "new_tag")
        fetched = service.get_prompt(prompt.id)
        assert "new_tag" in fetched.tags

        service.remove_tag(prompt.id, "new_tag")
        fetched = service.get_prompt(prompt.id)
        assert "new_tag" not in fetched.tags
