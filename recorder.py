#!/usr/bin/env python3
"""Skill Recorder - 录制用户操作并导出为 AI 可理解的 Skill 文件"""

import argparse
import os
import subprocess
import sys
import time
import threading
from datetime import datetime

from AppKit import NSApplication, NSRunLoop, NSDate, NSDefaultRunLoopMode

from event_capture import EventCapture
from exporter import export_markdown
from models import RecordingSession
from overlay import Overlay
from screenshot import capture_screenshot


def get_parent_app():
    try:
        ppid = os.getppid()
        result = subprocess.run(["ps", "-p", str(ppid), "-o", "comm="], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception:
        return None


def check_accessibility():
    try:
        from ApplicationServices import AXIsProcessTrusted
        return AXIsProcessTrusted()
    except ImportError:
        return False


def check_screen_recording():
    try:
        capture_screenshot()
        return True
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="Skill Recorder - 录制操作生成 Skill")
    parser.add_argument("-o", "--output", help="输出文件路径 (默认: recording_时间戳.md)")
    parser.add_argument("--title", default="操作录制", help="录制标题")
    args = parser.parse_args()

    parent_app = get_parent_app()

    # 权限检查
    print("检查权限...")
    if not check_accessibility():
        print(f"\n需要辅助功能权限！")
        print(f"系统设置 → 隐私与安全性 → 辅助功能")
        if parent_app:
            print(f"需要添加: {parent_app}")
        subprocess.Popen(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"])
        sys.exit(1)

    if not check_screen_recording():
        print(f"\n需要屏幕录制权限！")
        print(f"系统设置 → 隐私与安全性 → 屏幕录制")
        if parent_app:
            print(f"需要添加: {parent_app}")
        subprocess.Popen(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"])
        sys.exit(1)

    print("权限 OK")

    # 输出文件路径
    if args.output:
        output_path = args.output
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"recording_{ts}.md"

    # 初始化
    session = RecordingSession(title=args.title)
    capture = EventCapture(on_event=lambda e: session.events.append(e))
    capture.start()

    done = threading.Event()

    def on_toggle(recording):
        if recording:
            session.start_time = time.time()
            session.events.clear()
            capture.set_recording(True)
            print("录制中... 点击方块停止")
        else:
            session.end_time = time.time()
            capture.set_recording(False)
            threading.Timer(0.3, lambda: done.set()).start()

    # 创建浮动按钮
    overlay = Overlay(on_toggle)
    overlay.show()

    print(f"\nSkill Recorder 就绪")
    print(f"点击屏幕左上角红色圆点开始录制")
    print(f"输出文件: {output_path}\n")

    # 主线程运行 AppKit runloop
    while not done.is_set():
        NSRunLoop.currentRunLoop().runMode_beforeDate_(
            NSDefaultRunLoopMode,
            NSDate.dateWithTimeIntervalSinceNow_(0.1)
        )

    capture.stop()
    overlay.close()

    # 导出
    if session.events:
        try:
            from mss import mss as MSS
            with MSS() as sct:
                m = sct.monitors[1]
                session.metadata["screen"] = f"{m['width']}x{m['height']}"
        except Exception:
            pass

        result = export_markdown(session, output_path)
        print(f"\n录制完成！共 {len(session.events)} 个步骤，时长 {session.duration:.1f}s")
        print(f"已导出到: {result}")
        print(f"将此文件内容粘贴给 AI 即可生成 Skill。")
    else:
        print("\n未录制到任何事件。")


if __name__ == "__main__":
    main()
