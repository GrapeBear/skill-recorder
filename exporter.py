from datetime import datetime

from models import RecordingSession, ClickEvent, KeyEvent, ScrollEvent


def export_markdown(session: RecordingSession, output_path: str) -> str:
    """将录制会话导出为 Markdown 文件"""
    lines = []

    # 头部
    date_str = datetime.fromtimestamp(session.start_time).strftime("%Y-%m-%d %H:%M:%S")
    duration = session.duration
    total = len(session.events)

    lines.append(f"# {session.title}")
    lines.append("")
    lines.append(f"> 录制时间: {date_str} | 时长: {duration:.1f}s | 步骤数: {total}")
    if session.metadata:
        screen = session.metadata.get("screen", "")
        if screen:
            lines.append(f"> 屏幕: {screen}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 事件步骤
    for i, event in enumerate(session.events, 1):
        relative_time = event.timestamp - session.start_time

        if isinstance(event, ClickEvent):
            lines.append(f"## 步骤 {i}: 点击 ({event.x}, {event.y})")
            lines.append(f"**时间:** {relative_time:.1f}s | **按钮:** {event.button}")
            lines.append("")

        elif isinstance(event, KeyEvent):
            keys_display = _format_keys(event.keys)
            lines.append(f"## 步骤 {i}: 键盘输入")
            lines.append(f"**时间:** {relative_time:.1f}s | **时长:** {event.duration:.1f}s | **按键:** {keys_display}")
            lines.append("")

        elif isinstance(event, ScrollEvent):
            direction = "上" if event.dy > 0 else "下"
            lines.append(f"## 步骤 {i}: 滚动{direction} ({event.x}, {event.y})")
            lines.append(f"**时间:** {relative_time:.1f}s | **滚动量:** dx={event.dx}, dy={event.dy}")
            lines.append("")

        # 截图
        if event.screenshot_b64:
            lines.append(f"![截图](data:image/jpeg;base64,{event.screenshot_b64})")
            lines.append("")

        lines.append("---")
        lines.append("")

    # 总结
    lines.append("## 录制总结")
    lines.append("")
    lines.append(f"- 总步骤数: {total}")
    lines.append(f"- 总时长: {duration:.1f}s")
    lines.append(f"- 点击事件: {session.click_count}")
    lines.append(f"- 键盘输入: {session.key_count}")
    lines.append(f"- 滚动事件: {session.scroll_count}")

    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


def _format_keys(keys: list) -> str:
    """将按键列表格式化为可读字符串"""
    result = []
    for k in keys:
        if len(k) == 1:
            result.append(k)
        else:
            result.append(f"[{k}]")
    return " ".join(result)
