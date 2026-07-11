"""GraphAdapter — Graph 操作适配器。

封装对 ComfyUI 工作流图（graph）的操作。
"""

from __future__ import annotations

import logging
from typing import Any

from .comfyui_bridge import ComfyUIBridge

logger = logging.getLogger("shiyu-tools.core.graph")


class GraphAdapter:
    """Graph 操作适配器。

    提供对 ComfyUI 工作流图的安全封装操作。
    """

    def __init__(self, bridge: ComfyUIBridge) -> None:
        self._bridge = bridge

    # ──────────────────────────────────────────
    # 节点操作
    # ──────────────────────────────────────────

    def get_all_nodes(self) -> list[Any]:
        """获取图中所有节点。"""
        graph = self._bridge.get_graph()
        if graph is None:
            return []
        try:
            return list(graph.nodes) if hasattr(graph, 'nodes') else []
        except Exception as e:
            logger.error(f"Failed to get nodes: {e}")
            return []

    def get_node_by_id(self, node_id: str) -> Any | None:
        """根据 ID 获取节点。"""
        nodes = self.get_all_nodes()
        for node in nodes:
            if str(getattr(node, 'id', '')) == node_id:
                return node
            if str(getattr(node, 'name', '')) == node_id:
                return node
        return None

    def get_node_ids(self) -> list[str]:
        """获取所有节点 ID。"""
        nodes = self.get_all_nodes()
        return [str(getattr(n, 'id', '')) for n in nodes if hasattr(n, 'id')]

    def get_node_positions(self) -> dict[str, tuple[float, float]]:
        """获取所有节点位置。"""
        graph = self._bridge.get_graph()
        if graph is None:
            return {}

        positions = {}
        try:
            for node in graph.nodes if hasattr(graph, 'nodes') else []:
                node_id = str(getattr(node, 'id', ''))
                pos = getattr(node, 'pos', None) or getattr(node, 'position', None)
                if pos and node_id:
                    positions[node_id] = (float(pos[0]), float(pos[1]))
        except Exception as e:
            logger.error(f"Failed to get node positions: {e}")

        return positions

    # ──────────────────────────────────────────
    # 分组操作
    # ──────────────────────────────────────────

    def get_groups(self) -> list[Any]:
        """获取图中所有分组。"""
        graph = self._bridge.get_graph()
        if graph is None:
            return []
        try:
            return list(graph.groups) if hasattr(graph, 'groups') else []
        except Exception as e:
            logger.error(f"Failed to get groups: {e}")
            return []

    def get_group_by_id(self, group_id: str) -> Any | None:
        """根据 ID 获取分组。"""
        groups = self.get_groups()
        for group in groups:
            if str(getattr(group, 'id', '')) == group_id:
                return group
        return None

    # ──────────────────────────────────────────
    # 链接操作
    # ──────────────────────────────────────────

    def get_links(self) -> list[Any]:
        """获取图中所有连线。"""
        graph = self._bridge.get_graph()
        if graph is None:
            return []
        try:
            return list(graph.links) if hasattr(graph, 'links') else []
        except Exception as e:
            logger.error(f"Failed to get links: {e}")
            return []

    # ──────────────────────────────────────────
    # Canvas 操作
    # ──────────────────────────────────────────

    def select_nodes(self, node_ids: list[str]) -> bool:
        """选中指定节点。"""
        canvas = self._bridge.get_canvas()
        if canvas is None:
            return False
        try:
            if hasattr(canvas, 'select_nodes'):
                canvas.select_nodes(node_ids)
            return True
        except Exception as e:
            logger.error(f"Failed to select nodes: {e}")
            return False

    def clear_selection(self) -> bool:
        """清除选中状态。"""
        canvas = self._bridge.get_canvas()
        if canvas is None:
            return False
        try:
            if hasattr(canvas, 'clear_selection'):
                canvas.clear_selection()
            return True
        except Exception as e:
            logger.error(f"Failed to clear selection: {e}")
            return False
