"""PromptPanel — Prompt 侧边栏面板。"""

from __future__ import annotations

from ui.framework.sidebar import SidebarPanel


class PromptPanel(SidebarPanel):
    """Prompt 侧边栏面板。

    提供 Prompt 的列表显示、搜索、标签、收藏等 UI 功能。
    所有用户操作通过 Controller 发送命令，不直接调用 Service。

    职责：
    - 渲染 Prompt 列表
    - 搜索和标签过滤
    - 收藏切换
    - 右键菜单操作
    - 拖拽支持

    禁止：
    - ❌ 直接调用 Service
    - ❌ 包含业务逻辑
    - ❌ 直接操作存储
    """

    def __init__(self, controller) -> None:
        super().__init__()
        self._controller = controller
        self._title = "Prompt Manager"
        self._icon = "prompt_icon"
        self._search_query: str = ""
        self._active_tags: list[str] = []
        self._selected_prompts: list[str] = []

    # ──────────────────────────────────────────
    # UI 操作
    # ──────────────────────────────────────────

    def set_search_query(self, query: str) -> None:
        """设置搜索关键词。"""
        self._search_query = query
        self._trigger_search()

    def set_active_tags(self, tags: list[str]) -> None:
        """设置活跃标签。"""
        self._active_tags = tags
        self._trigger_search()

    def select_prompt(self, prompt_id: str) -> None:
        """选中 Prompt。"""
        self._selected_prompts = [prompt_id]

    def deselect_all(self) -> None:
        """取消选中。"""
        self._selected_prompts.clear()

    def _trigger_search(self) -> None:
        """触发搜索命令。"""
        from infrastructure.command.commands import SearchPromptCommand
        cmd = SearchPromptCommand(
            query=self._search_query,
            tags=self._active_tags,
        )
        self._controller._command_bus.execute(cmd)
