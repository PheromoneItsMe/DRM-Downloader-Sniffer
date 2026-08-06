# DRM-Sniffer: Automated Interceptor & Command Logger

**Module Author:** **`Pheromone`**

This module automatically intercepts DRM video playback in your browser, extracting **PSSH**, **MPD manifest URL**, and **License Server URL**, then automatically formats ready-to-run download commands into `download_commands.txt`.

---

## 📁 Directory Structure (`sniffer/`)

- **`drm_collector.py`** — Python HTTP listener server.
- **`drm_sniffer.user.js`** — Interception userscript for **Tampermonkey** (v2.7).
- **`run_sniffer.bat`** — 1-Click batch launcher for the collector server.

---

## 🚀 Setup & Usage (2 Steps):

### Step 1. Install Userscript in Tampermonkey
1. Open the **Tampermonkey** extension in your browser.
2. Click **Create a new script**.
3. Copy the contents of `drm_sniffer.user.js` and paste it into the editor.
4. Click **File -> Save** (Ctrl+S).

### Step 2. Start the Server
Launch `run_sniffer.bat` (or execute in terminal):
```bash
python sniffer/drm_collector.py
```

---

## 🎬 How It Works:

1. Keep the `run_sniffer.bat` server window running in the background.
2. Open any DRM video webpage and press Play.
3. A stylish green toast notification **"🎯 DRM Video Intercepted!"** will pop up in the top-right corner.
4. A complete download command will be appended to **`download_commands.txt`**!
