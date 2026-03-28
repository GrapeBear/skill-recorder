"""事件捕获 — 用 macOS 原生 CGEvent Tap 监听鼠标和键盘，不依赖 pynput"""

import threading
import time
from typing import Callable, Optional

from Quartz import (
    CGEventTapCreate, CGEventTapEnable, CFMachPortCreateRunLoopSource,
    CFRunLoopAddSource, CFRunLoopGetCurrent, CFRunLoopRun, CFRunLoopStop,
    kCGSessionEventTap, kCGHeadInsertEventTap, kCGEventTapOptionListenOnly,
    kCGEventKeyDown, kCGEventLeftMouseDown, kCGEventLeftMouseUp,
    kCGEventScrollWheel, kCGEventFlagsChanged,
    kCGKeyboardEventKeycode, kCGMouseEventNumber,
    CGEventGetIntegerValueField, CGEventGetLocation,
    CGEventGetFlags, kCGEventFlagMaskCommand, kCGEventFlagMaskShift,
    kCFRunLoopDefaultMode,
)
from models import ClickEvent, KeyEvent, ScrollEvent
from screenshot import capture_screenshot

DEBOUNCE_CLICK_MS = 0.2
KEY_BATCH_TIMEOUT = 1.0

# macOS keycode 映射
KEYCODE_MAP = {
    0: 'a', 1: 's', 2: 'd', 3: 'f', 4: 'h', 5: 'g', 6: 'z', 7: 'x',
    8: 'c', 9: 'v', 11: 'b', 12: 'q', 13: 'w', 14: 'e', 15: 'r',
    16: 'y', 17: 't', 18: '1', 19: '2', 20: '3', 21: '4', 22: '6',
    23: '5', 24: '=', 25: '9', 26: '7', 27: '-', 28: '8', 29: '0',
    30: ']', 31: 'o', 32: 'u', 33: '[', 34: 'i', 35: 'p', 36: "Return",
    37: 'l', 38: 'j', 39: "'", 40: 'k', 41: ';', 42: '\\', 43: ',',
    44: '/', 45: 'n', 46: 'm', 47: '.', 48: "Tab", 49: ' ',
    50: '`', 51: "Backspace",
    122: "F1", 120: "F2", 99: "F3", 118: "F4", 96: "F5", 97: "F6",
    98: "F7", 100: "F8", 101: "F9", 109: "F10", 103: "F11", 111: "F12",
    123: "←", 124: "→", 125: "↓", 126: "↑",
    117: "Delete", 51: "Backspace",
}

MODIFIER_KEYCODES = {54, 55, 56, 57, 58, 59, 60, 61, 62, 63}  # Cmd, Shift, Ctrl, Alt, Caps


