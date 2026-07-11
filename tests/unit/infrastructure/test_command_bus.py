"""测试：命令总线。"""

import pytest
from infrastructure.command.command_bus import CommandBus
from infrastructure.command.commands import Command
from dataclasses import dataclass


@dataclass
class TestCommand(Command):
    value: str = ""


class TestCommandBus:
    """CommandBus 单元测试。"""

    def test_execute(self):
        """注册处理器后应能执行命令。"""
        bus = CommandBus()
        result = []

        def handler(cmd):
            result.append(cmd.value)
            return cmd.value

        bus.register(TestCommand, handler)
        output = bus.execute(TestCommand(value="hello"))

        assert result == ["hello"]
        assert output == "hello"

    def test_execute_unregistered_raises(self):
        """未注册的命令应抛出异常。"""
        bus = CommandBus()
        with pytest.raises(RuntimeError):
            bus.execute(TestCommand(value="test"))

    def test_history_recording(self):
        """执行后应记录历史。"""
        bus = CommandBus()

        def handler(cmd):
            return cmd.value

        bus.register(TestCommand, handler)
        bus.execute(TestCommand(value="a"))
        bus.execute(TestCommand(value="b"))

        assert bus.history_count == 2
        assert bus.can_undo is True

    def test_clear_history(self):
        """清空历史。"""
        bus = CommandBus()

        def handler(cmd):
            return cmd.value

        bus.register(TestCommand, handler)
        bus.execute(TestCommand(value="a"))
        bus.clear_history()

        assert bus.history_count == 0
        assert bus.can_undo is False

    def test_can_redo(self):
        """撤销后应能重做。"""
        bus = CommandBus()

        def handler(cmd):
            return cmd.value

        bus.register(TestCommand, handler)
        bus.execute(TestCommand(value="a"))

        assert bus.can_redo is False
        bus.undo()
        assert bus.can_redo is True
