"""内置事件定义。

集中管理系统中所有事件名称，避免 magic string 散落各处。
"""


class ShiyuEvent:
    """事件名称常量基类。"""


class PromptEvent(ShiyuEvent):
    """Prompt 相关事件。"""
    CREATED = "prompt.created"
    UPDATED = "prompt.updated"
    DELETED = "prompt.deleted"
    SAVED = "prompt.saved"
    FAVORITED = "prompt.favorited"
    SEARCHED = "prompt.searched"
    IMPORTED = "prompt.imported"
    EXPORTED = "prompt.exported"


class GroupEvent(ShiyuEvent):
    """Node Group 相关事件。"""
    CREATED = "group.created"
    UPDATED = "group.updated"
    DELETED = "group.deleted"
    MOVED = "group.moved"
    COLLAPSED = "group.collapsed"
    LOCKED = "group.locked"
    UNLOCKED = "group.unlocked"
    NODE_ADDED = "group.node.added"
    NODE_REMOVED = "group.node.removed"
    NODE_LOCATED = "group.node.located"
    VISIBILITY_CHANGED = "group.visibility.changed"


class PluginEvent(ShiyuEvent):
    """插件自身生命周期事件。"""
    INITIALIZED = "plugin.initialized"
    BEFORE_SHUTDOWN = "plugin.before_shutdown"
    ERROR = "plugin.error"
    CONFIG_CHANGED = "plugin.config.changed"
    STORAGE_SAVED = "plugin.storage.saved"
    STORAGE_LOADED = "plugin.storage.loaded"
