from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RecordedEvent:
    """录制事件基类"""
    timestamp: float
    screenshot_b64: Optional[str] = None


@dataclass
class ClickEvent(RecordedEvent):
    """鼠标点击事件"""
    x: int = 0
    y: int = 0
    button: str = "left"  # left, right, middle
    action: str = "press"  # press, release


@dataclass
class KeyEvent(RecordedEvent):
    """键盘输入事件（批量合并）"""
    keys: list = field(default_factory=list)
    duration: float = 0.0


@dataclass
class ScrollEvent(RecordedEvent):
    """滚动事件"""
    x: int = 0
    y: int = 0
    dx: int = 0
    dy: int = 0


@dataclass
class RecordingSession:
    """录制会话"""
    events: list = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    title: str = "Untitled Recording"
    metadata: dict = field(default_factory=dict)

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    @property
    def click_count(self) -> int:
        return sum(1 for e in self.events if isinstance(e, ClickEvent))

    @property
    def key_count(self) -> int:
        return sum(1 for e in self.events if isinstance(e, KeyEvent))

    @property
    def scroll_count(self) -> int:
        return sum(1 for e in self.events if isinstance(e, ScrollEvent))
