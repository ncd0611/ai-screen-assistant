# AI Screen Assistant

> **Tiếng Việt** | **English**

Ứng dụng desktop overlay chụp màn hình và dùng AI (GitHub Models API) để gợi ý câu trả lời cho các câu hỏi hiển thị trên màn hình — **không kích hoạt bất kỳ cơ chế phát hiện nào của website**.

A desktop overlay application that captures your screen and uses AI (GitHub Models API) to suggest answers for questions visible on the screen — **without triggering any tab-switch, extension, or page-leave detection by websites**.

---

## 🏗️ Architecture

```
ai-screen-assistant/
├── main.py                 # Entry point — wires all components together
├── config.py               # Configuration (env vars, defaults)
├── capture/
│   ├── screen_capture.py   # mss-based screen capture → PIL Image + PNG bytes
│   └── ocr_engine.py       # EasyOCR fallback text extraction (EN + VI)
├── ai/
│   ├── github_ai_client.py # Async GitHub Models API client (vision + text)
│   └── prompt_builder.py   # Builds optimised message lists for the API
├── ui/
│   ├── overlay.py          # Semi-transparent PyQt6 always-on-top window
│   ├── region_selector.py  # Drag-to-select capture region
│   └── hotkey_manager.py   # pynput global hotkeys
├── requirements.txt
├── setup.py
└── .env.example

Flow:
  Hotkey (Ctrl+Shift+S)
      │
      ▼
  ScreenCapture.capture_as_base64()   ← mss (OS-level, no browser involved)
      │
      ▼
  GitHubAIClient.answer_from_screenshot()   ← httpx async POST
      │    (vision model: openai/gpt-4o)
      ▼
  OverlayWindow.show_result()   ← PyQt6 transparent window stays on top
```

---

## ✨ Features

- 🖥️ **OS-level screen capture** — uses `mss`, never touches the browser
- 🤖 **Vision AI** — sends screenshot directly to `openai/gpt-4o` (no OCR needed)
- 🔤 **OCR fallback** — EasyOCR for English + Vietnamese when vision is unavailable
- 🪟 **Transparent overlay** — draggable, always-on-top, semi-transparent PyQt6 window
- ⌨️ **Global hotkeys** — work even when the browser has focus
- 🔒 **Completely undetectable** by websites (see comparison table below)

---

## 🚫 Why a Desktop App (not a Chrome Extension)?

| Detection method | Chrome Extension | **Desktop App** |
|---|---|---|
| `document.hidden` / `visibilitychange` | ✅ Detected | ❌ Not triggered |
| `window.onblur` / `window.onfocus` | ✅ Detected | ❌ Not triggered |
| Extension presence checks | ✅ Detected | ❌ No extension |
| `navigator.sendBeacon` on unload | ✅ Detected | ❌ Never fires |

---

## 📋 Prerequisites

- Python 3.10 or higher
- A GitHub account with access to [GitHub Models](https://github.com/marketplace/models)
- A GitHub Personal Access Token with **Models** scope

---

## 🔑 Getting a GitHub Personal Access Token

1. Go to **GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)**
2. Click **Generate new token (classic)**
3. Give it a name (e.g. `ai-screen-assistant`)
4. Under **Scopes**, select **`read:user`** (Models API only needs this minimal scope)
5. Click **Generate token** and copy it immediately

> **Tip:** Fine-grained tokens also work — no repository permissions are required,
> just ensure the token is allowed to call GitHub Models.

---

## ⚙️ Enabling GitHub Models

1. Visit <https://github.com/marketplace/models>
2. Click **Get started** and follow the prompts to enable Models access on your account

---

## 🛠️ Installation

```bash
# 1. Clone the repository
git clone https://github.com/ncd0611/ai-screen-assistant.git
cd ai-screen-assistant

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate.bat     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy the example environment file and fill in your token
cp .env.example .env
# Edit .env and set GITHUB_TOKEN=ghp_...
```

---

## 🔧 Configuration

All options are set via environment variables (or the `.env` file):

| Variable | Default | Description |
|---|---|---|
| `GITHUB_TOKEN` | *(required)* | GitHub Personal Access Token |
| `AI_MODEL` | `openai/gpt-4o` | GitHub Models model identifier |
| `CAPTURE_REGION` | *(empty = full screen)* | `x,y,width,height` e.g. `100,100,800,600` |
| `HOTKEY_SCAN` | `<ctrl>+<shift>+s` | Scan & answer hotkey |
| `HOTKEY_TOGGLE` | `<ctrl>+<shift>+h` | Toggle overlay visibility |
| `HOTKEY_REGION` | `<ctrl>+<shift>+r` | Open region selector |
| `HOTKEY_QUIT` | `<ctrl>+<shift>+q` | Quit the application |

---

## ▶️ Usage

```bash
python main.py
```

The overlay window appears. Use these hotkeys at any time:

| Hotkey | Action |
|---|---|
| **Ctrl+Shift+S** | Capture screen → AI analyses and answers |
| **Ctrl+Shift+H** | Hide / show the overlay |
| **Ctrl+Shift+R** | Draw a capture region with your mouse |
| **Ctrl+Shift+Q** | Quit the application |

**Workflow:**
1. Open your browser and navigate to the question/exam page
2. Press **Ctrl+Shift+S** — the overlay briefly hides, takes a screenshot, then shows the AI answer
3. Read the answer in the overlay without switching tabs

---

## 🔍 Troubleshooting

| Problem | Solution |
|---|---|
| `GITHUB_TOKEN is not set` | Add your token to `.env` |
| `401 Unauthorized` from API | Check your token is valid and Models is enabled |
| Hotkeys not responding | Ensure no other app has registered the same hotkeys |
| Blank/black screenshot | Some Wayland compositors require `XDG_SESSION_TYPE=x11` |
| EasyOCR slow on first run | It downloads language models on first use — be patient |
| `PyQt6` not found | Run `pip install PyQt6` |

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `mss` | Fast cross-platform screen capture |
| `Pillow` | Image processing |
| `PyQt6` | Transparent overlay window |
| `pynput` | Global hotkeys |
| `httpx` | Async HTTP client for the AI API |
| `easyocr` | OCR fallback (English + Vietnamese) |
| `python-dotenv` | `.env` file loading |