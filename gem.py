"""
Gem — ラベンダー調マルチハブ
フォルダ管理・ターミナル接続・タスク管理をまとめて扱う
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import os
import json
import subprocess
import zlib
import struct
import base64
import ctypes
import datetime
import hashlib
import tempfile
import threading
import time
import io
import re
import calendar
import webbrowser
from ctypes import wintypes
from pathlib import Path
from PIL import ImageGrab

CONFIG_FILE   = Path(__file__).parent / "config.json"
LOG_DIR       = Path(__file__).parent / "logs"
TERATERM_EXE  = r"C:\Program Files\teraterm5\ttermpro.exe"

C = {
    "bg":        "#EDE8F5",
    "card":      "#F5F2FC",
    "card_h":    "#DDD4F4",
    "accent":    "#8B7CC8",
    "accent_dk": "#6A5BAA",
    "accent_lt": "#C4B8E8",
    "text":      "#3A2D6E",
    "text_sub":  "#7B6DB0",
    "border":    "#C0B0E0",
    "tab_act":   "#F5F2FC",   # active tab background
    "tab_inact": "#D8CFF0",   # inactive tab background
    "btn_del":   "#C8A0D0",
    "btn_del_h": "#A870B8",
}

THEMES: dict[str, dict] = {
    "lavender": {   # デフォルト（既存 C と同値）
        "bg": "#EDE8F5", "card": "#F5F2FC", "card_h": "#DDD4F4",
        "accent": "#8B7CC8", "accent_dk": "#6A5BAA", "accent_lt": "#C4B8E8",
        "text": "#3A2D6E", "text_sub": "#7B6DB0", "border": "#C0B0E0",
        "tab_act": "#F5F2FC", "tab_inact": "#D8CFF0",
        "btn_del": "#C8A0D0", "btn_del_h": "#A870B8",
    },
    "dark": {
        "bg": "#1E1E2E", "card": "#2A2A3E", "card_h": "#363650",
        "accent": "#7C6FBD", "accent_dk": "#5A4FA0", "accent_lt": "#9A8ED4",
        "text": "#E0DEFF", "text_sub": "#A09CC0", "border": "#4A4A6A",
        "tab_act": "#2A2A3E", "tab_inact": "#252535",
        "btn_del": "#7A4060", "btn_del_h": "#A05080",
    },
    "light": {
        "bg": "#F8F8FC", "card": "#FFFFFF", "card_h": "#EEF0FF",
        "accent": "#6655BB", "accent_dk": "#4A3DA0", "accent_lt": "#A89DD4",
        "text": "#222244", "text_sub": "#666699", "border": "#CCCCEE",
        "tab_act": "#FFFFFF", "tab_inact": "#E8E8F8",
        "btn_del": "#DD8899", "btn_del_h": "#BB5566",
    },
    "gemini": {   # Gemini風：クリーンホワイト + Google ブルー〜バイオレット
        "bg": "#F8F9FA", "card": "#FFFFFF", "card_h": "#E8F0FE",
        "accent": "#1B6EF3", "accent_dk": "#1251B5", "accent_lt": "#A8C7FA",
        "text": "#202124", "text_sub": "#5F6368", "border": "#DADCE0",
        "tab_act": "#FFFFFF", "tab_inact": "#F1F3F4",
        "btn_del": "#D93025", "btn_del_h": "#A50E0E",
    },
    "claude": {   # Claude Code風：ほぼ黒 + コーラルオレンジ
        "bg": "#1A1A1A", "card": "#242424", "card_h": "#2E2E2E",
        "accent": "#DA7756", "accent_dk": "#B85C3C", "accent_lt": "#E89A7A",
        "text": "#F0EDE8", "text_sub": "#9E9890", "border": "#383838",
        "tab_act": "#242424", "tab_inact": "#1E1E1E",
        "btn_del": "#8B3A3A", "btn_del_h": "#B04848",
    },
    "devil": {   # 小悪魔：漆黒＋クリムゾンレッド
        "bg": "#1A0A0E", "card": "#240F14", "card_h": "#331520",
        "accent": "#CC2244", "accent_dk": "#991833", "accent_lt": "#E06078",
        "text": "#F5E8EA", "text_sub": "#C09098", "border": "#4A1A25",
        "tab_act": "#240F14", "tab_inact": "#1E0B10",
        "btn_del": "#882030", "btn_del_h": "#BB3045",
    },
}

ICON_PALETTES: dict[str, dict] = {
    "lavender": {
        "BDR": ( 42,  32,  88, 255), "HL": (222, 213, 243, 255),
        "LT":  (178, 165, 220, 255), "F":  (128, 112, 190, 255),
        "MD":  ( 98,  82, 155, 255), "DK": ( 58,  46, 108, 255),
        "SP":  (215, 208, 242, 210),
    },
    "dark": {
        "BDR": ( 20,  15,  50, 255), "HL": (180, 168, 220, 255),
        "LT":  (150, 138, 205, 255), "F":  (124, 111, 189, 255),
        "MD":  ( 90,  79, 160, 255), "DK": ( 50,  40, 110, 255),
        "SP":  (175, 165, 220, 200),
    },
    "light": {
        "BDR": ( 35,  25,  80, 255), "HL": (200, 192, 228, 255),
        "LT":  (165, 153, 210, 255), "F":  (102,  85, 187, 255),
        "MD":  ( 74,  61, 160, 255), "DK": ( 45,  35, 100, 255),
        "SP":  (195, 185, 228, 210),
    },
    "gemini": {
        "BDR": ( 10,  35,  90, 255), "HL": (168, 199, 250, 255),
        "LT":  (110, 160, 245, 255), "F":  ( 27, 110, 243, 255),
        "MD":  ( 18,  81, 181, 255), "DK": ( 10,  50, 130, 255),
        "SP":  (168, 199, 250, 200),
    },
    "claude": {
        "BDR": ( 70,  30,  10, 255), "HL": (232, 154, 122, 255),
        "LT":  (220, 135, 100, 255), "F":  (218, 119,  86, 255),
        "MD":  (184,  92,  60, 255), "DK": (115,  52,  28, 255),
        "SP":  (235, 165, 130, 200),
    },
    "devil": {
        "BDR": ( 60,   8,  15, 255), "HL": (240, 160, 175, 255),
        "LT":  (210,  90, 115, 255), "F":  (180,  28,  60, 255),
        "MD":  (130,  18,  42, 255), "DK": ( 75,   8,  22, 255),
        "SP":  (220, 100, 120, 200),
    },
}

FONT       = ("Segoe UI", 10)
FONT_BOLD  = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 8)

CLIP_MAX = 50   # クリップボード履歴の最大保持件数


# ── Icon generation ───────────────────────────────────────

def _make_icon_png(palette: dict | None = None) -> str:
    """輪郭線付きカットジェム＋スパークルアイコン PNG を生成して Base64 返却する。"""
    p = palette or ICON_PALETTES["lavender"]
    W, H = 32, 32
    T   = (  0,   0,   0,   0)  # transparent
    BDR = p["BDR"]               # dark outline
    WH  = (255, 254, 255, 255)  # shine white（常に白）
    HL  = p["HL"]                # highlight
    LT  = p["LT"]                # light crown
    F   = p["F"]                 # main
    MD  = p["MD"]                # mid shadow
    DK  = p["DK"]                # deep shadow
    SP  = p["SP"]                # sparkle

    # ジェム輪郭 {y: (x_left, x_right)} 両端含む — 32x32 をほぼ全域使用
    ROWS = {
         2: (13, 18),   # table
         3: (11, 20),
         4: (10, 21),
         5: ( 8, 23),
         6: ( 6, 25),
         7: ( 5, 26),
         8: ( 3, 28),
         9: ( 2, 29),   # girdle
        10: ( 2, 29),   # girdle
        11: ( 2, 29),   # girdle
        12: ( 3, 28),   # pavilion
        13: ( 4, 27),
        14: ( 6, 25),
        15: ( 7, 24),
        16: ( 9, 22),
        17: (10, 21),
        18: (11, 20),
        19: (12, 19),
        20: (13, 18),
        21: (13, 18),
        22: (14, 17),
        23: (14, 17),
        24: (14, 17),
        25: (15, 16),
        26: (15, 16),
        27: (16, 16),   # culet
    }

    def in_gem(x, y):
        if y not in ROWS: return False
        lo, hi = ROWS[y]
        return lo <= x <= hi

    def is_edge(x, y):
        if not in_gem(x, y): return False
        return any(not in_gem(x+dx, y+dy)
                   for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)))

    # スパークル：十字型 5px（余白の 3 か所）
    SPARKLES: set[tuple[int, int]] = set()
    for sx, sy in ((1, 1), (30, 2), (28, 29)):
        for ddx, ddy in ((0,0),(1,0),(-1,0),(0,1),(0,-1)):
            SPARKLES.add((sx + ddx, sy + ddy))

    # 光沢スポット（左上クラウン内部）— shine を edge より優先
    SHINE    = {(12,3),(13,3),(11,4),(12,4),(13,4)}
    SHINE_HL = {(14,3),(11,5),(12,5),(13,5)}

    def px(x, y):
        if (x, y) in SPARKLES:
            return SP
        if not in_gem(x, y):
            return T
        # 光沢 → 輪郭 → ファセット の順に判定
        if (x, y) in SHINE:    return WH
        if (x, y) in SHINE_HL: return HL
        if is_edge(x, y):      return BDR

        dx = x - 16
        if y <= 8:    # upper crown: 明るく
            if dx <= -5: return LT
            if dx >= 5:  return F
            return HL
        if y <= 11:   # girdle: やや暗め
            if dx <= -4: return MD
            if dx >= 4:  return F
            return LT
        # pavilion: 暗く
        if dx <= -3: return DK
        if dx >= 3:  return MD
        return DK

    raw = b''
    for y in range(H):
        raw += b'\x00'
        for x in range(W):
            raw += bytes(px(x, y))

    def chunk(tag, data):
        c = tag + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)

    png = (
        b'\x89PNG\r\n\x1a\n'
        + chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 6, 0, 0, 0))
        + chunk(b'IDAT', zlib.compress(raw, 9))
        + chunk(b'IEND', b'')
    )
    return base64.b64encode(png).decode()


def _setup_taskbar_icon(root: tk.Tk, palette: dict | None = None) -> None:
    """AppUserModelID を設定し、ICO ファイルでタスクバーアイコンを適用する。"""
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Gem.Launcher.1")
    except Exception:
        pass

    ico_path = Path(__file__).parent / "gem.ico"
    # パレット指定時（テーマ変更）は常に再生成、初回はスクリプト更新時のみ
    force = palette is not None
    if not force:
        script_mtime = Path(__file__).stat().st_mtime
        ico_mtime    = ico_path.stat().st_mtime if ico_path.exists() else 0
        force = not ico_path.exists() or script_mtime > ico_mtime
    if force:
        try:
            from PIL import Image
            png_data = base64.b64decode(_make_icon_png(palette))
            img = Image.open(io.BytesIO(png_data)).convert("RGBA")
            img.save(str(ico_path), format="ICO",
                     sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        except Exception:
            pass

    if ico_path.exists():
        try:
            root.wm_iconbitmap(str(ico_path))
        except Exception:
            pass


# ── Monitor info retrieval ────────────────────────────────

def _get_monitors() -> list[dict]:
    """Return a list of connected monitors (left/top/right/bottom coords and resolution)."""
    monitors = []

    def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
        r = lprcMonitor.contents
        monitors.append({
            "left": r.left, "top": r.top,
            "right": r.right, "bottom": r.bottom,
            "width": r.right - r.left,
            "height": r.bottom - r.top,
        })
        return 1

    PROC = ctypes.WINFUNCTYPE(
        ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong,
        ctypes.POINTER(wintypes.RECT), ctypes.c_double,
    )
    ctypes.windll.user32.EnumDisplayMonitors(0, 0, PROC(callback), 0)
    return monitors


# ── Tera Term terminal functions ──────────────────────────


def _encode_pw(pw: str) -> str:
    return base64.b64encode(pw.encode()).decode()

def _decode_pw(enc: str) -> str:
    try:
        return base64.b64decode(enc.encode()).decode()
    except Exception:
        return ""


def _launch_teraterm(conn: dict):
    """Launch Tera Term with auto-login, command execution and auto-logging."""
    exe     = TERATERM_EXE
    host    = conn["host"]
    port    = int(conn.get("port", 22 if conn["protocol"] == "SSH" else 23))
    user    = conn.get("user", "")
    pw      = _decode_pw(conn.get("password", ""))
    proto   = conn["protocol"]
    cmds    = [c for c in conn.get("commands", []) if c.strip()]
    charset = conn.get("charset", "UTF-8")
    charset_arg = [f"/KT={charset}"] if charset else []

    # ログファイルを自動生成
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"{timestamp}_{host}.log"
    log_arg = [f"/L={log_path}"]

    PROMPT = "wait '$' '#' '%' '>'"

    def _ttl_sendln(s: str) -> list[str]:
        """TTL の sendln コードを生成する。シングルクォートを含む場合も正しく処理する。"""
        if "'" not in s:
            return [f"sendln '{s}'"]
        # シングルクォートを strconcat + char2str(39) で組み立てる
        parts = s.split("'")
        lines = [f"_s = '{parts[0]}'"]
        for part in parts[1:]:
            lines += ["char2str _c 39", "strconcat _s _c"]
            if part:
                lines.append(f"strconcat _s '{part}'")
        lines.append("sendln _s")
        return lines

    def _write_ttl(lines: list[str]) -> str:
        """TTL スクリプトを一時ファイルに書き出してパスを返す。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl",
                                         delete=False, encoding="utf-8") as f:
            f.write("\r\n".join(lines) + "\r\n")
            return f.name

    if proto == "SSH":
        # SSH: CLI引数でuser/pass渡し、コマンドがあればTTLでプロンプト待機
        if cmds:
            ttl_lines = [
                "timeout = 30",
                PROMPT,
            ]
            for cmd in cmds:
                ttl_lines += ["timeout = 60", "mpause 300"] + _ttl_sendln(cmd) + [PROMPT]
            ttl_arg = [f"/M={_write_ttl(ttl_lines)}"]
        else:
            ttl_arg = []
        args = [
            exe,
            f"{host}:{port}",
            "/ssh", "/2",
            "/auth=password",
            f"/user={user}",
            f"/passwd={pw}",
        ] + charset_arg + log_arg + ttl_arg
    else:  # Telnet: TTLスクリプトでlogin/passwordプロンプトに自動入力
        ttl_lines = [
            "timeout = 30",
            # login: / Login: / Username: / User: など各機器のプロンプトに対応
            "wait 'ogin:' 'sername:' 'ser:'",
            "mpause 300",   # プロンプト受信後、機器が入力待ちになるまで少し待つ
        ] + _ttl_sendln(user) + [
            "wait 'assword:'",
            "mpause 300",
        ] + _ttl_sendln(pw) + [
            PROMPT,
        ]
        for cmd in cmds:
            ttl_lines += ["timeout = 60", "mpause 300"] + _ttl_sendln(cmd) + [PROMPT]
        args = [
            exe,
            f"{host}:{port}",
            "/telnet",
        ] + charset_arg + log_arg + [f"/M={_write_ttl(ttl_lines)}"]

    subprocess.Popen(args)


