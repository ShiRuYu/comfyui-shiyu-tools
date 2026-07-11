"""routes.py — Shiyu Tools API 路由

注册 ComfyUI API 路由，供前端 JS 扩展调用。
所有业务逻辑委托给 PromptService / GroupService。
"""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from shiyu_tools import bootstrap

logger = logging.getLogger("shiyu-tools.routes")


def _get_kernel():
    return bootstrap()


def _get_prompt_service():
    m = _get_kernel().get_module("prompt")
    if m is None:
        raise RuntimeError("Prompt module not loaded")
    return m._service


def _get_group_service():
    m = _get_kernel().get_module("node_group")
    if m is None:
        raise RuntimeError("Node Group module not loaded")
    return m._service


# ══════════════════════════════════════════════
# Prompt 路由
# ══════════════════════════════════════════════

async def _list_prompts(request: web.Request) -> web.Response:
    try:
        svc = _get_prompt_service()
        query = request.query.get("query", "")
        tags_str = request.query.get("tags", "")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        favorites = request.query.get("favorites", "").lower() == "true"

        if query or tags or favorites:
            results = svc.search_prompts(query=query, tags=tags or None, favorites_only=favorites)
        else:
            results = svc.get_all_prompts()

        data = [svc.export_prompt(p.id) for p in results]
        return web.json_response({"success": True, "data": data, "count": len(data)})
    except Exception as e:
        logger.error(f"list_prompts: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def _create_prompt(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        svc = _get_prompt_service()
        p = svc.create_prompt(
            name=body.get("name", "Untitled"),
            positive=body.get("positive", ""),
            negative=body.get("negative", ""),
            tags=body.get("tags", []),
        )
        return web.json_response({"success": True, "data": svc.export_prompt(p.id)})
    except ValueError as e:
        return web.json_response({"success": False, "error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"create_prompt: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def _update_prompt(request: web.Request) -> web.Response:
    try:
        pid = request.match_info["prompt_id"]
        body = await request.json()
        svc = _get_prompt_service()
        p = svc.update_prompt(pid, body)
        if p is None:
            return web.json_response({"success": False, "error": "Not found"}, status=404)
        return web.json_response({"success": True, "data": svc.export_prompt(p.id)})
    except Exception as e:
        logger.error(f"update_prompt: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def _delete_prompt(request: web.Request) -> web.Response:
    try:
        pid = request.match_info["prompt_id"]
        svc = _get_prompt_service()
        return web.json_response({"success": svc.delete_prompt(pid)})
    except Exception as e:
        logger.error(f"delete_prompt: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def _toggle_favorite(request: web.Request) -> web.Response:
    try:
        pid = request.match_info["prompt_id"]
        svc = _get_prompt_service()
        p = svc.toggle_favorite(pid)
        if p is None:
            return web.json_response({"success": False, "error": "Not found"}, status=404)
        return web.json_response({"success": True, "favorite": p.metadata.favorite})
    except Exception as e:
        logger.error(f"toggle_favorite: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def _add_tag(request: web.Request) -> web.Response:
    try:
        pid = request.match_info["prompt_id"]
        body = await request.json()
        svc = _get_prompt_service()
        svc.add_tag(pid, body.get("tag", ""))
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"add_tag: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def _remove_tag(request: web.Request) -> web.Response:
    try:
        pid = request.match_info["prompt_id"]
        tag = request.match_info["tag"]
        svc = _get_prompt_service()
        svc.remove_tag(pid, tag)
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"remove_tag: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def _get_tags(request: web.Request) -> web.Response:
    try:
        svc = _get_prompt_service()
        return web.json_response({"success": True, "data": svc.get_all_tags()})
    except Exception as e:
        logger.error(f"get_tags: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


# ══════════════════════════════════════════════
# Node Group 路由
# ══════════════════════════════════════════════

async def _list_groups(request: web.Request) -> web.Response:
    try:
        svc = _get_group_service()
        groups = svc.get_all_groups()
        data = []
        for g in groups:
            stats = svc.get_group_statistics(g.id)
            data.append({
                "id": g.id, "name": g.name, "color": g.color,
                "parent": g.parent, "children": g.children,
                "nodeIds": g.node_ids, "collapsed": g.collapsed,
                "locked": g.locked, "visible": g.visible,
                "tags": g.tags,
                "metadata": {"description": g.metadata.description, "favorite": g.metadata.favorite},
                "statistics": stats,
            })
        return web.json_response({"success": True, "data": data})
    except Exception as e:
        logger.error(f"list_groups: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def _create_group(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        svc = _get_group_service()
        g = svc.create_group(
            name=body.get("name", "New Group"),
            color=body.get("color", "#4A90D9"),
            parent=body.get("parent"),
            tags=body.get("tags"),
        )
        return web.json_response({
            "success": True,
            "data": {"id": g.id, "name": g.name, "color": g.color, "parent": g.parent, "children": g.children},
        })
    except ValueError as e:
        return web.json_response({"success": False, "error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"create_group: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def _update_group(request: web.Request) -> web.Response:
    try:
        gid = request.match_info["group_id"]
        body = await request.json()
        svc = _get_group_service()
        g = svc.update_group(gid, body)
        if g is None:
            return web.json_response({"success": False, "error": "Not found"}, status=404)
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"update_group: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def _delete_group(request: web.Request) -> web.Response:
    try:
        gid = request.match_info["group_id"]
        svc = _get_group_service()
        return web.json_response({"success": svc.delete_group(gid)})
    except Exception as e:
        logger.error(f"delete_group: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def _add_nodes(request: web.Request) -> web.Response:
    try:
        gid = request.match_info["group_id"]
        body = await request.json()
        svc = _get_group_service()
        g = svc.add_nodes_to_group(gid, body.get("nodeIds", []))
        if g is None:
            return web.json_response({"success": False, "error": "Not found"}, status=404)
        return web.json_response({"success": True, "nodeCount": len(g.node_ids)})
    except Exception as e:
        logger.error(f"add_nodes: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def _remove_nodes(request: web.Request) -> web.Response:
    try:
        gid = request.match_info["group_id"]
        body = await request.json()
        svc = _get_group_service()
        g = svc.remove_nodes_from_group(gid, body.get("nodeIds", []))
        if g is None:
            return web.json_response({"success": False, "error": "Not found"}, status=404)
        return web.json_response({"success": True, "nodeCount": len(g.node_ids)})
    except Exception as e:
        logger.error(f"remove_nodes: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def _locate_group(request: web.Request) -> web.Response:
    try:
        gid = request.match_info["group_id"]
        svc = _get_group_service()
        node_ids = svc.locate_group(gid)
        if node_ids is None:
            return web.json_response({"success": False, "error": "Not found"}, status=404)
        return web.json_response({"success": True, "nodeIds": node_ids})
    except Exception as e:
        logger.error(f"locate_group: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def _toggle_collapse(request: web.Request) -> web.Response:
    try:
        gid = request.match_info["group_id"]
        svc = _get_group_service()
        g = svc.toggle_collapse(gid)
        if g is None:
            return web.json_response({"success": False, "error": "Not found"}, status=404)
        return web.json_response({"success": True, "collapsed": g.collapsed})
    except Exception as e:
        logger.error(f"toggle_collapse: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def _toggle_lock(request: web.Request) -> web.Response:
    try:
        gid = request.match_info["group_id"]
        svc = _get_group_service()
        g = svc.toggle_lock(gid)
        if g is None:
            return web.json_response({"success": False, "error": "Not found"}, status=404)
        return web.json_response({"success": True, "locked": g.locked})
    except Exception as e:
        logger.error(f"toggle_lock: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def _move_group(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        svc = _get_group_service()
        g = svc.move_group(body.get("groupId", ""), body.get("targetParent"), body.get("targetIndex", -1))
        if g is None:
            return web.json_response({"success": False, "error": "Not found"}, status=404)
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"move_group: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


# ══════════════════════════════════════════════
# 路由表 & 注册
# ══════════════════════════════════════════════

_ROUTES: list[tuple[str, str, Any]] = [
    # Prompt
    ("GET", "/shiyu-tools/prompts", _list_prompts),
    ("POST", "/shiyu-tools/prompts", _create_prompt),
    ("PUT", "/shiyu-tools/prompts/{prompt_id}", _update_prompt),
    ("DELETE", "/shiyu-tools/prompts/{prompt_id}", _delete_prompt),
    ("POST", "/shiyu-tools/prompts/{prompt_id}/favorite", _toggle_favorite),
    ("POST", "/shiyu-tools/prompts/{prompt_id}/tags", _add_tag),
    ("DELETE", "/shiyu-tools/prompts/{prompt_id}/tags/{tag}", _remove_tag),
    ("GET", "/shiyu-tools/prompts/tags", _get_tags),
    # Group
    ("GET", "/shiyu-tools/groups", _list_groups),
    ("POST", "/shiyu-tools/groups", _create_group),
    ("PUT", "/shiyu-tools/groups/{group_id}", _update_group),
    ("DELETE", "/shiyu-tools/groups/{group_id}", _delete_group),
    ("POST", "/shiyu-tools/groups/{group_id}/nodes", _add_nodes),
    ("DELETE", "/shiyu-tools/groups/{group_id}/nodes", _remove_nodes),
    ("POST", "/shiyu-tools/groups/{group_id}/locate", _locate_group),
    ("POST", "/shiyu-tools/groups/{group_id}/toggle-collapse", _toggle_collapse),
    ("POST", "/shiyu-tools/groups/{group_id}/toggle-lock", _toggle_lock),
    ("POST", "/shiyu-tools/groups/move", _move_group),
]


def register_routes(server_module) -> None:
    """注册所有 API 路由到 ComfyUI 的 PromptServer。

    由 __init__.py 在 ComfyUI 插件加载时调用。

    Args:
        server_module: 从 comfy 导入的 server 模块
    """
    prompt_server = server_module.PromptServer.instance
    count = 0
    for method, path, handler in _ROUTES:
        route_method = getattr(prompt_server.routes, method.lower(), None)
        if route_method:
            route_method(path)(handler)
            count += 1
    logger.info(f"[Shiyu Tools] Registered {count} API routes")
