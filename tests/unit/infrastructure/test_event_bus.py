"""测试：事件总线。"""

from infrastructure.event.event_bus import EventBus


class TestEventBus:
    """EventBus 单元测试。"""

    def test_emit_and_listen(self):
        """发布事件，监听器应收到。"""
        bus = EventBus()
        received = []

        def handler(event, data):
            received.append((event, data))

        bus.on("test.event", handler)
        bus.emit("test.event", {"key": "value"})

        assert len(received) == 1
        assert received[0] == ("test.event", {"key": "value"})

    def test_wildcard_listener(self):
        """通配符监听器应匹配多个事件。"""
        bus = EventBus()
        received = []

        def handler(event, data):
            received.append(event)

        bus.on("test.*", handler)
        bus.emit("test.a")
        bus.emit("test.b")
        bus.emit("other.c")

        assert len(received) == 2
        assert "test.a" in received
        assert "test.b" in received

    def test_once_listener(self):
        """一次性监听器只触发一次。"""
        bus = EventBus()
        count = 0

        def handler(event, data):
            nonlocal count
            count += 1

        bus.once("test.event", handler)
        bus.emit("test.event")
        bus.emit("test.event")

        assert count == 1

    def test_off_handler(self):
        """移除处理器后不应再触发。"""
        bus = EventBus()
        count = 0

        def handler(event, data):
            nonlocal count
            count += 1

        bus.on("test.event", handler)
        bus.off("test.event", handler)
        bus.emit("test.event")

        assert count == 0

    def test_off_all(self):
        """移除所有处理器。"""
        bus = EventBus()

        def handler1(event, data):
            pass

        def handler2(event, data):
            pass

        bus.on("test.event", handler1)
        bus.on("test.event", handler2)
        bus.off("test.event")

        assert bus.listener_count == 0

    def test_get_history(self):
        """应返回事件历史。"""
        bus = EventBus()
        bus.emit("test.a", {"v": 1})
        bus.emit("test.b", {"v": 2})

        history = bus.get_history(2)
        assert len(history) == 2
        assert history[0]["event"] == "test.a"
        assert history[1]["event"] == "test.b"
