"""macOS 浮动录制按钮 — 红色圆点(待机) / 红色方块(录制中)

用 AppKit 绘制悬浮窗口，用 CGEvent Tap 检测点击 overlay 区域。
"""

from AppKit import (
    NSApplication, NSWindow, NSView, NSColor, NSBezierPath,
    NSBackingStoreBuffered, NSFloatingWindowLevel, NSMakeRect, NSInsetRect,
)
from Quartz import (
    CGMainDisplayID, CGDisplayPixelsHigh,
    CGEventTapCreate, CGEventTapEnable, CFMachPortCreateRunLoopSource,
    CFRunLoopAddSource, CFRunLoopGetCurrent, CFRunLoopRun, CFRunLoopStop,
    kCGSessionEventTap, kCGHeadInsertEventTap, kCGEventTapOptionListenOnly,
    kCGEventLeftMouseDown, CGEventGetLocation, kCFRunLoopDefaultMode,
)
import objc
import threading

BUTTON_SIZE = 48
PADDING = 16


class _DotView(NSView):
    """绘制红色圆点/方块的 view"""

    def initWithFrame_(self, frame):
        self = objc.super(_DotView, self).initWithFrame_(frame)
        if self:
            self._recording = False
        return self

    def setRecording_(self, val):
        self._recording = val
        self.setNeedsDisplay_(True)

    def drawRect_(self, rect):
        b = self.bounds()
        red = NSColor.colorWithRed_green_blue_alpha_(0.90, 0.18, 0.18, 1.0)

        if self._recording:
            inset = 10
            r = NSInsetRect(b, inset, inset)
            path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(r, 4, 4)
        else:
            cx = b.size.width / 2
            cy = b.size.height / 2
            radius = min(b.size.width, b.size.height) / 2 - 4
            path = NSBezierPath.bezierPathWithOvalInRect_(
                NSMakeRect(cx - radius, cy - radius, radius * 2, radius * 2)
            )

        red.setFill()
        path.fill()

        # 白色描边
        NSColor.whiteColor().setStroke()
        path.setLineWidth_(2)
        path.stroke()


class Overlay:
    """屏幕左上角浮动的录制控制按钮"""

    def __init__(self, on_toggle):
        self._on_toggle = on_toggle
        self._recording = False
        self._window = None
        self._view = None
        self._tap = None
        self._run_loop = None
        self._tap_thread = None

        # overlay 在屏幕上的位置（左上角原点，y 向下，屏幕坐标）
        self._x = PADDING
        self._y = PADDING + 28  # 菜单栏高度

    def show(self):
        NSApplication.sharedApplication()

        screen_height = CGDisplayPixelsHigh(CGMainDisplayID())
        win_y = screen_height - self._y - BUTTON_SIZE

        frame = NSMakeRect(self._x, win_y, BUTTON_SIZE, BUTTON_SIZE)

        self._window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame, 0, NSBackingStoreBuffered, False
        )
        self._window.setLevel_(NSFloatingWindowLevel)
        self._window.setOpaque_(False)
        self._window.setBackgroundColor_(NSColor.clearColor())
        self._window.setHasShadow_(False)
        self._window.setMovableByWindowBackground_(True)

        self._view = _DotView.alloc().initWithFrame_(
            NSMakeRect(0, 0, BUTTON_SIZE, BUTTON_SIZE)
        )
        self._window.setContentView_(self._view)
        self._window.makeKeyAndOrderFront_(None)
        self._window.orderFrontRegardless()

        # 启动 CGEvent Tap 监听鼠标点击
        self._tap_thread = threading.Thread(target=self._run_tap, daemon=True)
        self._tap_thread.start()

    def _run_tap(self):
        event_mask = 1 << kCGEventLeftMouseDown

        self._tap = CGEventTapCreate(
            kCGSessionEventTap, kCGHeadInsertEventTap,
            kCGEventTapOptionListenOnly,
            event_mask, self._tap_callback, None
        )
        if self._tap is None:
            print("Overlay: CGEventTap 创建失败")
            return

        CGEventTapEnable(self._tap, True)
        source = CFMachPortCreateRunLoopSource(None, self._tap, 0)
        self._run_loop = CFRunLoopGetCurrent()
        CFRunLoopAddSource(self._run_loop, source, kCFRunLoopDefaultMode)
        CFRunLoopRun()

    def _tap_callback(self, proxy, event_type, event, refcon):
        if event_type != kCGEventLeftMouseDown:
            return event

        loc = CGEventGetLocation(event)
        x, y = int(loc.x), int(loc.y)

        # 检查是否点在 overlay 区域内
        if (self._x <= x <= self._x + BUTTON_SIZE and
                self._y <= y <= self._y + BUTTON_SIZE):
            self._recording = not self._recording
            # 更新 UI（直接设置，drawRect 会在下次 runloop 迭代时触发）
            self._view._recording = self._recording
            self._view.setNeedsDisplay_(True)
            # 触发回调
            try:
                self._on_toggle(self._recording)
            except Exception as e:
                print(f"Overlay callback error: {e}")

        return event

    def close(self):
        if self._run_loop:
            CFRunLoopStop(self._run_loop)
            self._run_loop = None
        if self._window:
            self._window.close()
            self._window = None

    @property
    def recording(self):
        return self._recording
