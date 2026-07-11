"""测试：生命周期管理。"""

import pytest
from kernel.lifecycle import LifecycleManager, LifecycleState, LifecycleError


class TestLifecycleManager:
    """LifecycleManager 单元测试。"""

    def test_initial_state(self):
        """应初始化为 UNINITIALIZED。"""
        manager = LifecycleManager()
        assert manager.state == LifecycleState.UNINITIALIZED

    def test_valid_transition(self):
        """合法的状态转换应成功。"""
        manager = LifecycleManager()
        manager.transition_to(LifecycleState.INITIALIZING)
        assert manager.state == LifecycleState.INITIALIZING

    def test_invalid_transition_raises_error(self):
        """不合法的状态转换应抛出异常。"""
        manager = LifecycleManager()
        with pytest.raises(LifecycleError):
            manager.transition_to(LifecycleState.READY)

    def test_is_at_least(self):
        """is_at_least 应正确判断。"""
        manager = LifecycleManager()
        assert manager.is_at_least(LifecycleState.UNINITIALIZED)

    def test_is_one_of(self):
        """is_one_of 应正确判断。"""
        manager = LifecycleManager()
        assert manager.is_one_of(LifecycleState.UNINITIALIZED)
        assert not manager.is_one_of(LifecycleState.READY)

    def test_full_lifecycle(self):
        """完整的生命周期流程。"""
        manager = LifecycleManager()
        assert manager.state == LifecycleState.UNINITIALIZED

        manager.transition_to(LifecycleState.INITIALIZING)
        manager.transition_to(LifecycleState.INITIALIZED)
        assert manager.state == LifecycleState.INITIALIZED

        manager.transition_to(LifecycleState.LOADING)
        manager.transition_to(LifecycleState.LOADED)
        assert manager.state == LifecycleState.LOADED

        manager.transition_to(LifecycleState.STARTING)
        manager.transition_to(LifecycleState.READY)
        assert manager.state == LifecycleState.READY

        manager.transition_to(LifecycleState.STOPPING)
        manager.transition_to(LifecycleState.DISPOSED)
        assert manager.state == LifecycleState.DISPOSED
