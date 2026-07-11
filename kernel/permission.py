"""Permission — 权限控制模块。"""

from __future__ import annotations

from enum import Enum, auto
from dataclasses import dataclass, field


class PermissionAction(Enum):
    """权限动作。"""
    CREATE = auto()
    READ = auto()
    UPDATE = auto()
    DELETE = auto()
    EXECUTE = auto()


@dataclass
class Permission:
    """权限定义。"""
    resource: str          # 资源类型，如 "prompt", "group"
    action: PermissionAction  # 动作
    role: str = "user"    # 角色，默认 "user"


class PermissionManager:
    """权限管理器。

    职责：
    - 权限校验
    - 角色管理

    当前为占位实现，后续可接入更完善的权限系统。
    """

    def __init__(self) -> None:
        self._permissions: dict[str, set[PermissionAction]] = {}

    def grant(self, role: str, resource: str, action: PermissionAction) -> None:
        """授予权限。"""
        key = f"{role}:{resource}"
        if key not in self._permissions:
            self._permissions[key] = set()
        self._permissions[key].add(action)

    def revoke(self, role: str, resource: str, action: PermissionAction) -> None:
        """撤销权限。"""
        key = f"{role}:{resource}"
        if key in self._permissions:
            self._permissions[key].discard(action)

    def check(self, role: str, resource: str, action: PermissionAction) -> bool:
        """检查是否有权限。"""
        key = f"{role}:{resource}"
        if key in self._permissions:
            return action in self._permissions[key]
        # 默认允许（开发阶段）
        return True

    def require(self, role: str, resource: str, action: PermissionAction) -> None:
        """要求权限，不满足时抛出异常。

        Raises:
            PermissionError: 权限不足
        """
        if not self.check(role, resource, action):
            raise PermissionError(
                f"Permission denied: {role} cannot {action.name} on {resource}"
            )
