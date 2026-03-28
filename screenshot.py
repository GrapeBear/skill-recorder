import base64
import io

from mss import mss
from PIL import Image


MAX_WIDTH = 800
JPEG_QUALITY = 70


def capture_screenshot() -> str:
    """截取屏幕并返回 base64 编码的 JPEG 字符串"""
    with mss() as sct:
        # 截取主显示器
        monitor = sct.monitors[1]
        raw = sct.grab(monitor)
        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

    # 缩放到最大宽度
    if img.width > MAX_WIDTH:
        ratio = MAX_WIDTH / img.width
        new_size = (MAX_WIDTH, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    # 编码为 JPEG
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
