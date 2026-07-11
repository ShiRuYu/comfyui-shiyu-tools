"""生命周期管理。

定义插件和模块的生命周期状态与转换规则。
"""

from __future__ import annotations

from enum import Enum, auto


class LifecycleState(Enum):
    """插件生命周期状态。"""

    # 初始状态
    UNINITIALIZED = auto()

    # 安装/初始化中
    INSTALLING = auto()
    INITIALIZING = auto()
    INITIALIZED = auto()

    # 加载数据
    LOADING = auto()
    LOADED = auto()

    # 启动完成
    STARTING = auto()
    READY = auto()

    # 停止/销毁
    STOPPING = auto()
    DISPOSED = auto()

    # 异常
    ERROR = auto()


# 合法的状态转换映射
_TRANSITIONS: dict[LifecycleState, set[LifecycleState]] = {
    LifecycleState.UNINITIALIZED: {LifecycleState.INSTALLING, LifecycleState.INITIALIZING, LifecycleState.ERROR},
    LifecycleState.INSTALLING: {LifecycleState.INITIALIZING, LifecycleState.ERROR},
    LifecycleState.INITIALIZING: {LifecycleState.INITIALIZED, LifecycleState.ERROR},
    LifecycleState.INITIALIZED: {LifecycleState.LOADING, LifecycleState.DISPOSED, LifecycleState.ERROR},
    LifecycleState.LOADING: {LifecycleState.LOADED, LifecycleState.ERROR},
    LifecycleState.LOADED: {LifecycleState.STARTING, LifecycleState.DISPOSED, LifecycleState.ERROR},
    LifecycleState.STARTING: {LifecycleState.READY, LifecycleState.ERROR},
    LifecycleState.READY: {LifecycleState.STOPPING, LifecycleState.ERROR},
    LifecycleState.STOPPING: {LifecycleState.DISPOSED, LifecycleState.ERROR},
    LifecycleState.DISPOSED: set(),
    LifecycleState.ERROR: {LifecycleState.DISPOSED, LifecycleState.UNINITIALIZED, LifecycleState.ERROR},
}


class LifecycleError(RuntimeError):
    """生命周期状态转换异常。"""
    pass


class LifecycleManager:
    """生命周期管理器。

    维护当前状态并校验状态转换的合法性。
    """

    def __init__(self, initial_state: LifecycleState = LifecycleState.UNINITIALIZED) -> None:
        self._state = initial_state

    @property
    def state(self) -> LifecycleState:
        """当前生命周期状态。"""
        return self._state

    def transition_to(self, target: LifecycleState) -> None:
        """尝试转换到目标状态。

        Args:
            target: 目标状态

        Raises:
            LifecycleError: 当转换不合法时
        """
        allowed = _TRANSITIONS.get(self._state, set())
        if target not in allowed:
            raise LifecycleError(
                f"Illegal lifecycle transition: {self._state.name} → {target.name}. "
                f"Allowed transitions from {self._state.name}: "
                f"{', '.join(s.name for s in allowed) if allowed else '<none>'}"
            )
        self._state = target

    def is_at_least(self, state: LifecycleState) -> bool:
        """判断当前状态是否至少达到指定状态（按枚举值顺序）。"""
        return self._state.value >= state.value

    def is_one_of(self, *states: LifecycleState) -> bool:
        """判断当前状态是否在指定状态集合中。"""
        return self._state in states
