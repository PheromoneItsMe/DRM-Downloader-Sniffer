#!/usr/bin/env python3
import http.server
import json
import os
import sys
import time
from datetime import datetime

# Ensure stdout uses UTF-8 encoding on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PORT = 8989
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
OUTPUT_TXT = os.path.join(PROJECT_DIR, "download_commands.txt")
OUTPUT_BAT = os.path.join(PROJECT_DIR, "download_all.bat")
PYTHON_EXE = r"C:\Users\SoloFun\python311\python.exe"
DRMDL_PY = os.path.join(PROJECT_DIR, "drmdl.py")
WVD_FILE = os.path.join(PROJECT_DIR, "file.wvd")

# Track pssh -> { 'timestamp': ..., 'command': ..., 'has_lic': ... }
seen_sessions = {}

def sanitize_filename(title):
    if not title or title.strip() in ["video", "Untitled from OTT Videos on Vimeo", "Vimeo Player"]:
        return "video"
    title = title.strip()
    invalid_chars = '<>:"/\\|?*\n\r\t'
    for char in invalid_chars:
        title = title.replace(char, "")
    title = title.replace(" ", "_")
    return title[:80]

def clean_mpd_url(url):
    if '?' in url:
        base = url.split('?')[0]
        if base.endswith('.mpd'):
            return base
    return url

class DRMCollectorHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b"DRM Sniffer Collector is active and running!")

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))

        try:
            payload = json.loads(post_data.decode('utf-8'))
            pssh = payload.get('pssh', '').strip()
            mpd_url = payload.get('mpd_url', '').strip()
            lic_url = payload.get('lic_url', '').strip()
            title = payload.get('title', 'video').strip()

            if not pssh or not mpd_url:
                return

            # Reject incomplete Vimeo URLs missing CDN signatures (exp= / pathsig=)
            if 'vimeocdn.com' in mpd_url and not ('exp=' in mpd_url or 'pathsig=' in mpd_url):
                print(f"[!] Ignoring incomplete MPD URL: {mpd_url}")
                return

            # Filter out telemetry and video segment chunks
            if 'events.gif' in mpd_url or 'segment.' in mpd_url or '.m4s' in mpd_url:
                return

            now = time.time()
            base_mpd = clean_mpd_url(mpd_url)
            dedupe_key = (pssh, base_mpd)

            # Check if we already logged this session
            if dedupe_key in seen_sessions:
                existing_data = seen_sessions[dedupe_key]
                if title and title not in ["video", "Untitled from OTT Videos on Vimeo"] and existing_data['title'] != title:
                    existing_data['title'] = title
                    safe_title = sanitize_filename(title)
                    existing_data['out_filename'] = f"C:\\Users\\SoloFun\\Desktop\\{safe_title}_{existing_data['time_str']}_720p.mp4"

                if not existing_data['has_lic'] and lic_url:
                    existing_data['has_lic'] = True
                    existing_data['lic_url'] = lic_url

                existing_data['command_ps'] = construct_command_ps(existing_data['out_filename'], pssh, mpd_url, existing_data['lic_url'])
                existing_data['command_bat'] = construct_command_bat(existing_data['out_filename'], pssh, mpd_url, existing_data['lic_url'])

                rewrite_all_commands()
                return

            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = sanitize_filename(title)
            out_filename = f"C:\\Users\\SoloFun\\Desktop\\{safe_title}_{timestamp_str}_720p.mp4"

            command_ps = construct_command_ps(out_filename, pssh, mpd_url, lic_url)
            command_bat = construct_command_bat(out_filename, pssh, mpd_url, lic_url)

            session_info = {
                'time': now,
                'time_str': timestamp_str,
                'title': title,
                'captured_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'pssh': pssh,
                'mpd_url': mpd_url,
                'lic_url': lic_url,
                'has_lic': bool(lic_url),
                'out_filename': out_filename,
                'command_ps': command_ps,
                'command_bat': command_bat
            }
            seen_sessions[dedupe_key] = session_info

            append_single_command(session_info)

            print("\n" + "=" * 80)
            print("[+] NEW DRM VIDEO CAPTURED & SAVED!")
            print("=" * 80)
            print(f"Title:    {title}")
            print(f"File:     {out_filename}")
            print(f"PSSH:     {pssh[:50]}...")
            print(f"MPD URL:  {mpd_url[:80]}...")
            print(f"License:  {lic_url[:80] if lic_url else 'Pending...'}")
            print("-" * 80)
            print(f"Saved to: {OUTPUT_TXT}")
            print(f"PowerShell Command:\n{command_ps}")
            print("=" * 80 + "\n")

        except Exception as e:
            print(f"Error processing payload: {e}")

    def log_message(self, format, *args):
        pass

def construct_command_ps(out_filename, pssh, mpd_url, lic_url):
    lic_param = f' -lic "{lic_url}"' if lic_url else ''
    return (
        f'& "{PYTHON_EXE}" "{DRMDL_PY}" '
        f'-out "{out_filename}" '
        f'-pssh "{pssh}" '
        f'-url "{mpd_url}" '
        f'-wvd "{WVD_FILE}" '
        f'-selection 1{lic_param} -res 720p'
    )

def construct_command_bat(out_filename, pssh, mpd_url, lic_url):
    lic_param = f' -lic "{lic_url}"' if lic_url else ''
    return (
        f'"{PYTHON_EXE}" "{DRMDL_PY}" '
        f'-out "{out_filename}" '
        f'-pssh "{pssh}" '
        f'-url "{mpd_url}" '
        f'-wvd "{WVD_FILE}" '
        f'-selection 1{lic_param} -res 720p'
    )

def append_single_command(info):
    with open(OUTPUT_TXT, "a", encoding="utf-8") as f:
        f.write(f"# Title: {info['title']}\n")
        f.write(f"# Captured at {info['captured_at']}\n")
        f.write(info['command_ps'] + "\n\n")

    with open(OUTPUT_BAT, "a", encoding="utf-8") as f:
        f.write(info['command_bat'] + "\n")

def rewrite_all_commands():
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write("# Список автоматически перехваченных команд скачивания DRM-видео\n")
        f.write("# Все новые видео будут добавляться сюда снизу.\n\n")
        for info in seen_sessions.values():
            f.write(f"# Title: {info['title']}\n")
            f.write(f"# Captured at {info['captured_at']}\n")
            f.write(info['command_ps'] + "\n\n")

    with open(OUTPUT_BAT, "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        for info in seen_sessions.values():
            f.write(info['command_bat'] + "\n")

def main():
    print("=" * 80)
    print(" DRM-Sniffer Collector Server Started!")
    print(f" Listening on: http://localhost:{PORT}/catch")
    print(f" Saving commands to: {OUTPUT_TXT}")
    print(" Browse DRM videos in Chrome/Edge. Commands will be saved automatically.")
    print(" Press Ctrl+C to stop.")
    print("=" * 80 + "\n")

    server = http.server.HTTPServer(('0.0.0.0', PORT), DRMCollectorHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping DRM-Sniffer Server. Goodbye!")

if __name__ == '__main__':
    main()