def _launch_rdp(conn: dict):
    """Auto-connect via Windows Remote Desktop."""
    host = conn["host"]
    port = int(conn.get("port", 3389))
    user = conn.get("user", "")
    pw   = _decode_pw(conn.get("password", ""))

    target = f"TERMSRV/{host}"
    # temporarily register credentials in Windows Credential Manager
    subprocess.run(
        ["cmdkey", f"/generic:{target}", f"/user:{user}", f"/pass:{pw}"],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    # launch mstsc (include port in address)
    address = f"{host}:{port}" if port != 3389 else host
    subprocess.Popen(["mstsc", f"/v:{address}"])


def _launch_smb(conn: dict):
    """Open Windows SMB share (UNC path) in Explorer."""
    unc  = conn["host"]   # \\server\share 形式
    user = conn.get("user", "")
    pw   = _decode_pw(conn.get("password", ""))

    if user and pw:
        # 資格情報を一時登録してからアクセス
        subprocess.run(
            ["net", "use", unc, pw, f"/user:{user}"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            capture_output=True,
        )
    os.startfile(unc)


class ConnectionDialog(tk.Toplevel):
    """Dialog for adding/editing connections."""

    def __init__(self, parent, initial: dict | None = None,
                 groups: list[str] | None = None):
        super().__init__(parent)
        self.title("Add Connection" if initial is None else "Edit Connection")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.result: dict | None = None
        self._groups = groups or []

        d = initial or {}
        self._name_var = tk.StringVar(value=d.get("name", ""))
        self._proto   = tk.StringVar(value=d.get("protocol", "SSH"))
        self._host    = tk.StringVar(value=d.get("host", ""))
        self._port    = tk.StringVar(value=str(d.get("port", 22)))
        self._user    = tk.StringVar(value=d.get("user", ""))
        self._pw      = tk.StringVar(value=_decode_pw(d.get("password", "")))
        self._charset = tk.StringVar(value=d.get("charset", "UTF-8"))
        self._group_var = tk.StringVar(value=d.get("group", ""))
        self._init_cmds = "\n".join(d.get("commands", []))

        self._proto.trace_add("write", self._on_proto_change)
        self._build()

        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")
        self.wait_window()

    def _row(self, label: str, row: int, var: tk.StringVar,
             show: str = "", width: int = 22):
        lbl = tk.Label(self._form, text=label, bg=C["bg"], fg=C["text_sub"],
                       font=FONT_SMALL, anchor="e", width=10)
        lbl.grid(row=row, column=0, padx=(12, 4), pady=3, sticky="e")
        e = tk.Entry(self._form, textvariable=var, font=FONT,
                     bg="#F0EBF8", fg=C["text"], relief="flat", bd=1,
                     insertbackground=C["accent"], width=width, show=show)
        e.grid(row=row, column=1, padx=(0, 12), pady=3, sticky="ew")
        return lbl, e

    def _build(self):
        self._form = tk.Frame(self, bg=C["bg"])
        self._form.pack(padx=4, pady=(12, 4))

        self._row("Name",     0, self._name_var)
        # Protocol dropdown
        tk.Label(self._form, text="Protocol", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="e", width=10).grid(
                     row=1, column=0, padx=(12, 4), pady=3, sticky="e")
        combo = ttk.Combobox(self._form, textvariable=self._proto,
                             values=["SSH", "Telnet", "RDP", "SMB"], state="readonly",
                             font=FONT, width=20)
        combo.grid(row=1, column=1, padx=(0, 12), pady=3, sticky="ew")

        self._host_lbl, _ = self._row("Host",     2, self._host)
        self._port_lbl, self._port_entry = self._row("Port", 3, self._port, width=8)
        self._row("Username", 4, self._user)
        self._row("Password", 5, self._pw, show="●")

        # 文字コード選択
        self._charset_lbl = tk.Label(self._form, text="Charset", bg=C["bg"], fg=C["text_sub"],
                                     font=FONT_SMALL, anchor="e", width=10)
        self._charset_lbl.grid(row=6, column=0, padx=(12, 4), pady=3, sticky="e")
        self._charset_combo = ttk.Combobox(
            self._form, textvariable=self._charset,
            values=["UTF-8", "SJIS", "EUC", "JIS"],
            state="readonly", font=FONT, width=20,
        )
        self._charset_combo.grid(row=6, column=1, padx=(0, 12), pady=3, sticky="ew")

        # グループ選択
        tk.Label(self._form, text="Group", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="e", width=10).grid(
                     row=7, column=0, padx=(12, 4), pady=3, sticky="e")
        self._group_combo = ttk.Combobox(
            self._form, textvariable=self._group_var,
            values=self._groups, font=FONT, width=20,
        )
        self._group_combo.grid(row=7, column=1, padx=(0, 12), pady=3, sticky="ew")

        # command input area
        self._cmd_lbl = tk.Label(self._form, text="Commands", bg=C["bg"], fg=C["text_sub"],
                                 font=FONT_SMALL, anchor="ne", width=10)
        self._cmd_lbl.grid(row=8, column=0, padx=(12, 4), pady=(6, 3), sticky="ne")
        self._cmd_text = tk.Text(
            self._form, font=("Consolas", 9),
            bg="#F0EBF8", fg=C["text"], relief="flat", bd=1,
            insertbackground=C["accent"],
            width=24, height=5,
            wrap="none",
        )
        self._cmd_text.insert("1.0", self._init_cmds)
        self._cmd_text.grid(row=8, column=1, padx=(0, 12), pady=(6, 3), sticky="ew")
        self._cmd_hint = tk.Label(self._form, text="One command per line\nExecuted after login",
                                  bg=C["bg"], fg=C["text_sub"],
                                  font=("Segoe UI", 7), justify="left")
        self._cmd_hint.grid(row=9, column=1, padx=(0, 12), sticky="w")

        btn_frame = tk.Frame(self, bg=C["bg"])
        btn_frame.pack(fill="x", padx=16, pady=(4, 14))
        tk.Button(btn_frame, text="Connect & Save", command=self._ok,
                  bg=C["accent"], fg="white", relief="flat", bd=0,
                  font=FONT_BOLD, cursor="hand2", padx=12, pady=4,
                  activebackground=C["accent_dk"], activeforeground="white",
                  ).pack(side="right", padx=(4, 0))
        tk.Button(btn_frame, text="Cancel", command=self.destroy,
                  bg=C["accent_lt"], fg=C["text"], relief="flat", bd=0,
                  font=FONT, cursor="hand2", padx=10, pady=4,
                  activebackground=C["border"], activeforeground=C["text"],
                  ).pack(side="right")

    def _on_proto_change(self, *_):
        proto = self._proto.get()
        defaults = {"SSH": "22", "Telnet": "23", "RDP": "3389"}
        if proto in defaults and self._port.get() in ("22", "23", "3389"):
            self._port.set(defaults[proto])
        is_smb = (proto == "SMB")
        is_rdp = (proto == "RDP")
        for w in (self._port_lbl, self._port_entry,
                  self._cmd_lbl, self._cmd_text, self._cmd_hint):
            if is_smb:
                w.grid_remove()
            else:
                w.grid()
        # CharsetはSSH/Telnetのみ表示
        for w in (self._charset_lbl, self._charset_combo):
            if is_smb or is_rdp:
                w.grid_remove()
            else:
                w.grid()
        self._host_lbl.configure(text="UNC Path" if is_smb else "Host")

    def _ok(self):
        if not self._name_var.get().strip() or not self._host.get().strip():
            messagebox.showwarning("Input Error",
                                   "Name and Host are required.", parent=self)
            return
        proto = self._proto.get()
        cmds = [] if proto == "SMB" else [
            l.strip() for l in self._cmd_text.get("1.0", "end").splitlines()
            if l.strip()
        ]
        port_str = self._port.get().strip()
        charset = self._charset.get() if proto in ("SSH", "Telnet") else ""
        self.result = {
            "name":     self._name_var.get().strip(),
            "protocol": proto,
            "host":     self._host.get().strip(),
            "port":     int(port_str) if port_str else 0,
            "user":     self._user.get().strip(),
            "password": _encode_pw(self._pw.get()),
            "commands": cmds,
            "charset":  charset,
            "group":    self._group_var.get().strip(),
        }
        self.destroy()


# ── Bookmark dialog ───────────────────────────────────────

class BookmarkDialog(tk.Toplevel):
    """ブックマークの追加・編集ダイアログ。"""

    def __init__(self, parent, initial: dict | None = None):
        super().__init__(parent)
        self.title("Add Bookmark" if initial is None else "Edit Bookmark")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.result: dict | None = None

        d = initial or {}
        self._name_var = tk.StringVar(value=d.get("name", ""))
        self._url_var  = tk.StringVar(value=d.get("url",  ""))

        self._build()
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")
        self.wait_window()

    def _build(self):
        form = tk.Frame(self, bg=C["bg"])
        form.pack(padx=16, pady=(14, 6))

        for row, (label, var) in enumerate([("Name", self._name_var),
                                            ("URL",  self._url_var)]):
            tk.Label(form, text=label, bg=C["bg"], fg=C["text_sub"],
                     font=FONT_SMALL, anchor="e", width=6).grid(
                         row=row, column=0, padx=(0, 6), pady=4, sticky="e")
            tk.Entry(form, textvariable=var, font=FONT,
                     bg="#F0EBF8", fg=C["text"], relief="flat", bd=1,
                     insertbackground=C["accent"], width=30).grid(
                         row=row, column=1, pady=4, sticky="ew")

        btn_frame = tk.Frame(self, bg=C["bg"])
        btn_frame.pack(fill="x", padx=16, pady=(4, 14))
        tk.Button(btn_frame, text="Save", command=self._ok,
                  bg=C["accent"], fg="white", relief="flat", bd=0,
                  font=FONT_BOLD, cursor="hand2", padx=12, pady=4,
                  activebackground=C["accent_dk"], activeforeground="white",
                  ).pack(side="right", padx=(4, 0))
        tk.Button(btn_frame, text="Cancel", command=self.destroy,
                  bg=C["accent_lt"], fg=C["text"], relief="flat", bd=0,
                  font=FONT, cursor="hand2", padx=10, pady=4,
                  activebackground=C["border"], activeforeground=C["text"],
                  ).pack(side="right")

    def _ok(self):
        name = self._name_var.get().strip()
        url  = self._url_var.get().strip()
        if not name or not url:
            messagebox.showwarning("Input Error",
                                   "Name and URL are required.", parent=self)
            return
        if not url.startswith("http"):
            url = "https://" + url
        self.result = {"name": name, "url": url}
        self.destroy()


# ── Task dialog ───────────────────────────────────────────

class TaskDialog(tk.Toplevel):
    """Dialog for adding/editing tasks."""

    def __init__(self, parent, initial: dict | None = None,
                 event_names: list | None = None):
        super().__init__(parent)
        self.title("Add Task" if initial is None else "Edit Task")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.result: dict | None = None
        self._event_names = event_names or []

        d = initial or {}
        self._event_var    = tk.StringVar(value=d.get("event", ""))
        self._process_var  = tk.StringVar(value=d.get("process", ""))
        self._progress_var = tk.IntVar(value=d.get("progress", 0))
        self._init_content = d.get("content", "")
        _wf = d.get("work_folders", [])
        if not _wf and d.get("work_folder"):
            _wf = [d["work_folder"]]
        self._work_folders_list: list = list(_wf)

        # deadline スピンボックス初期値
        dl_str = d.get("deadline", "")
        try:
            _dl = datetime.date.fromisoformat(dl_str)
        except ValueError:
            _dl = datetime.date.today()
        self._use_deadline = tk.BooleanVar(value=bool(dl_str))
        self._dl_year  = tk.IntVar(value=_dl.year)
        self._dl_month = tk.IntVar(value=_dl.month)
        self._dl_day   = tk.IntVar(value=_dl.day)
        self._dl_spinboxes: list = []

        self._build()
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")
        self.wait_window()

    def _entry_row(self, label: str, row: int, var: tk.StringVar, width: int = 24):
        tk.Label(self._form, text=label, bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="e", width=9).grid(
                     row=row, column=0, padx=(12, 4), pady=3, sticky="e")
        e = tk.Entry(self._form, textvariable=var, font=FONT,
                     bg="#F0EBF8", fg=C["text"], relief="flat", bd=1,
                     insertbackground=C["accent"], width=width)
        e.grid(row=row, column=1, padx=(0, 12), pady=3, sticky="ew")
        return e

    def _build(self):
        self._form = tk.Frame(self, bg=C["bg"])
        self._form.pack(padx=4, pady=(12, 4))

        # Event: コンボボックス（既存イベント名から選択 or 直接入力）
        tk.Label(self._form, text="Event", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="e", width=9).grid(
                     row=0, column=0, padx=(12, 4), pady=3, sticky="e")
        style = ttk.Style()
        style.configure("Task.TCombobox",
                        fieldbackground="#F0EBF8", background=C["accent_lt"],
                        foreground=C["text"], arrowcolor=C["accent"])
        self._event_cb = ttk.Combobox(
            self._form, textvariable=self._event_var,
            values=self._event_names, font=FONT, width=22,
            style="Task.TCombobox",
        )
        self._event_cb.grid(row=0, column=1, padx=(0, 12), pady=3, sticky="ew")

        self._entry_row("Process", 1, self._process_var)

        # content (multi-line)
        tk.Label(self._form, text="Content", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="ne", width=9).grid(
                     row=2, column=0, padx=(12, 4), pady=(6, 3), sticky="ne")
        self._content_text = tk.Text(
            self._form, font=FONT,
            bg="#F0EBF8", fg=C["text"], relief="flat", bd=1,
            insertbackground=C["accent"],
            width=26, height=4, wrap="word",
        )
        self._content_text.insert("1.0", self._init_content)
        self._content_text.grid(row=2, column=1, padx=(0, 12), pady=(6, 3), sticky="ew")

        # progress slider
        tk.Label(self._form, text="Progress", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="e", width=9).grid(
                     row=3, column=0, padx=(12, 4), pady=(6, 3), sticky="e")
        slider_frame = tk.Frame(self._form, bg=C["bg"])
        slider_frame.grid(row=3, column=1, padx=(0, 12), pady=(6, 3), sticky="ew")

        self._pct_label = tk.Label(slider_frame, text=f"{self._progress_var.get()}%",
                                   bg=C["bg"], fg=C["accent"], font=FONT_BOLD, width=4)
        self._pct_label.pack(side="right")

        scale = tk.Scale(slider_frame, variable=self._progress_var,
                         from_=0, to=100, orient="horizontal",
                         command=lambda v: self._pct_label.configure(text=f"{int(float(v))}%"),
                         bg=C["bg"], fg=C["text"], troughcolor=C["border"],
                         activebackground=C["accent_lt"],
                         highlightthickness=0, bd=0,
                         showvalue=False, resolution=5)
        scale.pack(side="left", fill="x", expand=True)

        # deadline input (スピンボックス分割 + チェックボックス)
        tk.Label(self._form, text="Deadline", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="e", width=9).grid(
                     row=4, column=0, padx=(12, 4), pady=(6, 3), sticky="e")
        dl_outer = tk.Frame(self._form, bg=C["bg"])
        dl_outer.grid(row=4, column=1, padx=(0, 12), pady=(6, 3), sticky="ew")

        tk.Checkbutton(dl_outer, text="Set",
                       variable=self._use_deadline, command=self._toggle_deadline,
                       bg=C["bg"], fg=C["text_sub"], selectcolor=C["bg"],
                       activebackground=C["bg"], font=FONT_SMALL,
                       cursor="hand2").pack(side="left")

        dl_spin_frame = tk.Frame(dl_outer, bg=C["bg"])
        dl_spin_frame.pack(side="left", padx=(8, 0))
        _spin_cfg = dict(font=FONT, bg="#F0EBF8", fg=C["text"], relief="flat", bd=1,
                         buttonbackground=C["accent_lt"],
                         insertbackground=C["accent"], wrap=True)

        def _dl_lbl(t):
            return tk.Label(dl_spin_frame, text=t, bg=C["bg"],
                            fg=C["text_sub"], font=FONT_SMALL)

        sp_y = tk.Spinbox(dl_spin_frame, textvariable=self._dl_year,
                          from_=2020, to=2099, width=5, **_spin_cfg)
        sp_y.pack(side="left")
        _dl_lbl("/").pack(side="left")
        sp_m = tk.Spinbox(dl_spin_frame, textvariable=self._dl_month,
                          from_=1, to=12, width=3, **_spin_cfg)
        sp_m.pack(side="left")
        _dl_lbl("/").pack(side="left")
        sp_d = tk.Spinbox(dl_spin_frame, textvariable=self._dl_day,
                          from_=1, to=31, width=3, **_spin_cfg)
        sp_d.pack(side="left")
        self._dl_spinboxes = [sp_y, sp_m, sp_d]
        self._toggle_deadline()

        # work folders (複数)
        tk.Label(self._form, text="Folders", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="ne", width=9).grid(
                     row=5, column=0, padx=(12, 4), pady=3, sticky="ne")
        wf_outer = tk.Frame(self._form, bg=C["bg"])
        wf_outer.grid(row=5, column=1, padx=(0, 12), pady=3, sticky="ew")

        wf_lb_frame = tk.Frame(wf_outer, bg=C["bg"])
        wf_lb_frame.pack(side="left", fill="both", expand=True)
        self._wf_lb = tk.Listbox(
            wf_lb_frame, height=3, font=FONT_SMALL,
            bg="#F0EBF8", fg=C["text"], selectbackground=C["accent_lt"],
            selectforeground=C["accent_dk"], relief="flat", bd=1,
            activestyle="none",
        )
        self._wf_lb.pack(side="left", fill="both", expand=True)
        _wf_sb = tk.Scrollbar(wf_lb_frame, orient="vertical",
                              command=self._wf_lb.yview)
        _wf_sb.pack(side="right", fill="y")
        self._wf_lb.configure(yscrollcommand=_wf_sb.set)
        for p in self._work_folders_list:
            self._wf_lb.insert("end", os.path.basename(p) or p)

        _wf_btn_cfg = dict(bg=C["accent_lt"], fg=C["text"], relief="flat", bd=0,
                           font=FONT_SMALL, cursor="hand2", padx=5,
                           activebackground=C["border"])
        wf_btn_col = tk.Frame(wf_outer, bg=C["bg"])
        wf_btn_col.pack(side="left", padx=(4, 0))
        tk.Button(wf_btn_col, text="+ Add",  command=self._add_work_folder,    **_wf_btn_cfg).pack(fill="x", pady=(0, 2))
        tk.Button(wf_btn_col, text="Remove", command=self._remove_work_folder, **_wf_btn_cfg).pack(fill="x")

        btn_frame = tk.Frame(self, bg=C["bg"])
        btn_frame.pack(fill="x", padx=16, pady=(4, 14))
        tk.Button(btn_frame, text="Save", command=self._ok,
                  bg=C["accent"], fg="white", relief="flat", bd=0,
                  font=FONT_BOLD, cursor="hand2", padx=16, pady=4,
                  activebackground=C["accent_dk"], activeforeground="white",
                  ).pack(side="right", padx=(4, 0))
        tk.Button(btn_frame, text="Cancel", command=self.destroy,
                  bg=C["accent_lt"], fg=C["text"], relief="flat", bd=0,
                  font=FONT, cursor="hand2", padx=10, pady=4,
                  activebackground=C["border"], activeforeground=C["text"],
                  ).pack(side="right")

    def _toggle_deadline(self):
        if self._use_deadline.get():
            state, bg = "normal", "#F0EBF8"
        else:
            state, bg = "disabled", C["border"]
        for sp in self._dl_spinboxes:
            sp.configure(state=state, bg=bg)

    def _add_work_folder(self):
        path = filedialog.askdirectory(title="Select work folder", parent=self)
        if path:
            path = os.path.normpath(path)
            self._work_folders_list.append(path)
            self._wf_lb.insert("end", os.path.basename(path) or path)

    def _remove_work_folder(self):
        sel = self._wf_lb.curselection()
        if sel:
            idx = sel[0]
            self._wf_lb.delete(idx)
            self._work_folders_list.pop(idx)

    def _ok(self):
        if not self._event_var.get().strip():
            messagebox.showwarning("Input Error", "Event name is required.", parent=self)
            return
        deadline = ""
        if self._use_deadline.get():
            try:
                dl = datetime.date(self._dl_year.get(), self._dl_month.get(),
                                   self._dl_day.get())
                deadline = dl.isoformat()
            except ValueError as e:
                messagebox.showwarning("Input Error", f"Invalid deadline:\n{e}", parent=self)
                return
        self.result = {
            "event":       self._event_var.get().strip(),
            "process":     self._process_var.get().strip(),
            "content":     self._content_text.get("1.0", "end").strip(),
            "progress":    self._progress_var.get(),
            "deadline":    deadline,
            "work_folders": list(self._work_folders_list),
        }
        self.destroy()


# ── Gantt chart window ────────────────────────────────────

class GanttWindow(tk.Toplevel):
    """タスクをガントチャートで可視化するウィンドウ。"""

    ROW_H = 28
    HDR_H = 50
    LBL_W = 185
    BAR_H = 16

    def __init__(self, parent, tasks: list[dict]):
        super().__init__(parent)
        self.title("Gantt Chart — Gem")
        self.configure(bg=C["bg"])
        self.geometry("900x500")
        self.resizable(True, True)
        self._tasks = tasks
        self._build()

    # ── 日付ユーティリティ ──

    @staticmethod
    def _parse_date(s: str) -> datetime.date | None:
        try:
            return datetime.date.fromisoformat(s)
        except (ValueError, TypeError):
            return None

    # ── 進捗率→色 ──

    @staticmethod
    def _bar_color(pct: int) -> str:
        if pct == 100: return "#A8DDB8"
        if pct >= 67:  return "#C8EDD4"
        if pct >= 34:  return "#FFF3BC"
        return "#FFAAAA"

    # ── ビルド ──

    def _build(self):
        if not self._tasks:
            tk.Label(self, text="No tasks.",
                     bg=C["bg"], fg=C["text_sub"], font=FONT).pack(expand=True)
            return

        today = datetime.date.today()

        # グループ化
        groups: dict[str, list[dict]] = {}
        for t in self._tasks:
            groups.setdefault(t["event"], []).append(t)

        # 日付範囲
        dates: list[datetime.date] = [today]
        for t in self._tasks:
            for key in ("created_at", "deadline"):
                d = self._parse_date(t.get(key, ""))
                if d:
                    dates.append(d)
        min_date = min(dates) - datetime.timedelta(days=7)
        max_date = max(dates) + datetime.timedelta(days=21)
        total_days = (max_date - min_date).days or 1

        # ピクセル/日（ウィンドウ幅に合わせて自動調整）
        bar_area = 900 - self.LBL_W - 20
        day_w = max(4, min(24, bar_area // total_days))

        # キャンバスサイズ
        n_rows = len(self._tasks) + len(groups)
        cw = self.LBL_W + total_days * day_w + 10
        ch = self.HDR_H + n_rows * self.ROW_H + 10

        # レイアウト
        outer = tk.Frame(self, bg=C["bg"])
        outer.pack(fill="both", expand=True, padx=4, pady=4)
        h_sb = tk.Scrollbar(outer, orient="horizontal")
        v_sb = tk.Scrollbar(outer, orient="vertical")
        h_sb.pack(side="bottom", fill="x")
        v_sb.pack(side="right", fill="y")
        cv = tk.Canvas(outer, bg=C["card"], highlightthickness=0,
                       xscrollcommand=h_sb.set, yscrollcommand=v_sb.set,
                       scrollregion=(0, 0, cw, ch))
        cv.pack(side="left", fill="both", expand=True)
        h_sb.config(command=cv.xview)
        v_sb.config(command=cv.yview)
        cv.bind("<MouseWheel>",
                lambda e: cv.yview_scroll(-1 * (e.delta // 120), "units"))

        # 描画
        self._draw_header(cv, min_date, max_date, day_w, cw)
        self._draw_rows(cv, groups, min_date, day_w, today, cw, ch)

        # 今日線
        tx = self.LBL_W + (today - min_date).days * day_w
        cv.create_line(tx, 0, tx, ch, fill="#C04040", width=1, dash=(5, 3))
        cv.create_text(tx + 3, self.HDR_H - 4,
                       text="Today", fill="#C04040", font=FONT_SMALL, anchor="sw")

        # 今日位置へスクロール
        cv.after(80, lambda: cv.xview_moveto(max(0.0, (tx - 220) / cw)))

    def _draw_header(self, cv, min_date, max_date, day_w, cw):
        HDR_H, LBL_W = self.HDR_H, self.LBL_W

        cv.create_rectangle(0, 0, cw, HDR_H, fill=C["tab_inact"], outline="")
        cv.create_rectangle(0, 0, LBL_W, HDR_H, fill=C["tab_inact"], outline="")
        cv.create_text(LBL_W // 2, HDR_H // 2,
                       text="Task", fill=C["text"], font=FONT_BOLD)
        cv.create_line(LBL_W, 0, LBL_W, HDR_H, fill=C["border"])

        # 月ラベル
        d = datetime.date(min_date.year, min_date.month, 1)
        while d <= max_date:
            x = LBL_W + (d - min_date).days * day_w
            cv.create_line(x, 0, x, HDR_H, fill=C["border"])
            cv.create_text(x + 4, 6, text=d.strftime("%b %Y"),
                           fill=C["text"], font=FONT_SMALL, anchor="nw")
            if d.month == 12:
                d = datetime.date(d.year + 1, 1, 1)
            else:
                d = datetime.date(d.year, d.month + 1, 1)

        # 週区切り＋日付
        total_days = (max_date - min_date).days
        for i in range(0, total_days + 1, 7):
            x = LBL_W + i * day_w
            wd = min_date + datetime.timedelta(days=i)
            cv.create_line(x, HDR_H * 2 // 3, x, HDR_H, fill=C["border"])
            cv.create_text(x + 3, HDR_H - 4, text=str(wd.day),
                           fill=C["text_sub"], font=FONT_SMALL, anchor="sw")

        cv.create_line(0, HDR_H, cw, HDR_H, fill=C["border"], width=1)

    def _draw_rows(self, cv, groups, min_date, day_w, today, cw, ch):
        HDR_H, ROW_H, LBL_W, BAR_H = self.HDR_H, self.ROW_H, self.LBL_W, self.BAR_H
        y = HDR_H

        for event_name, task_list in groups.items():
            # イベントヘッダー行
            cv.create_rectangle(0, y, cw, y + ROW_H, fill=C["accent_lt"], outline="")
            cv.create_text(10, y + ROW_H // 2, text=f"▶  {event_name}",
                           fill=C["accent_dk"], font=FONT_BOLD, anchor="w")
            cv.create_line(0, y + ROW_H, cw, y + ROW_H, fill=C["border"])
            y += ROW_H

            for ri, task in enumerate(task_list):
                pct   = task.get("progress", 0)
                label = task.get("process", "") or event_name
                ca    = self._parse_date(task.get("created_at", ""))
                dl    = self._parse_date(task.get("deadline", ""))

                start_d = ca if ca else today - datetime.timedelta(days=14)
                has_dl  = dl is not None
                end_d   = dl if dl else start_d + datetime.timedelta(days=28)

                # 行背景（交互）
                row_bg = C["card"] if ri % 2 == 0 else C["bg"]
                cv.create_rectangle(0, y, cw, y + ROW_H, fill=row_bg, outline="")

                # ラベル
                cv.create_text(10, y + ROW_H // 2, text=label,
                               fill=C["text"], font=FONT_SMALL, anchor="w")
                cv.create_line(LBL_W, y, LBL_W, y + ROW_H, fill=C["border"])

                # バー座標
                x1 = LBL_W + max(0, (start_d - min_date).days) * day_w
                x2 = LBL_W + max(0, (end_d   - min_date).days) * day_w
                x2 = max(x2, x1 + 8)
                by1 = y + (ROW_H - BAR_H) // 2
                by2 = by1 + BAR_H

                # バー背景
                bar_bg = C["accent_lt"] if has_dl else C["border"]
                cv.create_rectangle(x1, by1, x2, by2,
                                    fill=bar_bg, outline=C["accent"], width=1)

                # 進捗塗り
                fill_w = int((x2 - x1) * pct / 100)
                if fill_w > 2:
                    cv.create_rectangle(x1, by1, x1 + fill_w, by2,
                                        fill=self._bar_color(pct), outline="")

                # 進捗%テキスト
                cv.create_text((x1 + x2) // 2, (by1 + by2) // 2,
                               text=f"{pct}%", fill=C["text"], font=FONT_SMALL)

                # 締切マーカー
                if has_dl:
                    cv.create_line(x2, by1 - 2, x2, by2 + 2,
                                   fill=C["accent_dk"], width=2)

                cv.create_line(0, y + ROW_H, cw, y + ROW_H, fill=C["border"])
                y += ROW_H


# ── MJPEG AVI builder ─────────────────────────────────────

def _build_mjpeg_avi(frames: list[bytes], fps: int, width: int, height: int) -> bytes:
    """JPEG フレームのリストから MJPEG AVI バイト列を生成する"""
    n = len(frames)
    if n == 0:
        return b""

    def _chunk(fourcc: bytes, data: bytes) -> bytes:
        if len(data) % 2:
            data += b"\x00"
        return fourcc + struct.pack("<I", len(data)) + data

    def _list(fourcc: bytes, data: bytes) -> bytes:
        return b"LIST" + struct.pack("<I", 4 + len(data)) + fourcc + data

    frame_chunks = [_chunk(b"00dc", f) for f in frames]

    # idx1 — フレームオフセット索引
    offset = 4  # 'movi' FOURCC の直後から
    idx_data = b""
    for fc in frame_chunks:
        idx_data += b"00dc" + struct.pack("<III", 0x10, offset, len(fc) - 8)
        offset += len(fc)

    movi = _list(b"movi", b"".join(frame_chunks))

    # strf: BITMAPINFOHEADER (40 bytes)
    strf_data = (
        struct.pack("<IiiHH", 40, width, height, 1, 24)  # biSize/biWidth/biHeight/biPlanes/biBitCount
        + b"MJPG"                                         # biCompression
        + struct.pack("<i", width * height * 3)           # biSizeImage
        + struct.pack("<iiII", 0, 0, 0, 0)               # xPPM/yPPM/clrUsed/clrImportant
    )

    # strh: AVISTREAMHEADER (60 bytes data)
    max_f = max(len(f) for f in frames)
    strh_data = (
        b"vids" + b"MJPG"
        + struct.pack("<I", 0)              # dwFlags
        + struct.pack("<HH", 0, 0)          # wPriority, wLanguage
        + struct.pack("<I", 0)              # dwInitialFrames
        + struct.pack("<II", 1, fps)        # dwScale, dwRate
        + struct.pack("<II", 0, n)          # dwStart, dwLength
        + struct.pack("<I", max_f)          # dwSuggestedBufferSize
        + struct.pack("<i", -1)             # dwQuality (-1 = default)
        + struct.pack("<I", 0)              # dwSampleSize
        + struct.pack("<hhhh", 0, 0, width, height)  # rcFrame
    )

    strl = _list(b"strl", _chunk(b"strh", strh_data) + _chunk(b"strf", strf_data))

    # avih: AVIMAINHEADER (56 bytes data)
    avih_data = (
        struct.pack("<IIIIIIIIII",
            1000000 // fps, max_f * fps, 0, 0x10,  # microSecPerFrame, maxBytesPerSec, padding, flags
            n, 0, 1, max_f, width, height,         # totalFrames, initialFrames, streams, bufSize, W, H
        )
        + struct.pack("<IIII", 0, 0, 0, 0)         # dwReserved[4]
    )

    hdrl = _list(b"hdrl", _chunk(b"avih", avih_data) + strl)
    idx1 = _chunk(b"idx1", idx_data)
    riff_data = b"AVI " + hdrl + movi + idx1
    return b"RIFF" + struct.pack("<I", len(riff_data)) + riff_data


# ── Recording window ───────────────────────────────────────

class RecordingWindow(tk.Toplevel):
    MAX_FRAMES = 18000  # 10fps で最大30分相当

    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent
        self.title("Screen Recording")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.grab_set()

        self._monitors   = _get_monitors()
        self._monitor_var = tk.IntVar(value=-1)
        self._fps_var    = tk.IntVar(value=10)
        self._quality_var = tk.IntVar(value=85)
        self._save_dir   = tk.StringVar(value=str(Path.home() / "Videos"))
        self._hide_var   = tk.BooleanVar(value=True)

        self._recording  = False
        self._stop_event = threading.Event()
        self._frames: list[bytes] = []
        self._lock       = threading.Lock()
        self._timer_id   = None
        self._elapsed    = 0

        self._build()
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self):
        # ── モニター選択 ──
        tk.Label(self, text="Monitor", bg=C["bg"], fg=C["text"],
                 font=FONT_BOLD).pack(anchor="w", padx=14, pady=(14, 4))
        radio_frame = tk.Frame(self, bg=C["bg"])
        radio_frame.pack(fill="x", padx=14)
        rcfg = dict(bg=C["bg"], fg=C["text"], font=FONT,
                    activebackground=C["bg"], activeforeground=C["text"],
                    selectcolor=C["accent_lt"], relief="flat", bd=0)
        tk.Radiobutton(radio_frame, text="All screens",
                       variable=self._monitor_var, value=-1, **rcfg).pack(anchor="w")
        for i, m in enumerate(self._monitors):
            label = f"Monitor {i + 1}   {m['width']}x{m['height']}"
            if m["left"] != 0 or m["top"] != 0:
                label += f"  ({m['left']:+d}, {m['top']:+d})"
            tk.Radiobutton(radio_frame, text=label,
                           variable=self._monitor_var, value=i, **rcfg).pack(anchor="w")

        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", pady=8)

        # ── FPS ──
        tk.Label(self, text="FPS", bg=C["bg"], fg=C["text"],
                 font=FONT_BOLD).pack(anchor="w", padx=14)
        fps_frame = tk.Frame(self, bg=C["bg"])
        fps_frame.pack(fill="x", padx=14, pady=(4, 0))
        for v in (5, 10, 15):
            tk.Radiobutton(fps_frame, text=str(v), variable=self._fps_var, value=v,
                           **rcfg).pack(side="left", padx=(0, 12))

        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", pady=8)

        # ── JPEG 画質 ──
        tk.Label(self, text="Quality (JPEG)", bg=C["bg"], fg=C["text"],
                 font=FONT_BOLD).pack(anchor="w", padx=14)
        q_frame = tk.Frame(self, bg=C["bg"])
        q_frame.pack(fill="x", padx=14, pady=(4, 0))
        self._q_label = tk.Label(q_frame, text=f"{self._quality_var.get()}",
                                 bg=C["bg"], fg=C["accent"], font=FONT_BOLD, width=3)
        self._q_label.pack(side="right")
        tk.Scale(q_frame, variable=self._quality_var,
                 from_=60, to=95, orient="horizontal",
                 command=lambda v: self._q_label.configure(text=str(int(float(v)))),
                 bg=C["bg"], fg=C["text"], troughcolor=C["border"],
                 activebackground=C["accent_lt"],
                 highlightthickness=0, bd=0,
                 showvalue=False, resolution=5).pack(side="left", fill="x", expand=True)

        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", pady=8)

        # ── 保存先 ──
        tk.Label(self, text="Save to", bg=C["bg"], fg=C["text"],
                 font=FONT_BOLD).pack(anchor="w", padx=14)
        dir_frame = tk.Frame(self, bg=C["bg"])
        dir_frame.pack(fill="x", padx=14, pady=(4, 0))
        tk.Entry(dir_frame, textvariable=self._save_dir,
                 font=("Consolas", 8), bg="#F0EBF8", fg=C["text"],
                 relief="flat", bd=1, width=28,
                 insertbackground=C["accent"]).pack(side="left", fill="x", expand=True)
        tk.Button(dir_frame, text="...", command=self._browse_dir,
                  bg=C["accent_lt"], fg=C["text"], relief="flat", bd=0,
                  font=FONT, cursor="hand2", padx=6, pady=1,
                  activebackground=C["border"]).pack(side="left", padx=(4, 0))

        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", pady=8)

        # ── オプション ──
        tk.Checkbutton(self, text="Hide launcher while recording",
                       variable=self._hide_var,
                       bg=C["bg"], fg=C["text"], font=FONT,
                       activebackground=C["bg"], activeforeground=C["text"],
                       selectcolor=C["accent_lt"], relief="flat", bd=0,
                       ).pack(anchor="w", padx=14)

        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", pady=(8, 0))

        # ── ボタン & ステータス ──
        self._rec_btn = tk.Button(self, text="Start Recording",
                                  command=self._toggle_recording,
                                  bg=C["accent"], fg="white",
                                  relief="flat", bd=0, font=FONT_BOLD,
                                  cursor="hand2", padx=16, pady=8,
                                  activebackground=C["accent_dk"],
                                  activeforeground="white")
        self._rec_btn.pack(fill="x", padx=14, pady=12)

        self._status_var = tk.StringVar(value="Ready")
        tk.Label(self, textvariable=self._status_var,
                 bg=C["bg"], fg=C["text_sub"], font=FONT_SMALL,
                 anchor="center").pack(pady=(0, 10))

    def _browse_dir(self):
        d = filedialog.askdirectory(initialdir=self._save_dir.get(),
                                    title="Select save folder")
        if d:
            self._save_dir.set(d)

    def _toggle_recording(self):
        if self._recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        save_dir = Path(self._save_dir.get())
        if not save_dir.is_dir():
            messagebox.showwarning("Error", f"Save folder not found:\n{save_dir}", parent=self)
            return

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self._output_path = save_dir / f"recording_{ts}.avi"

        # キャプチャ範囲を決定（偶数サイズに切り捨て）
        idx = self._monitor_var.get()
        if idx == -1:
            self._bbox = None
        else:
            m = self._monitors[idx]
            self._bbox = (m["left"], m["top"], m["right"], m["bottom"])

        with self._lock:
            self._frames.clear()
        self._stop_event.clear()
        self._elapsed = 0
        self._recording = True

        self._rec_btn.configure(text="Stop Recording",
                                bg=C["btn_del_h"], activebackground=C["btn_del"])
        self._status_var.set("Recording...")

        if self._hide_var.get():
            self._parent.iconify()
            self.iconify()

        threading.Thread(target=self._capture_loop, daemon=True).start()
        self._tick_timer()

    def _capture_loop(self):
        fps      = self._fps_var.get()
        quality  = self._quality_var.get()
        interval = 1.0 / fps
        bbox     = self._bbox

        while not self._stop_event.is_set():
            t0 = time.monotonic()
            try:
                if bbox is None:
                    img = ImageGrab.grab(all_screens=True)
                else:
                    img = ImageGrab.grab(bbox=bbox, all_screens=True)
                # 偶数サイズに切り詰め（MJPEG で推奨）
                w = img.width  & ~1
                h = img.height & ~1
                if w != img.width or h != img.height:
                    img = img.crop((0, 0, w, h))

                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=quality, optimize=False)
                jpeg = buf.getvalue()

                with self._lock:
                    self._frames.append(jpeg)
                    count = len(self._frames)

                if count >= self.MAX_FRAMES:
                    self._stop_event.set()
                    break
            except Exception:
                pass

            wait = interval - (time.monotonic() - t0)
            if wait > 0:
                self._stop_event.wait(wait)

    def _tick_timer(self):
        if not self._recording:
            return
        self._elapsed += 1
        m, s = divmod(self._elapsed, 60)
        with self._lock:
            fc = len(self._frames)
        self._status_var.set(f"Recording...  {m:02d}:{s:02d}  ({fc} frames)")
        self._timer_id = self.after(1000, self._tick_timer)

    def _stop_recording(self):
        self._stop_event.set()
        if self._timer_id:
            self.after_cancel(self._timer_id)
            self._timer_id = None
        self._recording = False

        self._rec_btn.configure(text="Saving...", state="disabled")
        self._status_var.set("Saving AVI file...")

        if self._hide_var.get():
            self._parent.deiconify()
            self.deiconify()

        # 保存処理をバックグラウンドスレッドで実行（UI フリーズ防止）
        def _save():
            with self._lock:
                frames = list(self._frames)
            if frames:
                # キャプチャ範囲から幅・高さを取得（最初のフレームで判定）
                import struct as _s
                # JPEG SOF0 から幅高さを読む代わりに、直接 ImageGrab でサイズを取得
                # 最初のフレームを PIL で開いて幅高さを取得
                from PIL import Image
                sample = Image.open(io.BytesIO(frames[0]))
                w, h = sample.size
                sample.close()
                avi = _build_mjpeg_avi(frames, self._fps_var.get(), w, h)
                self._output_path.write_bytes(avi)
            self.after(0, self._on_save_done, len(frames))

        threading.Thread(target=_save, daemon=True).start()

    def _on_save_done(self, frame_count: int):
        self._rec_btn.configure(text="Start Recording",
                                bg=C["accent"], activebackground=C["accent_dk"],
                                state="normal")
        if frame_count == 0:
            self._status_var.set("No frames captured.")
            return
        self._status_var.set(f"Saved: {self._output_path.name}")
        subprocess.Popen(["explorer", str(self._output_path.parent)])

    def _on_close(self):
        if self._recording:
            if messagebox.askyesno("Stop Recording?",
                                   "Recording is in progress. Stop and close?",
                                   parent=self):
                self._stop_recording()
                # 保存完了後に自動で閉じるよう on_save_done をラップ
                orig = self._on_save_done
                def _close_after(fc, orig=orig):
                    orig(fc)
                    self.destroy()
                self._on_save_done = _close_after
        else:
            self.destroy()


# ── Screenshot window ─────────────────────────────────────

class ScreenshotWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent
        self.title("Screenshot")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.grab_set()

        self._monitors = _get_monitors()
        self._monitor_var = tk.IntVar(value=-1)   # -1 = all, 0,1,2... = individual
        self._save_dir = tk.StringVar(value=str(Path.home() / "Pictures"))
        self._hide_var = tk.BooleanVar(value=True)

        self._build()
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

    def _build(self):
        # ── Monitor selection ──
        tk.Label(self, text="Monitor", bg=C["bg"], fg=C["text"],
                 font=FONT_BOLD).pack(anchor="w", padx=14, pady=(14, 4))

        radio_frame = tk.Frame(self, bg=C["bg"])
        radio_frame.pack(fill="x", padx=14)

        radio_cfg = dict(bg=C["bg"], fg=C["text"], font=FONT,
                         activebackground=C["bg"], activeforeground=C["text"],
                         selectcolor=C["accent_lt"], relief="flat", bd=0)

        tk.Radiobutton(radio_frame, text="All screens",
                       variable=self._monitor_var, value=-1,
                       **radio_cfg).pack(anchor="w")

        for i, m in enumerate(self._monitors):
            label = f"Monitor {i + 1}   {m['width']}×{m['height']}"
            if m["left"] != 0 or m["top"] != 0:
                label += f"  ({m['left']:+d}, {m['top']:+d})"
            tk.Radiobutton(radio_frame, text=label,
                           variable=self._monitor_var, value=i,
                           **radio_cfg).pack(anchor="w")

        # separator
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", pady=8)

        # ── Save destination ──
        tk.Label(self, text="Save to", bg=C["bg"], fg=C["text"],
                 font=FONT_BOLD).pack(anchor="w", padx=14)

        dir_frame = tk.Frame(self, bg=C["bg"])
        dir_frame.pack(fill="x", padx=14, pady=(4, 0))

        tk.Entry(dir_frame, textvariable=self._save_dir,
                 font=("Consolas", 8), bg="#F0EBF8", fg=C["text"],
                 relief="flat", bd=1, width=28,
                 insertbackground=C["accent"]).pack(side="left", fill="x", expand=True)
        tk.Button(dir_frame, text="…",
                  command=self._browse_dir,
                  bg=C["accent_lt"], fg=C["text"],
                  relief="flat", bd=0, font=FONT,
                  cursor="hand2", padx=6, pady=1,
                  activebackground=C["border"]).pack(side="left", padx=(4, 0))

        # separator
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", pady=8)

        # ── Options ──
        tk.Checkbutton(self, text="Hide launcher before capture",
                       variable=self._hide_var,
                       bg=C["bg"], fg=C["text"], font=FONT,
                       activebackground=C["bg"], activeforeground=C["text"],
                       selectcolor=C["accent_lt"], relief="flat", bd=0,
                       ).pack(anchor="w", padx=14)

        # ── Capture button ──
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", pady=(8, 0))

        tk.Button(self, text="Capture",
                  command=self._capture,
                  bg=C["accent"], fg="white",
                  relief="flat", bd=0, font=FONT_BOLD,
                  cursor="hand2", padx=16, pady=8,
                  activebackground=C["accent_dk"], activeforeground="white",
                  ).pack(fill="x", padx=14, pady=12)

    def _browse_dir(self):
        d = filedialog.askdirectory(initialdir=self._save_dir.get(),
                                    title="Select save folder")
        if d:
            self._save_dir.set(d)

    def _capture(self):
        save_dir = Path(self._save_dir.get())
        if not save_dir.is_dir():
            messagebox.showwarning("Error", f"Save folder not found:\n{save_dir}", parent=self)
            return

        if self._hide_var.get():
            self._parent.iconify()
            self.withdraw()
            self.update()
            self.after(300, lambda: self._do_capture(save_dir))
        else:
            self._do_capture(save_dir)

    def _do_capture(self, save_dir: Path):
        idx = self._monitor_var.get()
        if idx == -1:
            img = ImageGrab.grab(all_screens=True)
        else:
            m = self._monitors[idx]
            img = ImageGrab.grab(bbox=(m["left"], m["top"], m["right"], m["bottom"]),
                                 all_screens=True)

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = "all" if idx == -1 else f"monitor{idx + 1}"
        filename = save_dir / f"screenshot_{suffix}_{ts}.png"
        img.save(filename)

        if self._hide_var.get():
            self._parent.deiconify()
            self.deiconify()

        subprocess.Popen(["explorer", str(save_dir)])


# ── Notification popup ────────────────────────────────────

_BG = "#FAF7FF"   # ポップアップ本体の背景（柔らかいラベンダーホワイト）


def _get_monitor_work_area(widget: tk.Misc) -> tuple[int, int, int, int]:
    """ウィジェットが表示されているモニタの作業領域 (left, top, right, bottom) を返す。
    タスクバーを除いた領域。取得失敗時はプライマリモニタのサイズにフォールバック。"""
    try:
        class _RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

        class _MONITORINFO(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.DWORD),
                        ("rcMonitor", _RECT), ("rcWork", _RECT),
                        ("dwFlags", wintypes.DWORD)]

        # ウィジェット中心座標でモニタを特定
        cx = widget.winfo_rootx() + widget.winfo_width() // 2
        cy = widget.winfo_rooty() + widget.winfo_height() // 2
        MONITOR_DEFAULTTONEAREST = 2
        monitor = ctypes.windll.user32.MonitorFromPoint(
            wintypes.POINT(cx, cy), MONITOR_DEFAULTTONEAREST
        )
        mi = _MONITORINFO()
        mi.cbSize = ctypes.sizeof(_MONITORINFO)
        ctypes.windll.user32.GetMonitorInfoW(monitor, ctypes.byref(mi))
        r = mi.rcWork
        return r.left, r.top, r.right, r.bottom
    except Exception:
        return 0, 0, widget.winfo_screenwidth(), widget.winfo_screenheight()

class NotificationPopup(tk.Toplevel):
    """右下フェードイン・プログレスバー付き通知ポップアップ"""

    FADE_MS    = 350    # フェードイン/アウト時間（ms）
    FADE_STEPS = 14     # フェードのステップ数

    def __init__(self, parent, task: dict, display_ms: int = 8000):
        super().__init__(parent)
        self._display_ms = display_ms
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)
        self.configure(bg=C["accent"])   # 外枠: アクセントカラー 2px

        # ── 残り時間を計算 ──
        sched_str = task.get("scheduled_at", "")
        try:
            sched      = datetime.datetime.fromisoformat(sched_str)
            delta_min  = int((sched - datetime.datetime.now()).total_seconds() / 60)
            time_str   = f"{sched.month}/{sched.day}  {sched.strftime('%H:%M')}"
            remain_str = f"in {delta_min} min"
        except (ValueError, TypeError):
            time_str   = sched_str
            remain_str = ""

        recurrence = task.get("recurrence", "none")
        recur_text = {"daily": "Daily", "weekly": "Weekly", "monthly": "Monthly"}.get(recurrence, "")

        # ── メインコンテナ（ボーダー 2px 分のパディング）──
        inner = tk.Frame(self, bg=_BG)
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        # ── ヘッダー帯 ──────────────────────────────────
        hdr = tk.Frame(inner, bg=C["accent_lt"])
        hdr.pack(fill="x")

        # 左：「通知」ラベル + 繰り返しバッジ
        hdr_l = tk.Frame(hdr, bg=C["accent_lt"])
        hdr_l.pack(side="left", padx=(10, 4), pady=(7, 5))
        tk.Label(hdr_l, text="Notify",
                 bg=C["accent_lt"], fg=C["accent_dk"],
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        if recur_text:
            tk.Label(hdr_l, text=recur_text,
                     bg=C["accent"], fg="white",
                     font=("Segoe UI", 7, "bold"),
                     padx=5, pady=1).pack(side="left", padx=(6, 0))

        # 右：装飾丸 3つ + 閉じるボタン
        hdr_r = tk.Frame(hdr, bg=C["accent_lt"])
        hdr_r.pack(side="right", padx=(0, 8), pady=6)

        # Claude ロゴ風の4頂点スター
        star_cv = tk.Canvas(hdr_r, bg=C["accent_lt"], width=14, height=14,
                            highlightthickness=0)
        star_cv.pack(side="left")
        star_cv.create_polygon(
            7, 1,  8, 6,  13, 7,  8, 8,  7, 13,  6, 8,  1, 7,  6, 6,
            fill=C["accent"], outline="",
        )

        close = tk.Label(hdr_r, text=" x ",
                         bg=C["accent_lt"], fg=C["accent_dk"],
                         font=("Segoe UI", 9, "bold"), cursor="hand2")
        close.pack(side="left", padx=(6, 0))
        close.bind("<Button-1>", lambda e: self.destroy())
        close.bind("<Enter>",    lambda e: close.configure(bg=C["accent"], fg="white"))
        close.bind("<Leave>",    lambda e: close.configure(bg=C["accent_lt"], fg=C["accent_dk"]))

        # ヘッダー下アクセント細線
        tk.Frame(inner, bg=C["accent"], height=1).pack(fill="x")

        # ── コンテンツ領域 ────────────────────────────────
        content = tk.Frame(inner, bg=_BG)
        content.pack(fill="both", expand=True, padx=14, pady=(10, 12))

        # タイトル
        title = task.get("title", "")
        tk.Label(content, text=title,
                 bg=_BG, fg=C["text"],
                 font=FONT_BOLD, anchor="w",
                 wraplength=240, justify="left").pack(fill="x", pady=(0, 6))

        # 日時ピル
        if time_str:
            pill = tk.Frame(content, bg=C["accent_lt"])
            pill.pack(anchor="w", pady=(0, 3))
            tk.Label(pill, text=time_str,
                     bg=C["accent_lt"], fg=C["accent_dk"],
                     font=FONT_SMALL, padx=8, pady=2).pack()

        # 残り時間
        if remain_str:
            tk.Label(content, text=remain_str,
                     bg=_BG, fg=C["accent"],
                     font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x")

        # 起動パス
        open_paths = task.get("open_paths", [])
        if not open_paths and task.get("open_path"):
            open_paths = [task["open_path"]]
        if open_paths:
            tk.Frame(content, bg=C["border"], height=1).pack(fill="x", pady=(6, 0))
            names = "  /  ".join(os.path.basename(p) or p for p in open_paths)
            tk.Label(content, text=f"Opens: {names}",
                     bg=_BG, fg=C["accent_dk"],
                     font=FONT_SMALL, anchor="w",
                     wraplength=240, justify="left").pack(fill="x", pady=(4, 0))

        # メモ
        notes = task.get("notes", "")
        if notes:
            tk.Frame(content, bg=C["border"], height=1).pack(fill="x", pady=(6, 0))
            tk.Label(content, text=notes,
                     bg=_BG, fg=C["text_sub"],
                     font=FONT_SMALL, anchor="w",
                     wraplength=240, justify="left").pack(fill="x", pady=(4, 0))

        # ── プログレスバー（底部、6px）──────────────────────
        self._pb = tk.Canvas(self, height=6, bg=C["accent_lt"],
                             highlightthickness=0)
        self._pb.pack(fill="x", side="bottom")

        # ── 配置（アプリが表示されているモニタの右下）────────────
        self.update_idletasks()
        w  = max(self.winfo_reqwidth(), 280)
        h  = max(self.winfo_reqheight(), 80)
        ml, mt, mr, mb = _get_monitor_work_area(parent)
        self.geometry(f"{w}x{h}+{mr - w - 20}+{mb - h - 12}")

        # クリックで閉じる
        for widget in (self, inner, content, hdr, hdr_l, hdr_r):
            widget.bind("<Button-1>", lambda e: self.destroy())

        # アニメーション開始
        self._start  = time.monotonic()
        self._pb_rect = None
        self._fade_in()

    def _fade_in(self):
        a = float(self.attributes("-alpha")) + 1.0 / self.FADE_STEPS
        self.attributes("-alpha", min(1.0, a))
        if a < 1.0:
            self.after(self.FADE_MS // self.FADE_STEPS, self._fade_in)
        else:
            self.attributes("-alpha", 1.0)
            pw = max(self._pb.winfo_width(), self.winfo_width())
            self._pb_rect = self._pb.create_rectangle(
                0, 0, pw, 6,
                fill=C["accent"], outline="",
            )
            self._tick_progress()

    def _tick_progress(self):
        if not self.winfo_exists():
            return
        elapsed = time.monotonic() - self._start - self.FADE_MS / 1000
        frac    = max(0.0, 1.0 - elapsed / (self._display_ms / 1000))
        pw      = max(self._pb.winfo_width(), self.winfo_width())
        self._pb.coords(self._pb_rect, 0, 0, int(pw * frac), 6)
        if frac > 0:
            self.after(50, self._tick_progress)
        else:
            self._fade_out()

    def _fade_out(self):
        a = float(self.attributes("-alpha")) - 1.0 / self.FADE_STEPS
        self.attributes("-alpha", max(0.0, a))
        if a > 0:
            self.after(self.FADE_MS // self.FADE_STEPS, self._fade_out)
        else:
            self.destroy()


# ── Notify item dialog ─────────────────────────────────────

class NotifyDialog(tk.Toplevel):
    """通知アイテムの追加/編集ダイアログ"""

    def __init__(self, parent, initial: dict | None = None):
        super().__init__(parent)
        self.title("Add Notification" if initial is None else "Edit Notification")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.result: dict | None = None

        d = initial or {}
        self._title_var     = tk.StringVar(value=d.get("title", ""))
        self._notify_var    = tk.IntVar(value=d.get("notify_before", 5))
        self._recur_var     = tk.StringVar(value=d.get("recurrence", "none"))
        # open_paths: 新形式リスト。旧形式 open_path 文字列も移行
        _op = d.get("open_paths", [])
        if not _op and d.get("open_path"):
            _op = [d["open_path"]]
        self._open_paths_list: list = list(_op)
        self._notes_init    = d.get("notes", "")

        # 既存の scheduled_at を分解してスピンボックス初期値に設定
        now = datetime.datetime.now()
        sched_str = d.get("scheduled_at", "")
        try:
            _dt = datetime.datetime.fromisoformat(sched_str)
        except ValueError:
            _dt = now
        self._sc_year  = tk.IntVar(value=_dt.year)
        self._sc_month = tk.IntVar(value=_dt.month)
        self._sc_day   = tk.IntVar(value=_dt.day)
        self._sc_hour  = tk.IntVar(value=_dt.hour)
        self._sc_min   = tk.IntVar(value=_dt.minute)

        self._build()
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")
        self.wait_window()

    def _row(self, label: str, row: int, var: tk.StringVar, width: int = 24):
        tk.Label(self._form, text=label, bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="e", width=9).grid(
                     row=row, column=0, padx=(12, 4), pady=3, sticky="e")
        e = tk.Entry(self._form, textvariable=var, font=FONT,
                     bg="#F0EBF8", fg=C["text"], relief="flat", bd=1,
                     insertbackground=C["accent"], width=width)
        e.grid(row=row, column=1, padx=(0, 12), pady=3, sticky="ew")
        return e

    def _build(self):
        self._form = tk.Frame(self, bg=C["bg"])
        self._form.pack(padx=4, pady=(12, 4))

        self._row("Title", 0, self._title_var)

        # scheduled input (スピンボックス分割)
        tk.Label(self._form, text="Scheduled", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="e", width=9).grid(
                     row=1, column=0, padx=(12, 4), pady=3, sticky="e")
        sc_frame = tk.Frame(self._form, bg=C["bg"])
        sc_frame.grid(row=1, column=1, padx=(0, 12), pady=3, sticky="ew")

        _spin_cfg = dict(font=FONT, bg="#F0EBF8", fg=C["text"], relief="flat", bd=1,
                         buttonbackground=C["accent_lt"], insertbackground=C["accent"],
                         wrap=True)

        def _lbl(text):
            return tk.Label(sc_frame, text=text, bg=C["bg"], fg=C["text_sub"], font=FONT_SMALL)

        tk.Spinbox(sc_frame, textvariable=self._sc_year,
                   from_=2020, to=2099, width=5, **_spin_cfg).pack(side="left")
        _lbl("/").pack(side="left")
        tk.Spinbox(sc_frame, textvariable=self._sc_month,
                   from_=1, to=12, width=3, **_spin_cfg).pack(side="left")
        _lbl("/").pack(side="left")
        tk.Spinbox(sc_frame, textvariable=self._sc_day,
                   from_=1, to=31, width=3, **_spin_cfg).pack(side="left")
        _lbl("  ").pack(side="left")
        tk.Spinbox(sc_frame, textvariable=self._sc_hour,
                   from_=0, to=23, width=3, **_spin_cfg).pack(side="left")
        _lbl(":").pack(side="left")
        tk.Spinbox(sc_frame, textvariable=self._sc_min,
                   from_=0, to=59, width=3, **_spin_cfg).pack(side="left")

        # notify before (minutes)
        tk.Label(self._form, text="Notify", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="e", width=9).grid(
                     row=2, column=0, padx=(12, 4), pady=3, sticky="e")
        ntf_frame = tk.Frame(self._form, bg=C["bg"])
        ntf_frame.grid(row=2, column=1, padx=(0, 12), pady=3, sticky="ew")
        tk.Spinbox(ntf_frame, textvariable=self._notify_var,
                   from_=1, to=60, width=5, font=FONT,
                   bg="#F0EBF8", fg=C["text"], relief="flat", bd=1,
                   buttonbackground=C["accent_lt"],
                   insertbackground=C["accent"]).pack(side="left")
        tk.Label(ntf_frame, text="minutes before",
                 bg=C["bg"], fg=C["text_sub"], font=FONT_SMALL).pack(side="left", padx=(6, 0))

        # recurrence
        tk.Label(self._form, text="Recurrence", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="e", width=9).grid(
                     row=3, column=0, padx=(12, 4), pady=3, sticky="e")
        recur_cb = ttk.Combobox(
            self._form, textvariable=self._recur_var,
            values=["none", "daily", "weekly", "monthly"],
            state="readonly", width=12, font=FONT,
        )
        recur_cb.grid(row=3, column=1, padx=(0, 12), pady=3, sticky="w")

        # open paths (複数)
        tk.Label(self._form, text="Open", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="ne", width=9).grid(
                     row=4, column=0, padx=(12, 4), pady=3, sticky="ne")
        open_outer = tk.Frame(self._form, bg=C["bg"])
        open_outer.grid(row=4, column=1, padx=(0, 12), pady=3, sticky="ew")

        lb_frame = tk.Frame(open_outer, bg=C["bg"])
        lb_frame.pack(side="left", fill="both", expand=True)
        self._paths_lb = tk.Listbox(
            lb_frame, height=3, font=FONT_SMALL,
            bg="#F0EBF8", fg=C["text"], selectbackground=C["accent_lt"],
            selectforeground=C["accent_dk"], relief="flat", bd=1,
            activestyle="none",
        )
        self._paths_lb.pack(side="left", fill="both", expand=True)
        _sb = tk.Scrollbar(lb_frame, orient="vertical",
                           command=self._paths_lb.yview)
        _sb.pack(side="right", fill="y")
        self._paths_lb.configure(yscrollcommand=_sb.set)
        for p in self._open_paths_list:
            self._paths_lb.insert("end", os.path.basename(p) or p)

        _btn_cfg = dict(bg=C["accent_lt"], fg=C["text"], relief="flat", bd=0,
                        font=FONT_SMALL, cursor="hand2", padx=5,
                        activebackground=C["border"])
        btn_col = tk.Frame(open_outer, bg=C["bg"])
        btn_col.pack(side="left", padx=(4, 0))
        tk.Button(btn_col, text="+ File",   command=self._add_open_file,   **_btn_cfg).pack(fill="x", pady=(0, 2))
        tk.Button(btn_col, text="+ Folder", command=self._add_open_folder, **_btn_cfg).pack(fill="x", pady=(0, 2))
        tk.Button(btn_col, text="Remove",   command=self._remove_open_path,**_btn_cfg).pack(fill="x")

        # notes (multi-line)
        tk.Label(self._form, text="Notes", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="ne", width=9).grid(
                     row=5, column=0, padx=(12, 4), pady=(6, 3), sticky="ne")
        self._notes_text = tk.Text(
            self._form, font=FONT,
            bg="#F0EBF8", fg=C["text"], relief="flat", bd=1,
            insertbackground=C["accent"],
            width=26, height=3, wrap="word",
        )
        self._notes_text.insert("1.0", self._notes_init)
        self._notes_text.grid(row=5, column=1, padx=(0, 12), pady=(6, 3), sticky="ew")

        btn_frame = tk.Frame(self, bg=C["bg"])
        btn_frame.pack(fill="x", padx=16, pady=(4, 14))
        tk.Button(btn_frame, text="Save", command=self._ok,
                  bg=C["accent"], fg="white", relief="flat", bd=0,
                  font=FONT_BOLD, cursor="hand2", padx=16, pady=4,
                  activebackground=C["accent_dk"], activeforeground="white",
                  ).pack(side="right", padx=(4, 0))
        tk.Button(btn_frame, text="Cancel", command=self.destroy,
                  bg=C["accent_lt"], fg=C["text"], relief="flat", bd=0,
                  font=FONT, cursor="hand2", padx=10, pady=4,
                  activebackground=C["border"], activeforeground=C["text"],
                  ).pack(side="right")

    def _add_open_file(self):
        path = filedialog.askopenfilename(title="Select file or application", parent=self)
        if path:
            path = os.path.normpath(path)
            self._open_paths_list.append(path)
            self._paths_lb.insert("end", os.path.basename(path) or path)

    def _add_open_folder(self):
        path = filedialog.askdirectory(title="Select folder", parent=self)
        if path:
            path = os.path.normpath(path)
            self._open_paths_list.append(path)
            self._paths_lb.insert("end", os.path.basename(path) or path)

    def _remove_open_path(self):
        sel = self._paths_lb.curselection()
        if sel:
            idx = sel[0]
            self._paths_lb.delete(idx)
            self._open_paths_list.pop(idx)

    def _ok(self):
        title = self._title_var.get().strip()
        if not title:
            messagebox.showwarning("Input Error", "Title is required.", parent=self)
            return
        try:
            dt = datetime.datetime(
                self._sc_year.get(), self._sc_month.get(), self._sc_day.get(),
                self._sc_hour.get(), self._sc_min.get(),
            )
        except ValueError as e:
            messagebox.showwarning("Input Error", f"Invalid date/time:\n{e}", parent=self)
            return
        self.result = {
            "title":         title,
            "scheduled_at":  dt.strftime("%Y-%m-%d %H:%M"),
            "notify_before": self._notify_var.get(),
            "recurrence":    self._recur_var.get(),
            "open_paths":    list(self._open_paths_list),
            "notes":         self._notes_text.get("1.0", "end").strip(),
        }
        self.destroy()


# ── Text input dialog ─────────────────────────────────────

class InputDialog(tk.Toplevel):
    def __init__(self, parent, title: str, label: str, default: str = ""):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.result: str | None = None

        tk.Label(self, text=label, bg=C["bg"], fg=C["text"],
                 font=FONT_BOLD).pack(anchor="w", padx=16, pady=(14, 4))

        self._var = tk.StringVar(value=default)
        entry = tk.Entry(self, textvariable=self._var,
                         font=FONT, bg="#F0EBF8", fg=C["text"],
                         relief="flat", bd=1,
                         insertbackground=C["accent"], width=28)
        entry.pack(padx=16, pady=(0, 10), fill="x")
        entry.select_range(0, "end")
        entry.focus_set()
        entry.bind("<Return>", lambda e: self._ok())
        entry.bind("<Escape>", lambda e: self._cancel())

        btn_frame = tk.Frame(self, bg=C["bg"])
        btn_frame.pack(fill="x", padx=16, pady=(0, 14))

        tk.Button(btn_frame, text="OK", command=self._ok,
                  bg=C["accent"], fg="white", relief="flat", bd=0,
                  font=FONT_BOLD, cursor="hand2", padx=16, pady=4,
                  activebackground=C["accent_dk"], activeforeground="white",
                  ).pack(side="right", padx=(4, 0))
        tk.Button(btn_frame, text="Cancel", command=self._cancel,
                  bg=C["accent_lt"], fg=C["text"], relief="flat", bd=0,
                  font=FONT, cursor="hand2", padx=10, pady=4,
                  activebackground=C["border"], activeforeground=C["text"],
                  ).pack(side="right")

        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")
        self.wait_window()

    def _ok(self):
        v = self._var.get().strip()
        if v:
            self.result = v
        self.destroy()

    def _cancel(self):
        self.destroy()


# ── Main application ──────────────────────────────────────

class FolderLauncher(tk.Tk):
    # _active >= 0  : folder category index
    # _active == -1 : Terminal tab

    # Ping モニター定数
    _PING_HISTORY = 30   # 棒グラフで保持する件数
    _PING_BAR_W   = 16   # バー幅 (px)
    _PING_BAR_GAP = 2    # バー間隔 (px)
    _PING_ROW_H   = 80   # ホスト行の高さ (px)
    _PING_MAX_MS  = 500  # グラフ縦軸上限 (ms)

    def __init__(self):
        super().__init__()
        self.title("Gem")
        self.geometry("480x400")
        self.resizable(True, True)
        self.configure(bg=C["bg"])
        self.minsize(320, 260)

        # 全設定を config.json から一括読み込み（テーマ決定が先）
        self._data: list[dict] = []
        self._conns: list[dict] = []
        self._tasks: list[dict] = []
        self._notify_items: list[dict] = []
        self._terminal_groups: list[str] = []
        self._selected_group: str | None = None   # None = All
        self._bookmarks: list[dict] = []
        self._bm_selected: int = 0
        self._active: int = 0   # -1=Terminal, -2=Tasks, -3=Notify, -4=Web, -5=Clip, -6=Ping
        self._theme: str = "lavender"   # _load_config() で上書きされる
        self._tick_id = None             # _tick() の after ID（再構築時のキャンセル用）
        self._clip_history: list[dict] = []   # {"text": str, "ts": str}
        self._clip_prev: str = ""             # 前回クリップボード値（変化検知用）
        self._ping_hosts: list[str] = []
        self._ping_data:  dict[str, list] = {}   # host -> [ms|None, ...]
        self._ping_interval: int = 5
        self._ping_running: bool = False
        self._ping_lock = threading.Lock()
        self._ping_next_id  = None   # 次の ping ラウンドの after ID
        self._ping_graph_id = None   # グラフ更新ループの after ID
        self._ping_canvases:   dict[str, tk.Canvas] = {}
        self._ping_stat_vars:  dict[str, tk.StringVar] = {}
        self._load_config()

        # テーマ確定後にアイコンを生成
        palette = ICON_PALETTES.get(self._theme)
        self._icon = tk.PhotoImage(data=_make_icon_png(palette))
        _setup_taskbar_icon(self, palette)
        self._task_sort: dict = {"col": None, "reverse": False}
        self._conn_sort: dict = {"col": None, "reverse": False}
        self._conn_search = tk.StringVar()
        self._conn_search.trace_add(
            "write",
            lambda *_: self._render_list() if self._active == -1 else None,
        )

        self._notified: set[str] = set()  # 通知済みキー管理
        self._notify_past_open: bool = False  # 過去通知セクションの開閉状態

        self._build_ui()
        self._render_tabs()
        self._render_list()
        self._check_schedule()
        self._check_clipboard()

    # ── 設定読み書き（config.json に統合）─────────────────

    def _load_config(self):
        migrated = False
        if not CONFIG_FILE.exists():
            # 旧形式の個別ファイルがあれば自動マイグレーション
            old_folders   = Path(__file__).parent / "folders.json"
            old_terminals = Path(__file__).parent / "terminals.json"
            old_tasks     = Path(__file__).parent / "tasks.json"
            cfg = {}
            if old_folders.exists():
                try:
                    cfg["folders"] = json.loads(old_folders.read_text(encoding="utf-8"))
                except Exception:
                    pass
            if old_terminals.exists():
                try:
                    cfg["terminals"] = json.loads(old_terminals.read_text(encoding="utf-8"))
                except Exception:
                    pass
            if old_tasks.exists():
                try:
                    cfg["tasks"] = json.loads(old_tasks.read_text(encoding="utf-8"))
                except Exception:
                    pass
            if not cfg:
                self._data = [{"category": "General", "folders": []}]
                self._banner_enabled_cfg = True
                self._notify_display_sec_cfg = 8
                return
            migrated = True  # マイグレーション成功
        else:
            try:
                cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            except Exception:
                cfg = {}

        # フォルダ設定（旧形式の自動変換）
        raw = cfg.get("folders", [])
        if raw and isinstance(raw[0], (str, dict)) and "category" not in raw[0]:
            folders = []
            for item in raw:
                if isinstance(item, str):
                    folders.append({"name": os.path.basename(item) or item, "path": item})
                else:
                    folders.append(item)
            self._data = [{"category": "General", "folders": folders}]
        else:
            self._data = raw or [{"category": "General", "folders": []}]

        if not self._data:
            self._data = [{"category": "General", "folders": []}]

        # ターミナル接続設定
        self._conns = cfg.get("terminals", [])
        self._terminal_groups = cfg.get("terminal_groups", [])
        self._bookmarks = cfg.get("bookmarks", [])

        # タスクデータ
        self._tasks = cfg.get("tasks", [])

        # 通知アイテム
        self._notify_items = cfg.get("notifications", [])

        # クリップボード履歴
        self._clip_history = cfg.get("clipboard_history", [])

        # Ping モニター
        self._ping_hosts    = cfg.get("ping_hosts", [])
        self._ping_interval = cfg.get("ping_interval", 5)

        # バナー表示設定
        self._banner_enabled_cfg: bool = cfg.get("banner_enabled", True)
        self._notify_display_sec_cfg: int = cfg.get("notify_display_sec", 8)

        # テーマ設定
        self._theme = cfg.get("theme", "lavender")
        C.update(THEMES.get(self._theme, THEMES["lavender"]))

        # 旧ファイルからのマイグレーション時は config.json に保存
        if migrated:
            self._save_config()

    def _save_config(self):
        cfg = {
            "folders":         self._data,
            "terminals":       self._conns,
            "terminal_groups": self._terminal_groups,
            "bookmarks":       self._bookmarks,
            "tasks":           self._tasks,
            "notifications":   self._notify_items,
            "banner_enabled":      self._banner_enabled.get() if hasattr(self, "_banner_enabled") else True,
            "notify_display_sec":  self._notify_display_sec.get() if hasattr(self, "_notify_display_sec") else 8,
            "theme":           self._theme,
            "clipboard_history": self._clip_history,
            "ping_hosts":    self._ping_hosts,
            "ping_interval": self._ping_interval,
        }
        CONFIG_FILE.write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _save(self):
        self._save_config()

    def _save_conns(self):
        self._save_config()

    def _save_tasks(self):
        self._save_config()

    def _save_notify(self):
        self._save_config()

    @property
    def _current(self) -> dict:
        return self._data[self._active]

    # ── UI construction ───────────────────────────────────

    def _build_ui(self):
        # header
        hdr = tk.Frame(self, bg=C["accent"], height=30)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Gem",
                 bg=C["accent"], fg="white", font=FONT_BOLD,
                 ).pack(side="left", padx=8, pady=4)

        self._clock_var = tk.StringVar()
        tk.Label(hdr, textvariable=self._clock_var,
                 bg=C["accent"], fg=C["accent_lt"],
                 font=("Consolas", 9)).pack(side="left", padx=6)

        # バナー通知ラベル（時計の右）
        self._banner_lbl = tk.Label(
            hdr, text="",
            bg=C["accent_dk"], fg="white",
            font=FONT_SMALL, padx=8, pady=0, anchor="w",
        )
        self._banner_lbl.pack(side="left", padx=(4, 0))

        # Banner トグル（_tick() より先に作成する）
        self._banner_enabled = tk.BooleanVar(value=self._banner_enabled_cfg)
        self._banner_enabled.trace_add("write", lambda *_: (self._update_banner(), self._save_config()))
        self._notify_display_sec = tk.IntVar(value=self._notify_display_sec_cfg)
        self._notify_display_sec.trace_add("write", lambda *_: self._save_config())

        self._tick()
        def _toggle_banner():
            self._banner_enabled.set(not self._banner_enabled.get())
            _banner_btn.configure(
                text="Banner ✓" if self._banner_enabled.get() else "Banner",
                bg=C["accent_dk"] if self._banner_enabled.get() else C["accent"],
            )
        _banner_btn = tk.Button(
            hdr, text="Banner ✓" if self._banner_enabled_cfg else "Banner",
            command=_toggle_banner,
            bg=C["accent_dk"] if self._banner_enabled_cfg else C["accent"],
            fg="white", relief="flat", bd=0, font=FONT_SMALL,
            activebackground=C["accent_lt"], activeforeground=C["text"],
            cursor="hand2",
        )
        _banner_btn.pack(side="right", padx=(0, 2))

        # 通知表示時間 Spinbox
        _sec_frame = tk.Frame(hdr, bg=C["accent"])
        _sec_frame.pack(side="right", padx=(0, 4))
        tk.Label(_sec_frame, text="Notify sec",
                 bg=C["accent"], fg=C["accent_lt"],
                 font=FONT_SMALL).pack(side="left")
        tk.Spinbox(_sec_frame, textvariable=self._notify_display_sec,
                   from_=3, to=60, width=3,
                   bg=C["accent_dk"], fg="white",
                   relief="flat", bd=0, font=FONT_SMALL,
                   buttonbackground=C["accent_dk"],
                   ).pack(side="left", padx=(2, 0))

        tk.Button(hdr, text="Screenshot",
                  command=self._open_screenshot,
                  bg=C["accent_dk"], fg="white", relief="flat", bd=0,
                  font=FONT, cursor="hand2",
                  activebackground=C["accent_lt"], activeforeground=C["text"],
                  padx=8, pady=1).pack(side="right", padx=(0, 6))

        tk.Button(hdr, text="Record",
                  command=self._open_recording,
                  bg=C["accent_dk"], fg="white", relief="flat", bd=0,
                  font=FONT, cursor="hand2",
                  activebackground=C["accent_lt"], activeforeground=C["text"],
                  padx=8, pady=1).pack(side="right", padx=(0, 2))

        self._theme_btn = tk.Button(
            hdr, text="Theme", font=FONT_SMALL,
            bg=C["accent_dk"], fg=C["tab_act"],
            activebackground=C["accent"], activeforeground=C["tab_act"],
            relief="flat", cursor="hand2", bd=0,
            command=self._show_theme_menu,
        )
        self._theme_btn.pack(side="right", padx=(0, 4), pady=3)

        self._show_options = tk.BooleanVar(value=False)
        tk.Checkbutton(hdr, text="Options",
                       variable=self._show_options,
                       bg=C["accent"], fg="white",
                       activebackground=C["accent"], activeforeground="white",
                       selectcolor=C["accent_dk"],
                       relief="flat", bd=0, font=FONT_SMALL,
                       ).pack(side="right", padx=(0, 2))

        # tab bar
        self._tab_bar = tk.Frame(self, bg=C["tab_inact"])
        self._tab_bar.pack(fill="x")

        # scrollable list
        wrapper = tk.Frame(self, bg=C["bg"])
        wrapper.pack(fill="both", expand=True, padx=4, pady=3)

        canvas = tk.Canvas(wrapper, bg=C["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(wrapper, orient="vertical", command=canvas.yview)
        self._list_frame = tk.Frame(canvas, bg=C["bg"])
        self._list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        _win_id = canvas.create_window((0, 0), window=self._list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        # sync _list_frame width with canvas width on resize
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfigure(_win_id, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))
        self._canvas = canvas

        # footer (buttons are reused on tab switch)
        self._footer = tk.Frame(self, bg=C["bg"], pady=3)
        self._footer.pack(fill="x", padx=4)
        self._footer_btn = tk.Button(
            self._footer, text="+ Add Folder",
            command=self._add_folder,
            bg=C["accent"], fg="white", relief="flat", bd=0,
            font=FONT_BOLD, cursor="hand2", padx=12, pady=4,
            activebackground=C["accent_dk"], activeforeground="white",
        )
        self._footer_btn.pack(side="left", fill="x", expand=True)
        _hover(self._footer_btn, C["accent_dk"], C["accent"])

        # フォルダタブ専用の「+ Add File」ボタン
        self._footer_btn2 = tk.Button(
            self._footer, text="+ Add File",
            command=self._add_file,
            bg=C["accent_lt"], fg=C["text"], relief="flat", bd=0,
            font=FONT_BOLD, cursor="hand2", padx=12, pady=4,
            activebackground=C["border"], activeforeground=C["text"],
        )
        self._footer_btn2.pack(side="left", fill="x", expand=True, padx=(2, 0))
        _hover(self._footer_btn2, C["border"], C["accent_lt"])

        # Tasksタブ専用の「Export」ボタン
        self._footer_btn3 = tk.Button(
            self._footer, text="Export",
            command=self._export_tasks,
            bg=C["accent_lt"], fg=C["text"], relief="flat", bd=0,
            font=FONT_BOLD, cursor="hand2", padx=12, pady=4,
            activebackground=C["border"], activeforeground=C["text"],
        )
        _hover(self._footer_btn3, C["border"], C["accent_lt"])

    # ── Tab bar ───────────────────────────────────────────

    def _render_tabs(self):
        for w in self._tab_bar.winfo_children():
            w.destroy()

        # category tabs (left side)
        for i, cat in enumerate(self._data):
            is_active = (i == self._active)
            btn = tk.Button(
                self._tab_bar,
                text=cat["category"],
                command=lambda i=i: self._switch_tab(i),
                bg=C["tab_act"] if is_active else C["tab_inact"],
                fg=C["text"] if is_active else C["text_sub"],
                relief="flat", bd=0,
                font=FONT_BOLD if is_active else FONT,
                cursor="hand2", padx=10, pady=3,
                activebackground=C["tab_act"],
                activeforeground=C["text"],
            )
            btn.pack(side="left")
            # right-click for category actions
            btn.bind("<Button-3>", lambda e, i=i: self._tab_context_menu(e, i))

        # '+' category add button
        tk.Button(
            self._tab_bar, text=" + ",
            command=self._add_category,
            bg=C["tab_inact"], fg=C["text_sub"],
            relief="flat", bd=0,
            font=FONT, cursor="hand2", padx=4, pady=3,
            activebackground=C["accent_lt"],
            activeforeground=C["text"],
        ).pack(side="left", padx=(2, 0))

        # separator (spacer)
        tk.Frame(self._tab_bar, bg=C["tab_inact"]).pack(side="left", fill="x", expand=True)

        # Terminal tab (rightmost, fixed)
        is_term = (self._active == -1)
        term_btn = tk.Button(
            self._tab_bar,
            text="Terminal",
            command=lambda: self._switch_tab(-1),
            bg=C["tab_act"] if is_term else C["tab_inact"],
            fg=C["text"] if is_term else C["text_sub"],
            relief="flat", bd=0,
            font=FONT_BOLD if is_term else FONT,
            cursor="hand2", padx=10, pady=5,
            activebackground=C["tab_act"],
            activeforeground=C["text"],
        )
        term_btn.pack(side="right")

        # Tasks tab (left of Terminal, fixed)
        is_tasks = (self._active == -2)
        tasks_btn = tk.Button(
            self._tab_bar,
            text="Tasks",
            command=lambda: self._switch_tab(-2),
            bg=C["tab_act"] if is_tasks else C["tab_inact"],
            fg=C["text"] if is_tasks else C["text_sub"],
            relief="flat", bd=0,
            font=FONT_BOLD if is_tasks else FONT,
            cursor="hand2", padx=10, pady=5,
            activebackground=C["tab_act"],
            activeforeground=C["text"],
        )
        tasks_btn.pack(side="right")

        # Notify tab (left of Tasks, fixed)
        is_notify = (self._active == -3)
        notify_btn = tk.Button(
            self._tab_bar,
            text="Notify",
            command=lambda: self._switch_tab(-3),
            bg=C["tab_act"] if is_notify else C["tab_inact"],
            fg=C["text"] if is_notify else C["text_sub"],
            relief="flat", bd=0,
            font=FONT_BOLD if is_notify else FONT,
            cursor="hand2", padx=10, pady=5,
            activebackground=C["tab_act"],
            activeforeground=C["text"],
        )
        notify_btn.pack(side="right")

        # Web tab (left of Notify, fixed)
        is_web = (self._active == -4)
        web_btn = tk.Button(
            self._tab_bar,
            text="Web",
            command=lambda: self._switch_tab(-4),
            bg=C["tab_act"] if is_web else C["tab_inact"],
            fg=C["text"] if is_web else C["text_sub"],
            relief="flat", bd=0,
            font=FONT_BOLD if is_web else FONT,
            cursor="hand2", padx=10, pady=5,
            activebackground=C["tab_act"],
            activeforeground=C["text"],
        )
        web_btn.pack(side="right")

        # Clip tab (left of Web, fixed)
        is_clip = (self._active == -5)
        clip_count = len(self._clip_history)
        clip_label = f"Clip ({clip_count})" if clip_count else "Clip"
        tk.Button(
            self._tab_bar,
            text=clip_label,
            command=lambda: self._switch_tab(-5),
            bg=C["tab_act"] if is_clip else C["tab_inact"],
            fg=C["text"] if is_clip else C["text_sub"],
            relief="flat", bd=0,
            font=FONT_BOLD if is_clip else FONT,
            cursor="hand2", padx=10, pady=5,
            activebackground=C["tab_act"],
            activeforeground=C["text"],
        ).pack(side="right")

        # Ping tab (left of Clip, fixed)
        is_ping = (self._active == -6)
        tk.Button(
            self._tab_bar,
            text="Ping",
            command=lambda: self._switch_tab(-6),
            bg=C["tab_act"] if is_ping else C["tab_inact"],
            fg=C["text"] if is_ping else C["text_sub"],
            relief="flat", bd=0,
            font=FONT_BOLD if is_ping else FONT,
            cursor="hand2", padx=10, pady=5,
            activebackground=C["tab_act"],
            activeforeground=C["text"],
        ).pack(side="right")

    def _switch_tab(self, idx: int):
        # Pingタブを離れるときはモニターを停止する
        if self._active == -6 and idx != -6:
            self._ping_stop()
        self._active = idx
        self._render_tabs()
        self._update_footer()
        self._render_list()
        # Pingタブに入ったときはモニターを開始する
        if idx == -6:
            self._ping_start()

    def _update_footer(self):
        """Update footer button text/command based on active tab."""
        self._footer_btn3.pack_forget()
        if self._active == -1:
            self._footer_btn.configure(text="+ Add Connection", command=self._add_conn)
            self._footer_btn2.pack_forget()
        elif self._active == -2:
            self._footer_btn.configure(text="+ Add Task", command=self._add_task)
            self._footer_btn2.configure(text="Gantt", command=self._open_gantt)
            self._footer_btn2.pack(side="left", fill="x", expand=True, padx=(2, 0))
            self._footer_btn3.pack(side="left", fill="x", expand=True, padx=(2, 0))
        elif self._active == -3:
            self._footer_btn.configure(text="+ Add Notification", command=self._add_notify_item)
            self._footer_btn2.pack_forget()
        elif self._active == -4:
            self._footer_btn.configure(text="+ Add Bookmark", command=self._add_bookmark)
            self._footer_btn2.configure(text="+ Add Category", command=self._add_bm_category)
            self._footer_btn2.pack(side="left", fill="x", expand=True, padx=(2, 0))
        elif self._active == -5:
            self._footer_btn.configure(text="Clear All", command=self._clear_clip_history)
            self._footer_btn2.pack_forget()
        elif self._active == -6:
            self._footer_btn.configure(text="+ Add Host", command=self._ping_add_host)
            self._footer_btn2.pack_forget()
        else:
            self._footer_btn.configure(text="+ Add Folder", command=self._add_folder)
            self._footer_btn2.configure(text="+ Add File", command=self._add_file)
            self._footer_btn2.pack(side="left", fill="x", expand=True, padx=(2, 0))

    def _tab_context_menu(self, event, idx: int):
        menu = tk.Menu(self, tearoff=0,
                       bg=C["card"], fg=C["text"],
                       activebackground=C["card_h"],
                       activeforeground=C["text"],
                       relief="flat", font=FONT)
        menu.add_command(label="Rename",
                         command=lambda: self._rename_category(idx))
        menu.add_command(label="Delete",
                         command=lambda: self._delete_category(idx))
        menu.tk_popup(event.x_root, event.y_root)

    # ── Category operations ───────────────────────────────

    def _add_category(self):
        dlg = InputDialog(self, "Add Category", "Category name:")
        if dlg.result is None:
            return
        self._data.append({"category": dlg.result, "folders": []})
        self._active = len(self._data) - 1
        self._save()
        self._render_tabs()
        self._update_footer()
        self._render_list()

    def _rename_category(self, idx: int):
        dlg = InputDialog(self, "Rename Category", "New name:",
                          default=self._data[idx]["category"])
        if dlg.result is None:
            return
        self._data[idx]["category"] = dlg.result
        self._save()
        self._render_tabs()

    def _delete_category(self, idx: int):
        name = self._data[idx]["category"]
        if not messagebox.askyesno("Delete Category",
                                   f"Delete category \"{name}\" and all its folders?",
                                   parent=self):
            return
        self._data.pop(idx)
        if not self._data:
            self._data = [{"category": "General", "folders": []}]
        self._active = min(self._active, len(self._data) - 1)
        self._save()
        self._render_tabs()
        self._render_list()

    # ── List render (folder/terminal/task/notify switch) ───

    def _render_list(self):
        for w in self._list_frame.winfo_children():
            w.destroy()

        if self._active == -1:
            self._render_terminal_list()
        elif self._active == -2:
            self._render_task_list()
        elif self._active == -3:
            self._render_notify_list()
        elif self._active == -4:
            self._render_bookmark_list()
        elif self._active == -5:
            self._render_clip_list()
        elif self._active == -6:
            self._render_ping_list()
        else:
            self._render_folder_list()

    # ── Folder list ───────────────────────────────────────

    def _render_folder_list(self):
        folders = self._current["folders"]
        if not folders:
            tk.Label(
                self._list_frame,
                text="No folders registered.\nClick \"+ Add Folder\" to add one.",
                bg=C["bg"], fg=C["text_sub"],
                font=FONT_SMALL, justify="center",
            ).pack(pady=20)
            return

        for i, entry in enumerate(folders):
            self._make_card(i, entry["name"], entry["path"],
                            entry.get("type", "folder"))

    def _make_card(self, idx: int, name: str, path: str, item_type: str = "folder"):
        card = tk.Frame(self._list_frame, bg=C["card"],
                        pady=4, padx=8, relief="flat", bd=0,
                        highlightthickness=1, highlightbackground=C["border"])
        card.pack(fill="x", pady=2, padx=2)

        left = tk.Frame(card, bg=C["card"])
        left.pack(side="left", fill="both", expand=True)

        type_tag = "[F] " if item_type == "file" else ""
        tk.Label(left, text=f"{type_tag}{name}",
                 bg=C["card"], fg=C["text"],
                 font=FONT_BOLD, anchor="w").pack(fill="x")

        del_btn = tk.Button(
            card, text="✕",
            command=lambda i=idx: self._remove_folder(i),
            bg=C["card"], fg=C["btn_del"],
            relief="flat", bd=0,
            font=("Segoe UI", 11), cursor="hand2",
            activebackground=C["card"], activeforeground=C["btn_del_h"],
        )
        del_btn.pack(side="right", padx=(6, 0))

        edit_btn = tk.Button(
            card, text="Edit",
            command=lambda i=idx, n=name, p=path: self._edit_folder(i, n, p),
            bg=C["card"], fg=C["text_sub"],
            relief="flat", bd=0,
            font=FONT_SMALL, cursor="hand2",
            activebackground=C["card"], activeforeground=C["text"],
        )
        edit_btn.pack(side="right", padx=(0, 2))

        def _show_ctx(e):
            self._card_context_menu(e, idx, name, path)

        def _bind_open(w):
            if w in (del_btn, edit_btn):
                return
            w.bind("<Button-1>", lambda e, p=path, t=item_type: self._open_item(p, t))
            w.bind("<Button-3>", _show_ctx)
            w.bind("<Enter>",    lambda e, f=card: _set_bg(f, C["card_h"]))
            w.bind("<Leave>",    lambda e, f=card: _set_bg(f, C["card"]))
            w.configure(cursor="hand2")
            for child in w.winfo_children():
                _bind_open(child)

        _bind_open(card)

    def _card_context_menu(self, event, idx: int, name: str, path: str):
        folders = self._current["folders"]
        menu = tk.Menu(self, tearoff=0,
                       bg=C["card"], fg=C["text"],
                       activebackground=C["card_h"], activeforeground=C["text"],
                       relief="flat", font=FONT)

        # 並び替え
        menu.add_command(
            label="↑ Move Up",
            command=lambda: self._move_folder_order(idx, -1),
            state="normal" if idx > 0 else "disabled",
        )
        menu.add_command(
            label="↓ Move Down",
            command=lambda: self._move_folder_order(idx, +1),
            state="normal" if idx < len(folders) - 1 else "disabled",
        )

        other_cats = [(ci, cat) for ci, cat in enumerate(self._data)
                      if cat is not self._current]
        if other_cats:
            menu.add_separator()
            move_menu = tk.Menu(menu, tearoff=0,
                                bg=C["card"], fg=C["text"],
                                activebackground=C["card_h"], activeforeground=C["text"],
                                relief="flat", font=FONT)
            for ci, cat in other_cats:
                move_menu.add_command(
                    label=cat["category"],
                    command=lambda ci=ci: self._move_folder_to(idx, ci),
                )
            menu.add_cascade(label="Move to ▶", menu=move_menu)

        menu.add_separator()
        menu.add_command(label="Rename",
                         command=lambda: self._edit_folder(idx, name, path))
        menu.add_command(label="Remove",
                         command=lambda: self._remove_folder(idx))
        menu.tk_popup(event.x_root, event.y_root)

    # ── Folder operations ─────────────────────────────────

    def _add_folder(self):
        path = filedialog.askdirectory(title="Select a folder")
        if not path:
            return
        path = os.path.normpath(path)
        if any(e["path"] == path for e in self._current["folders"]):
            messagebox.showinfo("Info", "This folder is already registered.", parent=self)
            return

        dlg = InputDialog(self, "Set Display Name", "Enter a display name:",
                          default=os.path.basename(path) or path)
        if dlg.result is None:
            return

        self._current["folders"].append({"name": dlg.result, "path": path})
        self._save()
        self._render_list()

    def _add_file(self):
        path = filedialog.askopenfilename(title="Select a file")
        if not path:
            return
        path = os.path.normpath(path)
        if any(e["path"] == path for e in self._current["folders"]):
            messagebox.showinfo("Info", "This file is already registered.", parent=self)
            return

        dlg = InputDialog(self, "Set Display Name", "Enter a display name:",
                          default=os.path.basename(path) or path)
        if dlg.result is None:
            return

        self._current["folders"].append({"name": dlg.result, "path": path, "type": "file"})
        self._save()
        self._render_list()

    def _edit_folder(self, idx: int, current_name: str, current_path: str):
        dlg = InputDialog(self, "Edit Display Name", "Enter a display name:",
                          default=current_name)
        if dlg.result is None:
            return
        self._current["folders"][idx]["name"] = dlg.result
        self._save()
        self._render_list()

    def _remove_folder(self, idx: int):
        name = self._current["folders"][idx]["name"]
        if messagebox.askyesno("Remove", f"Remove \"{name}\" from the list?", parent=self):
            self._current["folders"].pop(idx)
            self._save()
            self._render_list()

    def _move_folder_order(self, idx: int, direction: int):
        """Move a folder up or down within the same category."""
        folders = self._current["folders"]
        new_idx = idx + direction
        if 0 <= new_idx < len(folders):
            folders[idx], folders[new_idx] = folders[new_idx], folders[idx]
            self._save()
            self._render_list()

    def _move_folder_to(self, idx: int, target_cat_idx: int):
        """Move a folder to another category."""
        entry = self._current["folders"].pop(idx)
        self._data[target_cat_idx]["folders"].append(entry)
        self._save()
        self._render_list()

    # ── Terminal list ─────────────────────────────────────

    def _render_terminal_list(self):
        # ── 2ペイン構造（左: グループサイドバー, 右: 接続リスト）──
        pane = tk.Frame(self._list_frame, bg=C["bg"])
        pane.pack(fill="both", expand=True)

        # 左サイドバー（幅固定 110px）
        sidebar = tk.Frame(pane, bg=C["card"], width=110,
                           highlightthickness=1, highlightbackground=C["border"])
        sidebar.pack(side="left", fill="y", padx=(0, 4))
        sidebar.pack_propagate(False)
        self._render_group_sidebar(sidebar)

        # 右メインエリア
        main_frame = tk.Frame(pane, bg=C["bg"])
        main_frame.pack(side="left", fill="both", expand=True)

        # ── ツールバー（検索・ソート）──────────────────────
        toolbar = tk.Frame(main_frame, bg=C["bg"])
        toolbar.pack(fill="x", pady=(0, 4))

        tk.Label(toolbar, text="Search:", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL).pack(side="left", padx=(2, 2))
        tk.Entry(toolbar, textvariable=self._conn_search,
                 font=FONT, bg="#F0EBF8", fg=C["text"],
                 relief="flat", bd=1, insertbackground=C["accent"],
                 ).pack(side="left", fill="x", expand=True)

        def _sort_cmd(key: str):
            if self._conn_sort["col"] == key:
                self._conn_sort["reverse"] = not self._conn_sort["reverse"]
            else:
                self._conn_sort["col"] = key
                self._conn_sort["reverse"] = False
            self._render_list()

        def _hdr(key: str, label: str) -> str:
            if self._conn_sort["col"] == key:
                return label + (" ▼" if self._conn_sort["reverse"] else " ▲")
            return label

        sort_frame = tk.Frame(toolbar, bg=C["bg"])
        sort_frame.pack(side="right", padx=(4, 0))
        for key, label in [("name", "Name"), ("protocol", "Proto"),
                            ("host", "Host"), ("count", "Count"), ("last", "Last")]:
            b = tk.Button(sort_frame, text=_hdr(key, label),
                          command=lambda k=key: _sort_cmd(k),
                          bg=C["tab_inact"], fg=C["text_sub"],
                          relief="flat", bd=0, font=FONT_SMALL,
                          cursor="hand2", padx=6, pady=2,
                          activebackground=C["card_h"],
                          activeforeground=C["text"])
            b.pack(side="left", padx=1)
            _hover(b, C["card_h"], C["tab_inact"])

        # ── フィルタリング & ソート ──────────────────────
        query = self._conn_search.get().lower()
        sg = self._selected_group  # None = All
        conns_idx = [
            (i, c) for i, c in enumerate(self._conns)
            if (sg is None or c.get("group", "") == sg)
            and (not query
                 or query in c["name"].lower()
                 or query in c["host"].lower()
                 or query in c["protocol"].lower())
        ]
        col = self._conn_sort["col"]
        rev = self._conn_sort["reverse"]
        if col == "name":
            conns_idx.sort(key=lambda x: x[1]["name"].lower(), reverse=rev)
        elif col == "protocol":
            conns_idx.sort(key=lambda x: x[1]["protocol"].lower(), reverse=rev)
        elif col == "host":
            conns_idx.sort(key=lambda x: x[1]["host"].lower(), reverse=rev)
        elif col == "count":
            conns_idx.sort(key=lambda x: x[1].get("connect_count", 0), reverse=rev)
        elif col == "last":
            conns_idx.sort(key=lambda x: x[1].get("last_connected") or "", reverse=rev)

        if not conns_idx:
            msg = ("No connections match." if query or sg is not None
                   else "No connections registered.\nClick \"+ Add Connection\".")
            tk.Label(main_frame, text=msg,
                     bg=C["bg"], fg=C["text_sub"],
                     font=FONT_SMALL, justify="center").pack(pady=20)
            return

        for i, conn in conns_idx:
            self._make_conn_card(i, conn, main_frame)

        # ── ドラッグ&ドロップ（ソート・検索・グループ絞り込みなし時のみ有効）──
        if col is not None or query or sg is not None:
            return
        cards = [w for w in main_frame.winfo_children()
                 if isinstance(w, tk.Frame) and w is not toolbar]
        dnd: dict = {"src": None, "moved": False}

        def _cards_now():
            return [w for w in main_frame.winfo_children()
                    if isinstance(w, tk.Frame) and w is not toolbar]

        def on_press(e, card):
            dnd["src"]   = card
            dnd["moved"] = False

        def on_motion(e, card):
            src = dnd["src"]
            if src is None or src is card:
                return
            cur = _cards_now()
            try:
                si, ti = cur.index(src), cur.index(card)
            except ValueError:
                return
            if si == ti:
                return
            mid = card.winfo_rooty() + card.winfo_height() // 2
            insert_at = ti if e.y_root < mid else ti + 1
            cur.pop(si)
            cur.insert(min(insert_at, len(cur)), src)
            for w in cur:
                w.pack_forget()
            for w in cur:
                w.pack(fill="x", pady=2, padx=2)
            dnd["moved"] = True

        def on_release(ev):
            # サイドバーのグループボタンへのドロップをチェック
            target = ev.widget.winfo_containing(ev.x_root, ev.y_root)
            if (hasattr(self, "_sidebar_group_btns")
                    and target in self._sidebar_group_btns
                    and dnd["src"] is not None):
                src_card = dnd["src"]
                if hasattr(src_card, "_conn_orig_idx"):
                    new_grp = self._sidebar_group_btns[target]
                    if new_grp is None:
                        new_grp = ""
                    self._conns[src_card._conn_orig_idx]["group"] = new_grp
                    self._save_conns()
                    self._render_list()
                dnd["src"]   = None
                dnd["moved"] = False
                return
            if dnd["moved"]:
                new_order = [w._conn_orig_idx for w in _cards_now()
                             if hasattr(w, "_conn_orig_idx")]
                self._conns[:] = [self._conns[i] for i in new_order]
                self._save_conns()
            dnd["src"]   = None
            dnd["moved"] = False

        for card_w in cards:
            for w in (card_w, *card_w.winfo_children()):
                w.bind("<ButtonPress-1>",   lambda e, c=card_w: on_press(e, c))
                w.bind("<B1-Motion>",       lambda e, c=card_w: on_motion(e, c))
                w.bind("<ButtonRelease-1>", on_release)

    def _render_group_sidebar(self, parent: tk.Frame):
        """左サイドバーにグループボタンを描画する。"""
        self._sidebar_group_btns: dict = {}

        def _select_group(grp: str | None):
            self._selected_group = grp
            self._render_list()

        def _make_grp_btn(label: str, grp: str | None):
            is_active = (self._selected_group == grp)
            bg_c = C["accent"] if is_active else C["card"]
            fg_c = "white" if is_active else C["text_sub"]
            b = tk.Button(parent, text=label,
                          command=lambda g=grp: _select_group(g),
                          bg=bg_c, fg=fg_c,
                          relief="flat", bd=0, font=FONT_SMALL,
                          cursor="hand2", anchor="w", padx=6,
                          activebackground=C["card_h"],
                          activeforeground=C["text"],
                          wraplength=100, justify="left")
            b.pack(fill="x", pady=1, padx=2)
            if not is_active:
                _hover(b, C["card_h"], C["card"])
            self._sidebar_group_btns[b] = grp
            return b

        _make_grp_btn("All", None)
        for grp in self._terminal_groups:
            b = _make_grp_btn(grp, grp)
            # 右クリックメニュー（Rename / Delete）
            menu = tk.Menu(parent, tearoff=0)
            menu.add_command(label="Rename",
                             command=lambda g=grp: self._rename_terminal_group(g))
            menu.add_command(label="Delete",
                             command=lambda g=grp: self._delete_terminal_group(g))
            b.bind("<Button-3>", lambda e, m=menu: m.tk_popup(e.x_root, e.y_root))

        # + グループ追加ボタン
        add_btn = tk.Button(parent, text="+ Add Group",
                            command=self._add_terminal_group,
                            bg=C["bg"], fg=C["text_sub"],
                            relief="flat", bd=0, font=FONT_SMALL,
                            cursor="hand2", anchor="w", padx=6,
                            activebackground=C["card_h"],
                            activeforeground=C["text"],
                            wraplength=100, justify="left")
        add_btn.pack(fill="x", pady=(8, 1), padx=2)
        _hover(add_btn, C["card_h"], C["bg"])

    def _make_conn_card(self, idx: int, conn: dict,
                        parent_frame: tk.Frame | None = None):
        if parent_frame is None:
            parent_frame = self._list_frame
        card = tk.Frame(parent_frame, bg=C["card"],
                        pady=4, padx=8, relief="flat", bd=0,
                        highlightthickness=1, highlightbackground=C["border"])
        card._conn_orig_idx = idx   # ドラッグ&ドロップ用に元インデックスを保持
        card.pack(fill="x", pady=2, padx=2)

        left = tk.Frame(card, bg=C["card"])
        left.pack(side="left", fill="both", expand=True)

        proto_color = {"SSH": C["accent"], "RDP": C["accent_dk"],
                       "SMB": C["text_sub"]}.get(conn["protocol"], C["text_sub"])
        # グループバッジ（グループ未所属の場合は非表示）
        grp = conn.get("group", "")
        name_text = f"  {conn['name']}"
        if grp:
            name_text += f"  [{grp}]"
        tk.Label(left, text=name_text,
                 bg=C["card"], fg=C["text"],
                 font=FONT_BOLD, anchor="w").pack(fill="x")
        if conn["protocol"] == "SMB":
            sub_text = f"SMB  {conn['host']}"
        else:
            ncmds = len(conn.get("commands", []))
            cmd_str = f"  {ncmds} cmd{'s' if ncmds != 1 else ''}" if ncmds else ""
            sub_text = f"{conn['protocol']}  {conn['user']}@{conn['host']}:{conn.get('port', 22)}{cmd_str}"
        # 接続統計
        cnt = conn.get("connect_count", 0)
        last = conn.get("last_connected")
        stats_parts = []
        if cnt:
            stats_parts.append(f"{cnt}x")
        if last:
            stats_parts.append(last[:10])  # ISO形式から日付部分のみ
        if stats_parts:
            sub_text += "  |  " + "  ".join(stats_parts)
        tk.Label(left, text=sub_text,
                 bg=C["card"], fg=proto_color,
                 font=FONT_SMALL, anchor="w").pack(fill="x")

        del_btn = tk.Button(card, text="✕",
                            command=lambda i=idx: self._remove_conn(i),
                            bg=C["card"], fg=C["btn_del"],
                            relief="flat", bd=0,
                            font=("Segoe UI", 11), cursor="hand2",
                            activebackground=C["card"], activeforeground=C["btn_del_h"])
        del_btn.pack(side="right", padx=(6, 0))

        edit_btn = tk.Button(card, text="Edit",
                             command=lambda i=idx: self._edit_conn(i),
                             bg=C["card"], fg=C["text_sub"],
                             relief="flat", bd=0,
                             font=FONT_SMALL, cursor="hand2",
                             activebackground=C["card"], activeforeground=C["text"])
        edit_btn.pack(side="right", padx=(0, 2))

        for widget in (card, left) + tuple(left.winfo_children()):
            widget.bind("<Button-1>", lambda e, c=conn: self._connect_server(c))
            widget.bind("<Enter>",    lambda e, f=card: _set_bg(f, C["card_h"]))
            widget.bind("<Leave>",    lambda e, f=card: _set_bg(f, C["card"]))
            widget.configure(cursor="hand2")

    # ── Terminal connection operations ────────────────────

    def _add_conn(self):
        dlg = ConnectionDialog(self, groups=self._terminal_groups)
        if dlg.result is None:
            return
        conn = dlg.result
        self._conns.append(conn)
        self._save_conns()
        self._render_list()
        # connect immediately after adding
        self._connect_server(conn)

    def _remove_conn(self, idx: int):
        name = self._conns[idx]["name"]
        if messagebox.askyesno("Remove", f"Remove \"{name}\"?", parent=self):
            self._conns.pop(idx)
            self._save_conns()
            self._render_list()

    def _edit_conn(self, idx: int):
        dlg = ConnectionDialog(self, initial=self._conns[idx],
                               groups=self._terminal_groups)
        if dlg.result is None:
            return
        # 統計データを引き継ぐ
        prev = self._conns[idx]
        result = dlg.result
        result["connect_count"] = prev.get("connect_count", 0)
        result["last_connected"] = prev.get("last_connected")
        self._conns[idx] = result
        self._save_conns()
        self._render_list()

    def _connect_server(self, conn: dict):
        try:
            proto = conn["protocol"]
            if proto == "RDP":
                _launch_rdp(conn)
            elif proto == "SMB":
                _launch_smb(conn)
            else:
                _launch_teraterm(conn)
            # 接続統計を更新（self._conns の実体を更新）
            for c in self._conns:
                if c is conn or (c.get("name") == conn.get("name") and
                                 c.get("host") == conn.get("host")):
                    c["connect_count"] = c.get("connect_count", 0) + 1
                    c["last_connected"] = datetime.datetime.now().isoformat(timespec="seconds")
                    break
            self._save_conns()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect:\n{e}", parent=self)

    # ── Terminal group operations ─────────────────────────

    def _add_terminal_group(self):
        name = simpledialog.askstring("Add Group", "Group name:",
                                      parent=self)
        if not name:
            return
        name = name.strip()
        if not name:
            return
        if name in self._terminal_groups:
            messagebox.showwarning("Duplicate", f'Group "{name}" already exists.', parent=self)
            return
        self._terminal_groups.append(name)
        self._save_config()
        self._render_list()

    def _rename_terminal_group(self, grp: str):
        new_name = simpledialog.askstring("Rename Group",
                                          f'New name for "{grp}":',
                                          initialvalue=grp, parent=self)
        if not new_name:
            return
        new_name = new_name.strip()
        if not new_name or new_name == grp:
            return
        if new_name in self._terminal_groups:
            messagebox.showwarning("Duplicate", f'Group "{new_name}" already exists.', parent=self)
            return
        idx = self._terminal_groups.index(grp)
        self._terminal_groups[idx] = new_name
        for conn in self._conns:
            if conn.get("group") == grp:
                conn["group"] = new_name
        if self._selected_group == grp:
            self._selected_group = new_name
        self._save_config()
        self._render_list()

    def _delete_terminal_group(self, grp: str):
        if not messagebox.askyesno(
                "Delete Group",
                f'Delete group "{grp}"?\n(Connections will be moved to ungrouped.)',
                parent=self):
            return
        self._terminal_groups.remove(grp)
        for conn in self._conns:
            if conn.get("group") == grp:
                conn["group"] = ""
        if self._selected_group == grp:
            self._selected_group = None
        self._save_config()
        self._render_list()

    # ── Bookmark list ─────────────────────────────────────

    # ── Clipboard history ─────────────────────────────────

    def _check_clipboard(self):
        """500ms ごとにクリップボードを監視して変化があれば履歴に追加する。"""
        try:
            text = self.clipboard_get()
            if text and text != self._clip_prev:
                self._clip_prev = text
                # 重複があれば先頭に移動
                self._clip_history = [e for e in self._clip_history if e["text"] != text]
                self._clip_history.insert(0, {
                    "text": text,
                    "ts": datetime.datetime.now().strftime("%m/%d %H:%M"),
                })
                # 最大件数超過分を削除
                del self._clip_history[CLIP_MAX:]
                self._save_config()
                if self._active == -5:
                    self._render_list()
                else:
                    self._render_tabs()   # 件数バッジだけ更新
        except Exception:
            pass
        self.after(500, self._check_clipboard)

    def _clear_clip_history(self):
        if not self._clip_history:
            return
        if messagebox.askyesno("Clear All", "クリップボード履歴をすべて削除しますか？", parent=self):
            self._clip_history.clear()
            self._clip_prev = ""
            self._save_config()
            self._render_tabs()
            self._render_list()

    def _render_clip_list(self):
        if not self._clip_history:
            tk.Label(
                self._list_frame,
                text="クリップボード履歴はありません。\nテキストをコピーすると自動で記録されます。",
                bg=C["bg"], fg=C["text_sub"],
                font=FONT_SMALL, justify="center",
            ).pack(pady=20)
            return

        for idx, entry in enumerate(self._clip_history):
            text = entry["text"]
            ts   = entry.get("ts", "")

            card = tk.Frame(
                self._list_frame, bg=C["card"],
                pady=4, padx=8, relief="flat", bd=0,
                highlightthickness=1, highlightbackground=C["border"],
            )
            card.pack(fill="x", pady=2, padx=2)

            # 本文プレビュー（最大2行・80文字）
            preview = text.replace("\r\n", "\n").replace("\r", "\n")
            lines   = preview.splitlines()
            line1   = lines[0][:80] if lines else ""
            has_more = len(lines) > 1 or len(lines[0]) > 80 if lines else False
            display  = line1 + ("…" if has_more else "")

            left = tk.Frame(card, bg=C["card"])
            left.pack(side="left", fill="both", expand=True)

            tk.Label(left, text=display,
                     bg=C["card"], fg=C["text"],
                     font=FONT, anchor="w").pack(fill="x")
            tk.Label(left, text=ts,
                     bg=C["card"], fg=C["text_sub"],
                     font=FONT_SMALL, anchor="w").pack(fill="x")

            # 削除ボタン
            del_btn = tk.Button(
                card, text="✕",
                command=lambda i=idx: self._remove_clip(i),
                bg=C["card"], fg=C["btn_del"],
                relief="flat", bd=0,
                font=("Segoe UI", 11), cursor="hand2",
                activebackground=C["card"], activeforeground=C["btn_del_h"],
            )
            del_btn.pack(side="right", padx=(6, 0))

            # コピーボタン
            copy_btn = tk.Button(
                card, text="Copy",
                command=lambda t=text: self._copy_clip(t),
                bg=C["card"], fg=C["text_sub"],
                relief="flat", bd=0,
                font=FONT_SMALL, cursor="hand2",
                activebackground=C["card"], activeforeground=C["text"],
            )
            copy_btn.pack(side="right", padx=(0, 2))

            def _bind_card(w, t=text):
                if w in (del_btn, copy_btn):
                    return
                w.bind("<Button-1>", lambda e, txt=t: self._copy_clip(txt))
                w.bind("<Enter>",    lambda e, f=card: _set_bg(f, C["card_h"]))
                w.bind("<Leave>",    lambda e, f=card: _set_bg(f, C["card"]))
                w.configure(cursor="hand2")
                for child in w.winfo_children():
                    _bind_card(child)

            _bind_card(card)

    def _copy_clip(self, text: str):
        """テキストをクリップボードにコピーする（履歴の重複追加を防ぐため _clip_prev も更新）。"""
        self.clipboard_clear()
        self.clipboard_append(text)
        self._clip_prev = text

    def _remove_clip(self, idx: int):
        self._clip_history.pop(idx)
        self._save_config()
        self._render_tabs()
        self._render_list()

    # ── Ping monitor ──────────────────────────────────────

    def _render_ping_list(self):
        """Ping モニター UI を描画する。"""
        # ── 設定バー ──────────────────────────────────────
        cfg_bar = tk.Frame(self._list_frame, bg=C["bg"])
        cfg_bar.pack(fill="x", pady=(0, 4))

        tk.Label(cfg_bar, text="Interval:", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL).pack(side="left", padx=(2, 2))
        self._ping_interval_var = tk.StringVar(value=str(self._ping_interval))
        tk.Entry(cfg_bar, textvariable=self._ping_interval_var,
                 width=4, font=FONT, bg=C["card"], fg=C["text"],
                 relief="flat", bd=1, insertbackground=C["accent"],
                 ).pack(side="left")
        tk.Label(cfg_bar, text="sec", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL).pack(side="left", padx=(2, 8))

        def _apply_interval():
            try:
                v = int(self._ping_interval_var.get())
                if v > 0:
                    self._ping_interval = v
                    self._save_config()
            except ValueError:
                pass

        tk.Button(cfg_bar, text="Apply", command=_apply_interval,
                  bg=C["tab_inact"], fg=C["text_sub"], relief="flat", bd=0,
                  font=FONT_SMALL, cursor="hand2", padx=6, pady=2,
                  activebackground=C["card_h"],
                  activeforeground=C["text"]).pack(side="left")

        tk.Label(cfg_bar, text=f"{len(self._ping_hosts)} host(s)",
                 bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL).pack(side="right", padx=8)

        # ── スクロール可能エリア ───────────────────────
        outer = tk.Frame(self._list_frame, bg=C["bg"])
        outer.pack(fill="both", expand=True)

        vsb = tk.Scrollbar(outer, orient="vertical")
        vsb.pack(side="right", fill="y")

        scroll_cv = tk.Canvas(outer, bg=C["bg"],
                              yscrollcommand=vsb.set,
                              highlightthickness=0)
        scroll_cv.pack(side="left", fill="both", expand=True)
        vsb.configure(command=scroll_cv.yview)

        inner = tk.Frame(scroll_cv, bg=C["bg"])
        win_id = scroll_cv.create_window(0, 0, anchor="nw", window=inner)

        def _on_inner_cfg(e):
            scroll_cv.configure(scrollregion=scroll_cv.bbox("all"))

        def _on_cv_cfg(e):
            scroll_cv.itemconfigure(win_id, width=e.width)

        inner.bind("<Configure>", _on_inner_cfg)
        scroll_cv.bind("<Configure>", _on_cv_cfg)
        scroll_cv.bind("<MouseWheel>",
                       lambda e: scroll_cv.yview_scroll(int(-1*(e.delta/120)), "units"))

        if not self._ping_hosts:
            tk.Label(inner,
                     text="接続先ホストを追加してください\n（「+ Add Host」ボタン）",
                     bg=C["bg"], fg=C["text_sub"],
                     font=FONT_SMALL, justify="center").pack(pady=30)
            return

        # ── 各ホスト行 ─────────────────────────────────
        self._ping_row_canvases = {}
        self._ping_status_dots  = {}
        self._ping_stat_labels  = {}
        bar_area_w = (self._PING_BAR_W + self._PING_BAR_GAP) * self._PING_HISTORY

        for host in self._ping_hosts:
            row = tk.Frame(inner, bg=C["card"],
                           highlightthickness=1, highlightbackground=C["border"])
            row.pack(fill="x", padx=4, pady=2)

            # 左：ステータスドット + ホスト名 + 統計テキスト
            lbl_frame = tk.Frame(row, bg=C["card"], width=160)
            lbl_frame.pack(side="left", fill="y")
            lbl_frame.pack_propagate(False)

            name_row = tk.Frame(lbl_frame, bg=C["card"])
            name_row.pack(fill="x", padx=6, pady=(10, 0))
            dot_cv = tk.Canvas(name_row, width=10, height=10,
                               bg=C["card"], highlightthickness=0)
            dot_cv.pack(side="left", padx=(0, 4))
            dot_cv.create_oval(1, 1, 9, 9, fill=C["text_sub"], outline="", tags="dot")
            self._ping_status_dots[host] = dot_cv

            short = host if len(host) <= 20 else host[:19] + "…"
            tk.Label(name_row, text=short, bg=C["card"], fg=C["text"],
                     font=FONT_SMALL, anchor="w").pack(side="left")

            sv = tk.StringVar(value="---")
            self._ping_stat_vars[host] = sv
            stat_lbl = tk.Label(lbl_frame, textvariable=sv,
                                bg=C["card"], fg=C["text_sub"],
                                font=("Segoe UI", 7), anchor="w")
            stat_lbl.pack(fill="x", padx=6)
            self._ping_stat_labels[host] = stat_lbl

            # 中：棒グラフ Canvas
            cv = tk.Canvas(row, bg=C["card"],
                           width=bar_area_w, height=self._PING_ROW_H,
                           highlightthickness=0)
            cv.pack(side="left", padx=(0, 4))
            self._ping_row_canvases[host] = cv

            # 右：削除ボタン
            def _del(h=host):
                if h in self._ping_hosts:
                    self._ping_hosts.remove(h)
                if h in self._ping_data:
                    del self._ping_data[h]
                self._save_config()
                self._render_list()

            del_btn = tk.Button(row, text="✕", command=_del,
                                bg=C["card"], fg=C["btn_del"],
                                relief="flat", bd=0, font=("Segoe UI", 11),
                                cursor="hand2",
                                activebackground=C["card"],
                                activeforeground=C["btn_del_h"])
            del_btn.pack(side="right", padx=(0, 6))

        # 初回描画
        self._ping_redraw()

    def _ping_redraw(self):
        """全ホストの棒グラフを再描画する。メインスレッドから呼ぶこと。"""
        if not hasattr(self, "_ping_row_canvases"):
            return

        bw      = self._PING_BAR_W
        bg_gap  = self._PING_BAR_GAP
        row_h   = self._PING_ROW_H
        max_ms  = self._PING_MAX_MS

        for host, cv in self._ping_row_canvases.items():
            cv.delete("all")
            history = self._ping_data.get(host, [])

            # グリッド線
            for gms in [100, 200, 300]:
                gy = row_h - int(gms / max_ms * (row_h - 8)) - 4
                if gy < 2:
                    continue
                cv.create_line(0, gy, (bw + bg_gap) * self._PING_HISTORY, gy,
                               fill=C["border"], dash=(2, 4))
                cv.create_text(2, gy - 1, text=f"{gms}", anchor="sw",
                               fill=C["text_sub"], font=("Segoe UI", 6))

            # バー描画
            for j, ms in enumerate(history):
                x = j * (bw + bg_gap)
                if ms is None:
                    # タイムアウト
                    cv.create_rectangle(x, 4, x + bw, row_h - 4,
                                        fill="#CC3344", outline="")
                    cv.create_text(x + bw // 2, row_h // 2,
                                   text="TO", fill="white",
                                   font=("Segoe UI", 6))
                else:
                    clipped = min(ms, max_ms)
                    bh = max(3, int(clipped / max_ms * (row_h - 12)))
                    color = (C["accent"]    if ms < 100 else
                             C["accent_dk"] if ms < 200 else
                             "#DD8844")
                    cv.create_rectangle(x, row_h - 4 - bh, x + bw, row_h - 4,
                                        fill=color, outline="")
                    if bh >= 16:
                        cv.create_text(x + bw // 2, row_h - 4 - bh // 2,
                                       text=str(int(ms)), fill="white",
                                       font=("Segoe UI", 6))

            # 統計テキスト更新
            if host in self._ping_stat_vars and history:
                last = history[-1]
                vals = [v for v in history if v is not None]
                if last is None:
                    stat = "Timeout"
                elif vals:
                    avg = sum(vals) / len(vals)
                    mn  = min(vals)
                    stat = f"{int(last)}ms  avg {int(avg)}ms  min {int(mn)}ms"
                else:
                    stat = f"{int(last)}ms"
                self._ping_stat_vars[host].set(stat)

                # ステータスドット・ラベル色を更新（緑=OK / 赤=Timeout）
                ok = (last is not None)
                dot_color  = "#44CC77" if ok else "#CC3344"
                stat_color = "#44CC77" if ok else "#CC4455"
                if host in self._ping_status_dots:
                    self._ping_status_dots[host].itemconfigure("dot", fill=dot_color)
                if host in self._ping_stat_labels:
                    self._ping_stat_labels[host].configure(fg=stat_color)

    def _ping_add_host(self):
        """Ping ホスト追加ダイアログを開く。ターミナル接続先を候補として提示する。"""
        suggestions = [c["host"] for c in self._conns
                       if c["host"] not in self._ping_hosts]
        hint = "ホスト名または IP アドレス"
        if suggestions:
            hint += f"\n例: {', '.join(suggestions[:4])}"
        dlg = InputDialog(self, "Add Ping Host", hint)
        if dlg.result is None:
            return
        host = dlg.result.strip()
        if not host:
            return
        if host in self._ping_hosts:
            messagebox.showinfo("Info", f"'{host}' は既に登録済みです。", parent=self)
            return
        self._ping_hosts.append(host)
        self._ping_data[host] = []
        self._save_config()
        self._render_list()

    def _ping_start(self):
        """Ping モニターを開始する。"""
        if self._ping_running:
            return
        self._ping_running = True
        # 既存データを保持しつつ、新ホストの分を初期化
        for h in self._ping_hosts:
            self._ping_data.setdefault(h, [])
        self._ping_schedule_round()

    def _ping_stop(self):
        """Ping モニターを停止する。"""
        self._ping_running = False
        if self._ping_next_id is not None:
            self.after_cancel(self._ping_next_id)
            self._ping_next_id = None
        if self._ping_graph_id is not None:
            self.after_cancel(self._ping_graph_id)
            self._ping_graph_id = None

    def _ping_schedule_round(self):
        """次の ping ラウンドをスレッドで起動する。"""
        if not self._ping_running:
            return
        threading.Thread(target=self._ping_round, daemon=True).start()

    def _ping_round(self):
        """全ホストへ並列 ping を実行し、終了後にグラフを更新する。"""
        hosts = list(self._ping_hosts)
        threads = [
            threading.Thread(target=self._ping_one, args=(h,), daemon=True)
            for h in hosts
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=3.5)
        if self._ping_running:
            self.after(0, self._ping_redraw)
            interval_ms = max(1000, self._ping_interval * 1000)
            self._ping_next_id = self.after(interval_ms, self._ping_schedule_round)

    def _ping_one(self, host: str):
        """1 ホストへ ping を実行し、応答時間を _ping_data に追加する。"""
        try:
            result = subprocess.run(
                ["ping", "-n", "1", "-w", "2000", host],
                capture_output=True, text=True, timeout=3.0,
            )
            if "TTL=" in result.stdout or "ttl=" in result.stdout:
                # 英語: "time=5ms" / "time<1ms"、日本語: "時間 =5ms" / "時間 <1ms"
                m = re.search(r"(?:[Tt]ime|時間)\s*=\s*(\d+)\s*ms", result.stdout)
                if m:
                    ms = float(m.group(1))
                elif re.search(r"(?:[Tt]ime|時間)\s*<", result.stdout):
                    ms = 0.5  # <1ms は 0.5ms として扱う
                else:
                    ms = 1.0  # TTLあり・時間不詳は 1ms 扱い
            else:
                ms = None
        except Exception:
            ms = None

        with self._ping_lock:
            hist = self._ping_data.setdefault(host, [])
            hist.append(ms)
            if len(hist) > self._PING_HISTORY:
                hist.pop(0)

    def _render_bookmark_list(self):
        pane = tk.Frame(self._list_frame, bg=C["bg"])
        pane.pack(fill="both", expand=True)

        if not self._bookmarks:
            tk.Label(pane,
                     text="No categories.\nClick \"+ Add Category\" to start.",
                     bg=C["bg"], fg=C["text_sub"],
                     font=FONT_SMALL, justify="center").pack(pady=20)
            return

        # 左サイドバー
        sidebar = tk.Frame(pane, bg=C["card"], width=110,
                           highlightthickness=1, highlightbackground=C["border"])
        sidebar.pack(side="left", fill="y", padx=(0, 4))
        sidebar.pack_propagate(False)
        self._render_bm_sidebar(sidebar)

        # 右メインエリア
        main_frame = tk.Frame(pane, bg=C["bg"])
        main_frame.pack(side="left", fill="both", expand=True)

        cat = self._bookmarks[self._bm_selected]
        items = cat.get("items", [])
        if not items:
            tk.Label(main_frame,
                     text="No bookmarks.\nClick \"+ Add Bookmark\" to add one.",
                     bg=C["bg"], fg=C["text_sub"],
                     font=FONT_SMALL, justify="center").pack(pady=20)
            return

        for i, item in enumerate(items):
            self._make_bookmark_card(i, item, main_frame)

    def _render_bm_sidebar(self, parent: tk.Frame):
        for i, cat in enumerate(self._bookmarks):
            is_active = (i == self._bm_selected)
            bg_c = C["accent"] if is_active else C["card"]
            fg_c = "white" if is_active else C["text_sub"]
            b = tk.Button(parent, text=cat["category"],
                          command=lambda idx=i: self._bm_select(idx),
                          bg=bg_c, fg=fg_c,
                          relief="flat", bd=0, font=FONT_SMALL,
                          cursor="hand2", anchor="w", padx=6,
                          activebackground=C["card_h"],
                          activeforeground=C["text"],
                          wraplength=100, justify="left")
            b.pack(fill="x", pady=1, padx=2)
            if not is_active:
                _hover(b, C["card_h"], C["card"])
            menu = tk.Menu(parent, tearoff=0)
            menu.add_command(label="Rename",
                             command=lambda idx=i: self._rename_bm_category(idx))
            menu.add_command(label="Delete",
                             command=lambda idx=i: self._delete_bm_category(idx))
            b.bind("<Button-3>", lambda e, m=menu: m.tk_popup(e.x_root, e.y_root))

        add_btn = tk.Button(parent, text="+ Add Category",
                            command=self._add_bm_category,
                            bg=C["bg"], fg=C["text_sub"],
                            relief="flat", bd=0, font=FONT_SMALL,
                            cursor="hand2", anchor="w", padx=6,
                            activebackground=C["card_h"],
                            activeforeground=C["text"],
                            wraplength=100, justify="left")
        add_btn.pack(fill="x", pady=(8, 1), padx=2)
        _hover(add_btn, C["card_h"], C["bg"])

    def _bm_select(self, idx: int):
        self._bm_selected = idx
        self._render_list()

    def _make_bookmark_card(self, item_idx: int, item: dict,
                            parent_frame: tk.Frame):
        card = tk.Frame(parent_frame, bg=C["card"],
                        pady=4, padx=8, relief="flat", bd=0,
                        highlightthickness=1, highlightbackground=C["border"])
        card.pack(fill="x", pady=2, padx=2)

        left = tk.Frame(card, bg=C["card"])
        left.pack(side="left", fill="both", expand=True)

        tk.Label(left, text=f"  {item['name']}",
                 bg=C["card"], fg=C["text"],
                 font=FONT_BOLD, anchor="w").pack(fill="x")
        tk.Label(left, text=f"  {item['url']}",
                 bg=C["card"], fg=C["accent"],
                 font=FONT_SMALL, anchor="w").pack(fill="x")

        del_btn = tk.Button(card, text="✕",
                            command=lambda i=item_idx: self._remove_bookmark(i),
                            bg=C["card"], fg=C["btn_del"],
                            relief="flat", bd=0,
                            font=("Segoe UI", 11), cursor="hand2",
                            activebackground=C["card"], activeforeground=C["btn_del_h"])
        del_btn.pack(side="right", padx=(6, 0))

        edit_btn = tk.Button(card, text="Edit",
                             command=lambda i=item_idx: self._edit_bookmark(i),
                             bg=C["card"], fg=C["text_sub"],
                             relief="flat", bd=0,
                             font=FONT_SMALL, cursor="hand2",
                             activebackground=C["card"], activeforeground=C["text"])
        edit_btn.pack(side="right", padx=(0, 2))

        def _open(e=None):
            webbrowser.open(item["url"])

        for w in (card, left) + tuple(left.winfo_children()):
            w.bind("<Button-1>", _open)
            w.bind("<Enter>", lambda e, f=card: _set_bg(f, C["card_h"]))
            w.bind("<Leave>", lambda e, f=card: _set_bg(f, C["card"]))
            w.configure(cursor="hand2")

    # ── Bookmark operations ───────────────────────────────

    def _add_bookmark(self):
        if not self._bookmarks:
            messagebox.showinfo("Info", "Add a category first.", parent=self)
            return
        dlg = BookmarkDialog(self)
        if dlg.result is None:
            return
        self._bookmarks[self._bm_selected]["items"].append(dlg.result)
        self._save_config()
        self._render_list()

    def _edit_bookmark(self, item_idx: int):
        item = self._bookmarks[self._bm_selected]["items"][item_idx]
        dlg = BookmarkDialog(self, initial=item)
        if dlg.result is None:
            return
        self._bookmarks[self._bm_selected]["items"][item_idx] = dlg.result
        self._save_config()
        self._render_list()

    def _remove_bookmark(self, item_idx: int):
        name = self._bookmarks[self._bm_selected]["items"][item_idx]["name"]
        if messagebox.askyesno("Remove", f'Remove "{name}"?', parent=self):
            self._bookmarks[self._bm_selected]["items"].pop(item_idx)
            self._save_config()
            self._render_list()

    def _add_bm_category(self):
        name = simpledialog.askstring("Add Category", "Category name:", parent=self)
        if not name:
            return
        name = name.strip()
        if not name:
            return
        self._bookmarks.append({"category": name, "items": []})
        self._bm_selected = len(self._bookmarks) - 1
        self._save_config()
        self._render_list()

    def _rename_bm_category(self, idx: int):
        old = self._bookmarks[idx]["category"]
        new = simpledialog.askstring("Rename Category", "New name:",
                                     initialvalue=old, parent=self)
        if not new or not new.strip() or new.strip() == old:
            return
        self._bookmarks[idx]["category"] = new.strip()
        self._save_config()
        self._render_list()

    def _delete_bm_category(self, idx: int):
        name = self._bookmarks[idx]["category"]
        if not messagebox.askyesno("Delete Category",
                                   f'Delete category "{name}" and all its bookmarks?',
                                   parent=self):
            return
        self._bookmarks.pop(idx)
        self._bm_selected = max(0, min(self._bm_selected, len(self._bookmarks) - 1))
        self._save_config()
        self._render_list()

    # ── Task list ─────────────────────────────────────────

    def _render_task_list(self):
        # configure Treeview style to match theme
        style = ttk.Style()
        style.configure("TaskTree.Treeview",
                        background=C["card"], foreground=C["text"],
                        fieldbackground=C["card"], rowheight=26, font=FONT)
        style.configure("TaskTree.Treeview.Heading",
                        background=C["tab_inact"], foreground=C["text"],
                        font=FONT_BOLD, relief="flat", padding=4)
        style.map("TaskTree.Treeview",
                  background=[("selected", C["card_h"])],
                  foreground=[("selected", C["text"])])

        if not self._tasks:
            tk.Label(
                self._list_frame,
                text="No tasks registered.\nClick \"+ Add Task\" to add one.",
                bg=C["bg"], fg=C["text_sub"],
                font=FONT_SMALL, justify="center",
            ).pack(pady=20)
            return

        # group by event name (preserve insertion order)
        groups: dict[str, list[tuple[int, dict]]] = {}
        for i, task in enumerate(self._tasks):
            groups.setdefault(task["event"], []).append((i, task))

        # ── Apply sort ──
        col = self._task_sort["col"]
        rev = self._task_sort["reverse"]
        if col == "event":
            groups = dict(sorted(groups.items(),
                                 key=lambda x: x[0].lower(), reverse=rev))
        elif col == "process":
            for ev in groups:
                groups[ev].sort(key=lambda x: x[1].get("process", "").lower(), reverse=rev)
        elif col == "content":
            for ev in groups:
                groups[ev].sort(key=lambda x: x[1].get("content", "").lower(), reverse=rev)
        elif col == "progress":
            for ev in groups:
                groups[ev].sort(key=lambda x: x[1].get("progress", 0), reverse=rev)
        elif col == "deadline":
            for ev in groups:
                groups[ev].sort(key=lambda x: x[1].get("deadline", "9999-99-99"), reverse=rev)
        elif col == "updated":
            for ev in groups:
                groups[ev].sort(key=lambda x: x[1].get("updated", ""), reverse=rev)

        def _hdr(key: str, label: str) -> str:
            if self._task_sort["col"] == key:
                return label + (" ▼" if self._task_sort["reverse"] else " ▲")
            return label

        def _sort_cmd(key: str):
            if self._task_sort["col"] == key:
                self._task_sort["reverse"] = not self._task_sort["reverse"]
            else:
                self._task_sort["col"] = key
                self._task_sort["reverse"] = False
            self._render_list()

        n_rows = len(self._tasks) + len(groups)
        tree_height = max(3, min(n_rows, 14))

        tree_wrap = tk.Frame(self._list_frame, bg=C["bg"])
        tree_wrap.pack(fill="both", expand=True, padx=2, pady=(2, 0))

        def _days_left_str(deadline: str) -> str:
            """Return remaining days display text from deadline string."""
            if not deadline:
                return ""
            try:
                d = datetime.date.fromisoformat(deadline)
                delta = (d - datetime.date.today()).days
                if delta > 0:   return f"+{delta}d"
                if delta == 0:  return "Today"
                return f"{delta}d"
            except ValueError:
                return ""

        cols = ("process", "content", "progress", "deadline", "remaining", "updated")
        tree = ttk.Treeview(tree_wrap, columns=cols, show="tree headings",
                            style="TaskTree.Treeview", height=tree_height,
                            selectmode="browse")

        tree.heading("#0",        text=_hdr("event",    "Event"),
                     anchor="w",  command=lambda: _sort_cmd("event"))
        tree.heading("process",   text=_hdr("process",  "Process"),
                     anchor="w",  command=lambda: _sort_cmd("process"))
        tree.heading("content",   text=_hdr("content",  "Content"),
                     anchor="w",  command=lambda: _sort_cmd("content"))
        tree.heading("progress",  text=_hdr("progress", "Progress"),
                     anchor="center", command=lambda: _sort_cmd("progress"))
        tree.heading("deadline",  text=_hdr("deadline", "Deadline"),
                     anchor="center", command=lambda: _sort_cmd("deadline"))
        tree.heading("remaining", text="Remaining", anchor="center")
        tree.heading("updated",   text=_hdr("updated",  "Updated"),
                     anchor="center", command=lambda: _sort_cmd("updated"))

        tree.column("#0",        width=100, minwidth=70,  stretch=True)
        tree.column("process",   width=170, minwidth=70,  stretch=False)
        tree.column("content",   width=120, minwidth=60,  stretch=True)
        tree.column("progress",  width=58,  minwidth=45,  stretch=False)
        tree.column("deadline",  width=82,  minwidth=70,  stretch=False)
        tree.column("remaining", width=68,  minwidth=55,  stretch=False)
        tree.column("updated",   width=82,  minwidth=70,  stretch=False)

        vsb = ttk.Scrollbar(tree_wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # row color by progress (red=critical / yellow=caution / green=ok)
        tree.tag_configure("p_red",    background="#FFCCCC", foreground="#7A1A1A")  # 0–33%
        tree.tag_configure("p_yellow", background="#FFF3BC", foreground="#6B4E00")  # 34–66%
        tree.tag_configure("p_green",  background="#C8EDD4", foreground="#1A5C2E")  # 67–99%
        tree.tag_configure("done",     background="#A8DDB8", foreground="#0F4020")  # 100%

        def _progress_tag(pct: int) -> str:
            if pct == 100: return "done"
            if pct >= 67:  return "p_green"
            if pct >= 34:  return "p_yellow"
            return "p_red"

        for event_name, task_list in groups.items():
            parent = tree.insert("", "end", text=event_name, open=True,
                                 values=("", "", "", "", "", ""))
            for i, task in task_list:
                pct      = task.get("progress", 0)
                content  = task.get("content", "").replace("\n", " ")
                deadline = task.get("deadline", "")
                remaining = _days_left_str(deadline)
                updated  = task.get("updated", "")
                tree.insert(parent, "end", iid=str(i), text="",
                            tags=(_progress_tag(pct),),
                            values=(task.get("process", ""), content,
                                    f"{pct}%", deadline, remaining, updated))

        # detail panel (show full text of selected row)
        tk.Frame(self._list_frame, bg=C["border"], height=1).pack(
            fill="x", padx=2, pady=(4, 0))
        detail_bg = tk.Frame(self._list_frame, bg=C["card"],
                             highlightthickness=1, highlightbackground=C["border"])
        detail_bg.pack(fill="x", padx=2, pady=(0, 2))
        detail_lbl = tk.Label(detail_bg,
                              text="Select a task to view details.",
                              bg=C["card"], fg=C["text_sub"], font=FONT_SMALL,
                              anchor="nw", justify="left", wraplength=272)
        detail_lbl.pack(padx=8, pady=(6, 2), fill="x")

        folder_frame = tk.Frame(detail_bg, bg=C["card"])
        folder_frame.pack(fill="x", padx=6, pady=(0, 2))
        memo_row = tk.Frame(detail_bg, bg=C["card"])
        memo_row.pack(fill="x", padx=6, pady=(0, 4))

        def on_select(_e):
            sel = tree.selection()
            if not sel:
                return
            try:
                idx = int(sel[0])
            except ValueError:
                return  # skip event parent rows
            task = self._tasks[idx]
            deadline  = task.get("deadline", "")
            remaining = _days_left_str(deadline)
            dl_part  = f"  Deadline: {deadline}  ({remaining})" if deadline else ""
            upd_part = f"  Updated: {task['updated']}" if task.get("updated") else ""
            detail_lbl.configure(fg=C["text"], text=(
                f"[{task['event']}]  {task.get('process', '')}"
                f"  {task.get('progress', 0)}%{dl_part}{upd_part}\n"
                f"{task.get('content', '')}"
            ))

            # 作業フォルダ ボタン群（毎回再構築）
            for w in folder_frame.winfo_children():
                w.destroy()
            wfs = task.get("work_folders", [])
            if not wfs and task.get("work_folder"):
                wfs = [task["work_folder"]]
            for wf in wfs:
                name = os.path.basename(wf) or wf
                tk.Button(folder_frame, text=name,
                          command=lambda p=wf: subprocess.Popen(["explorer", p]),
                          bg=C["accent_lt"], fg=C["accent_dk"],
                          relief="flat", bd=0,
                          font=FONT, cursor="hand2", padx=10, pady=4,
                          activebackground=C["border"],
                          activeforeground=C["accent_dk"],
                          ).pack(side="left", padx=(0, 4), pady=3)

            # メモ行（毎回再構築）
            for w in memo_row.winfo_children():
                w.destroy()
            m_list = task.get("memos", [])
            if not m_list and task.get("memo"):
                m_list = [{"title": "Memo", "content": task["memo"]}]
            count = len(m_list)
            if count:
                titles = ", ".join(m.get("title", "Untitled") for m in m_list[:3])
                if count > 3:
                    titles += f" … +{count - 3}"
                tk.Label(memo_row, text=titles,
                         bg=C["card"], fg=C["text_sub"],
                         font=FONT_SMALL, anchor="w").pack(
                             side="left", fill="x", expand=True)
            btn_text = f"Memos ({count})" if count else "+ Memo"
            tk.Button(memo_row,
                      text=btn_text,
                      command=lambda i=idx: self._open_memo(i),
                      bg=C["accent_lt"], fg=C["accent_dk"],
                      relief="flat", bd=0,
                      font=FONT, cursor="hand2", padx=10, pady=4,
                      activebackground=C["border"],
                      activeforeground=C["accent_dk"],
                      ).pack(side="right")

        tree.bind("<<TreeviewSelect>>", on_select)
        tree.bind("<Double-1>",  lambda e: self._task_tree_edit(tree))
        tree.bind("<Button-3>",  lambda e: self._task_tree_menu(e, tree))

        # ── Drag & drop reordering ──
        dnd: dict = {"src": None, "moved": False}

        def _is_task_row(iid: str) -> bool:
            try:
                int(iid)
                return True
            except ValueError:
                return False

        def on_dnd_press(e):
            region = tree.identify_region(e.x, e.y)
            if region not in ("cell", "tree"):
                return
            item = tree.identify_row(e.y)
            dnd["src"] = item if (item and _is_task_row(item)) else None
            dnd["moved"] = False

        def on_dnd_motion(e):
            src = dnd["src"]
            if not src:
                return
            target = tree.identify_row(e.y)
            if not target or target == src:
                return
            src_is_task = _is_task_row(src)
            tgt_is_task = _is_task_row(target)
            bbox = tree.bbox(target)
            if not bbox:
                return
            tgt_idx = tree.index(target)
            if e.y >= bbox[1] + bbox[3] // 2:
                tgt_idx += 1
            if src_is_task and tgt_is_task:
                # タスク行 → 同グループ内でのみ移動
                if tree.parent(src) != tree.parent(target):
                    return
                tree.move(src, tree.parent(src), tgt_idx)
                dnd["moved"] = True
            elif not src_is_task and not tgt_is_task:
                # イベント行 → グループごと並び替え
                tree.move(src, "", tgt_idx)
                dnd["moved"] = True

        def on_dnd_release(e):
            src = dnd["src"]
            dnd["src"] = None
            if not src or not dnd["moved"]:
                return
            # rebuild self._tasks from current tree order
            new_tasks = []
            for ev_row in tree.get_children():
                for child in tree.get_children(ev_row):
                    new_tasks.append(self._tasks[int(child)])
            self._tasks[:] = new_tasks
            self._task_sort = {"col": None, "reverse": False}
            self._save_tasks()
            self._render_list()

        tree.bind("<ButtonPress-1>",   on_dnd_press)
        tree.bind("<B1-Motion>",       on_dnd_motion)
        tree.bind("<ButtonRelease-1>", on_dnd_release)

    def _task_tree_edit(self, tree):
        sel = tree.selection()
        if not sel:
            return
        try:
            idx = int(sel[0])
            self._edit_task(idx)
        except ValueError:
            # イベント親行のダブルクリック → リネーム
            self._rename_event(tree.item(sel[0], "text"))

    def _task_tree_menu(self, event, tree):
        row = tree.identify_row(event.y)
        if not row:
            return
        tree.selection_set(row)
        menu = tk.Menu(self, tearoff=0,
                       bg=C["card"], fg=C["text"],
                       activebackground=C["card_h"], activeforeground=C["text"],
                       relief="flat", font=FONT)
        try:
            idx = int(row)
            # タスク行
            menu.add_command(label="Edit",   command=lambda: self._edit_task(idx))
            menu.add_separator()
            menu.add_command(label="Delete", command=lambda: self._remove_task(idx))
        except ValueError:
            # イベント親行
            ev_name = tree.item(row, "text")
            menu.add_command(label="Rename",
                             command=lambda: self._rename_event(ev_name))
        menu.tk_popup(event.x_root, event.y_root)

    # ── Task operations ───────────────────────────────────

    def _event_names(self) -> list:
        return sorted(set(t["event"] for t in self._tasks if t.get("event")))

    def _add_task(self):
        dlg = TaskDialog(self, event_names=self._event_names())
        if dlg.result is None:
            return
        today = datetime.date.today().isoformat()
        dlg.result["created_at"] = today   # 作成日
        dlg.result["updated"]    = today   # 最終更新日
        self._tasks.append(dlg.result)
        self._save_tasks()
        self._render_list()

    def _edit_task(self, idx: int):
        dlg = TaskDialog(self, initial=self._tasks[idx],
                         event_names=self._event_names())
        if dlg.result is None:
            return
        # 既存フィールド（memos, created_at 等）を保持しつつ上書き
        merged = dict(self._tasks[idx])
        merged.update(dlg.result)
        merged["updated"] = datetime.date.today().isoformat()   # 最終更新日を更新
        self._tasks[idx] = merged
        self._save_tasks()
        self._render_list()

    def _remove_task(self, idx: int):
        name = self._tasks[idx]["event"]
        if messagebox.askyesno("Remove", f"Remove \"{name}\"?", parent=self):
            self._tasks.pop(idx)
            self._save_tasks()
            self._render_list()

    def _open_gantt(self):
        GanttWindow(self, self._tasks)

    def _export_tasks(self):
        """タスク一覧をテキストファイルに出力してエクスプローラーで開く。"""
        if not self._tasks:
            messagebox.showinfo("Export", "タスクが登録されていません。", parent=self)
            return

        save_path = filedialog.asksaveasfilename(
            parent=self,
            title="タスクをエクスポート",
            defaultextension=".txt",
            initialfile=f"tasks_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            filetypes=[("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")],
        )
        if not save_path:
            return

        today = datetime.date.today()

        def days_left(dl_str: str) -> str:
            if not dl_str:
                return ""
            try:
                d = datetime.date.fromisoformat(dl_str)
                delta = (d - today).days
                if delta > 0:  return f"あと {delta} 日"
                if delta == 0: return "今日が締切"
                return f"{abs(delta)} 日超過"
            except ValueError:
                return ""

        # イベントでグループ化（順序保持）
        groups: dict[str, list[dict]] = {}
        for task in self._tasks:
            groups.setdefault(task["event"], []).append(task)

        total = len(self._tasks)
        done  = sum(1 for t in self._tasks if t.get("progress", 0) == 100)
        avg   = sum(t.get("progress", 0) for t in self._tasks) // total if total else 0

        lines: list[str] = []
        SEP2 = "-" * 50

        for event_name, task_list in groups.items():
            lines.append("")
            ev_done = sum(1 for t in task_list if t.get("progress", 0) == 100)
            lines.append(f"■ {event_name}  （{ev_done}/{len(task_list)} 完了）")
            lines.append(SEP2)

            for task in task_list:
                pct      = task.get("progress", 0)
                process  = task.get("process", "（プロセス名なし）")
                content  = task.get("content", "").strip()
                deadline = task.get("deadline", "")
                updated  = task.get("updated", "")
                wfs      = task.get("work_folders", [])
                if not wfs and task.get("work_folder"):
                    wfs = [task["work_folder"]]
                memos = task.get("memos", [])
                if not memos and task.get("memo"):
                    memos = [{"title": "Memo", "content": task["memo"]}]

                # 進捗バー（20文字幅）
                bar_filled = int(pct / 5)
                bar = "█" * bar_filled + "░" * (20 - bar_filled)

                lines.append(f"  ▶ {process}")
                lines.append(f"    進捗   : [{bar}] {pct}%")

                if deadline:
                    dl_note = days_left(deadline)
                    lines.append(f"    締切   : {deadline}  {dl_note}")
                if updated:
                    lines.append(f"    更新   : {updated}")
                if content:
                    # 内容は折り返して表示（60文字ごと）
                    for line in content.splitlines():
                        if line.strip():
                            lines.append(f"    内容   : {line}")
                if wfs:
                    for wf in wfs:
                        lines.append(f"    フォルダ: {wf}")
                if memos:
                    for memo in memos:
                        m_title   = memo.get("title", "Untitled")
                        m_content = memo.get("content", "").strip()
                        lines.append(f"    メモ [{m_title}]")
                        for ml in m_content.splitlines():
                            if ml.strip():
                                lines.append(f"      {ml}")
                lines.append("")

        Path(save_path).write_text("\n".join(lines), encoding="utf-8-sig")
        subprocess.Popen(["notepad", save_path])

    def _open_memo(self, task_idx: int):
        """タスクのメモ一覧・編集ウィンドウ（複数メモ対応）"""
        task = self._tasks[task_idx]

        # 旧形式 "memo" (str) → "memos" (list) 移行
        if "memo" in task and "memos" not in task:
            old = task.pop("memo", "")
            task["memos"] = ([{"title": "Memo", "content": old,
                                "created": datetime.date.today().isoformat()}]
                             if old else [])

        memos: list = task.setdefault("memos", [])

        win = tk.Toplevel(self)
        win.title(f"Memos — {task.get('event', '')}")
        win.configure(bg=C["bg"])
        win.geometry("580x400")
        win.resizable(True, True)

        # ── 左ペイン（メモ一覧）────────────────────────────
        left = tk.Frame(win, bg=C["bg"], width=170)
        left.pack(side="left", fill="y", padx=(10, 0), pady=10)
        left.pack_propagate(False)

        tk.Label(left, text="Memos", bg=C["bg"], fg=C["text"],
                 font=FONT_BOLD, anchor="w").pack(fill="x", pady=(0, 4))

        lb = tk.Listbox(left, font=FONT_SMALL,
                        bg="#F0EBF8", fg=C["text"],
                        selectbackground=C["accent_lt"],
                        selectforeground=C["accent_dk"],
                        relief="flat", bd=1, activestyle="none")
        lb.pack(fill="both", expand=True)
        for m in memos:
            lb.insert("end", m.get("title", "Untitled"))

        lb_btn = tk.Frame(left, bg=C["bg"])
        lb_btn.pack(fill="x", pady=(4, 0))
        _lb_btn_cfg = dict(relief="flat", bd=0, font=FONT_SMALL,
                           cursor="hand2", padx=6)
        new_btn = tk.Button(lb_btn, text="+ New",
                            bg=C["accent_lt"], fg=C["text"],
                            activebackground=C["border"], **_lb_btn_cfg)
        new_btn.pack(side="left", padx=(0, 2))
        del_btn = tk.Button(lb_btn, text="Delete",
                            bg=C["btn_del"], fg="white",
                            activebackground=C["btn_del_h"], **_lb_btn_cfg)
        del_btn.pack(side="left")

        # ── 区切り線 ────────────────────────────────────────
        tk.Frame(win, bg=C["border"], width=1).pack(
            side="left", fill="y", padx=(8, 0))

        # ── 右ペイン（編集エリア）───────────────────────────
        right = tk.Frame(win, bg=C["bg"])
        right.pack(side="left", fill="both", expand=True,
                   padx=(8, 10), pady=10)

        tk.Label(right, text="Title", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="w").pack(fill="x")
        title_var = tk.StringVar()
        title_entry = tk.Entry(right, textvariable=title_var, font=FONT,
                               bg="#F0EBF8", fg=C["text"], relief="flat", bd=1,
                               insertbackground=C["accent"])
        title_entry.pack(fill="x", pady=(0, 6))

        tk.Label(right, text="Content", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="w").pack(fill="x")
        txt = tk.Text(right, font=FONT, bg="#F0EBF8", fg=C["text"],
                      relief="flat", bd=1, insertbackground=C["accent"],
                      wrap="word", undo=True)
        txt.pack(fill="both", expand=True, pady=(0, 6))

        save_row = tk.Frame(right, bg=C["bg"])
        save_row.pack(fill="x")
        tk.Button(save_row, text="Save", command=lambda: _save_current(),
                  bg=C["accent"], fg="white", relief="flat", bd=0,
                  font=FONT_BOLD, cursor="hand2", padx=16, pady=3,
                  activebackground=C["accent_dk"],
                  activeforeground="white").pack(side="right")

        # ── ロジック ────────────────────────────────────────
        _sel = [-1]

        def _load(idx):
            _sel[0] = idx
            if 0 <= idx < len(memos):
                m = memos[idx]
                title_var.set(m.get("title", ""))
                txt.delete("1.0", "end")
                txt.insert("1.0", m.get("content", ""))
                txt.edit_reset()
            else:
                title_var.set("")
                txt.delete("1.0", "end")

        def _save_current():
            idx = _sel[0]
            if 0 <= idx < len(memos):
                memos[idx]["title"]   = title_var.get().strip() or "Untitled"
                memos[idx]["content"] = txt.get("1.0", "end-1c").strip()
                lb.delete(idx)
                lb.insert(idx, memos[idx]["title"])
                lb.selection_set(idx)
            self._save_tasks()

        def _new_memo():
            _save_current()
            new_m = {"title": "New Memo", "content": "",
                     "created": datetime.date.today().isoformat()}
            memos.append(new_m)
            lb.insert("end", new_m["title"])
            lb.selection_clear(0, "end")
            lb.selection_set("end")
            lb.see("end")
            _load(len(memos) - 1)
            title_entry.focus_set()
            title_entry.select_range(0, "end")

        def _delete_memo():
            idx = _sel[0]
            if idx < 0 or idx >= len(memos):
                return
            if not messagebox.askyesno(
                    "Delete", f"Delete \"{memos[idx]['title']}\"?", parent=win):
                return
            memos.pop(idx)
            lb.delete(idx)
            self._save_tasks()
            if memos:
                new_idx = min(idx, len(memos) - 1)
                lb.selection_set(new_idx)
                _load(new_idx)
            else:
                _load(-1)

        def _on_lb_select(_e):
            sel = lb.curselection()
            if sel:
                _save_current()
                _load(sel[0])

        lb.bind("<<ListboxSelect>>", _on_lb_select)
        new_btn.configure(command=_new_memo)
        del_btn.configure(command=_delete_memo)

        win.bind("<Control-s>", lambda e: _save_current())
        win.protocol("WM_DELETE_WINDOW", lambda: (_save_current(), win.destroy()))

        if memos:
            lb.selection_set(0)
            _load(0)

    def _rename_event(self, old_name: str):
        dlg = InputDialog(self, "Rename Event", f"New name for '{old_name}':", old_name)
        new_name = dlg.result
        if not new_name or new_name == old_name:
            return
        for task in self._tasks:
            if task["event"] == old_name:
                task["event"] = new_name
        self._save_tasks()
        self._render_list()

    # ── Notify list ───────────────────────────────────────

    def _render_notify_list(self):
        now = datetime.datetime.now()

        # Upcoming / Past に分類
        # Past = 時刻が過去 かつ recurrence == "none"
        upcoming: list[tuple[int, dict]] = []
        past:     list[tuple[int, dict]] = []
        for i, item in enumerate(self._notify_items):
            try:
                sched = datetime.datetime.fromisoformat(item.get("scheduled_at", ""))
                if sched < now and item.get("recurrence", "none") == "none":
                    past.append((i, item))
                else:
                    upcoming.append((i, item))
            except ValueError:
                upcoming.append((i, item))

        if not upcoming and not past:
            tk.Label(
                self._list_frame,
                text="No notifications registered.\nClick \"+ Add Notification\" to add one.",
                bg=C["bg"], fg=C["text_sub"],
                font=FONT_SMALL, justify="center",
            ).pack(pady=20)
            return

        # ── Upcoming ──
        for i, item in upcoming:
            self._make_notify_card(i, item, now, parent=self._list_frame)

        # ── Past（折りたたみ可能）──
        if past:
            tk.Frame(self._list_frame, bg=C["border"], height=1).pack(
                fill="x", padx=2, pady=(8, 0))

            past_frame = tk.Frame(self._list_frame, bg=C["bg"])

            arrow  = "▼" if self._notify_past_open else "▶"
            toggle = tk.Label(
                self._list_frame,
                text=f"{arrow}  Past  ({len(past)})",
                bg=C["bg"], fg=C["text_sub"],
                font=FONT_SMALL, cursor="hand2", anchor="w",
            )
            toggle.pack(fill="x", padx=6, pady=(2, 0))

            def _toggle_past(lbl=toggle, frame=past_frame):
                self._notify_past_open = not self._notify_past_open
                if self._notify_past_open:
                    lbl.configure(text=f"▼  Past  ({len(past)})")
                    frame.pack(fill="x")
                else:
                    lbl.configure(text=f"▶  Past  ({len(past)})")
                    frame.pack_forget()

            toggle.bind("<Button-1>", lambda e: _toggle_past())

            for i, item in past:
                self._make_notify_card(i, item, now, parent=past_frame, dim=True)

            if self._notify_past_open:
                past_frame.pack(fill="x")

    def _make_notify_card(self, idx: int, item: dict, now: datetime.datetime,
                          parent: tk.Frame | None = None, dim: bool = False):
        if parent is None:
            parent = self._list_frame

        sched_str = item.get("scheduled_at", "")
        title     = item.get("title", "")

        try:
            sched = datetime.datetime.fromisoformat(sched_str)
            delta_s = int((sched - now).total_seconds())
            if delta_s < 0:
                time_label = f"{sched_str}  (passed)"
            elif delta_s < 3600:
                time_label = f"{sched_str}  ({delta_s // 60}m left)"
            elif delta_s < 86400:
                time_label = f"{sched_str}  ({delta_s // 3600}h left)"
            else:
                time_label = f"{sched_str}  ({delta_s // 86400}d left)"
        except ValueError:
            time_label = sched_str

        card_bg = C["bg"] if dim else C["card"]
        card = tk.Frame(parent, bg=card_bg,
                        pady=4, padx=8, relief="flat", bd=0,
                        highlightthickness=1, highlightbackground=C["border"])
        card.pack(fill="x", pady=2, padx=2)

        left = tk.Frame(card, bg=card_bg)
        left.pack(side="left", fill="both", expand=True)

        title_row = tk.Frame(left, bg=card_bg)
        title_row.pack(fill="x")
        tk.Label(title_row, text=title,
                 bg=card_bg, fg=C["text_sub"] if dim else C["text"],
                 font=FONT_BOLD, anchor="w").pack(side="left")
        recur = item.get("recurrence", "none")
        recur_text = {"daily": "Daily", "weekly": "Weekly", "monthly": "Monthly"}.get(recur, "")
        if recur_text:
            tk.Label(title_row, text=recur_text,
                     bg=C["accent_lt"], fg=C["accent_dk"],
                     font=FONT_SMALL, padx=4, pady=1, relief="flat",
                     ).pack(side="left", padx=(6, 0))

        tk.Label(left, text=time_label,
                 bg=card_bg, fg=C["text_sub"],
                 font=FONT_SMALL, anchor="w").pack(fill="x")
        open_paths = item.get("open_paths", [])
        if not open_paths and item.get("open_path"):
            open_paths = [item["open_path"]]
        if open_paths:
            op_label = (f"Opens: {os.path.basename(open_paths[0]) or open_paths[0]}"
                        if len(open_paths) == 1 else f"Opens: {len(open_paths)} items")
            tk.Label(left, text=op_label,
                     bg=card_bg, fg=C["accent_dk"],
                     font=FONT_SMALL, anchor="w").pack(fill="x")
        notes = item.get("notes", "")
        if notes:
            tk.Label(left, text=notes,
                     bg=card_bg, fg=C["text_sub"],
                     font=FONT_SMALL, anchor="w").pack(fill="x")

        del_btn = tk.Button(
            card, text="✕",
            command=lambda i=idx: self._remove_notify_item(i),
            bg=card_bg, fg=C["btn_del"],
            relief="flat", bd=0,
            font=("Segoe UI", 11), cursor="hand2",
            activebackground=card_bg, activeforeground=C["btn_del_h"],
        )
        del_btn.pack(side="right", padx=(6, 0))

        edit_btn = tk.Button(
            card, text="Edit",
            command=lambda i=idx: self._edit_notify_item(i),
            bg=card_bg, fg=C["text_sub"],
            relief="flat", bd=0,
            font=FONT_SMALL, cursor="hand2",
            activebackground=card_bg, activeforeground=C["text"],
        )
        edit_btn.pack(side="right", padx=(0, 2))

        preview_btn = tk.Button(
            card, text="Preview",
            command=lambda i=idx: NotificationPopup(self, self._notify_items[i], self._notify_display_sec.get() * 1000),
            bg=card_bg, fg=C["text_sub"],
            relief="flat", bd=0,
            font=FONT_SMALL, cursor="hand2",
            activebackground=card_bg, activeforeground=C["text"],
        )
        preview_btn.pack(side="right", padx=(0, 2))

    # ── Notify operations ─────────────────────────────────

    def _add_notify_item(self):
        dlg = NotifyDialog(self)
        if dlg.result is None:
            return
        self._notify_items.append(dlg.result)
        self._save_notify()
        self._render_list()
        self._update_banner()

    def _edit_notify_item(self, idx: int):
        dlg = NotifyDialog(self, initial=self._notify_items[idx])
        if dlg.result is None:
            return
        self._notify_items[idx] = dlg.result
        self._save_notify()
        self._render_list()
        self._update_banner()

    def _remove_notify_item(self, idx: int):
        title = self._notify_items[idx].get("title", "")
        if messagebox.askyesno("Remove", f"Remove \"{title}\"?", parent=self):
            self._notify_items.pop(idx)
            self._save_notify()
            self._render_list()
            self._update_banner()

    # ── Theme ─────────────────────────────────────────────

    def _show_theme_menu(self):
        menu = tk.Menu(self, tearoff=0)
        labels = {"lavender": "Lavender", "dark": "Dark", "light": "Light", "gemini": "Gemini", "claude": "Claude", "devil": "Devil"}
        for key, label in labels.items():
            prefix = "✓ " if self._theme == key else "  "
            menu.add_command(
                label=prefix + label,
                command=lambda k=key: self._apply_theme(k),
            )
        btn = self._theme_btn
        menu.tk_popup(btn.winfo_rootx(), btn.winfo_rooty() + btn.winfo_height())

    def _apply_theme(self, theme_name: str):
        if theme_name not in THEMES:
            return
        self._theme = theme_name
        C.update(THEMES[theme_name])
        self._save_config()

        # _tick() の after ループをキャンセル（二重ループ防止）
        if self._tick_id is not None:
            self.after_cancel(self._tick_id)
            self._tick_id = None

        # アイコンをテーマカラーで再生成
        palette = ICON_PALETTES.get(theme_name)
        png_b64 = _make_icon_png(palette)
        self._icon = tk.PhotoImage(data=png_b64)
        self.wm_iconphoto(True, self._icon)
        _setup_taskbar_icon(self, palette)

        # 全ウィジェットを破棄して再構築
        for w in self.winfo_children():
            w.destroy()
        self.configure(bg=C["bg"])

        self._build_ui()
        self._render_tabs()
        self._render_list()

    # ── Other ─────────────────────────────────────────────

    def _tick(self):
        self._clock_var.set(datetime.datetime.now().strftime("%H:%M:%S"))
        self._update_banner()
        self._tick_id = self.after(1000, self._tick)

    def _update_banner(self):
        """次の通知をバナーラベルに表示する。"""
        if not hasattr(self, "_banner_lbl"):
            return
        if not self._banner_enabled.get():
            self._banner_lbl.configure(text="")
            return
        now = datetime.datetime.now()
        upcoming = []
        for item in self._notify_items:
            try:
                sched = datetime.datetime.fromisoformat(item.get("scheduled_at", ""))
                if sched > now:
                    upcoming.append((sched, item))
            except ValueError:
                pass
        if not upcoming:
            self._banner_lbl.configure(text="")
            return
        upcoming.sort(key=lambda x: x[0])
        sched, item = upcoming[0]
        delta_s = int((sched - now).total_seconds())
        if delta_s < 60:
            remaining = f"{delta_s}s"
        elif delta_s < 3600:
            remaining = f"{delta_s // 60}m"
        elif delta_s < 86400:
            remaining = f"{delta_s // 3600}h"
        else:
            remaining = f"{delta_s // 86400}d"
        title    = item.get("title", "")
        time_str = sched.strftime("%H:%M")
        self._banner_lbl.configure(text=f"  {title}  {time_str}  ({remaining})  ")

    def _open_recording(self):
        RecordingWindow(self)

    def _open_screenshot(self):
        if self._show_options.get():
            ScreenshotWindow(self)
        else:
            # quick capture with defaults (all screens, Pictures, hide launcher)
            self.iconify()
            self.after(300, self._default_capture)

    def _default_capture(self):
        save_dir = Path.home() / "Pictures"
        img = ImageGrab.grab(all_screens=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = save_dir / f"screenshot_all_{ts}.png"
        img.save(filename)
        self.deiconify()
        subprocess.Popen(["explorer", str(save_dir)])

    def _open_folder(self, path: str):
        if not os.path.isdir(path):
            messagebox.showwarning("Error", f"Folder not found:\n{path}", parent=self)
            return
        subprocess.Popen(["explorer", os.path.normpath(path)])

    def _open_item(self, path: str, item_type: str):
        if item_type == "file":
            if not os.path.isfile(path):
                messagebox.showwarning("Error", f"File not found:\n{path}", parent=self)
                return
            os.startfile(path)
        else:
            if not os.path.isdir(path):
                messagebox.showwarning("Error", f"Folder not found:\n{path}", parent=self)
                return
            subprocess.Popen(["explorer", os.path.normpath(path)])

    def _check_schedule(self):
        """スケジュール通知を定期チェック（30秒ごと）"""
        now = datetime.datetime.now()
        updated = False
        for i, item in enumerate(self._notify_items):
            sched_str = item.get("scheduled_at", "")
            if not sched_str:
                continue
            try:
                sched = datetime.datetime.fromisoformat(sched_str)
            except ValueError:
                continue
            notify_before = item.get("notify_before", 5)
            notify_at = sched - datetime.timedelta(minutes=notify_before)
            key = f"{i}_{sched_str}"
            if notify_at <= now < sched and key not in self._notified:
                self._notified.add(key)
                NotificationPopup(self, item, self._notify_display_sec.get() * 1000)
                open_paths = item.get("open_paths", [])
                if not open_paths and item.get("open_path"):
                    open_paths = [item["open_path"]]
                for op in open_paths:
                    try:
                        if os.path.isdir(op):
                            subprocess.Popen(["explorer", op])
                        else:
                            os.startfile(op)
                    except Exception:
                        pass
            # スケジュール時刻を過ぎたら、繰り返し設定に従い次回日時へ更新
            if now >= sched:
                self._notified.discard(key)
                recurrence = item.get("recurrence", "none")
                if recurrence == "daily":
                    next_sched = sched + datetime.timedelta(days=1)
                    item["scheduled_at"] = next_sched.strftime("%Y-%m-%d %H:%M")
                    updated = True
                elif recurrence == "weekly":
                    next_sched = sched + datetime.timedelta(weeks=1)
                    item["scheduled_at"] = next_sched.strftime("%Y-%m-%d %H:%M")
                    updated = True
                elif recurrence == "monthly":
                    # 月末対応: 翌月の末日を超えないよう調整
                    year, month = sched.year, sched.month
                    month += 1
                    if month > 12:
                        month = 1
                        year += 1
                    last_day = calendar.monthrange(year, month)[1]
                    day = min(sched.day, last_day)
                    next_sched = sched.replace(year=year, month=month, day=day)
                    item["scheduled_at"] = next_sched.strftime("%Y-%m-%d %H:%M")
                    updated = True
        if updated:
            self._save_notify()
            if self._active == -3:
                self._render_list()
        self.after(30000, self._check_schedule)


# ── Login window ──────────────────────────────────────────

class LoginWindow(tk.Tk):
    _USER = "admin"
    _HASH = hashlib.sha256(b"nanahira").hexdigest()

    def __init__(self):
        super().__init__()
        self.title("Gem")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.authenticated = False

        self._icon = tk.PhotoImage(data=_make_icon_png())
        _setup_taskbar_icon(self)

        self._build()

        self.update_idletasks()
        w  = self.winfo_width()
        h  = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    def _build(self):
        W = 300

        # ── デコレーションヘッダー Canvas ──
        cv = tk.Canvas(self, width=W, height=175,
                       bg=C["accent_lt"], highlightthickness=0)
        cv.pack(fill="x")

        # 背景装飾：大きめの薄い円
        cv.create_oval(-40, -40,  130,  130, fill="#D8D0F0", outline="")
        cv.create_oval(200, 100,  360,  230, fill="#C8BAE8", outline="")
        cv.create_oval(240, -20,  320,   60, fill="#DDD5F4", outline="")

        # アイコン（2倍ズーム）
        icon_big = self._icon.zoom(2)
        self._login_icon = icon_big   # GC対策
        cv.create_image(W // 2, 75, image=icon_big)

        # タイトル・サブタイトル
        cv.create_text(W // 2, 118, text="Gem",
                       fill=C["accent_dk"], font=("Segoe UI", 20, "bold"))

        # ── 入力カード ──
        card = tk.Frame(self, bg=C["card"],
                        highlightthickness=1, highlightbackground=C["border"])
        card.pack(fill="x", padx=22, pady=(18, 0))

        inner = tk.Frame(card, bg=C["card"])
        inner.pack(fill="x", padx=18, pady=14)

        def _field(label_text, var, show=None):
            tk.Label(inner, text=label_text, bg=C["card"], fg=C["text_sub"],
                     font=FONT_SMALL, anchor="w").pack(fill="x")
            kw = {"show": show} if show else {}
            e = tk.Entry(inner, textvariable=var, font=FONT,
                         bg=C["card"], fg=C["text"], relief="flat", bd=0,
                         insertbackground=C["accent"], width=22, **kw)
            e.pack(fill="x", pady=(2, 0), ipady=5)
            tk.Frame(inner, bg=C["accent_lt"], height=2).pack(fill="x", pady=(1, 12))
            return e

        self._user_var = tk.StringVar()
        _field("Username", self._user_var)

        self._pw_var = tk.StringVar()
        pw_e = _field("Password", self._pw_var, show="●")
        pw_e.bind("<Return>", lambda e: self._login())

        # エラーメッセージ
        self._err_var = tk.StringVar()
        tk.Label(self, textvariable=self._err_var,
                 bg=C["bg"], fg="#B84060",
                 font=FONT_SMALL).pack(pady=(8, 0))

        # ログインボタン
        btn = tk.Button(self, text="Login  →", command=self._login,
                        bg=C["accent"], fg="white", relief="flat", bd=0,
                        font=("Segoe UI", 10, "bold"), cursor="hand2",
                        padx=32, pady=8,
                        activebackground=C["accent_dk"], activeforeground="white")
        btn.pack(pady=(8, 22))
        btn.bind("<Enter>", lambda e: btn.configure(bg=C["accent_dk"]))
        btn.bind("<Leave>", lambda e: btn.configure(bg=C["accent"]))

    def _login(self):
        user = self._user_var.get().strip()
        pw   = self._pw_var.get()
        if (user == self._USER and
                hashlib.sha256(pw.encode()).hexdigest() == self._HASH):
            self.authenticated = True
            self.destroy()
        else:
            self._err_var.set("✕  Invalid username or password")
            self._pw_var.set("")
            self._shake()

    def _shake(self, n: int = 8, d: int = 7):
        """ウィンドウを左右に揺らすアニメーション。"""
        if n <= 0:
            return
        x, y = self.winfo_x(), self.winfo_y()
        offset = d if n % 2 == 0 else -d
        self.geometry(f"+{x + offset}+{y}")
        self.after(35, lambda: self._shake(n - 1, d))


# ── Utilities ─────────────────────────────────────────────

def _hover(widget, on_color, off_color):
    widget.bind("<Enter>", lambda e: widget.config(bg=on_color))
    widget.bind("<Leave>", lambda e: widget.config(bg=off_color))

def _set_bg(frame: tk.Frame, color: str):
    frame.configure(bg=color)
    for child in frame.winfo_children():
        try:
            child.configure(bg=color)
        except Exception:
            pass


if __name__ == "__main__":
    login = LoginWindow()
    login.mainloop()
    if login.authenticated:
        app = FolderLauncher()
        app.mainloop()