class EventCapture:
    """用 CGEvent Tap 捕获鼠标和键盘事件"""

    def __init__(self, on_event: Callable):
        self._on_event = on_event
        self._recording = False

        # 点击去抖
        self._last_click_time = 0.0

        # 按键批量合并
        self._key_buffer: list = []
        self._key_start_time: float = 0.0
        self._key_timer: Optional[threading.Timer] = None

        # CGEvent tap
        self._tap = None
        self._run_loop = None
        self._thread: Optional[threading.Thread] = None

    @property
    def recording(self) -> bool:
        return self._recording

    def set_recording(self, value: bool):
        self._recording = value
        if not value:
            self._flush_keys()

    def start(self):
        """在后台线程启动 CGEvent Tap"""
        self._thread = threading.Thread(target=self._run_tap, daemon=True)
        self._thread.start()

    def stop(self):
        """停止事件监听"""
        self._flush_keys()
        if self._run_loop:
            CFRunLoopStop(self._run_loop)

    def _run_tap(self):
        """后台线程：创建并运行 CGEvent Tap"""
        event_mask = (
            (1 << kCGEventLeftMouseDown) |
            (1 << kCGEventLeftMouseUp) |
            (1 << kCGEventScrollWheel) |
            (1 << kCGEventKeyDown) |
            (1 << kCGEventFlagsChanged)
        )

        self._tap = CGEventTapCreate(
            kCGSessionEventTap, kCGHeadInsertEventTap,
            kCGEventTapOptionListenOnly,
            event_mask, self._callback, None
        )

        if self._tap is None:
            print("ERROR: CGEventTap 创建失败，需要辅助功能权限")
            return

        CGEventTapEnable(self._tap, True)
        source = CFMachPortCreateRunLoopSource(None, self._tap, 0)
        self._run_loop = CFRunLoopGetCurrent()
        CFRunLoopAddSource(self._run_loop, source, kCFRunLoopDefaultMode)
        CFRunLoopRun()

    def _callback(self, proxy, event_type, event, refcon):
        """CGEvent 回调"""
        if not self._recording:
            return event

        if event_type == kCGEventLeftMouseDown:
            self._handle_click(event)
        elif event_type == kCGEventScrollWheel:
            self._handle_scroll(event)
        elif event_type == kCGEventKeyDown:
            self._handle_key(event)

        return event

    def _handle_click(self, event):
        loc = CGEventGetLocation(event)
        x, y = int(loc.x), int(loc.y)

        now = time.time()
        if now - self._last_click_time < DEBOUNCE_CLICK_MS:
            return
        self._last_click_time = now

        self._flush_keys()

        self._on_event(ClickEvent(
            timestamp=now,
            x=x, y=y,
            button="left",
            action="press",
            screenshot_b64=capture_screenshot(),
        ))

    def _handle_scroll(self, event):
        self._flush_keys()
        loc = CGEventGetLocation(event)
        dy = CGEventGetIntegerValueField(event, 1)  # kCGScrollWheelEventDeltaAxis1

        self._on_event(ScrollEvent(
            timestamp=time.time(),
            x=int(loc.x), y=int(loc.y),
            dx=0, dy=dy,
            screenshot_b64=capture_screenshot(),
        ))

    def _handle_key(self, event):
        keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
        if keycode in MODIFIER_KEYCODES:
            return

        key_str = KEYCODE_MAP.get(keycode)
        if key_str is None:
            key_str = f"<keycode:{keycode}>"

        flags = CGEventGetFlags(event)
        shifted = bool(flags & kCGEventFlagMaskShift)

        # Shift 修饰：字母大写，数字变符号
        if shifted and len(key_str) == 1 and key_str.isalpha():
            key_str = key_str.upper()
        elif shifted and key_str == '1': key_str = '!'
        elif shifted and key_str == '2': key_str = '@'
        elif shifted and key_str == '3': key_str = '#'
        elif shifted and key_str == '4': key_str = '$'
        elif shifted and key_str == '5': key_str = '%'
        elif shifted and key_str == '6': key_str = '^'
        elif shifted and key_str == '7': key_str = '&'
        elif shifted and key_str == '8': key_str = '*'
        elif shifted and key_str == '9': key_str = '('
        elif shifted and key_str == '0': key_str = ')'

        if not self._key_buffer:
            self._key_start_time = time.time()
        self._key_buffer.append(key_str)

        if self._key_timer:
            self._key_timer.cancel()
        self._key_timer = threading.Timer(KEY_BATCH_TIMEOUT, self._flush_keys)
        self._key_timer.daemon = True
        self._key_timer.start()

    def _flush_keys(self):
        if self._key_timer:
            self._key_timer.cancel()
            self._key_timer = None
        if not self._key_buffer:
            return

        keys = self._key_buffer.copy()
        duration = time.time() - self._key_start_time
        self._key_buffer.clear()

        self._on_event(KeyEvent(
            timestamp=self._key_start_time,
            keys=keys,
            duration=duration,
            screenshot_b64=capture_screenshot(),
        ))
