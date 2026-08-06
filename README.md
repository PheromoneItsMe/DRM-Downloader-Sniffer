# 🎬 DRM-Downloader & Automatic DRM-Sniffer

An advanced tool suite for automated interception, multi-threaded downloading, decryption, and merging of protected **Widevine DRM (L3)** video streams (Vimeo, OTT platforms, and broadcasting web services).

---

## 👤 Authors & Credits

- **Author of Enhancements, Multi-threading & Sniffer:** **`Pheromone`**
- **Original Base Project:** [e-ave/DRM-Downloader](https://github.com/e-ave/DRM-Downloader) (`wvdumper` / `TPD-Keys`)

---

## 🚀 Key Features

1. **Automated Browser Sniffer (`sniffer/`):**
   - Intercepts PSSH (Widevine EME), signed `.mpd` manifest URLs, and Widevine License Server URLs in real-time while watching videos.
   - Extracts exact movie and episode titles directly from page DOM structures.
   - Automatically logs ready-to-run download commands into `download_commands.txt` with zero duplicates.
2. **High-Speed Multi-Threaded Downloading (`-N 16`):**
   - Fetches video fragments concurrently across 16 parallel threads, eliminating network latency and boosting download speeds for `720p` and `1080p` streams by 4x–8x.
3. **Automated Decryption & Merging:**
   - Decrypts audio and video streams via Bento4 (`mp4decrypt`) using your CDM keys (`file.wvd`), followed by seamless merging into a single `.mp4` file via `ffmpeg`.
4. **Overwrite Protection:**
   - Saves every video with its title and a unique timestamp (`Video_Title_20260806_020402_720p.mp4`).

---

## 🛠️ System Requirements

### 1. Required External Tools (Must be in your PATH):
* [Python 3.9+](https://www.python.org/downloads/)
* [FFmpeg](https://ffmpeg.org/download.html)
* [mp4decrypt (Bento4)](https://www.bento4.com/downloads/)
* [yt-dlp](https://github.com/yt-dlp/yt-dlp)
* [aria2](https://github.com/aria2/aria2) *(optional)*

### 2. Python Dependencies (`requirements.txt`):
```bash
pip install -r requirements.txt
```
Dependencies: `requests`, `frida`, `frida-tools`, `protobuf`, `pycryptodome`, `pywidevine`, `httpx`

---

## 📡 Setup & Running the DRM-Sniffer

### Step 1. Start the Collector Server
Run the `sniffer/run_sniffer.bat` file or execute in terminal:
```bash
python sniffer/drm_collector.py
```
The server will start listening on `http://localhost:8989/catch`.

### Step 2. Install the Userscript in Tampermonkey
1. Copy the code from **[`sniffer/drm_sniffer.user.js`](file:///C:/Users/SoloFun/Desktop/DRM-Downloader-main/sniffer/drm_sniffer.user.js)** (Author: **`Pheromone`**).
2. Paste it into Tampermonkey and save (**Ctrl + S**).

When playing DRM video on any supported web page, a green toast notification will appear in the top-right corner, and a ready-to-run download command will automatically be saved to **`download_commands.txt`**.

---

## 💻 Manual Download Execution (`drmdl.py`)

Universal CLI command syntax:

### PowerShell Syntax:
```powershell
& python drmdl.py -out "video_720p.mp4" -pssh "PSSH_HERE" -url "MPD_URL_HERE" -wvd "file.wvd" -selection 1 -lic "LICENSE_URL_HERE" -res 720p
```

### CMD / Bash Syntax:
```bash
python drmdl.py -out "video_720p.mp4" -pssh "PSSH_HERE" -url "MPD_URL_HERE" -wvd "file.wvd" -selection 1 -lic "LICENSE_URL_HERE" -res 720p
```

### Command Parameters:
* `-out` — Output `.mp4` file path.
* `-pssh` — Base64 PSSH string.
* `-url` — URL to index `.mpd` manifest.
* `-wvd` — Path to Widevine CDM device file (`file.wvd`).
* `-selection` — License server mode (default: `1`).
* `-lic` — License server URL.
* `-res` — Target video resolution (`720p`, `1080p`, `4k`).

---

## 📱 How to Dump Your Own CDM Device File (`file.wvd`)

1. Launch an Android Studio emulator (Android 9.0 Pie).
2. Start `frida-server` inside the emulator.
3. Run `wvdumper` (`python dump_keys.py`).
4. Play any DRM video inside Chrome on the emulator to extract `client_id.bin` and `private_key.pem`.
5. Generate `file.wvd` via `pywidevine`:
   ```bash
   pywidevine create-device -k device_private_key -c device_client_id_blob -t "ANDROID" -l 3 -o output
   ```
