"""
Boltz Local Server — runs Windows apps AND proxies Claude AI calls
Run with:  python boltz_server.py
Requires:  pip install requests   (only external dependency)
"""

import subprocess, os, sys, json, threading, webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
try:
    import requests
except ImportError:
    print("\n  [!] Missing dependency. Run:  pip install requests\n")
    sys.exit(1)

PORT       = 7825
CLAUDE_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# ── Read API key ─────────────────────────────────────────────────────────────
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not API_KEY:
    # Try reading from a key file next to this script
    key_file = os.path.join(os.path.dirname(__file__), "api_key.txt")
    if os.path.exists(key_file):
        API_KEY = open(key_file).read().strip()
if not API_KEY:
    print("\n  ⚡ Boltz needs your Anthropic API key.")
    print("  Either:")
    print("  1) Set env var:  set ANTHROPIC_API_KEY=sk-ant-...")
    print("  2) Put your key in api_key.txt next to this script")
    print("  3) Paste it now:\n")
    API_KEY = input("  API Key: ").strip()
    if not API_KEY:
        print("  No key provided — exiting.")
        sys.exit(1)
    # Offer to save it
    save = input("  Save to api_key.txt for next time? (y/n): ").strip().lower()
    if save == 'y':
        with open(os.path.join(os.path.dirname(__file__), "api_key.txt"), "w") as f:
            f.write(API_KEY)
        print("  Saved.\n")

