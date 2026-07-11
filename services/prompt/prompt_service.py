"""PromptService — Prompt 业务逻辑。

职责：
- 标签管理
- 搜索
- 收藏
- 导入/导出
- 版本控制
"""

from __future__ import annotations

import datetime
import json
import uuid
from typing import Any

from infrastructure.event.event_bus import EventBus
from infrastructure.command.command_bus import CommandBus
from infrastructure.event.events import PromptEvent
from infrastructure.repository.prompt_repository import (
    PromptDocument,
    PromptMetadata,
    PromptVersion,
    PromptRepository,
)


class PromptService:
    """Prompt 业务逻辑层。

    职责：
    - Prompt CRUD 的业务逻辑
    - 标签管理
    - 搜索算法
    - 收藏管理
    - 导入/导出
    - 版本历史

    禁止：
    - ❌ 直接操作存储（通过 Repository）
    - ❌ 直接操作 UI
    - ❌ 直接操作 ComfyUI Graph
    """

    def __init__(
        self,
        repository: PromptRepository,
        event_bus: EventBus,
        command_bus: CommandBus,
    ) -> None:
        self._repo = repository
        self._event_bus = event_bus
        self._command_bus = command_bus

    # ──────────────────────────────────────────
    # CRUD
    # ──────────────────────────────────────────

    def create_prompt(
        self,
        name: str,
        positive: str,
        negative: str = "",
        tags: list[str] | None = None,
        variables: dict[str, str] | None = None,
    ) -> PromptDocument:
        """创建新的 Prompt。

        Args:
            name: Prompt 名称
            positive: 正向 Prompt
            negative: 负向 Prompt（可选）
            tags: 标签列表（可选）
            variables: 变量字典（可选）

        Returns:
            创建的 PromptDocument

        Raises:
            ValueError: 名称或 positive 为空
        """
        if not name or not name.strip():
            raise ValueError("Prompt name must not be empty")
        if not positive or not positive.strip():
            raise ValueError("Prompt positive must not be empty")

        now = datetime.datetime.now().isoformat()
        prompt = PromptDocument(
            id=str(uuid.uuid4()),
            metadata=PromptMetadata(
                name=name.strip(),
                created_at=now,
                updated_at=now,
            ),
            positive=positive.strip(),
            negative=negative.strip() if negative else "",
            tags=tags or [],
            variables=variables or {},
            created_at=now,
            updated_at=now,
        )

        self._repo.create(prompt)
        self._event_bus.emit(PromptEvent.CREATED, {
            "prompt_id": prompt.id,
        })

        return prompt

    def update_prompt(
        self,
        prompt_id: str,
        changes: dict[str, Any],
    ) -> PromptDocument | None:
        """更新 Prompt。

        Args:
            prompt_id: Prompt ID
            changes: 要更新的字段字典

        Returns:
            更新后的 PromptDocument，不存在返回 None
        """
        prompt = self._repo.get_by_id(prompt_id)
        if prompt is None:
            return None

        # 记录历史版本（仅当内容变化时）
        if "positive" in changes or "negative" in changes:
            prompt.history.append(PromptVersion(
                content=prompt.positive,
                timestamp=datetime.datetime.now().isoformat(),
                note=f"Updated: {', '.join(changes.keys())}",
            ))

        # 应用变更
        for key, value in changes.items():
            if hasattr(prompt, key):
                setattr(prompt, key, value)

        prompt.updated_at = datetime.datetime.now().isoformat()
        self._repo.update(prompt_id, prompt)

        self._event_bus.emit(PromptEvent.UPDATED, {
            "prompt_id": prompt_id,
            "changes": changes,
        })

        return prompt

    def delete_prompt(self, prompt_id: str) -> bool:
        """删除 Prompt。"""
        result = self._repo.delete(prompt_id)
        if result:
            self._event_bus.emit(PromptEvent.DELETED, {"prompt_id": prompt_id})
        return result

    def get_prompt(self, prompt_id: str) -> PromptDocument | None:
        """获取指定 Prompt。"""
        return self._repo.get_by_id(prompt_id)

    def get_all_prompts(self) -> list[PromptDocument]:
        """获取所有 Prompt。"""
        return self._repo.get_all()

    # ──────────────────────────────────────────
    # 标签管理
    # ──────────────────────────────────────────

    def get_all_tags(self) -> list[str]:
        """获取所有标签（去重）。"""
        tags: set[str] = set()
        for prompt in self._repo.get_all():
            tags.update(prompt.tags)
        return sorted(tags)

    def get_prompts_by_tag(self, tag: str) -> list[PromptDocument]:
        """根据标签获取 Prompt。"""
        return self._repo.find_by_tag(tag)

    def add_tag(self, prompt_id: str, tag: str) -> PromptDocument | None:
        """为 Prompt 添加标签。"""
        prompt = self._repo.get_by_id(prompt_id)
        if prompt is None:
            return None
        if tag not in prompt.tags:
            prompt.tags.append(tag)
            prompt.updated_at = datetime.datetime.now().isoformat()
            self._repo.update(prompt_id, prompt)
        return prompt

    def remove_tag(self, prompt_id: str, tag: str) -> PromptDocument | None:
        """移除 Prompt 的标签。"""
        prompt = self._repo.get_by_id(prompt_id)
        if prompt is None:
            return None
        if tag in prompt.tags:
            prompt.tags.remove(tag)
            prompt.updated_at = datetime.datetime.now().isoformat()
            self._repo.update(prompt_id, prompt)
        return prompt

    # ──────────────────────────────────────────
    # 搜索
    # ──────────────────────────────────────────

    def search_prompts(
        self,
        query: str = "",
        tags: list[str] | None = None,
        favorites_only: bool = False,
    ) -> list[PromptDocument]:
        """搜索 Prompt。

        Args:
            query: 搜索关键词（匹配名称、正向、负向）
            tags: 过滤标签（交集）
            favorites_only: 仅收藏

        Returns:
            匹配的 Prompt 列表
        """
        results = self._repo.get_all()

        # 搜索关键词
        if query:
            query_lower = query.lower()
            results = [
                p for p in results
                if query_lower in p.metadata.name.lower()
                or query_lower in p.positive.lower()
                or query_lower in p.negative.lower()
            ]

        # 标签过滤
        if tags:
            tag_set = set(tags)
            results = [p for p in results if tag_set.issubset(set(p.tags))]

        # 收藏过滤
        if favorites_only:
            results = [p for p in results if p.metadata.favorite]

        self._event_bus.emit(PromptEvent.SEARCHED, {
            "query": query,
            "tags": tags,
            "results_count": len(results),
        })

        return results

    # ──────────────────────────────────────────
    # 收藏
    # ──────────────────────────────────────────

    def toggle_favorite(self, prompt_id: str) -> PromptDocument | None:
        """切换收藏状态。"""
        prompt = self._repo.get_by_id(prompt_id)
        if prompt is None:
            return None

        prompt.metadata.favorite = not prompt.metadata.favorite
        prompt.updated_at = datetime.datetime.now().isoformat()
        self._repo.update(prompt_id, prompt)

        self._event_bus.emit(PromptEvent.FAVORITED, {
            "prompt_id": prompt_id,
            "favorite": prompt.metadata.favorite,
        })

        return prompt

    def get_favorites(self) -> list[PromptDocument]:
        """获取所有收藏的 Prompt。"""
        return self._repo.find_favorites()

    # ──────────────────────────────────────────
    # 导入/导出
    # ──────────────────────────────────────────

    def export_prompt(self, prompt_id: str) -> dict[str, Any] | None:
        """导出单个 Prompt 为可序列化字典。"""
        prompt = self._repo.get_by_id(prompt_id)
        if prompt is None:
            return None

        data = self._repo._to_dict(prompt)
        self._event_bus.emit(PromptEvent.EXPORTED, {"prompt_id": prompt_id})
        return data

    def export_all(self) -> list[dict[str, Any]]:
        """导出所有 Prompt。"""
        return [self._repo._to_dict(p) for p in self._repo.get_all()]

    def import_prompt(self, data: dict[str, Any]) -> PromptDocument | None:
        """导入 Prompt。"""
        try:
            prompt = self._repo._from_dict(data)
            if prompt is None:
                return None
            prompt.id = prompt.id or str(uuid.uuid4())
            prompt.created_at = prompt.created_at or datetime.datetime.now().isoformat()
            prompt.updated_at = datetime.datetime.now().isoformat()

            self._repo.create(prompt)
            self._event_bus.emit(PromptEvent.IMPORTED, {"prompt_id": prompt.id})
            return prompt
        except Exception as e:
            print(f"[PromptService] Import failed: {e}")
            return None

    # ──────────────────────────────────────────
    # 版本历史
    # ──────────────────────────────────────────

    def get_history(self, prompt_id: str) -> list[PromptVersion]:
        """获取 Prompt 的版本历史。"""
        prompt = self._repo.get_by_id(prompt_id)
        if prompt is None:
            return []
        return list(prompt.history)

    def restore_version(self, prompt_id: str, version_index: int) -> PromptDocument | None:
        """恢复历史版本。"""
        prompt = self._repo.get_by_id(prompt_id)
        if prompt is None:
            return None
        if version_index < 0 or version_index >= len(prompt.history):
            return None

        version = prompt.history[version_index]
        prompt.positive = version.content
        prompt.updated_at = datetime.datetime.now().isoformat()

        self._repo.update(prompt_id, prompt)
        self._event_bus.emit(PromptEvent.UPDATED, {
            "prompt_id": prompt_id,
            "restored_version": version_index,
        })

        return prompt
