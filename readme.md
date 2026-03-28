# Skill Recorder

操作录一遍，AI 帮你做千遍。

Skill Recorder 可以录制你的鼠标点击、键盘输入和屏幕截图，导出为结构化的 Markdown 文件。将文件内容粘贴给 Claude、ChatGPT 等 AI，AI 即可理解你的操作流程并生成可复用的自动化脚本。

## 工作原理

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   用户操作   │────▶│    录制器     │────▶│  .md 文件   │
│   电脑流程   │     │  点击红按钮   │     │  含截图     │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │ 粘贴
                                                 ▼
                                          ┌─────────────┐
                                          │     AI      │
                                          │  理解操作   │
                                          │  生成 Skill │
                                          └─────────────┘
```

## 功能特性

- **浮动录制按钮** — 屏幕左上角红色圆点，点击即录，再点即停
- **智能截图** — 每次点击、滚动、输入停顿时自动截图
- **去噪处理** — 自动去除重复点击、合并连续按键、忽略鼠标移动
- **单文件输出** — 截图内嵌为 base64，一个 `.md` 文件包含所有内容
- **AI 友好** — 结构化格式，LLM 可直接解析理解
- **原生 macOS** — 基于 CGEvent Tap + AppKit，无重量级 GUI 框架依赖

## 系统要求

- macOS 12+
- Python 3.8+
- 辅助功能与屏幕录制权限

## 安装

```bash
git clone https://github.com/yourname/skill-recorder.git
cd skill-recorder
pip install -r requirements.txt
```

## 使用方法

```bash
python recorder.py
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-o, --output` | 输出文件路径 | `recording_YYYYMMDD_HHMMSS.md` |
| `--title` | 录制标题 | `"操作录制"` |

### 示例

```bash
# 基本录制
python recorder.py

# 自定义输出和标题
python recorder.py -o my_workflow.md --title "部署到生产环境"
```

### 操作步骤

1. 运行 `python recorder.py`
2. 屏幕左上角出现红色圆点
3. 点击红色圆点 → 圆点变红色方块，录制开始
4. 执行你的操作流程（点击、输入、滚动都会被记录）
5. 点击红色方块 → 录制停止，自动导出 `.md` 文件
6. 将文件内容粘贴给 AI 助手即可

## 权限配置（macOS）

首次运行需要授予两个系统权限：

### 辅助功能
> 系统设置 → 隐私与安全性 → 辅助功能

用于捕获键盘和鼠标事件。

### 屏幕录制
> 系统设置 → 隐私与安全性 → 屏幕录制

用于截取屏幕截图。

将你运行脚本使用的应用（**终端**、**iTerm2** 或 **VS Code**）添加到以上两个列表中。

## 输出格式

生成的 Markdown 文件格式如下：

```markdown
# 操作录制

> 录制时间: 2026-03-28 11:30:00 | 时长: 5.2s | 步骤数: 4
> 屏幕: 2560x1600

---

## 步骤 1: 点击 (450, 320)
**时间:** 0.0s | **按钮:** left

![截图](data:image/jpeg;base64,...)

---

## 步骤 2: 键盘输入
**时间:** 1.3s | **时长:** 2.1s | **按键:** h e l l o   w o r l d

![截图](data:image/jpeg;base64,...)

---

