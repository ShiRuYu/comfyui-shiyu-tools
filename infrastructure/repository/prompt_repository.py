"""PromptRepository — Prompt 数据访问层。

Prompt 不是字符串，而是 Document 结构。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from infrastructure.storage.storage import Storage
from .base_repository import BaseRepository


@dataclass
class PromptMetadata:
    """Prompt 元数据。"""
    name: str = ""
    description: str = ""
    category: str = ""
    favorite: bool = False
    shortcut: str = ""
    author: str = ""
    icon: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class PromptVersion:
    """Prompt 版本记录。"""
    content: str = ""
    timestamp: str = ""
    note: str = ""


@dataclass
class PromptDocument:
    """Prompt 文档 — 不是字符串，而是完整的 Document。"""
    id: str = ""
    metadata: PromptMetadata = field(default_factory=PromptMetadata)
    positive: str = ""
    negative: str = ""
    tags: list[str] = field(default_factory=list)
    variables: dict[str, str] = field(default_factory=dict)
    history: list[PromptVersion] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class PromptRepository(BaseRepository[PromptDocument]):
    """Prompt 数据访问。

    职责：
    - Prompt 文档的 CRUD
    - 标签索引维护
    - 搜索支持

    禁止：
    - ❌ 包含业务逻辑（如收藏逻辑、搜索算法）
    - ❌ 直接操作文件
    """

    def __init__(self, storage: Storage) -> None:
        super().__init__(storage, "prompts", PromptDocument)

    # ──────────────────────────────────────────
    # 自定义查询
    # ──────────────────────────────────────────

    def find_by_tag(self, tag: str) -> list[PromptDocument]:
        """根据标签查找 Prompt。"""
        return [p for p in self.get_all() if tag in p.tags]

    def find_by_category(self, category: str) -> list[PromptDocument]:
        """根据分类查找 Prompt。"""
        return [p for p in self.get_all() if p.metadata.category == category]

    def find_favorites(self) -> list[PromptDocument]:
        """获取所有收藏的 Prompt。"""
        return [p for p in self.get_all() if p.metadata.favorite]

    def find_by_name(self, name: str) -> list[PromptDocument]:
        """根据名称模糊查找。"""
        name_lower = name.lower()
        return [p for p in self.get_all() if name_lower in p.metadata.name.lower()]