# ── App registry ─────────────────────────────────────────────────────────────
APPS = {
    "notepad":            ["notepad.exe"],
    "calculator":         ["calc.exe"],
    "paint":              ["mspaint.exe"],
    "task manager":       ["taskmgr.exe"],
    "taskmgr":            ["taskmgr.exe"],
    "file explorer":      ["explorer.exe"],
    "explorer":           ["explorer.exe"],
    "control panel":      ["control.exe"],
    "settings":           ["ms-settings:"],
    "powershell":         ["powershell.exe"],
    "cmd":                ["cmd.exe"],
    "terminal":           ["wt.exe"],
    "wordpad":            ["wordpad.exe"],
    "snipping tool":      ["snippingtool.exe"],
    "snip":               ["snippingtool.exe"],
    "magnifier":          ["magnify.exe"],
    "narrator":           ["narrator.exe"],
    "character map":      ["charmap.exe"],
    "disk cleanup":       ["cleanmgr.exe"],
    "registry editor":    ["regedit.exe"],
    "regedit":            ["regedit.exe"],
    "device manager":     ["devmgmt.msc"],
    "services":           ["services.msc"],
    "event viewer":       ["eventvwr.msc"],
    "task scheduler":     ["taskschd.msc"],
    "disk management":    ["diskmgmt.msc"],
    "system info":        ["msinfo32.exe"],
    "directx":            ["dxdiag.exe"],
    "system config":      ["msconfig.exe"],
    "resource monitor":   ["resmon.exe"],
    "performance monitor":["perfmon.exe"],
    "on-screen keyboard": ["osk.exe"],
    "remote desktop":     ["mstsc.exe"],
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
    "firefox": [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ],
    "brave": [r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"],
    "word": [
        r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
    ],
    "excel": [
        r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE",
    ],
    "powerpoint": [
        r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\POWERPNT.EXE",
    ],
    "outlook": [
        r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\OUTLOOK.EXE",
    ],
    "vs code": [
        r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        r"C:\Program Files\Microsoft VS Code\Code.exe",
    ],
    "vscode": [r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe"],
    "visual studio": [
        r"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\devenv.exe",
        r"C:\Program Files\Microsoft Visual Studio\2019\Community\Common7\IDE\devenv.exe",
    ],
    "git bash": [
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
    ],
    "spotify":  [r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe"],
    "vlc": [
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
    ],
    "winrar": [
        r"C:\Program Files\WinRAR\WinRAR.exe",
        r"C:\Program Files (x86)\WinRAR\WinRAR.exe",
    ],
    "7-zip": [
        r"C:\Program Files\7-Zip\7zFM.exe",
        r"C:\Program Files (x86)\7-Zip\7zFM.exe",
    ],
    "steam": [
        r"C:\Program Files (x86)\Steam\steam.exe",
        r"C:\Program Files\Steam\steam.exe",
    ],
    "discord": [r"C:\Users\%USERNAME%\AppData\Local\Discord\Update.exe"],
    "slack":   [r"C:\Users\%USERNAME%\AppData\Local\slack\slack.exe"],
    "zoom":    [r"C:\Users\%USERNAME%\AppData\Roaming\Zoom\bin\Zoom.exe"],
    "teams":   [r"C:\Users\%USERNAME%\AppData\Local\Microsoft\Teams\current\Teams.exe"],
}

def expand(path):
    return os.path.expandvars(os.path.expanduser(path))

def launch(app_key):
    key = app_key.lower().strip()
    candidates = APPS.get(key)
    if not candidates:
        for k, v in APPS.items():
            if key in k or k in key:
                candidates = v
                break
    if not candidates:
        candidates = [app_key]
    # URI scheme (ms-settings:, etc.)
    if len(candidates) == 1 and ":" in candidates[0] and not candidates[0].endswith(".exe"):
        try:
            os.startfile(candidates[0])
            return True, candidates[0]
        except Exception as e:
            return False, str(e)
    for raw in candidates:
        path = expand(raw)
        if os.path.isabs(path):
            if os.path.exists(path):
                subprocess.Popen([path], creationflags=subprocess.DETACHED_PROCESS)
                return True, path
        else:
            try:
                subprocess.Popen([path], creationflags=subprocess.DETACHED_PROCESS)
                return True, path
            except FileNotFoundError:
                continue
    return False, f"Could not find '{app_key}'"

def run_ps(command):
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=15
        )
        return True, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, str(e)

def run_cmd(command):
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
        return True, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, str(e)

# ── HTTP Handler ──────────────────────────────────────────────────────────────
class BoltzHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass

    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.cors()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            html_path = os.path.join(os.path.dirname(__file__), "boltz.html")
            if os.path.exists(html_path):
                content = open(html_path, "rb").read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.cors()
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_json(404, {"error": "boltz.html not found"})
        elif path == "/ping":
            self.send_json(200, {"status": "ok", "port": PORT})
        elif path == "/apps":
            self.send_json(200, {"apps": sorted(APPS.keys())})
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self):
        length  = int(self.headers.get("Content-Length", 0))
        body    = json.loads(self.rfile.read(length) or b"{}")
        path    = urlparse(self.path).path

        # ── /chat — proxy to Claude API ──────────────────────────────────────
        if path == "/chat":
            payload = {
                "model":      CLAUDE_MODEL,
                "max_tokens": body.get("max_tokens", 1000),
                "system":     body.get("system", ""),
                "messages":   body.get("messages", []),
            }
            try:
                r = requests.post(
                    CLAUDE_URL,
                    headers={
                        "x-api-key":         API_KEY,
                        "anthropic-version": "2023-06-01",
                        "Content-Type":      "application/json",
                    },
                    json=payload,
                    timeout=60,
                )
                self.send_json(r.status_code, r.json())
            except Exception as e:
                self.send_json(500, {"error": str(e)})

        elif path == "/run":
            app = body.get("app", "").strip()
            if not app:
                self.send_json(400, {"error": "Missing 'app'"}); return
            ok, detail = launch(app)
            self.send_json(200, {"success": ok, "detail": detail, "app": app})

        elif path == "/ps":
            cmd = body.get("command", "").strip()
            if not cmd:
                self.send_json(400, {"error": "Missing 'command'"}); return
            ok, output = run_ps(cmd)
            self.send_json(200, {"success": ok, "output": output})

        elif path == "/cmd":
            cmd = body.get("command", "").strip()
            if not cmd:
                self.send_json(400, {"error": "Missing 'command'"}); return
            ok, output = run_cmd(cmd)
            self.send_json(200, {"success": ok, "output": output})

        else:
            self.send_json(404, {"error": "not found"})


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", PORT), BoltzHandler)
    print(f"\n  ⚡ Boltz is live at http://127.0.0.1:{PORT}")
    print(f"  Press Ctrl+C to stop.\n")
    threading.Timer(0.8, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}")).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Boltz stopped.")
        sys.exit(0)