## 录制总结
- 总步骤数: 4
- 总时长: 5.2s
- 点击事件: 3
- 键盘输入: 1
- 滚动事件: 0
```

## 隐私提示

录制过程中会捕获所有键盘输入，可能包含密码等敏感信息。录制时请注意不要输入敏感内容。

## 项目结构

```
skill-recorder/
├── recorder.py        # 主入口，CLI + AppKit runloop
├── overlay.py         # 浮动录制按钮（红色圆点/方块）
├── event_capture.py   # CGEvent Tap 鼠标/键盘事件监听
├── screenshot.py      # 屏幕截图（mss + Pillow）
├── exporter.py        # Markdown 导出，内嵌截图
├── models.py          # 数据类（ClickEvent, KeyEvent, ScrollEvent）
└── requirements.txt   # 依赖列表
```

## 技术栈

- **[CGEvent Tap](https://developer.apple.com/documentation/coregraphics/cgevent)** — macOS 原生底层事件监听
- **[AppKit](https://developer.apple.com/documentation/appkit)** — macOS 原生浮动窗口与 UI
- **[mss](https://github.com/BoboTiG/python-mss)** — 超快原生屏幕截图
- **[Pillow](https://python-pillow.org/)** — 图片缩放与 JPEG 压缩

## 许可证

MIT

---

# Skill Recorder

Record your operations once, let AI replay them forever.

Skill Recorder captures your mouse clicks, keyboard input, and screenshots, then exports a structured Markdown file. Paste it into Claude, ChatGPT, or any AI — they'll understand what you did and generate reusable automation scripts.

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  You operate │────▶│   Recorder   │────▶│  .md file   │
│  the computer│     │  click dot   │     │ with screens│
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │ paste
                                                 ▼
                                          ┌─────────────┐
                                          │     AI      │
                                          │ understands │
                                          │ & generates │
                                          │   a Skill   │
                                          └─────────────┘
```

## Features

- **Floating record button** — red dot on screen, click to start, click to stop
- **Smart capture** — screenshots at every click, scroll, and after typing pauses
- **Noise filtering** — auto-debounces clicks, batches keystrokes, ignores mouse moves
- **Self-contained output** — single `.md` file with embedded screenshots
- **AI-ready** — structured format that LLMs can directly parse
- **Native macOS** — built on CGEvent Tap + AppKit, no heavy GUI framework

## Requirements

- macOS 12+
- Python 3.8+
- Accessibility & Screen Recording permissions

## Installation

```bash
git clone https://github.com/yourname/skill-recorder.git
cd skill-recorder
pip install -r requirements.txt
```

## Usage

```bash
python recorder.py
```

| Flag | Description | Default |
|------|-------------|---------|
| `-o, --output` | Output file path | `recording_YYYYMMDD_HHMMSS.md` |
| `--title` | Recording title | `"操作录制"` |

### Steps

1. Run `python recorder.py`
2. A red dot appears in the top-left corner of your screen
3. Click the red dot → it turns into a red square, recording starts
4. Perform your workflow (click, type, scroll — everything is captured)
5. Click the red square → recording stops, `.md` file is auto-generated
6. Paste the file content into your AI assistant

## Permissions (macOS)

On first run, you'll need to grant two permissions:

### Accessibility
> System Settings → Privacy & Security → Accessibility

Required for capturing keyboard and mouse events.

### Screen Recording
> System Settings → Privacy & Security → Screen Recording

Required for taking screenshots.

Add **Terminal**, **iTerm2**, or **VS Code** (whichever you run the script from) to both lists.

## Privacy Note

The recorder captures all keyboard input during a recording session, which may include passwords or other sensitive data. Be mindful of what you type while recording.

## Project Structure

```
skill-recorder/
├── recorder.py        # Main entry, CLI + AppKit runloop
├── overlay.py         # Floating record button (red dot/square)
├── event_capture.py   # CGEvent Tap for mouse/keyboard
├── screenshot.py      # Screen capture (mss + Pillow)
├── exporter.py        # Markdown export with embedded images
├── models.py          # Data classes (ClickEvent, KeyEvent, ScrollEvent)
└── requirements.txt   # Dependencies
```

## Tech Stack

- **[CGEvent Tap](https://developer.apple.com/documentation/coregraphics/cgevent)** — macOS native low-level event listening
- **[AppKit](https://developer.apple.com/documentation/appkit)** — macOS native floating window & UI
- **[mss](https://github.com/BoboTiG/python-mss)** — ultra-fast native screenshot capture
- **[Pillow](https://python-pillow.org/)** — image resizing and JPEG compression

## License

MIT
