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
from PIL import ImageGrab, Image
import pystray

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
    "violet": {   # デフォルト（既存 C と同値）
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
    "scarlet": {   # 小悪魔：漆黒＋クリムゾンレッド
        "bg": "#1A0A0E", "card": "#240F14", "card_h": "#331520",
        "accent": "#CC2244", "accent_dk": "#991833", "accent_lt": "#E06078",
        "text": "#F5E8EA", "text_sub": "#C09098", "border": "#4A1A25",
        "tab_act": "#240F14", "tab_inact": "#1E0B10",
        "btn_del": "#882030", "btn_del_h": "#BB3045",
    },
    "ocean": {   # 深海ブルー
        "bg": "#0D1B2A", "card": "#1A2940", "card_h": "#243550",
        "accent": "#2196C4", "accent_dk": "#1570A0", "accent_lt": "#5BB8D4",
        "text": "#C8E8F5", "text_sub": "#7AAFC8", "border": "#2A4060",
        "tab_act": "#1A2940", "tab_inact": "#152030",
        "btn_del": "#8B3A3A", "btn_del_h": "#B04848",
    },
    "rose": {   # ローズピンク
        "bg": "#FDF0F3", "card": "#FFFFFF", "card_h": "#FFE4EC",
        "accent": "#E0608A", "accent_dk": "#C0407A", "accent_lt": "#F0A0BC",
        "text": "#4A1A2A", "text_sub": "#A06080", "border": "#F0C0D0",
        "tab_act": "#FFFFFF", "tab_inact": "#FAE0E8",
        "btn_del": "#E06080", "btn_del_h": "#C04060",
    },
    "mint": {   # ミントグリーン
        "bg": "#F0FAF5", "card": "#FFFFFF", "card_h": "#D8F5E8",
        "accent": "#3DAA78", "accent_dk": "#2A8A60", "accent_lt": "#80CCA8",
        "text": "#1A3A28", "text_sub": "#5A8A70", "border": "#B0E0C8",
        "tab_act": "#FFFFFF", "tab_inact": "#E0F5EC",
        "btn_del": "#C06060", "btn_del_h": "#A04040",
    },
    "peach": {   # ピーチ：暖かみのあるオレンジ〜ピンクパステル
        "bg": "#FFF5EE", "card": "#FFFAF7", "card_h": "#FFE8D8",
        "accent": "#E8845A", "accent_dk": "#C86030", "accent_lt": "#F5C0A0",
        "text": "#4A2010", "text_sub": "#A06848", "border": "#F5D0B8",
        "tab_act": "#FFFAF7", "tab_inact": "#FFE8D8",
        "btn_del": "#D05050", "btn_del_h": "#A83030",
    },
    "sky": {   # スカイブルー：さわやかな水色パステル
        "bg": "#EEF7FF", "card": "#F5FBFF", "card_h": "#D4EDFF",
        "accent": "#4DA8DA", "accent_dk": "#2A88BE", "accent_lt": "#9DD4F0",
        "text": "#0C2C44", "text_sub": "#4A80A8", "border": "#B0D8F0",
        "tab_act": "#F5FBFF", "tab_inact": "#DCF0FF",
        "btn_del": "#C05870", "btn_del_h": "#A03858",
    },
    "lemon": {   # レモン：明るく元気なイエローパステル
        "bg": "#FDFCE8", "card": "#FFFFF0", "card_h": "#F5F0B8",
        "accent": "#C8A800", "accent_dk": "#A08800", "accent_lt": "#E8D870",
        "text": "#383000", "text_sub": "#787040", "border": "#E8DC90",
        "tab_act": "#FFFFF0", "tab_inact": "#F5EEC0",
        "btn_del": "#C06040", "btn_del_h": "#A04020",
    },
    "lavender": {   # ラベンダー：やさしい紫パステル（violetより淡め）
        "bg": "#F3F0FF", "card": "#FAF8FF", "card_h": "#E4DEFF",
        "accent": "#9B88D8", "accent_dk": "#7A66C0", "accent_lt": "#C8BCEE",
        "text": "#2E2460", "text_sub": "#7868B0", "border": "#D0C8F0",
        "tab_act": "#FAF8FF", "tab_inact": "#E8E0FF",
        "btn_del": "#C888B0", "btn_del_h": "#A86898",
    },
    "sakura": {   # サクラ：桜色の淡いピンク
        "bg": "#FFF0F5", "card": "#FFF8FA", "card_h": "#FFD8E8",
        "accent": "#E87898", "accent_dk": "#C85878", "accent_lt": "#F5B0C8",
        "text": "#4A1828", "text_sub": "#A06888", "border": "#F0C0D4",
        "tab_act": "#FFF8FA", "tab_inact": "#FFE0EC",
        "btn_del": "#D05878", "btn_del_h": "#B03858",
    },
}

ICON_PALETTES: dict[str, dict] = {
    "violet": {
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
    "scarlet": {
        "BDR": ( 60,   8,  15, 255), "HL": (240, 160, 175, 255),
        "LT":  (210,  90, 115, 255), "F":  (180,  28,  60, 255),
        "MD":  (130,  18,  42, 255), "DK": ( 75,   8,  22, 255),
        "SP":  (220, 100, 120, 200),
    },
    "ocean": {
        "BDR": (  8,  30,  55, 255), "HL": ( 91, 184, 212, 255),
        "LT":  ( 55, 150, 195, 255), "F":  ( 33, 150, 196, 255),
        "MD":  ( 21, 112, 160, 255), "DK": ( 10,  65, 105, 255),
        "SP":  (100, 200, 230, 200),
    },
    "rose": {
        "BDR": ( 90,  20,  45, 255), "HL": (245, 185, 210, 255),
        "LT":  (235, 150, 185, 255), "F":  (224,  96, 138, 255),
        "MD":  (192,  64, 122, 255), "DK": (130,  30,  80, 255),
        "SP":  (250, 190, 215, 210),
    },
    "mint": {
        "BDR": ( 18,  65,  42, 255), "HL": (155, 220, 190, 255),
        "LT":  (105, 195, 155, 255), "F":  ( 61, 170, 120, 255),
        "MD":  ( 42, 138,  96, 255), "DK": ( 22,  88,  60, 255),
        "SP":  (140, 215, 175, 210),
    },
    "peach": {
        "BDR": (120,  50,  20, 255), "HL": (250, 210, 185, 255),
        "LT":  (240, 175, 145, 255), "F":  (232, 132,  90, 255),
        "MD":  (200,  96,  48, 255), "DK": (140,  55,  22, 255),
        "SP":  (248, 200, 170, 210),
    },
    "sky": {
        "BDR": ( 12,  50,  90, 255), "HL": (157, 212, 245, 255),
        "LT":  (100, 185, 230, 255), "F":  ( 77, 168, 218, 255),
        "MD":  ( 42, 136, 190, 255), "DK": ( 18,  90, 140, 255),
        "SP":  (155, 215, 248, 210),
    },
    "lemon": {
        "BDR": ( 90,  75,   0, 255), "HL": (245, 235, 130, 255),
        "LT":  (228, 210,  80, 255), "F":  (200, 168,   0, 255),
        "MD":  (160, 136,   0, 255), "DK": (100,  85,   0, 255),
        "SP":  (242, 232, 120, 210),
    },
    "lavender": {
        "BDR": ( 46,  36, 100, 255), "HL": (210, 200, 245, 255),
        "LT":  (185, 172, 232, 255), "F":  (155, 136, 216, 255),
        "MD":  (122, 102, 192, 255), "DK": ( 78,  62, 145, 255),
        "SP":  (210, 200, 245, 210),
    },
    "sakura": {
        "BDR": ( 95,  30,  55, 255), "HL": (252, 195, 218, 255),
        "LT":  (242, 165, 195, 255), "F":  (232, 120, 152, 255),
        "MD":  (200,  88, 120, 255), "DK": (140,  45,  80, 255),
        "SP":  (250, 195, 220, 210),
    },
}

FONT       = ("Segoe UI", 10)
FONT_BOLD  = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 8)

CLIP_MAX = 50   # クリップボード履歴の最大保持件数


def _fmt_duration(seconds: float) -> str:
    """秒数を '2h 30m' 形式の文字列に変換する。"""
    seconds = int(seconds)
    h, m = divmod(seconds // 60, 60)
    if h:
        return f"{h}h {m:02d}m"
    return f"{m}m"


# ── Icon generation ───────────────────────────────────────

def _make_icon_png(palette: dict | None = None) -> str:
    """輪郭線付きクラゲアイコン PNG を生成して Base64 返却する。"""
    p = palette or ICON_PALETTES["violet"]
    W, H = 32, 32
    T   = (  0,   0,   0,   0)  # transparent
    BDR = p["BDR"]               # dark outline
    WH  = (255, 254, 255, 255)  # shine white（常に白）
    HL  = p["HL"]                # highlight
    LT  = p["LT"]                # light
    F   = p["F"]                 # main
    MD  = p["MD"]                # mid shadow
    DK  = p["DK"]                # deep shadow
    SP  = p["SP"]                # sparkle

    # クラゲのベル（頭部）輪郭 {y: (x_left, x_right)} 両端含む
    BELL = {
         2: (13, 18),  # 頂点
         3: (10, 21),
         4: (8,  23),
         5: (6,  25),
         6: (4,  27),
         7: (3,  28),
         8: (2,  29),
         9: (2,  29),
        10: (2,  29),
        11: (2,  29),
        12: (3,  28),
        13: (4,  27),
        14: (5,  26),  # ベル底部
    }

    def in_bell(x, y):
        if y not in BELL: return False
        lo, hi = BELL[y]
        return lo <= x <= hi

    def is_bell_edge(x, y):
        if not in_bell(x, y): return False
        return any(not in_bell(x+dx, y+dy)
                   for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)))

    # 触手ピクセル（5本、波打ちながら下に伸びる）
    TENTACLE: set[tuple[int, int]] = set()
    TENTACLE_EDGE: set[tuple[int, int]] = set()
    for base_x in (7, 11, 15, 19, 23):
        for dy in range(14):
            y = 15 + dy
            if y >= H: break
            wave = (dy // 2) % 2
            x = base_x + wave
            TENTACLE.add((x, y))
            TENTACLE.add((x + 1, y))  # 2px 幅で視認性確保
    # 触手の輪郭（隣接する透明ピクセルのみ）
    for tx, ty in TENTACLE:
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = tx+dx, ty+dy
            if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in TENTACLE:
                TENTACLE_EDGE.add((nx, ny))

    # 光沢スポット（左上ベル内部）
    SHINE    = {(12,4),(13,4),(11,5),(12,5)}
    SHINE_HL = {(14,4),(11,6),(12,6),(13,6)}

    def px(x, y):
        # 触手本体
        if (x, y) in TENTACLE:
            return F
        # 触手輪郭（ベル領域と重ならない部分のみ）
        if (x, y) in TENTACLE_EDGE and not in_bell(x, y):
            return BDR
        if not in_bell(x, y):
            return T
        # 光沢 → 輪郭 → グラデーション の順に判定
        if (x, y) in SHINE:       return WH
        if (x, y) in SHINE_HL:    return HL
        if is_bell_edge(x, y):    return BDR
        dx = x - 15
        if y <= 6:    # 頂部: 明るく
            if dx <= -4: return LT
            if dx >= 4:  return F
            return HL
        if y <= 10:   # 中部
            if dx <= -4: return HL
            if dx >= 4:  return F
            return LT
        # 底部: やや暗め
        if dx <= -3: return MD
        if dx >= 3:  return F
        return MD

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


_gem_ico_path: str | None = None  # 全 Toplevel に自動適用するため保持


def _setup_taskbar_icon(root: tk.Tk, palette: dict | None = None) -> None:
    """AppUserModelID を設定し、ICO ファイルでタスクバーアイコンを適用する。"""
    global _gem_ico_path
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
        _gem_ico_path = str(ico_path)
        def _apply(path=ico_path):
            try:
                root.wm_iconbitmap(str(path))
            except Exception:
                pass
        _apply()
        # ウィンドウ表示後に確実に適用（タイミングずれ対策）
        root.after(200, _apply)


# Toplevel 生成時に自動でアイコンを適用するモンキーパッチ
_orig_toplevel_init = tk.Toplevel.__init__

def _patched_toplevel_init(self, master=None, **kwargs):
    _orig_toplevel_init(self, master, **kwargs)
    if _gem_ico_path:
        try:
            self.wm_iconbitmap(_gem_ico_path)
        except Exception:
            pass

tk.Toplevel.__init__ = _patched_toplevel_init


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
                     bg=C["card"], fg=C["text"], relief="flat", bd=1,
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
        _, self._pw_entry = self._row("Password", 5, self._pw, show="*")
        self._show_pw = False
        self._pw_toggle = tk.Button(
            self._form, text="show", font=("Segoe UI", 8),
            bg=C["bg"], fg=C["text_sub"], relief="flat", bd=0,
            cursor="hand2", command=self._toggle_pw,
        )
        self._pw_toggle.grid(row=5, column=2, padx=(0, 4), pady=3)

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
            bg=C["card"], fg=C["text"], relief="flat", bd=1,
            insertbackground=C["accent"],
            width=24, height=5,
            wrap="none",
        )
        self._cmd_text.insert("1.0", self._init_cmds)
        self._cmd_text.grid(row=8, column=1, padx=(0, 12), pady=(6, 3), sticky="ew")
        hint_row = tk.Frame(self._form, bg=C["bg"])
        hint_row.grid(row=9, column=1, padx=(0, 12), pady=(0, 2), sticky="ew")
        self._cmd_hint = tk.Label(hint_row, text="One command per line\nExecuted after login",
                                  bg=C["bg"], fg=C["text_sub"],
                                  font=("Segoe UI", 7), justify="left")
        self._cmd_hint.pack(side="left")
        tk.Button(hint_row, text="Import...", command=self._import_cmd_file,
                  bg=C["card"], fg=C["text_sub"], relief="flat", bd=0,
                  font=("Segoe UI", 7), cursor="hand2", padx=6, pady=1,
                  activebackground=C["card_h"], activeforeground=C["text"],
                  ).pack(side="right")

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

    def _import_cmd_file(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="コマンドファイルを選択",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            messagebox.showerror("Import Error", str(e), parent=self)
            return
        # 既存の内容に追記（末尾に空行を挟む）
        current = self._cmd_text.get("1.0", "end-1c").rstrip("\n")
        new_lines = text.rstrip("\n")
        merged = (current + "\n" + new_lines) if current else new_lines
        self._cmd_text.delete("1.0", "end")
        self._cmd_text.insert("1.0", merged)

    def _toggle_pw(self):
        self._show_pw = not self._show_pw
        self._pw_entry.config(show="" if self._show_pw else "*")
        self._pw_toggle.config(
            text="hide" if self._show_pw else "show",
            fg=C["accent"] if self._show_pw else C["text_sub"],
        )

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
                     bg=C["card"], fg=C["text"], relief="flat", bd=1,
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
        self._recur_var    = tk.StringVar(value=d.get("recur", "none"))
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
                     bg=C["card"], fg=C["text"], relief="flat", bd=1,
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
                        fieldbackground=C["card"], background=C["accent_lt"],
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
            bg=C["card"], fg=C["text"], relief="flat", bd=1,
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
        _spin_cfg = dict(font=FONT, bg=C["card"], fg=C["text"], relief="flat", bd=1,
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
            bg=C["card"], fg=C["text"], selectbackground=C["accent_lt"],
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

        # Recur row
        tk.Label(self._form, text="Recur", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="e", width=9).grid(
                     row=6, column=0, padx=(12, 4), pady=3, sticky="e")
        recur_frame = tk.Frame(self._form, bg=C["bg"])
        recur_frame.grid(row=6, column=1, padx=(0, 12), pady=3, sticky="w")
        for val, lbl in [("none", "None"), ("daily", "Daily"), ("weekly", "Weekly"),
                         ("biweekly", "Biweekly"), ("monthly", "Monthly"), ("yearly", "Yearly")]:
            tk.Radiobutton(recur_frame, text=lbl, variable=self._recur_var, value=val,
                           bg=C["bg"], fg=C["text"], selectcolor=C["bg"],
                           activebackground=C["bg"], font=FONT_SMALL,
                           cursor="hand2").pack(side="left", padx=(0, 6))

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
            state, bg = "normal", C["card"]
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
            "event":        self._event_var.get().strip(),
            "process":      self._process_var.get().strip(),
            "content":      self._content_text.get("1.0", "end").strip(),
            "progress":     self._progress_var.get(),
            "deadline":     deadline,
            "work_folders": list(self._work_folders_list),
            "recur":        self._recur_var.get(),
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
            cv.create_text(10, y + ROW_H // 2, text=f"> {event_name}",
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
                 font=("Consolas", 8), bg=C["card"], fg=C["text"],
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
                 font=("Consolas", 8), bg=C["card"], fg=C["text"],
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
        inner = tk.Frame(self, bg=C["card"])
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
        content = tk.Frame(inner, bg=C["card"])
        content.pack(fill="both", expand=True, padx=14, pady=(10, 12))

        # タイトル
        title = task.get("title", "")
        tk.Label(content, text=title,
                 bg=C["card"], fg=C["text"],
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
                     bg=C["card"], fg=C["accent"],
                     font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x")

        # 起動パス
        open_paths = task.get("open_paths", [])
        if not open_paths and task.get("open_path"):
            open_paths = [task["open_path"]]
        if open_paths:
            tk.Frame(content, bg=C["border"], height=1).pack(fill="x", pady=(6, 0))
            names = "  /  ".join(os.path.basename(p) or p for p in open_paths)
            tk.Label(content, text=f"Opens: {names}",
                     bg=C["card"], fg=C["accent_dk"],
                     font=FONT_SMALL, anchor="w",
                     wraplength=240, justify="left").pack(fill="x", pady=(4, 0))

        # メモ
        notes = task.get("notes", "")
        if notes:
            tk.Frame(content, bg=C["border"], height=1).pack(fill="x", pady=(6, 0))
            tk.Label(content, text=notes,
                     bg=C["card"], fg=C["text_sub"],
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
                     bg=C["card"], fg=C["text"], relief="flat", bd=1,
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

        _spin_cfg = dict(font=FONT, bg=C["card"], fg=C["text"], relief="flat", bd=1,
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
                   bg=C["card"], fg=C["text"], relief="flat", bd=1,
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
            bg=C["card"], fg=C["text"], selectbackground=C["accent_lt"],
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
            bg=C["card"], fg=C["text"], relief="flat", bd=1,
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
                         font=FONT, bg=C["card"], fg=C["text"],
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


class RuleDialog(tk.Toplevel):
    """Dialog for adding/editing automation rules."""

    def __init__(self, parent, initial: dict | None = None,
                 conn_names: list[str] | None = None):
        super().__init__(parent)
        self.title("Edit Rule" if initial else "Add Rule")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.result: dict | None = None
        self._conn_names = conn_names or []

        d = initial or {}
        trig = d.get("trigger", {})
        act  = d.get("action",  {})

        # ── Variables ─────────────────────────────────────
        self._name_var     = tk.StringVar(value=d.get("name", ""))
        self._trig_type    = tk.StringVar(value=trig.get("type", "time"))
        self._schedule     = tk.StringVar(value=trig.get("schedule", "daily"))
        self._weekday      = tk.StringVar(value=str(trig.get("weekday", 0)))
        _today = datetime.date.today()
        _dparts = trig.get("date", "").split("-")
        self._date_y = tk.StringVar(value=_dparts[0] if len(_dparts) == 3 else str(_today.year))
        self._date_m = tk.StringVar(value=_dparts[1] if len(_dparts) == 3 else f"{_today.month:02d}")
        self._date_d = tk.StringVar(value=_dparts[2] if len(_dparts) == 3 else f"{_today.day:02d}")
        self._time_h       = tk.StringVar(value=(trig.get("time", "09:00").split(":")[0]))
        self._time_m       = tk.StringVar(value=(trig.get("time", "09:00").split(":")[1] if ":" in trig.get("time", "09:00") else "00"))
        self._file_path    = tk.StringVar(value=trig.get("path", ""))
        self._file_event   = tk.StringVar(value=trig.get("event", "modified"))

        self._act_type     = tk.StringVar(value=act.get("type", "connect"))
        self._conn_name    = tk.StringVar(value=act.get("conn_name", conn_names[0] if conn_names else ""))
        self._task_event   = tk.StringVar(value=act.get("task_event", ""))
        self._task_process = tk.StringVar(value=act.get("task_process", ""))
        self._notify_title = tk.StringVar(value=act.get("title", ""))
        self._notify_msg   = tk.StringVar(value=act.get("message", ""))
        self._open_path    = tk.StringVar(value=act.get("path", ""))
        self._launch_exe   = tk.StringVar(value=act.get("exe", ""))
        self._launch_args  = tk.StringVar(value=act.get("args", ""))

        self._id = d.get("id", str(int(time.time() * 1000)))
        self._enabled = d.get("enabled", True)

        self._build()

        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")
        self.wait_window()

    def _build(self):
        pad = {"padx": 16, "pady": (0, 6)}

        # ── Rule name ─────────────────────────────────────
        tk.Label(self, text="Name:", bg=C["bg"], fg=C["text"],
                 font=FONT_BOLD).pack(anchor="w", padx=16, pady=(14, 2))
        tk.Entry(self, textvariable=self._name_var,
                 font=FONT, bg=C["card"], fg=C["text"],
                 relief="flat", bd=1, insertbackground=C["accent"],
                 width=32).pack(fill="x", **pad)

        # ── Trigger ───────────────────────────────────────
        sep1 = tk.Frame(self, bg=C["border"], height=1)
        sep1.pack(fill="x", padx=8, pady=(6, 8))
        tk.Label(self, text="Trigger", bg=C["bg"], fg=C["accent"],
                 font=FONT_BOLD).pack(anchor="w", padx=16, pady=(0, 4))

        trow = tk.Frame(self, bg=C["bg"])
        trow.pack(fill="x", padx=16, pady=(0, 4))
        tk.Label(trow, text="Type:", bg=C["bg"], fg=C["text"],
                 font=FONT, width=10, anchor="w").pack(side="left")
        ttk.Combobox(trow, textvariable=self._trig_type,
                     values=["time", "file"],
                     state="readonly", width=12,
                     font=FONT).pack(side="left")

        # Trigger detail frame (dynamically rebuilt)
        self._trig_detail = tk.Frame(self, bg=C["bg"])
        self._trig_detail.pack(fill="x", padx=16, pady=(0, 4))
        self._trig_type.trace_add("write", lambda *_: self._refresh_trig())
        self._schedule.trace_add("write", lambda *_: self._refresh_trig())
        self._refresh_trig()

        # ── Action ────────────────────────────────────────
        sep2 = tk.Frame(self, bg=C["border"], height=1)
        sep2.pack(fill="x", padx=8, pady=(6, 8))
        tk.Label(self, text="Action", bg=C["bg"], fg=C["accent"],
                 font=FONT_BOLD).pack(anchor="w", padx=16, pady=(0, 4))

        arow = tk.Frame(self, bg=C["bg"])
        arow.pack(fill="x", padx=16, pady=(0, 4))
        tk.Label(arow, text="Type:", bg=C["bg"], fg=C["text"],
                 font=FONT, width=10, anchor="w").pack(side="left")
        ttk.Combobox(arow, textvariable=self._act_type,
                     values=["connect", "add_task", "notify", "open", "launch"],
                     state="readonly", width=12,
                     font=FONT).pack(side="left")

        # Action detail frame (dynamically rebuilt)
        self._act_detail = tk.Frame(self, bg=C["bg"])
        self._act_detail.pack(fill="x", padx=16, pady=(0, 4))
        self._act_type.trace_add("write", lambda *_: self._refresh_act())
        self._refresh_act()

        # ── Buttons ───────────────────────────────────────
        sep3 = tk.Frame(self, bg=C["border"], height=1)
        sep3.pack(fill="x", padx=8, pady=(8, 0))
        btn_frame = tk.Frame(self, bg=C["bg"])
        btn_frame.pack(fill="x", padx=16, pady=(8, 14))

        tk.Button(btn_frame, text="Save", command=self._save,
                  bg=C["accent"], fg="white", relief="flat", bd=0,
                  font=FONT_BOLD, cursor="hand2", padx=16, pady=4,
                  activebackground=C["accent_dk"], activeforeground="white",
                  ).pack(side="right", padx=(4, 0))
        tk.Button(btn_frame, text="Cancel", command=self.destroy,
                  bg=C["accent_lt"], fg=C["text"], relief="flat", bd=0,
                  font=FONT, cursor="hand2", padx=10, pady=4,
                  activebackground=C["border"], activeforeground=C["text"],
                  ).pack(side="right")

    def _refresh_trig(self):
        """Rebuild the trigger detail frame based on the selected trigger type."""
        for w in self._trig_detail.winfo_children():
            w.destroy()

        ttype = self._trig_type.get()

        def lbl(text):
            tk.Label(self._trig_detail, text=text, bg=C["bg"], fg=C["text"],
                     font=FONT, width=10, anchor="w").pack(side="left")

        if ttype == "time":
            # Schedule row
            sr = tk.Frame(self._trig_detail, bg=C["bg"])
            sr.pack(fill="x", pady=(0, 4))
            tk.Label(sr, text="Schedule:", bg=C["bg"], fg=C["text"],
                     font=FONT, width=12, anchor="w").pack(side="left")
            ttk.Combobox(sr, textvariable=self._schedule,
                         values=["daily", "weekdays", "weekly", "once"],
                         state="readonly", width=12, font=FONT).pack(side="left")

            sched = self._schedule.get()
            if sched == "weekly":
                wr = tk.Frame(self._trig_detail, bg=C["bg"])
                wr.pack(fill="x", pady=(0, 4))
                tk.Label(wr, text="Weekday:", bg=C["bg"], fg=C["text"],
                         font=FONT, width=12, anchor="w").pack(side="left")
                ttk.Combobox(wr, textvariable=self._weekday,
                             values=["0", "1", "2", "3", "4", "5", "6"],
                             state="readonly", width=4, font=FONT).pack(side="left")
                tk.Label(wr, text="(0=Mon - 6=Sun)", bg=C["bg"], fg=C["text_sub"],
                         font=FONT_SMALL).pack(side="left", padx=(4, 0))
            elif sched == "once":
                dr = tk.Frame(self._trig_detail, bg=C["bg"])
                dr.pack(fill="x", pady=(0, 4))
                tk.Label(dr, text="Date:", bg=C["bg"], fg=C["text"],
                         font=FONT, width=12, anchor="w").pack(side="left")
                sb_kw = dict(font=FONT, bg=C["card"], fg=C["text"],
                             buttonbackground=C["border"], relief="flat")
                tk.Spinbox(dr, textvariable=self._date_y, from_=2020, to=2099,
                           width=5, **sb_kw).pack(side="left")
                tk.Label(dr, text="-", bg=C["bg"], fg=C["text"],
                         font=FONT).pack(side="left")
                tk.Spinbox(dr, textvariable=self._date_m, from_=1, to=12,
                           width=3, format="%02.0f", **sb_kw).pack(side="left")
                tk.Label(dr, text="-", bg=C["bg"], fg=C["text"],
                         font=FONT).pack(side="left")
                tk.Spinbox(dr, textvariable=self._date_d, from_=1, to=31,
                           width=3, format="%02.0f", **sb_kw).pack(side="left")

            # Time row
            tr = tk.Frame(self._trig_detail, bg=C["bg"])
            tr.pack(fill="x", pady=(0, 4))
            tk.Label(tr, text="Time (HH:MM):", bg=C["bg"], fg=C["text"],
                     font=FONT, width=12, anchor="w").pack(side="left")
            tk.Spinbox(tr, textvariable=self._time_h, from_=0, to=23,
                       width=3, format="%02.0f", font=FONT,
                       bg=C["card"], fg=C["text"],
                       buttonbackground=C["border"]).pack(side="left")
            tk.Label(tr, text=":", bg=C["bg"], fg=C["text"],
                     font=FONT).pack(side="left")
            tk.Spinbox(tr, textvariable=self._time_m, from_=0, to=59,
                       width=3, format="%02.0f", font=FONT,
                       bg=C["card"], fg=C["text"],
                       buttonbackground=C["border"]).pack(side="left")

        else:  # file
            # Path row
            pr = tk.Frame(self._trig_detail, bg=C["bg"])
            pr.pack(fill="x", pady=(0, 4))
            tk.Label(pr, text="File path:", bg=C["bg"], fg=C["text"],
                     font=FONT, width=12, anchor="w").pack(side="left")
            tk.Entry(pr, textvariable=self._file_path,
                     font=FONT, bg=C["card"], fg=C["text"],
                     relief="flat", bd=1, insertbackground=C["accent"],
                     width=22).pack(side="left", fill="x", expand=True, padx=(4, 4))
            tk.Button(pr, text="...",
                      command=lambda: self._file_path.set(
                          filedialog.askopenfilename(parent=self) or self._file_path.get()),
                      bg=C["tab_inact"], fg=C["text"], relief="flat", bd=0,
                      font=FONT_SMALL, cursor="hand2", padx=6, pady=2,
                      activebackground=C["border"], activeforeground=C["text"],
                      ).pack(side="left")

            # Event row
            er = tk.Frame(self._trig_detail, bg=C["bg"])
            er.pack(fill="x", pady=(0, 4))
            tk.Label(er, text="Event:", bg=C["bg"], fg=C["text"],
                     font=FONT, width=12, anchor="w").pack(side="left")
            ttk.Combobox(er, textvariable=self._file_event,
                         values=["modified", "created"],
                         state="readonly", width=12, font=FONT).pack(side="left")

    def _refresh_act(self):
        """Rebuild the action detail frame based on the selected action type."""
        for w in self._act_detail.winfo_children():
            w.destroy()

        atype = self._act_type.get()

        if atype == "connect":
            cr = tk.Frame(self._act_detail, bg=C["bg"])
            cr.pack(fill="x", pady=(0, 4))
            tk.Label(cr, text="Connection:", bg=C["bg"], fg=C["text"],
                     font=FONT, width=10, anchor="w").pack(side="left")
            ttk.Combobox(cr, textvariable=self._conn_name,
                         values=self._conn_names,
                         state="readonly" if self._conn_names else "normal",
                         width=20, font=FONT).pack(side="left")

        elif atype == "add_task":
            for label, var in [("Event:", self._task_event),
                                ("Process:", self._task_process)]:
                row = tk.Frame(self._act_detail, bg=C["bg"])
                row.pack(fill="x", pady=(0, 4))
                tk.Label(row, text=label, bg=C["bg"], fg=C["text"],
                         font=FONT, width=10, anchor="w").pack(side="left")
                tk.Entry(row, textvariable=var,
                         font=FONT, bg=C["card"], fg=C["text"],
                         relief="flat", bd=1, insertbackground=C["accent"],
                         width=22).pack(side="left", fill="x", expand=True, padx=(4, 0))

        elif atype == "notify":
            for label, var in [("Title:", self._notify_title),
                                ("Message:", self._notify_msg)]:
                row = tk.Frame(self._act_detail, bg=C["bg"])
                row.pack(fill="x", pady=(0, 4))
                tk.Label(row, text=label, bg=C["bg"], fg=C["text"],
                         font=FONT, width=10, anchor="w").pack(side="left")
                tk.Entry(row, textvariable=var,
                         font=FONT, bg=C["card"], fg=C["text"],
                         relief="flat", bd=1, insertbackground=C["accent"],
                         width=22).pack(side="left", fill="x", expand=True, padx=(4, 0))

        elif atype == "launch":
            for label, var, is_exe in [("App:", self._launch_exe, True),
                                        ("Args:", self._launch_args, False)]:
                row = tk.Frame(self._act_detail, bg=C["bg"])
                row.pack(fill="x", pady=(0, 4))
                tk.Label(row, text=label, bg=C["bg"], fg=C["text"],
                         font=FONT, width=10, anchor="w").pack(side="left")
                tk.Entry(row, textvariable=var,
                         font=FONT, bg=C["card"], fg=C["text"],
                         relief="flat", bd=1, insertbackground=C["accent"],
                         width=22).pack(side="left", fill="x", expand=True, padx=(4, 4))
                if is_exe:
                    tk.Button(row, text="...",
                              command=lambda: self._launch_exe.set(
                                  filedialog.askopenfilename(
                                      parent=self,
                                      filetypes=[("Executable", "*.exe *.bat *.cmd *.ps1"),
                                                 ("All files", "*.*")]) or self._launch_exe.get()),
                              bg=C["tab_inact"], fg=C["text"], relief="flat", bd=0,
                              font=FONT_SMALL, cursor="hand2", padx=6, pady=2,
                              activebackground=C["border"], activeforeground=C["text"],
                              ).pack(side="left")

        elif atype == "open":
            pr = tk.Frame(self._act_detail, bg=C["bg"])
            pr.pack(fill="x", pady=(0, 4))
            tk.Label(pr, text="Path:", bg=C["bg"], fg=C["text"],
                     font=FONT, width=10, anchor="w").pack(side="left")
            tk.Entry(pr, textvariable=self._open_path,
                     font=FONT, bg=C["card"], fg=C["text"],
                     relief="flat", bd=1, insertbackground=C["accent"],
                     width=22).pack(side="left", fill="x", expand=True, padx=(4, 4))
            btn_kw = dict(bg=C["tab_inact"], fg=C["text"], relief="flat", bd=0,
                          font=FONT_SMALL, cursor="hand2", padx=6, pady=2,
                          activebackground=C["border"], activeforeground=C["text"])
            tk.Button(pr, text="File...",
                      command=lambda: self._open_path.set(
                          filedialog.askopenfilename(parent=self) or self._open_path.get()),
                      **btn_kw).pack(side="left")
            tk.Button(pr, text="Folder...",
                      command=lambda: self._open_path.set(
                          filedialog.askdirectory(parent=self) or self._open_path.get()),
                      **btn_kw).pack(side="left", padx=(2, 0))

    def _save(self):
        name = self._name_var.get().strip()
        if not name:
            messagebox.showwarning("Input Error", "Please enter a rule name.", parent=self)
            return

        ttype = self._trig_type.get()
        if ttype == "time":
            try:
                h = int(self._time_h.get())
                m = int(self._time_m.get())
                time_str = f"{h:02d}:{m:02d}"
            except ValueError:
                time_str = "09:00"
            trigger = {
                "type":     "time",
                "schedule": self._schedule.get(),
                "time":     time_str,
            }
            if self._schedule.get() == "weekly":
                try:
                    trigger["weekday"] = int(self._weekday.get())
                except ValueError:
                    trigger["weekday"] = 0
            elif self._schedule.get() == "once":
                try:
                    y = int(self._date_y.get())
                    mo = int(self._date_m.get())
                    day = int(self._date_d.get())
                    trigger["date"] = f"{y:04d}-{mo:02d}-{day:02d}"
                except ValueError:
                    trigger["date"] = datetime.date.today().isoformat()
        else:
            trigger = {
                "type":  "file",
                "path":  self._file_path.get().strip(),
                "event": self._file_event.get(),
            }

        atype = self._act_type.get()
        if atype == "connect":
            action = {"type": "connect", "conn_name": self._conn_name.get()}
        elif atype == "add_task":
            action = {
                "type":         "add_task",
                "task_event":   self._task_event.get().strip(),
                "task_process": self._task_process.get().strip(),
            }
        elif atype == "notify":
            action = {
                "type":    "notify",
                "title":   self._notify_title.get().strip(),
                "message": self._notify_msg.get().strip(),
            }
        elif atype == "launch":
            action = {
                "type": "launch",
                "exe":  self._launch_exe.get().strip(),
                "args": self._launch_args.get().strip(),
            }
        else:  # open
            action = {"type": "open", "path": self._open_path.get().strip()}

        self.result = {
            "id":      self._id,
            "name":    name,
            "enabled": self._enabled,
            "trigger": trigger,
            "action":  action,
        }
        self.destroy()


# ── Main application ──────────────────────────────────────

class FolderLauncher(tk.Tk):
    # _active >= 0  : folder category index
    # _active == -1 : Terminal tab

    # システムタブ定義 (key, 表示名, _active値)
    _SYSTEM_TABS = [
        ("dashboard", "Home",      -8),
        ("auto",      "Auto",      -9),
        ("terminal",  "Terminal",  -1),
        ("tasks",     "Tasks",     -2),
        ("pomodoro",  "Pomodoro", -10),
        ("calendar",  "Calendar", -11),
        ("notify",    "Notify",    -3),
        ("web",       "Web",       -4),
        ("clip",      "Clip",      -5),
        ("ping",      "Ping",      -6),
        ("memo",      "Memo",      -7),
    ]
    _DEFAULT_PINS = ["dashboard", "terminal", "tasks", "notify"]

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

        # Windows のネイティブ ttk テーマは Treeview 見出し等の背景色を無視するため
        # clam テーマに切り替えてカスタムカラーを有効にする
        ttk.Style(self).theme_use("clam")

        # 全設定を config.json から一括読み込み（テーマ決定が先）
        self._data: list[dict] = []
        self._conns: list[dict] = []
        self._tasks: list[dict] = []
        self._notify_items: list[dict] = []
        self._terminal_groups: list[str] = []
        self._selected_group: str | None = None   # None = All
        self._bookmarks: list[dict] = []
        self._bm_selected: int = 0
        self._active: int = 0   # -1=Terminal, -2=Tasks, -3=Notify, -4=Web, -5=Clip, -6=Ping, -7=Memo
        self._pinned_tabs: list[str] = list(self._DEFAULT_PINS)
        self._memos: list[dict] = []   # {"title": str, "body": str}
        self._memo_sel: int | None = None
        self._work_active: dict | None = None  # {"task_idx": int, "start": datetime}
        self._sleep_win: tk.Toplevel | None = None
        self._sleep_tick_id = None
        self._tray_icon: pystray.Icon | None = None
        self._work_anim_id = None
        self._work_anim_dots = 0
        self._work_bar_lbl: tk.Label | None = None
        self._theme: str = "violet"   # _load_config() で上書きされる
        self._tick_id = None             # _tick() の after ID（再構築時のキャンセル用）
        self._clip_history: list[dict] = []   # {"text": str, "ts": str}
        self._clip_prev: str = ""             # 前回クリップボード値（変化検知用）
        self._ping_hosts: list[str] = []
        self._ping_data:  dict[str, list] = {}   # host -> [ms|None, ...]
        self._ping_interval: int = 5
        self._ping_enabled: bool = True
        self._ping_running: bool = False
        self._ping_lock = threading.Lock()
        self._ping_next_id  = None   # 次の ping ラウンドの after ID
        self._ping_graph_id = None   # グラフ更新ループの after ID
        self._ping_canvases:   dict[str, tk.Canvas] = {}
        self._ping_stat_vars:  dict[str, tk.StringVar] = {}
        self._dashboard_refresh_id = None
        # Auto tab: rule management
        self._rules: list[dict] = []
        self._rule_fired: set[str] = set()
        self._file_mtimes: dict[str, float | None] = {}
        self._file_watcher_started: bool = False
        self._conn_ping_cache:   dict[str, str | None] = {}  # host -> "ok"|"fail"|None
        self._conn_ping_dots:    dict[str, list]        = {}  # host -> [Canvas, ...]
        self._conn_ping_running: set[str]               = set()   # ダッシュボード自動リフレッシュの after ID
        self._conn_ping_enabled: bool = True   # Terminal ping ドット ON/OFF
        # Pomodoro
        self._pomo_state: str = "idle"   # idle/work/break/long_break/paused
        self._pomo_paused_state: str = "work"  # 一時停止前の状態
        self._pomo_remaining: int = 25 * 60   # 残り秒数
        self._pomo_cycle: int = 0             # 完了したポモドーロ数
        self._pomo_session: int = 0           # 合計セッション数
        self._pomo_after_id = None            # after() ID
        self._pomo_work_min: int = 25
        self._pomo_break_min: int = 5
        self._pomo_long_break_min: int = 15
        self._pomo_task_idx: int | None = None  # リンクしているタスクのindex
        self._pomo_lbl_time: tk.Label | None = None
        self._pomo_lbl_state: tk.Label | None = None
        self._pomo_lbl_cycle: tk.Label | None = None
        self._pomo_canvas: tk.Canvas | None = None
        # Calendar
        _today = datetime.date.today()
        self._cal_year:    int = _today.year
        self._cal_month:   int = _today.month
        self._cal_sel_day: int | None = None
        self._load_config()

        # テーマ確定後にアイコンを生成
        palette = ICON_PALETTES.get(self._theme)
        self._icon = tk.PhotoImage(data=_make_icon_png(palette))
        _setup_taskbar_icon(self, palette)
        self._task_sort: dict = {"col": None, "reverse": False}
        self._task_view: str = "list"  # "list" or "kanban"
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
        self.after(30_000, self._check_rules)
        self.after(600, self._show_startup_summary)
        self._check_recurring_tasks()

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
                self._topmost_cfg = False
                self._alpha_cfg = 1.0
                self._card_size = "normal"
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
        self._ping_enabled  = cfg.get("ping_enabled", True)
        self._conn_ping_enabled = cfg.get("conn_ping_enabled", True)

        # Memo pad
        self._memos = cfg.get("memos", [])

        # タブピン留め設定
        self._pinned_tabs = cfg.get("pinned_tabs", list(self._DEFAULT_PINS))

        # 自動化ルール
        self._rules = cfg.get("rules", [])

        # バナー表示設定
        self._banner_enabled_cfg: bool = cfg.get("banner_enabled", True)
        self._notify_display_sec_cfg: int = cfg.get("notify_display_sec", 8)
        self._topmost_cfg: bool = cfg.get("topmost", False)
        self._alpha_cfg: float = float(cfg.get("alpha", 1.0))
        self._card_size: str = cfg.get("card_size", "normal")

        # テーマ設定
        self._theme = cfg.get("theme", "violet")
        C.update(THEMES.get(self._theme, THEMES["violet"]))

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
            "ping_hosts":      self._ping_hosts,
            "ping_interval":   self._ping_interval,
            "ping_enabled":    self._ping_enabled,
            "conn_ping_enabled": self._conn_ping_enabled,
            "topmost":         self.attributes("-topmost"),
            "alpha":           self.attributes("-alpha"),
            "card_size":       self._card_size,
            "memos":         self._memos,
            "pinned_tabs":   self._pinned_tabs,
            "rules":         self._rules,
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

        # Banner notification label
        self._banner_lbl = tk.Label(
            hdr, text="",
            bg=C["accent_dk"], fg="white",
            font=FONT_SMALL, padx=8, pady=0, anchor="w",
        )
        self._banner_lbl.pack(side="left", padx=(4, 0))

        # Setup vars (must be before _tick())
        self._banner_enabled = tk.BooleanVar(value=self._banner_enabled_cfg)
        self._banner_enabled.trace_add("write", lambda *_: (self._update_banner(), self._save_config()))
        self._notify_display_sec = tk.IntVar(value=self._notify_display_sec_cfg)
        self._notify_display_sec.trace_add("write", lambda *_: self._save_config())
        self.attributes("-topmost", self._topmost_cfg)
        self.attributes("-alpha", self._alpha_cfg)
        self._show_options = tk.BooleanVar(value=False)

        self._tick()

        _btn_cfg = dict(bg=C["accent_dk"], fg="white", relief="flat", bd=0,
                        font=FONT_SMALL, cursor="hand2",
                        activebackground=C["accent_lt"], activeforeground=C["text"],
                        padx=8, pady=1)

        # ⚙ Settings menu (rightmost)
        def _show_settings():
            m = tk.Menu(self, tearoff=0,
                        bg=C["card"], fg=C["text"],
                        activebackground=C["card_h"], activeforeground=C["text"],
                        relief="flat", font=FONT_SMALL)

            # Theme submenu
            theme_sub = tk.Menu(m, tearoff=0,
                                bg=C["card"], fg=C["text"],
                                activebackground=C["card_h"], activeforeground=C["text"],
                                relief="flat", font=FONT_SMALL)
            for key, label in [("violet","Violet"),("dark","Dark"),("light","Light"),
                                ("gemini","Gemini"),("claude","Claude"),("scarlet","Scarlet"),
                                ("ocean","Ocean"),("rose","Rose"),("mint","Mint")]:
                prefix = "* " if self._theme == key else "  "
                theme_sub.add_command(label=prefix + label,
                                      command=lambda k=key: self._apply_theme(k))
            m.add_cascade(label="Theme", menu=theme_sub)
            m.add_separator()

            # Banner toggle
            m.add_checkbutton(label="Banner notifications",
                              variable=self._banner_enabled,
                              onvalue=True, offvalue=False)

            # Notify duration
            def _edit_notify_sec():
                dlg = InputDialog(self, "Notify Duration",
                                  f"Display seconds (3–60):",
                                  default=str(self._notify_display_sec.get()))
                if dlg.result:
                    try:
                        self._notify_display_sec.set(max(3, min(60, int(dlg.result))))
                    except ValueError:
                        pass
            m.add_command(label=f"Notify duration: {self._notify_display_sec.get()} s",
                          command=_edit_notify_sec)
            m.add_separator()

            # Pin on top
            is_top = bool(self.attributes("-topmost"))
            def _toggle_topmost():
                self.attributes("-topmost", not bool(self.attributes("-topmost")))
                self._save_config()
            m.add_command(label=("* " if is_top else "  ") + "Pin on top",
                          command=_toggle_topmost)
            m.add_separator()

            # Screenshot options mode
            m.add_checkbutton(label="Screenshot options",
                              variable=self._show_options,
                              onvalue=True, offvalue=False)
            m.add_separator()

            # Card size submenu
            size_sub = tk.Menu(m, tearoff=0,
                               bg=C["card"], fg=C["text"],
                               activebackground=C["card_h"], activeforeground=C["text"],
                               relief="flat", font=FONT_SMALL)
            for key, label in [("compact", "Compact"), ("normal", "Normal"), ("large", "Large")]:
                prefix = "* " if self._card_size == key else "  "
                size_sub.add_command(
                    label=prefix + label,
                    command=lambda k=key: self._set_card_size(k))
            m.add_cascade(label="Card size", menu=size_sub)

            # Transparency
            m.add_command(label="Transparency...", command=self._open_transparency_dialog)

            m.tk_popup(_cfg_btn.winfo_rootx(),
                       _cfg_btn.winfo_rooty() + _cfg_btn.winfo_height())

        _cfg_btn = tk.Button(hdr, text="...", command=_show_settings, **_btn_cfg)
        _cfg_btn.pack(side="right", padx=(0, 6))

        # Record
        tk.Button(hdr, text="Record", command=self._open_recording,
                  **_btn_cfg).pack(side="right", padx=(0, 2))

        # Screenshot
        tk.Button(hdr, text="Screenshot", command=self._open_screenshot,
                  **_btn_cfg).pack(side="right", padx=(0, 2))

        # Sleep ▾
        def _sleep_menu(e=None):
            m = tk.Menu(self, tearoff=0,
                        bg=C["card"], fg=C["text"],
                        activebackground=C["card_h"], activeforeground=C["text"],
                        relief="flat", font=FONT_SMALL)
            m.add_command(label="Window",      command=lambda: self._open_sleep_screen(False))
            m.add_command(label="Full Screen", command=lambda: self._open_sleep_screen(True))
            m.tk_popup(e.x_root, e.y_root)
        _sleep_btn = tk.Button(hdr, text="Sleep", **_btn_cfg)
        _sleep_btn.pack(side="right", padx=(0, 2))
        _sleep_btn.bind("<Button-1>", _sleep_menu)

        # Minimize to tray
        self.bind("<Unmap>", self._on_unmap)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

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

        # ≡ メニューボタン（最右端）
        self._menu_btn = tk.Button(
            self._tab_bar, text="  =  ",
            command=self._show_tabs_menu,
            bg=C["tab_inact"], fg=C["text_sub"],
            relief="flat", bd=0,
            font=FONT, cursor="hand2", padx=6, pady=5,
            activebackground=C["tab_act"],
            activeforeground=C["text"],
        )
        self._menu_btn.pack(side="right")

        # ピン留め済みのシステムタブのみ表示（右側から逆順で pack）
        for key, label, idx in reversed(self._SYSTEM_TABS):
            if key not in self._pinned_tabs:
                continue
            if key == "clip":
                count = len(self._clip_history)
                label = f"Clip ({count})" if count else "Clip"
            is_active = (self._active == idx)
            btn = tk.Button(
                self._tab_bar,
                text=label,
                command=lambda idx=idx: self._switch_tab(idx),
                bg=C["tab_act"] if is_active else C["tab_inact"],
                fg=C["text"] if is_active else C["text_sub"],
                relief="flat", bd=0,
                font=FONT_BOLD if is_active else FONT,
                cursor="hand2", padx=10, pady=5,
                activebackground=C["tab_act"],
                activeforeground=C["text"],
            )
            btn.pack(side="right")
            btn.bind("<Button-3>", lambda e, k=key: self._unpin_tab(k))

    def _switch_tab(self, idx: int):
        # Pingタブを離れるときはモニターを停止する
        if self._active == -6 and idx != -6:
            self._ping_stop()
        # ダッシュボードを離れるときは自動リフレッシュをキャンセルする
        if self._active == -8 and idx != -8:
            if self._dashboard_refresh_id is not None:
                self.after_cancel(self._dashboard_refresh_id)
                self._dashboard_refresh_id = None
        self._active = idx
        self._render_tabs()
        self._update_footer()
        self._render_list()
        # Pingタブに入ったときはモニターを開始する（有効時のみ）
        if idx == -6 and self._ping_enabled:
            self._ping_start()
        # Start file watcher when entering the Auto tab
        if idx == -9:
            self._ensure_file_watcher()
        # ポモドーロタブを離れたら表示ラベルをリセット（タイマーは動き続ける）
        if idx != -10:
            self._pomo_lbl_time = None
            self._pomo_lbl_state = None
            self._pomo_lbl_cycle = None
            self._pomo_canvas = None

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
        elif self._active == -7:
            self._footer_btn.configure(text="+ Add Memo", command=self._add_memo)
            self._footer_btn2.pack_forget()
        elif self._active == -8:
            self._footer_btn.configure(text="Refresh", command=self._render_dashboard)
            self._footer_btn2.pack_forget()
        elif self._active == -9:
            self._footer_btn.configure(text="+ Add Rule", command=self._add_rule)
            self._footer_btn2.pack_forget()
        elif self._active == -10:
            self._footer_btn.configure(text="Settings", command=self._pomo_open_settings)
            self._footer_btn2.pack_forget()
        elif self._active == -11:
            self._footer_btn.configure(text="Today", command=self._cal_go_today)
            self._footer_btn2.pack_forget()
        else:
            self._footer_btn.configure(text="+ Add Folder", command=self._add_folder)
            self._footer_btn2.configure(text="+ Add File", command=self._add_file)
            self._footer_btn2.pack(side="left", fill="x", expand=True, padx=(2, 0))

    def _show_tabs_menu(self):
        """≡ボタンのドロップダウンメニューを表示する。"""
        menu = tk.Menu(self, tearoff=0,
                       bg=C["card"], fg=C["text"],
                       activebackground=C["card_h"],
                       activeforeground=C["text"],
                       relief="flat", font=FONT)

        # 全システムタブを一覧（ピン留め済みは先頭に「+」マーク）
        for key, label, idx in self._SYSTEM_TABS:
            pinned = key in self._pinned_tabs
            prefix = "+ " if pinned else "  "
            menu.add_command(
                label=f"{prefix}{label}",
                command=lambda idx=idx: self._switch_tab(idx),
            )

        menu.add_separator()

        # ピン留め管理サブメニュー
        pin_menu = tk.Menu(menu, tearoff=0,
                           bg=C["card"], fg=C["text"],
                           activebackground=C["card_h"],
                           activeforeground=C["text"],
                           relief="flat", font=FONT)
        for key, label, _ in self._SYSTEM_TABS:
            pinned = key in self._pinned_tabs
            pin_menu.add_command(
                label=f"{'Remove' if pinned else 'Add'}:  {label}",
                command=lambda k=key: self._toggle_pin(k),
            )
        menu.add_cascade(label="Customize tabs...", menu=pin_menu)

        btn = self._menu_btn
        menu.tk_popup(btn.winfo_rootx(), btn.winfo_rooty() + btn.winfo_height())

    def _toggle_pin(self, key: str):
        """タブのピン留めをトグルする。"""
        if key in self._pinned_tabs:
            self._pinned_tabs.remove(key)
        else:
            self._pinned_tabs.append(key)
        self._save_config()
        self._render_tabs()

    def _unpin_tab(self, key: str):
        """右クリックでタブバーからタブを外す。"""
        if key in self._pinned_tabs:
            self._pinned_tabs.remove(key)
            self._save_config()
            self._render_tabs()

    def _tab_context_menu(self, event, idx: int):
        menu = tk.Menu(self, tearoff=0,
                       bg=C["card"], fg=C["text"],
                       activebackground=C["card_h"],
                       activeforeground=C["text"],
                       relief="flat", font=FONT)
        menu.add_command(label="Rename",
                         command=lambda: self._rename_category(idx))
        menu.add_separator()
        menu.add_command(label="Move Left",
                         command=lambda: self._move_category(idx, -1),
                         state="normal" if idx > 0 else "disabled")
        menu.add_command(label="Move Right",
                         command=lambda: self._move_category(idx, +1),
                         state="normal" if idx < len(self._data) - 1 else "disabled")
        menu.add_separator()
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

    def _move_category(self, idx: int, direction: int):
        new_idx = idx + direction
        if not (0 <= new_idx < len(self._data)):
            return
        self._data[idx], self._data[new_idx] = self._data[new_idx], self._data[idx]
        self._active = new_idx
        self._save()
        self._render_tabs()
        self._render_list()

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
        elif self._active == -7:
            self._render_memo_list()
        elif self._active == -8:
            self._render_dashboard()
        elif self._active == -9:
            self._render_rules_list()
        elif self._active == -10:
            self._render_pomodoro()
        elif self._active == -11:
            self._render_calendar()
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
        size = self._card_size
        pad_y = {"compact": 1, "normal": 4, "large": 8}.get(size, 4)
        pad_x = {"compact": 6, "normal": 8, "large": 12}.get(size, 8)
        name_font = FONT_SMALL if size == "compact" else FONT_BOLD

        card = tk.Frame(self._list_frame, bg=C["card"],
                        pady=pad_y, padx=pad_x, relief="flat", bd=0,
                        highlightthickness=1, highlightbackground=C["border"])
        card.pack(fill="x", pady=(1 if size == "compact" else 2), padx=2)

        left = tk.Frame(card, bg=C["card"])
        left.pack(side="left", fill="both", expand=True)

        type_tag = "[F] " if item_type == "file" else ""
        tk.Label(left, text=f"{type_tag}{name}",
                 bg=C["card"], fg=C["text"],
                 font=name_font, anchor="w").pack(fill="x")

        if size == "large":
            tk.Label(left, text=path,
                     bg=C["card"], fg=C["text_sub"],
                     font=FONT_SMALL, anchor="w").pack(fill="x")

        del_btn = tk.Button(
            card, text="x",
            command=lambda i=idx: self._remove_folder(i),
            bg=C["card"], fg=C["btn_del"],
            relief="flat", bd=0,
            font=("Segoe UI", 11), cursor="hand2",
            activebackground=C["card"], activeforeground=C["btn_del_h"],
        )
        del_btn.pack(side="right", padx=(6, 0))

        extra_btns = [del_btn]
        if size != "compact":
            edit_btn = tk.Button(
                card, text="Edit",
                command=lambda i=idx, n=name, p=path: self._edit_folder(i, n, p),
                bg=C["card"], fg=C["text_sub"],
                relief="flat", bd=0,
                font=FONT_SMALL, cursor="hand2",
                activebackground=C["card"], activeforeground=C["text"],
            )
            edit_btn.pack(side="right", padx=(0, 2))
            extra_btns.append(edit_btn)

        def _show_ctx(e):
            self._card_context_menu(e, idx, name, path)

        def _bind_open(w):
            if w in extra_btns:
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
            label="Move Up",
            command=lambda: self._move_folder_order(idx, -1),
            state="normal" if idx > 0 else "disabled",
        )
        menu.add_command(
            label="Move Down",
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
            menu.add_cascade(label="Move to", menu=move_menu)

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
                 font=FONT, bg=C["card"], fg=C["text"],
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
                return label + (" v" if self._conn_sort["reverse"] else " ^")
            return label

        # Terminal ping ドット ON/OFF トグル
        def _toggle_conn_ping():
            self._conn_ping_enabled = not self._conn_ping_enabled
            self._save_config()
            self._render_list()

        ping_lbl = "Ping ON" if self._conn_ping_enabled else "Ping OFF"
        ping_fg  = C["accent"] if self._conn_ping_enabled else C["text_sub"]
        tk.Button(toolbar, text=ping_lbl, command=_toggle_conn_ping,
                  bg=C["tab_inact"], fg=ping_fg, relief="flat", bd=0,
                  font=FONT_SMALL, cursor="hand2", padx=6, pady=2,
                  activebackground=C["card_h"],
                  activeforeground=ping_fg).pack(side="left", padx=(4, 0))

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

        self._conn_ping_dots.clear()
        for i, conn in conns_idx:
            self._make_conn_card(i, conn, main_frame)

        # 表示中の各ホストへ ping プローブを開始（有効時のみ）
        if self._conn_ping_enabled:
            for _, conn in conns_idx:
                host = conn.get("host", "")
                if host and host not in self._conn_ping_running:
                    self._conn_ping_probe(host)

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

        _make_grp_btn("All", None).configure(
            command=lambda: _select_group(None))

        grp_btns: list[tk.Button] = []
        for grp in self._terminal_groups:
            b = _make_grp_btn(grp, grp)
            grp_btns.append(b)
            # 右クリックメニュー（Rename / Delete）
            menu = tk.Menu(parent, tearoff=0)
            menu.add_command(label="Rename",
                             command=lambda g=grp: self._rename_terminal_group(g))
            menu.add_command(label="Delete",
                             command=lambda g=grp: self._delete_terminal_group(g))
            b.bind("<Button-3>", lambda e, m=menu: m.tk_popup(e.x_root, e.y_root))

        # ── グループボタンのドラッグ並び替え ──────────────────
        dnd: dict = {"src": None, "moved": False}

        def _grp_btns_now() -> list[tk.Button]:
            """parent の pack 順でグループボタンを返す。"""
            grp_set = set(grp_btns)
            return [w for w in parent.pack_slaves() if w in grp_set]

        def _btn_bg(b: tk.Button) -> str:
            grp = self._sidebar_group_btns.get(b)
            return C["accent"] if self._selected_group == grp else C["card"]

        def on_press(e, btn):
            dnd["src"]   = btn
            dnd["moved"] = False

        def on_motion(e, btn):
            src = dnd["src"]
            if src is None:
                return
            dnd["moved"] = True
            cur = _grp_btns_now()
            for b in cur:
                if b is src:
                    b.configure(bg=C["accent_lt"])
                    continue
                by = b.winfo_rooty()
                bh = b.winfo_height()
                if by <= e.y_root <= by + bh:
                    b.configure(bg=C["card_h"])
                else:
                    b.configure(bg=_btn_bg(b))

        def on_release(e, btn, grp):
            src = dnd["src"]
            dnd["src"] = None
            if not dnd["moved"]:
                dnd["moved"] = False
                _select_group(grp)
                return
            dnd["moved"] = False
            # ドロップ先を確定してデータを並び替え
            cur = _grp_btns_now()
            try:
                si = cur.index(btn)
            except ValueError:
                self._render_list()
                return
            ti = None
            for j, b in enumerate(cur):
                if b is btn:
                    continue
                by = b.winfo_rooty()
                bh = b.winfo_height()
                if by <= e.y_root <= by + bh:
                    ti = j + 1 if e.y_root > by + bh // 2 else j
                    break
            if ti is not None and ti != si:
                item = self._terminal_groups.pop(si)
                self._terminal_groups.insert(min(ti, len(self._terminal_groups)), item)
                self._save_config()
            self._render_list()

        for b in grp_btns:
            grp = self._sidebar_group_btns[b]
            b.bind("<Button-1>",        lambda e, btn=b:         on_press(e, btn))
            b.bind("<B1-Motion>",       lambda e, btn=b:         on_motion(e, btn))
            b.bind("<ButtonRelease-1>", lambda e, btn=b, g=grp:  on_release(e, btn, g))

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

        del_btn = tk.Button(card, text="x",
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

        # 接続可否ドット（バックグラウンド ping 結果を反映、無効時は非表示）
        host = conn.get("host", "")
        if self._conn_ping_enabled:
            status = self._conn_ping_cache.get(host)
            dot_color = {"ok": "#4caf50", "fail": C["btn_del"]}.get(status, C["border"])
            dot_cv = tk.Canvas(card, width=12, height=12, bg=C["card"], highlightthickness=0)
            dot_cv.pack(side="right", padx=(0, 6))
            dot_cv.create_oval(1, 1, 11, 11, fill=dot_color, outline="")
            self._conn_ping_dots.setdefault(host, []).append(dot_cv)

        for widget in (card, left) + tuple(left.winfo_children()):
            widget.bind("<Button-1>", lambda e, c=conn: self._connect_server(c))
            widget.bind("<Enter>",    lambda e, f=card: _set_bg(f, C["card_h"]))
            widget.bind("<Leave>",    lambda e, f=card: _set_bg(f, C["card"]))
            widget.configure(cursor="hand2")

    def _conn_ping_probe(self, host: str):
        """バックグラウンドで ping を実行し、ドットの色を更新する。"""
        self._conn_ping_running.add(host)

        def _probe():
            try:
                result = subprocess.run(
                    ["ping", "-n", "1", "-w", "2000", host],
                    capture_output=True, text=True, timeout=3.5,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                ok = "TTL=" in result.stdout or "ttl=" in result.stdout
            except Exception:
                ok = False
            self._conn_ping_cache[host] = "ok" if ok else "fail"
            self.after(0, lambda: self._conn_ping_update_dots(host))

        threading.Thread(target=_probe, daemon=True).start()

    def _conn_ping_update_dots(self, host: str):
        """ping 結果に合わせてドット Canvas の色を更新する。"""
        self._conn_ping_running.discard(host)
        status = self._conn_ping_cache.get(host)
        color = "#4caf50" if status == "ok" else C["btn_del"]
        for cv in self._conn_ping_dots.get(host, []):
            try:
                cv.delete("all")
                cv.create_oval(1, 1, 11, 11, fill=color, outline="")
            except tk.TclError:
                pass  # ウィジェットが既に破棄済み

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
        name = conn.get("name") or conn.get("host", "")
        if not messagebox.askokcancel(
            "Connect", f"Connect to {name}?", parent=self
        ):
            return
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
                card, text="x",
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

    # ── Dashboard ─────────────────────────────────────────

    def _render_dashboard(self):
        """ダッシュボード（Home タブ）を描画する。"""
        # 既存の自動リフレッシュ予約をキャンセル
        if self._dashboard_refresh_id is not None:
            self.after_cancel(self._dashboard_refresh_id)
            self._dashboard_refresh_id = None

        # _list_frame の中身をリセット
        for w in self._list_frame.winfo_children():
            w.destroy()

        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        # スクロール可能なキャンバスエリアを構築
        canvas = tk.Canvas(self._list_frame, bg=C["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self._list_frame, orient="vertical", command=canvas.yview,
                                 bg=C["bg"], troughcolor=C["bg"], activebackground=C["accent"])
        inner = tk.Frame(canvas, bg=C["bg"])

        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        inner.bind("<MouseWheel>", _on_mousewheel)

        # ── セクション1: 今日の作業 ──────────────────────────
        self._dash_section_header(inner, "Today's Tasks")

        today_tasks = [
            t for t in self._tasks
            if not t.get("done", False) and (
                t.get("deadline", "")[:10] == today_str
                or any(wl[:10] == today_str for wl in t.get("work_log", []))
            )
        ]
        if today_tasks:
            for task in today_tasks:
                row = self._dash_task_row(inner, task, today_str, now)
                row.bind("<MouseWheel>", _on_mousewheel)
        else:
            tk.Label(inner, text="No tasks due today.",
                     bg=C["bg"], fg=C["text_sub"], font=FONT_SMALL
                     ).pack(anchor="w", padx=8, pady=4)

        # ── セクション2: 直近の通知 ──────────────────────────
        self._dash_section_header(inner, "Upcoming Notifications")

        deadline_24h = now + datetime.timedelta(hours=24)
        upcoming = sorted(
            [
                item for item in self._notify_items
                if not item.get("done", False)
                and item.get("scheduled_at", "")
                and now <= datetime.datetime.strptime(item["scheduled_at"], "%Y-%m-%d %H:%M") <= deadline_24h
            ],
            key=lambda x: x["scheduled_at"]
        )[:5]

        if upcoming:
            for item in upcoming:
                row = self._dash_notify_row(inner, item, now)
                row.bind("<MouseWheel>", _on_mousewheel)
        else:
            tk.Label(inner, text="No notifications in the next 24 hours.",
                     bg=C["bg"], fg=C["text_sub"], font=FONT_SMALL
                     ).pack(anchor="w", padx=8, pady=4)

        # ── セクション3: Ping ステータス ─────────────────────
        self._dash_section_header(inner, "Ping Status")

        if self._ping_hosts:
            for host in self._ping_hosts:
                row = self._dash_ping_row(inner, host)
                row.bind("<MouseWheel>", _on_mousewheel)
        else:
            tk.Label(inner, text="No ping hosts registered.",
                     bg=C["bg"], fg=C["text_sub"], font=FONT_SMALL
                     ).pack(anchor="w", padx=8, pady=4)

        # 30秒後に自動リフレッシュ
        self._dashboard_refresh_id = self.after(30_000, self._dashboard_auto_refresh)

    def _dashboard_auto_refresh(self):
        """30秒ごとにダッシュボードを自動更新する。"""
        self._dashboard_refresh_id = None
        if self._active != -8:
            return
        self._render_dashboard()

    def _dash_section_header(self, parent: tk.Frame, title: str) -> tk.Frame:
        """ダッシュボードのセクションヘッダーバーを作成する。"""
        bar = tk.Frame(parent, bg=C["accent_lt"])
        bar.pack(fill="x", pady=(8, 2), padx=2)
        tk.Label(bar, text=title, bg=C["accent_lt"], fg=C["accent_dk"],
                 font=FONT_BOLD, anchor="w", padx=6, pady=2).pack(fill="x")
        return bar

    def _dash_task_row(self, parent: tk.Frame, task: dict,
                       today_str: str, now: datetime.datetime) -> tk.Frame:
        """ダッシュボード用タスク行カードを作成して返す。"""
        card = tk.Frame(parent, bg=C["card"], padx=8, pady=4,
                        highlightthickness=1, highlightbackground=C["border"])
        card.pack(fill="x", pady=2, padx=4)

        # 上段: イベント / プロセス
        event   = task.get("event", "")
        process = task.get("process", "")
        label   = f"{event} / {process}" if event and process else (event or process or "(untitled)")
        tk.Label(card, text=label, bg=C["card"], fg=C["text"],
                 font=FONT_BOLD, anchor="w").pack(fill="x")

        # 下段: 進捗バー + 残日数
        pct = task.get("progress", 0)
        filled  = int(pct / 10)
        bar_str = "#" * filled + "-" * (10 - filled)

        dl_str = task.get("deadline", "")
        if dl_str:
            try:
                dl = datetime.datetime.fromisoformat(dl_str[:10])
                days_left = (dl.date() - now.date()).days
                if days_left == 0:
                    dl_label = "due today"
                elif days_left < 0:
                    dl_label = f"{abs(days_left)}d overdue"
                else:
                    dl_label = f"{days_left}d left"
            except ValueError:
                dl_label = ""
        else:
            dl_label = ""

        sub_text = f"{bar_str} {pct}%  {dl_label}".strip()
        tk.Label(card, text=sub_text, bg=C["card"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="w").pack(fill="x")
        return card

    def _dash_notify_row(self, parent: tk.Frame, item: dict, now: datetime.datetime) -> tk.Frame:
        """ダッシュボード用通知行カードを作成して返す。"""
        card = tk.Frame(parent, bg=C["card"], padx=8, pady=4,
                        highlightthickness=1, highlightbackground=C["border"])
        card.pack(fill="x", pady=2, padx=4)

        # 上段: タイトル
        tk.Label(card, text=item.get("title", "(untitled)"), bg=C["card"], fg=C["text"],
                 font=FONT_BOLD, anchor="w").pack(fill="x")

        # 下段: 日時 + 残り時間
        sched_str = item.get("scheduled_at", "")
        try:
            sched_dt  = datetime.datetime.strptime(sched_str, "%Y-%m-%d %H:%M")
            delta_sec = int((sched_dt - now).total_seconds())
            if delta_sec >= 3600:
                remain = f"in ~{delta_sec // 3600}h"
            else:
                remain = f"in ~{delta_sec // 60}m"
            sub_text = f"{sched_str}  ({remain})"
        except ValueError:
            sub_text = sched_str

        tk.Label(card, text=sub_text, bg=C["card"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="w").pack(fill="x")
        return card

    def _dash_ping_row(self, parent: tk.Frame, host: str) -> tk.Frame:
        """ダッシュボード用 Ping ステータス行カードを作成して返す。"""
        card = tk.Frame(parent, bg=C["card"], padx=8, pady=4,
                        highlightthickness=1, highlightbackground=C["border"])
        card.pack(fill="x", pady=2, padx=4)

        inner = tk.Frame(card, bg=C["card"])
        inner.pack(fill="x")

        # 左端: ステータスドット
        dot_canvas = tk.Canvas(inner, width=14, height=14, bg=C["card"],
                               highlightthickness=0)
        dot_canvas.pack(side="left", padx=(0, 6))

        history = self._ping_data.get(host, [])
        if not history:
            dot_color = C["text_sub"]  # データなし = グレー
            ms_text   = "---"
        else:
            last_ms = history[-1]
            if last_ms is None:
                dot_color = C["btn_del"]   # Timeout = 赤
                ms_text   = "Timeout"
            else:
                dot_color = "#4caf50"      # 応答あり = 緑
                ms_text   = f"{last_ms} ms"

        dot_canvas.create_oval(2, 2, 12, 12, fill=dot_color, outline=dot_color)

        # 中央: ホスト名（24文字超は省略）
        display_host = host if len(host) <= 24 else host[:21] + "..."
        tk.Label(inner, text=display_host, bg=C["card"], fg=C["text"],
                 font=FONT, anchor="w").pack(side="left", fill="x", expand=True)

        # 右端: ms 値
        tk.Label(inner, text=ms_text, bg=C["card"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="e").pack(side="right")

        return card

    # ── Auto (Rules) ──────────────────────────────────────

    def _render_rules_list(self):
        """Render the rule list in the Auto tab."""
        if not self._rules:
            tk.Label(
                self._list_frame,
                text="No rules registered.\nClick \"+ Add Rule\" to add one.",
                bg=C["bg"], fg=C["text_sub"],
                font=FONT_SMALL, justify="center",
            ).pack(pady=20)
            return
        for i, rule in enumerate(self._rules):
            self._make_rule_card(i, rule)

    def _make_rule_card(self, idx: int, rule: dict):
        """Render a single rule card."""
        card = tk.Frame(self._list_frame, bg=C["card"],
                        pady=6, padx=8, relief="flat", bd=0,
                        highlightthickness=1, highlightbackground=C["border"])
        card.pack(fill="x", pady=2, padx=2)

        # Top row: rule name + enabled/disabled toggle
        top = tk.Frame(card, bg=C["card"])
        top.pack(fill="x")

        enabled = rule.get("enabled", True)
        toggle_text = "ON" if enabled else "OFF"
        toggle_fg   = C["accent"] if enabled else C["text_sub"]

        tk.Label(top, text=rule.get("name", "(No name)"),
                 bg=C["card"], fg=C["text"],
                 font=FONT_BOLD, anchor="w").pack(side="left", fill="x", expand=True)

        tk.Button(top, text=toggle_text,
                  command=lambda i=idx: self._toggle_rule(i),
                  bg=C["card"], fg=toggle_fg,
                  relief="flat", bd=0,
                  font=FONT_SMALL, cursor="hand2",
                  activebackground=C["card_h"], activeforeground=toggle_fg,
                  ).pack(side="right", padx=(4, 0))

        # Delete button
        tk.Button(top, text="x",
                  command=lambda i=idx: self._remove_rule(i),
                  bg=C["card"], fg=C["btn_del"],
                  relief="flat", bd=0,
                  font=("Segoe UI", 11), cursor="hand2",
                  activebackground=C["card_h"], activeforeground=C["btn_del_h"],
                  ).pack(side="right")

        # Edit button
        tk.Button(top, text="Edit",
                  command=lambda i=idx: self._edit_rule(i),
                  bg=C["card"], fg=C["text_sub"],
                  relief="flat", bd=0,
                  font=FONT_SMALL, cursor="hand2",
                  activebackground=C["card_h"], activeforeground=C["text"],
                  ).pack(side="right", padx=(0, 4))

        # Bottom row: trigger summary + action summary
        bot = tk.Frame(card, bg=C["card"])
        bot.pack(fill="x", pady=(2, 0))

        trigger = rule.get("trigger", {})
        action  = rule.get("action",  {})

        # Trigger summary
        ttype = trigger.get("type", "time")
        if ttype == "time":
            sched = trigger.get("schedule", "daily")
            t     = trigger.get("time", "00:00")
            sched_labels = {"daily": "Daily", "weekdays": "Weekdays", "weekly": "Weekly", "once": "Once"}
            sched_str = sched_labels.get(sched, sched)
            if sched == "weekly":
                wd = trigger.get("weekday", 0)
                wd_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                sched_str += f" ({wd_names[wd]})"
            elif sched == "once":
                sched_str += f" {trigger.get('date', '')}"
            trigger_summary = f"{sched_str} {t}"
        else:
            path  = trigger.get("path", "")
            event = trigger.get("event", "modified")
            event_label = "modified" if event == "modified" else "created"
            trigger_summary = f"{path} when {event_label}"

        # Action summary
        atype = action.get("type", "connect")
        action_labels = {
            "connect":  f"Connect: {action.get('conn_name', '')}",
            "add_task": f"Add Task: {action.get('task_event', '')}",
            "notify":   f"Notify: {action.get('title', '')}",
            "open":     f"Open: {action.get('path', '')}",
            "launch":   f"Launch: {os.path.basename(action.get('exe', ''))}",
        }
        action_summary = action_labels.get(atype, atype)

        tk.Label(bot, text=trigger_summary,
                 bg=C["card"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="w").pack(side="left")
        tk.Label(bot, text=action_summary,
                 bg=C["card"], fg=C["accent"],
                 font=FONT_SMALL, anchor="e").pack(side="right")

    def _add_rule(self):
        """Add a new rule."""
        dlg = RuleDialog(self, conn_names=[c["name"] for c in self._conns])
        if dlg.result:
            self._rules.append(dlg.result)
            self._save_config()
            self._render_list()

    def _edit_rule(self, idx: int):
        """Edit an existing rule."""
        dlg = RuleDialog(self, initial=self._rules[idx],
                         conn_names=[c["name"] for c in self._conns])
        if dlg.result:
            self._rules[idx] = dlg.result
            self._save_config()
            self._render_list()

    def _remove_rule(self, idx: int):
        """Delete a rule."""
        name = self._rules[idx].get("name", "this rule")
        if messagebox.askyesno("Confirm", f"Delete \"{name}\"?", parent=self):
            self._rules.pop(idx)
            self._save_config()
            self._render_list()

    def _toggle_rule(self, idx: int):
        """Toggle a rule's enabled state."""
        self._rules[idx]["enabled"] = not self._rules[idx].get("enabled", True)
        self._save_config()
        self._render_list()

    def _check_rules(self):
        """Check time-based rules every 30 seconds."""
        now   = datetime.datetime.now()
        today = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")
        wd    = now.weekday()  # 0=Monday

        for rule in self._rules:
            if not rule.get("enabled", True):
                continue
            trigger = rule.get("trigger", {})
            if trigger.get("type") != "time":
                continue

            rule_time = trigger.get("time", "")
            if rule_time != time_str:
                continue

            schedule = trigger.get("schedule", "daily")
            if schedule == "weekdays" and wd >= 5:
                continue
            if schedule == "weekly" and wd != trigger.get("weekday", 0):
                continue
            if schedule == "once" and trigger.get("date", "") != today:
                continue

            fire_key = f"{rule['id']}_{today}_{time_str}"
            if fire_key in self._rule_fired:
                continue

            self._rule_fired.add(fire_key)
            self._fire_rule(rule)

            if schedule == "once":
                rule["enabled"] = False
                self._save_config()

        self.after(30_000, self._check_rules)

    def _ensure_file_watcher(self):
        """Start the file watcher thread (only once)."""
        if self._file_watcher_started:
            return
        self._file_watcher_started = True
        t = threading.Thread(target=self._file_watch_loop, daemon=True)
        t.start()

    def _file_watch_loop(self):
        """Background loop that checks file triggers every 5 seconds."""
        while True:
            time.sleep(5)
            for rule in list(self._rules):
                if not rule.get("enabled", True):
                    continue
                trigger = rule.get("trigger", {})
                if trigger.get("type") != "file":
                    continue
                path = trigger.get("path", "")
                if not path:
                    continue
                try:
                    mtime = os.path.getmtime(path)
                except FileNotFoundError:
                    continue
                except Exception:
                    continue

                prev = self._file_mtimes.get(path)
                self._file_mtimes[path] = mtime
                if prev is None:
                    # First run: record mtime without firing
                    continue
                if mtime != prev:
                    self.after(0, lambda r=rule: self._fire_rule(r))

    def _fire_rule(self, rule: dict):
        """Execute the action of a triggered rule."""
        action = rule.get("action", {})
        atype  = action.get("type", "")

        if atype == "connect":
            conn_name = action.get("conn_name", "")
            conn = next((c for c in self._conns if c.get("name") == conn_name), None)
            if conn is None:
                return
            proto = conn.get("protocol", "SSH")
            if proto == "RDP":
                _launch_rdp(conn)
            elif proto == "SMB":
                _launch_smb(conn)
            else:
                _launch_teraterm(conn)

        elif atype == "add_task":
            task = {
                "event":   action.get("task_event", "Auto Task"),
                "process": action.get("task_process", ""),
                "progress": 0,
                "priority": "Medium",
                "start": datetime.date.today().isoformat(),
                "due": "",
                "memo": f"Auto rule: {rule.get('name', '')}",
            }
            self._tasks.append(task)
            self._save_config()
            if self._active == -2:
                self._render_list()

        elif atype == "notify":
            item = {
                "event":        action.get("title", rule.get("name", "Rule Fired")),
                "process":      action.get("message", ""),
                "scheduled_at": "",
                "recurrence":   "none",
            }
            NotificationPopup(self, item, self._notify_display_sec.get() * 1000)

        elif atype == "open":
            path = action.get("path", "")
            if path:
                try:
                    if os.path.isdir(path):
                        subprocess.Popen(["explorer", os.path.normpath(path)])
                    else:
                        os.startfile(path)
                except Exception:
                    pass

        elif atype == "launch":
            exe = action.get("exe", "")
            if exe:
                try:
                    args_str = action.get("args", "").strip()
                    cmd = [exe] + args_str.split() if args_str else [exe]
                    subprocess.Popen(cmd)
                except Exception:
                    pass

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

        # ON/OFF トグルボタン
        toggle_text = "Stop" if self._ping_running else "Start"
        toggle_fg   = C["btn_del"] if self._ping_running else C["accent"]
        tk.Button(cfg_bar, text=toggle_text,
                  command=self._ping_toggle,
                  bg=C["tab_inact"], fg=toggle_fg, relief="flat", bd=0,
                  font=FONT_SMALL, cursor="hand2", padx=8, pady=2,
                  activebackground=C["card_h"],
                  activeforeground=toggle_fg).pack(side="left", padx=(6, 0))

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

            del_btn = tk.Button(row, text="x", command=_del,
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

    def _ping_toggle(self):
        """Ping モニターの ON/OFF を切り替える。"""
        if self._ping_running:
            self._ping_enabled = False
            self._ping_stop()
        else:
            self._ping_enabled = True
            self._ping_start()
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
                creationflags=subprocess.CREATE_NO_WINDOW,
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

    # ── Memo pad ──────────────────────────────────────────

    def _render_memo_list(self):
        """Render memo pad UI."""
        outer = tk.Frame(self._list_frame, bg=C["bg"])
        outer.pack(fill="both", expand=True)

        # ── Left pane: title list ──
        left = tk.Frame(outer, bg=C["bg"], width=130)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Frame(outer, bg=C["border"], width=1).pack(side="left", fill="y")

        # ── Right pane: edit area ──
        right = tk.Frame(outer, bg=C["bg"])
        right.pack(side="left", fill="both", expand=True)

        # Helper to render right pane content
        def _show_editor(idx: int | None):
            for w in right.winfo_children():
                w.destroy()
            if idx is None or not self._memos:
                tk.Label(right, text="Select or add a memo",
                         bg=C["bg"], fg=C["text_sub"], font=FONT_SMALL).pack(pady=20)
                return

            memo = self._memos[idx]

            # Title input
            title_var = tk.StringVar(value=memo.get("title", ""))
            tk.Label(right, text="Title", bg=C["bg"], fg=C["text_sub"],
                     font=FONT_SMALL, anchor="w").pack(fill="x", padx=10, pady=(8, 0))
            title_e = tk.Entry(right, textvariable=title_var, font=FONT,
                               bg=C["card"], fg=C["text"], relief="flat", bd=1,
                               insertbackground=C["accent"])
            title_e.pack(fill="x", padx=10, pady=(2, 6))

            # Body text area
            tk.Label(right, text="Body", bg=C["bg"], fg=C["text_sub"],
                     font=FONT_SMALL, anchor="w").pack(fill="x", padx=10)
            body_frame = tk.Frame(right, bg=C["bg"])
            body_frame.pack(fill="both", expand=True, padx=10, pady=(2, 4))
            body_txt = tk.Text(body_frame, font=("Consolas", 10),
                               bg=C["card"], fg=C["text"], relief="flat", bd=1,
                               insertbackground=C["accent"],
                               wrap="word", undo=True)
            body_txt.insert("1.0", memo.get("body", ""))
            vsb = tk.Scrollbar(body_frame, command=body_txt.yview)
            body_txt.configure(yscrollcommand=vsb.set)
            body_txt.pack(side="left", fill="both", expand=True)
            vsb.pack(side="right", fill="y")

            # Button row
            btn_row = tk.Frame(right, bg=C["bg"])
            btn_row.pack(fill="x", padx=10, pady=(0, 8))

            def _save_memo(*_):
                self._memos[idx]["title"] = title_var.get()
                self._memos[idx]["body"]  = body_txt.get("1.0", "end-1c")
                self._save_config()
                _refresh_list()

            def _copy_body():
                self.clipboard_clear()
                self.clipboard_append(body_txt.get("1.0", "end-1c"))

            def _delete_memo():
                self._memos.pop(idx)
                self._memo_sel = None
                self._save_config()
                self._render_list()

            tk.Button(btn_row, text="Save", command=_save_memo,
                      bg=C["accent"], fg="white", relief="flat", bd=0,
                      font=FONT_BOLD, cursor="hand2", padx=10, pady=3,
                      activebackground=C["accent_dk"], activeforeground="white",
                      ).pack(side="left")
            tk.Button(btn_row, text="Copy", command=_copy_body,
                      bg=C["card"], fg=C["text"], relief="flat", bd=0,
                      font=FONT, cursor="hand2", padx=10, pady=3,
                      activebackground=C["card_h"], activeforeground=C["text"],
                      ).pack(side="left", padx=(6, 0))
            tk.Button(btn_row, text="Delete", command=_delete_memo,
                      bg=C["btn_del"], fg="white", relief="flat", bd=0,
                      font=FONT, cursor="hand2", padx=10, pady=3,
                      activebackground=C["btn_del_h"], activeforeground="white",
                      ).pack(side="right")

            # Save on focus out
            title_e.bind("<FocusOut>", _save_memo)
            body_txt.bind("<FocusOut>", _save_memo)

        # Helper to refresh left pane list
        def _refresh_list():
            for w in left.winfo_children():
                w.destroy()
            if not self._memos:
                tk.Label(left, text="No memos", bg=C["bg"], fg=C["text_sub"],
                         font=FONT_SMALL).pack(pady=10)
                return
            for i, m in enumerate(self._memos):
                is_sel = (i == self._memo_sel)
                btn = tk.Button(
                    left, text=m.get("title") or "(no title)",
                    bg=C["card_h"] if is_sel else C["bg"],
                    fg=C["text"], relief="flat", bd=0,
                    font=FONT_BOLD if is_sel else FONT,
                    cursor="hand2", anchor="w", padx=8, pady=4,
                    wraplength=115, justify="left",
                    activebackground=C["card_h"], activeforeground=C["text"],
                )
                btn.pack(fill="x", pady=1)
                btn.configure(command=lambda i=i: _select(i))

        def _select(i: int):
            self._memo_sel = i
            _refresh_list()
            _show_editor(i)

        _refresh_list()
        _show_editor(self._memo_sel)

    def _add_memo(self):
        self._memos.append({"title": "New Memo", "body": ""})
        self._memo_sel = len(self._memos) - 1
        self._save_config()
        self._render_list()

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

        del_btn = tk.Button(card, text="x",
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

    # ── Calendar ───────────────────────────────────────────

    def _render_calendar(self):
        """タスク締め切りカレンダーを描画する。"""
        import calendar as _cal_mod
        f = self._list_frame
        _dark = self._theme in ("dark", "claude", "scarlet", "ocean")
        today = datetime.date.today()

        # タスクを締め切り日でインデックス化
        deadline_map: dict[str, list[dict]] = {}
        for task in self._tasks:
            dl = task.get("deadline", "")
            if dl:
                deadline_map.setdefault(dl, []).append(task)

        # ── ナビゲーションヘッダー ──
        nav = tk.Frame(f, bg=C["bg"])
        nav.pack(fill="x", padx=6, pady=(6, 2))

        tk.Button(nav, text="<",
                  command=self._cal_prev_month,
                  bg=C["card"], fg=C["text"], relief="flat", bd=0,
                  font=FONT_BOLD, cursor="hand2", padx=10, pady=3,
                  activebackground=C["card_h"], activeforeground=C["text"],
                  ).pack(side="left")

        tk.Label(nav,
                 text=f"{self._cal_year}  /  {self._cal_month:02d}",
                 bg=C["bg"], fg=C["text"], font=FONT_BOLD,
                 ).pack(side="left", fill="x", expand=True)

        tk.Button(nav, text=">",
                  command=self._cal_next_month,
                  bg=C["card"], fg=C["text"], relief="flat", bd=0,
                  font=FONT_BOLD, cursor="hand2", padx=10, pady=3,
                  activebackground=C["card_h"], activeforeground=C["text"],
                  ).pack(side="right")

        # ── カレンダーグリッド ──
        grid_frame = tk.Frame(f, bg=C["bg"])
        grid_frame.pack(fill="x", padx=6, pady=(0, 4))
        for col in range(7):
            grid_frame.columnconfigure(col, weight=1)

        # 曜日ヘッダー（月曜始まり）
        DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        DOW_FG = [C["text_sub"]] * 5 + [
            "#6080FF" if not _dark else "#99AAFF",   # Sat
            "#FF6060" if not _dark else "#FF9999",   # Sun
        ]
        for col, (d, fg) in enumerate(zip(DOW, DOW_FG)):
            tk.Label(grid_frame, text=d, bg=C["bg"], fg=fg,
                     font=FONT_SMALL, anchor="center",
                     ).grid(row=0, column=col, sticky="ew", padx=1, pady=(0, 2))

        # 日付セル
        weeks = _cal_mod.monthcalendar(self._cal_year, self._cal_month)
        for row_i, week in enumerate(weeks):
            for col_i, day in enumerate(week):
                date_str = (
                    f"{self._cal_year}-{self._cal_month:02d}-{day:02d}"
                    if day else ""
                )
                tasks_on_day = deadline_map.get(date_str, [])
                is_today     = (day and
                                self._cal_year == today.year and
                                self._cal_month == today.month and
                                day == today.day)
                is_selected  = (day and day == self._cal_sel_day)
                is_past      = (day and
                                datetime.date(self._cal_year, self._cal_month, day) < today)

                # セル背景色
                if is_selected:
                    cell_bg = C["accent"]
                    day_fg  = "white"
                elif is_today:
                    cell_bg = C["accent_lt"]
                    day_fg  = C["accent_dk"]
                else:
                    cell_bg = C["card"]
                    day_fg  = C["text_sub"] if (not day or is_past) else C["text"]

                cell = tk.Frame(grid_frame, bg=cell_bg,
                                highlightthickness=1,
                                highlightbackground=C["border"])
                cell.grid(row=row_i + 1, column=col_i,
                          sticky="nsew", padx=1, pady=1, ipady=2)

                if day:
                    # 日付番号
                    dow_fg = day_fg
                    if not is_selected and not is_today:
                        if col_i == 5:
                            dow_fg = "#6080FF" if not _dark else "#99AAFF"
                        elif col_i == 6:
                            dow_fg = "#FF6060" if not _dark else "#FF9999"
                    tk.Label(cell, text=str(day), bg=cell_bg, fg=dow_fg,
                             font=FONT_SMALL, anchor="nw",
                             ).pack(anchor="nw", padx=3, pady=(1, 0))

                    # タスクドット or 件数
                    if tasks_on_day:
                        n = len(tasks_on_day)
                        all_done = all(t.get("progress", 0) == 100 for t in tasks_on_day)
                        any_overdue = (is_past and
                                       any(t.get("progress", 0) < 100 for t in tasks_on_day))
                        if any_overdue:
                            dot_fg = "#FF6060" if not _dark else "#FF9999"
                        elif all_done:
                            dot_fg = "#60BB80" if not _dark else "#80DDA0"
                        else:
                            dot_fg = C["accent"]
                        tk.Label(cell,
                                 text=f"* {n}" if n > 1 else "*",
                                 bg=cell_bg, fg=dot_fg,
                                 font=FONT_SMALL, anchor="center",
                                 ).pack(anchor="center")

                    # クリックで選択
                    def _on_click(d=day):
                        self._cal_sel_day = d if self._cal_sel_day != d else None
                        self._render_list()
                    cell.bind("<Button-1>", lambda e, d=day: _on_click(d))
                    for child in cell.winfo_children():
                        child.bind("<Button-1>", lambda e, d=day: _on_click(d))

        # ── 選択日のタスク詳細 ──
        if self._cal_sel_day:
            date_str = f"{self._cal_year}-{self._cal_month:02d}-{self._cal_sel_day:02d}"
            tasks_on_day = deadline_map.get(date_str, [])

            detail = tk.Frame(f, bg=C["card"],
                              highlightthickness=1, highlightbackground=C["border"])
            detail.pack(fill="x", padx=6, pady=(2, 4))

            tk.Label(detail,
                     text=f"{self._cal_year}/{self._cal_month:02d}/{self._cal_sel_day:02d}",
                     bg=C["card"], fg=C["accent"], font=FONT_BOLD,
                     ).pack(anchor="w", padx=8, pady=(5, 2))

            if not tasks_on_day:
                tk.Label(detail, text="No tasks due.",
                         bg=C["card"], fg=C["text_sub"], font=FONT_SMALL,
                         ).pack(anchor="w", padx=12, pady=(0, 6))
            else:
                for task in tasks_on_day:
                    pct  = task.get("progress", 0)
                    name = f"[{task['event']}] {task.get('process','')}"
                    if pct == 100:
                        color = "#60BB80" if not _dark else "#80DDA0"
                        suffix = "  (done)"
                    elif pct > 0:
                        color = C["accent"]
                        suffix = f"  {pct}%"
                    else:
                        color = C["text"]
                        suffix = "  (todo)"
                    row = tk.Frame(detail, bg=C["card"])
                    row.pack(fill="x", padx=8, pady=1)
                    tk.Label(row, text=name + suffix,
                             bg=C["card"], fg=color, font=FONT_SMALL,
                             anchor="w").pack(side="left")
                tk.Frame(detail, bg=C["card"], height=4).pack()

    def _cal_prev_month(self):
        if self._cal_month == 1:
            self._cal_year -= 1
            self._cal_month = 12
        else:
            self._cal_month -= 1
        self._cal_sel_day = None
        self._render_list()

    def _cal_next_month(self):
        if self._cal_month == 12:
            self._cal_year += 1
            self._cal_month = 1
        else:
            self._cal_month += 1
        self._cal_sel_day = None
        self._render_list()

    def _cal_go_today(self):
        today = datetime.date.today()
        self._cal_year  = today.year
        self._cal_month = today.month
        self._cal_sel_day = today.day
        self._render_list()

    # ── Pomodoro ───────────────────────────────────────────

    def _render_pomodoro(self):
        """ポモドーロタブを描画する。"""
        f = self._list_frame
        _dark = self._theme in ("dark", "claude", "scarlet", "ocean")

        state_text = {
            "idle": "Ready", "work": "Work", "break": "Break",
            "long_break": "Long Break", "paused": "Paused",
        }
        state_colors = {
            "idle":       C["text_sub"],
            "work":       C["accent"],
            "break":      "#4CAF50" if not _dark else "#80DDA0",
            "long_break": "#2196F3" if not _dark else "#80C8FF",
            "paused":     C["text_sub"],
        }

        # ── タイマーカード ──
        card = tk.Frame(f, bg=C["card"],
                        highlightthickness=1, highlightbackground=C["border"])
        card.pack(fill="x", padx=6, pady=(6, 3))

        # 1行目: [状態]  [MM:SS]  [サイクル]
        row1 = tk.Frame(card, bg=C["card"])
        row1.pack(fill="x", padx=10, pady=(6, 2))

        self._pomo_lbl_state = tk.Label(
            row1,
            text=state_text.get(self._pomo_state, "Ready"),
            bg=C["card"], fg=state_colors.get(self._pomo_state, C["text_sub"]),
            font=FONT_SMALL, width=9, anchor="w",
        )
        self._pomo_lbl_state.pack(side="left")

        mins, secs = divmod(self._pomo_remaining, 60)
        self._pomo_lbl_time = tk.Label(
            row1, text=f"{mins:02d}:{secs:02d}",
            bg=C["card"], fg=C["text"],
            font=("Segoe UI", 18, "bold"),
        )
        self._pomo_lbl_time.pack(side="left", padx=(4, 4))

        self._pomo_lbl_cycle = tk.Label(
            row1, text=self._pomo_cycle_text(),
            bg=C["card"], fg=C["text_sub"],
            font=FONT_SMALL,
        )
        self._pomo_lbl_cycle.pack(side="left")

        # 2行目: プログレスバー（細い横バー）
        self._pomo_canvas = tk.Canvas(card, height=6, bg=C["border"],
                                      highlightthickness=0)
        self._pomo_canvas.pack(fill="x", padx=10, pady=(2, 6))
        self._pomo_draw_arc()

        # ── ボタン行 ──
        btn_row = tk.Frame(f, bg=C["bg"])
        btn_row.pack(fill="x", padx=6, pady=(0, 3))

        if self._pomo_state in ("idle", "paused"):
            tk.Button(btn_row, text="Start",
                      command=self._pomo_start,
                      bg=C["accent"], fg="white", relief="flat", bd=0,
                      font=FONT_BOLD, cursor="hand2", pady=4,
                      activebackground=C["accent_dk"], activeforeground="white",
                      ).pack(side="left", fill="x", expand=True, padx=(0, 2))
        else:
            tk.Button(btn_row, text="Pause",
                      command=self._pomo_pause,
                      bg=C["accent_lt"], fg=C["accent_dk"], relief="flat", bd=0,
                      font=FONT_BOLD, cursor="hand2", pady=4,
                      activebackground=C["border"], activeforeground=C["accent_dk"],
                      ).pack(side="left", fill="x", expand=True, padx=(0, 2))

        tk.Button(btn_row, text="Reset",
                  command=self._pomo_reset,
                  bg=C["card"], fg=C["text_sub"], relief="flat", bd=0,
                  font=FONT, cursor="hand2", pady=4,
                  activebackground=C["card_h"], activeforeground=C["text"],
                  ).pack(side="left", fill="x", expand=True)

        # ── リンクタスク ──
        task_row = tk.Frame(f, bg=C["bg"])
        task_row.pack(fill="x", padx=6, pady=(0, 3))

        tk.Label(task_row, text="Task:",
                 bg=C["bg"], fg=C["text_sub"], font=FONT_SMALL).pack(side="left")

        task_names = ["(none)"] + [
            f"[{t['event']}] {t.get('process','')}" for t in self._tasks
        ]
        task_var = tk.StringVar()
        if self._pomo_task_idx is not None and self._pomo_task_idx < len(self._tasks):
            t = self._tasks[self._pomo_task_idx]
            task_var.set(f"[{t['event']}] {t.get('process','')}")
        else:
            task_var.set("(none)")

        om = tk.OptionMenu(task_row, task_var, *task_names)
        om.configure(bg=C["card"], fg=C["text"], relief="flat",
                     font=FONT_SMALL, cursor="hand2",
                     activebackground=C["card_h"], activeforeground=C["text"],
                     highlightthickness=0)
        om["menu"].configure(bg=C["card"], fg=C["text"],
                             activebackground=C["card_h"],
                             activeforeground=C["text"], font=FONT_SMALL)
        om.pack(side="left", padx=(4, 0), fill="x", expand=True)

        def _on_task_select(*_):
            val = task_var.get()
            if val == "(none)":
                self._pomo_task_idx = None
            else:
                for i, t in enumerate(self._tasks):
                    if f"[{t['event']}] {t.get('process','')}" == val:
                        self._pomo_task_idx = i
                        break
        task_var.trace_add("write", _on_task_select)

        # ── 統計 ──
        tk.Label(f,
                 text=f"Sessions: {self._pomo_session}   "
                      f"{self._pomo_work_min}m / {self._pomo_break_min}m / {self._pomo_long_break_min}m",
                 bg=C["bg"], fg=C["text_sub"], font=FONT_SMALL,
                 ).pack(anchor="w", padx=8, pady=(0, 4))

    def _pomo_cycle_text(self) -> str:
        dots = ""
        for i in range(4):
            dots += "* " if i < (self._pomo_cycle % 4) else "- "
        return dots.strip()

    def _pomo_draw_arc(self):
        """円形プログレスバーを描画する。"""
        c = self._pomo_canvas
        if c is None:
            return
        c.update_idletasks()
        w = c.winfo_width()
        if w <= 1:
            w = 260
        c.delete("all")
        _dark = self._theme in ("dark", "claude", "scarlet", "ocean")

        total = self._pomo_total_seconds()
        ratio = max(0.0, min(1.0, self._pomo_remaining / total)) if total > 0 else 1.0

        arc_colors = {
            "work":       C["accent"],
            "break":      "#4CAF50" if not _dark else "#80DDA0",
            "long_break": "#2196F3" if not _dark else "#80C8FF",
        }
        bar_color = arc_colors.get(self._pomo_state, C["accent_lt"])

        fill_w = int(w * ratio)
        if fill_w > 0:
            c.create_rectangle(0, 0, fill_w, 6, fill=bar_color, outline="")

    def _pomo_total_seconds(self) -> int:
        state = self._pomo_state
        if state == "paused":
            state = self._pomo_paused_state
        if state == "work":
            return self._pomo_work_min * 60
        elif state == "long_break":
            return self._pomo_long_break_min * 60
        else:
            return self._pomo_break_min * 60

    def _pomo_start(self):
        if self._pomo_state == "idle":
            self._pomo_remaining = self._pomo_work_min * 60
            self._pomo_state = "work"
        elif self._pomo_state == "paused":
            self._pomo_state = self._pomo_paused_state
        self._pomo_tick()
        self._render_list()

    def _pomo_pause(self):
        if self._pomo_state in ("work", "break", "long_break"):
            self._pomo_paused_state = self._pomo_state
            self._pomo_state = "paused"
            if self._pomo_after_id:
                self.after_cancel(self._pomo_after_id)
                self._pomo_after_id = None
        self._render_list()

    def _pomo_reset(self):
        if self._pomo_after_id:
            self.after_cancel(self._pomo_after_id)
            self._pomo_after_id = None
        self._pomo_state = "idle"
        self._pomo_remaining = self._pomo_work_min * 60
        self._render_list()

    def _pomo_tick(self):
        if self._pomo_state not in ("work", "break", "long_break"):
            return
        self._pomo_remaining -= 1

        # ラベル更新（タブが表示中のみ）
        if self._pomo_lbl_time is not None:
            mins, secs = divmod(self._pomo_remaining, 60)
            try:
                self._pomo_lbl_time.configure(text=f"{mins:02d}:{secs:02d}")
            except tk.TclError:
                self._pomo_lbl_time = None
        if self._pomo_canvas is not None:
            try:
                self._pomo_draw_arc()
            except tk.TclError:
                self._pomo_canvas = None

        if self._pomo_remaining <= 0:
            self._pomo_on_complete()
            return

        self._pomo_after_id = self.after(1000, self._pomo_tick)

    def _pomo_on_complete(self):
        self.bell()
        if self._pomo_state == "work":
            self._pomo_session += 1
            self._pomo_cycle += 1
            # リンクタスクに作業ログを記録
            if self._pomo_task_idx is not None and self._pomo_task_idx < len(self._tasks):
                task = self._tasks[self._pomo_task_idx]
                now = datetime.datetime.now()
                start = now - datetime.timedelta(minutes=self._pomo_work_min)
                task.setdefault("work_logs", []).append({
                    "start": start.isoformat(timespec="seconds"),
                    "end":   now.isoformat(timespec="seconds"),
                    "note":  "Pomodoro",
                })
                self._save_config()
            # 4サイクルで長休憩
            if self._pomo_cycle % 4 == 0:
                self._pomo_state = "long_break"
                self._pomo_remaining = self._pomo_long_break_min * 60
            else:
                self._pomo_state = "break"
                self._pomo_remaining = self._pomo_break_min * 60
        else:
            self._pomo_state = "work"
            self._pomo_remaining = self._pomo_work_min * 60

        if self._active == -10:
            self._render_list()
        else:
            # バックグラウンドでも自動開始
            self._pomo_after_id = self.after(1000, self._pomo_tick)

    def _pomo_open_settings(self):
        dlg = tk.Toplevel(self)
        dlg.title("Pomodoro Settings")
        dlg.configure(bg=C["bg"])
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        def _row(label, default):
            row = tk.Frame(dlg, bg=C["bg"])
            row.pack(fill="x", padx=16, pady=4)
            tk.Label(row, text=label, bg=C["bg"], fg=C["text"],
                     font=FONT, width=14, anchor="w").pack(side="left")
            var = tk.StringVar(value=str(default))
            tk.Entry(row, textvariable=var, bg=C["card"], fg=C["text"],
                     insertbackground=C["text"], relief="flat",
                     font=FONT, width=6).pack(side="left", padx=(4, 0))
            return var

        tk.Label(dlg, text="Pomodoro Settings", bg=C["bg"], fg=C["text"],
                 font=FONT_BOLD, pady=10).pack()

        v_work  = _row("Work (min):",       self._pomo_work_min)
        v_break = _row("Break (min):",      self._pomo_break_min)
        v_long  = _row("Long break (min):", self._pomo_long_break_min)

        def _save():
            try:
                self._pomo_work_min       = max(1, int(v_work.get()))
                self._pomo_break_min      = max(1, int(v_break.get()))
                self._pomo_long_break_min = max(1, int(v_long.get()))
            except ValueError:
                pass
            if self._pomo_state == "idle":
                self._pomo_remaining = self._pomo_work_min * 60
            dlg.destroy()
            self._render_list()

        btn_row = tk.Frame(dlg, bg=C["bg"])
        btn_row.pack(pady=(8, 12))
        tk.Button(btn_row, text="Save",
                  command=_save,
                  bg=C["accent"], fg="white", relief="flat", bd=0,
                  font=FONT_BOLD, cursor="hand2", padx=20, pady=6,
                  activebackground=C["accent_dk"], activeforeground="white",
                  ).pack(side="left", padx=4)
        tk.Button(btn_row, text="Cancel",
                  command=dlg.destroy,
                  bg=C["card"], fg=C["text_sub"], relief="flat", bd=0,
                  font=FONT, cursor="hand2", padx=12, pady=6,
                  activebackground=C["card_h"], activeforeground=C["text"],
                  ).pack(side="left", padx=4)

    # ── Task list ─────────────────────────────────────────

    def _render_kanban(self):
        """Render tasks as a Kanban board: Todo / Doing / Done columns."""
        if not self._tasks:
            tk.Label(
                self._list_frame,
                text="No tasks registered.\nClick \"+ Add Task\" to add one.",
                bg=C["bg"], fg=C["text_sub"],
                font=FONT_SMALL, justify="center",
            ).pack(pady=20)
            return

        # Classify tasks
        cols_data: dict[str, list[tuple[int, dict]]] = {
            "Todo": [], "Doing": [], "Done": []
        }
        for i, task in enumerate(self._tasks):
            pct = task.get("progress", 0)
            if pct == 100:
                cols_data["Done"].append((i, task))
            elif pct == 0:
                cols_data["Todo"].append((i, task))
            else:
                cols_data["Doing"].append((i, task))

        board = tk.Frame(self._list_frame, bg=C["bg"])
        board.pack(fill="both", expand=True, padx=2, pady=2)
        board.columnconfigure(0, weight=1)
        board.columnconfigure(1, weight=1)
        board.columnconfigure(2, weight=1)

        col_order = ["Todo", "Doing", "Done"]
        _dark = self._theme in ("dark", "claude", "scarlet", "ocean")
        col_header_colors = {
            "Todo":  ("#5C3A5C", "#DDB8DD") if _dark else ("#EDD0ED", "#5C1A5C"),
            "Doing": ("#3A4A5C", "#B0C8FF") if _dark else ("#D0DEFF", "#1A2A5C"),
            "Done":  ("#1A3C24", "#80DDA0") if _dark else ("#C8EDD4", "#1A5C2E"),
        }

        for col_num, col_name in enumerate(col_order):
            tasks = cols_data[col_name]
            hdr_bg, hdr_fg = col_header_colors[col_name]

            col_frame = tk.Frame(board, bg=C["card"],
                                 highlightthickness=1,
                                 highlightbackground=C["border"])
            col_frame.grid(row=0, column=col_num, sticky="nsew",
                           padx=(0 if col_num == 0 else 3, 0), pady=0)

            # Column header
            tk.Label(col_frame,
                     text=f"{col_name}  ({len(tasks)})",
                     bg=hdr_bg, fg=hdr_fg,
                     font=FONT_BOLD, anchor="w", padx=8, pady=5,
                     ).pack(fill="x")

            # Scrollable area for cards
            canvas = tk.Canvas(col_frame, bg=C["card"], highlightthickness=0)
            vsb = tk.Scrollbar(col_frame, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=vsb.set)
            vsb.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)

            inner = tk.Frame(canvas, bg=C["card"])
            inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")

            def _on_configure(e, c=canvas, w=inner_id):
                c.configure(scrollregion=c.bbox("all"))
                c.itemconfigure(w, width=c.winfo_width())

            canvas.bind("<Configure>", _on_configure)
            inner.bind("<Configure>", lambda e, c=canvas: c.configure(
                scrollregion=c.bbox("all")))

            def _bind_scroll(widget, c=canvas):
                widget.bind("<MouseWheel>",
                            lambda e, cv=c: cv.yview_scroll(-1 * (e.delta // 120), "units"))
                for child in widget.winfo_children():
                    _bind_scroll(child, c)

            if not tasks:
                tk.Label(inner, text="(empty)",
                         bg=C["card"], fg=C["text_sub"],
                         font=FONT_SMALL, pady=10,
                         ).pack()
            else:
                for i, task in tasks:
                    pct = task.get("progress", 0)
                    deadline = task.get("deadline", "")
                    process = task.get("process", "")
                    event = task.get("event", "")

                    card = tk.Frame(inner, bg=C["card_h"],
                                    highlightthickness=1,
                                    highlightbackground=C["border"],
                                    padx=6, pady=5)
                    card.pack(fill="x", padx=4, pady=3)
                    card.bind("<MouseWheel>",
                              lambda e, cv=canvas: cv.yview_scroll(
                                  -1 * (e.delta // 120), "units"))

                    # Title row: [event] process
                    title_frame = tk.Frame(card, bg=C["card_h"])
                    title_frame.pack(fill="x")
                    tk.Label(title_frame, text=f"[{event}]",
                             bg=C["card_h"], fg=C["text_sub"],
                             font=FONT_SMALL, anchor="w",
                             ).pack(side="left")
                    tk.Label(title_frame, text=process,
                             bg=C["card_h"], fg=C["text"],
                             font=FONT_BOLD, anchor="w",
                             ).pack(side="left", padx=(4, 0), fill="x", expand=True)

                    # Progress bar
                    bar_bg = tk.Frame(card, bg=C["border"], height=4)
                    bar_bg.pack(fill="x", pady=(3, 1))
                    bar_bg.update_idletasks()
                    if pct > 0:
                        fill_color = (
                            C["accent"] if pct < 100
                            else (C["accent_dk"] if _dark else "#2E8B57")
                        )
                        tk.Frame(bar_bg, bg=fill_color, height=4,
                                 width=int(bar_bg.winfo_reqwidth() * pct / 100)
                                 ).place(x=0, y=0, relwidth=pct / 100, relheight=1)
                    tk.Label(card, text=f"{pct}%",
                             bg=C["card_h"], fg=C["text_sub"],
                             font=FONT_SMALL, anchor="e",
                             ).pack(fill="x")

                    if deadline:
                        try:
                            d = datetime.date.fromisoformat(deadline)
                            delta = (d - datetime.date.today()).days
                            if delta < 0:
                                dl_text = f"Overdue {abs(delta)}d"
                                dl_fg = C["btn_del"]
                            elif delta == 0:
                                dl_text = "Due today"
                                dl_fg = C["btn_del"]
                            else:
                                dl_text = f"Due +{delta}d"
                                dl_fg = C["text_sub"]
                        except ValueError:
                            dl_text = deadline
                            dl_fg = C["text_sub"]
                        tk.Label(card, text=dl_text,
                                 bg=C["card_h"], fg=dl_fg,
                                 font=FONT_SMALL, anchor="w",
                                 ).pack(fill="x")

                    # Action buttons row
                    btn_row = tk.Frame(card, bg=C["card_h"])
                    btn_row.pack(fill="x", pady=(4, 0))

                    def _make_edit_cmd(task_idx=i):
                        def _cmd():
                            self._task_quick_edit(task_idx)
                        return _cmd

                    tk.Button(btn_row, text="Edit",
                              command=_make_edit_cmd(i),
                              bg=C["accent_lt"], fg=C["accent_dk"],
                              relief="flat", bd=0,
                              font=FONT_SMALL, cursor="hand2", padx=6, pady=2,
                              activebackground=C["border"],
                              activeforeground=C["accent_dk"],
                              ).pack(side="left")

                    # Move left / right
                    prev_col = col_order[col_num - 1] if col_num > 0 else None
                    next_col = col_order[col_num + 1] if col_num < 2 else None

                    def _make_move_cmd(task_idx, col_idx, direction):
                        def _cmd():
                            t = self._tasks[task_idx]
                            # col_idx: 0=Todo, 1=Doing, 2=Done
                            if direction == "next":
                                t["progress"] = 50 if col_idx == 0 else 100
                            else:
                                t["progress"] = 50 if col_idx == 2 else 0
                            t["updated"] = datetime.date.today().isoformat()
                            self._save_config()
                            self._render_list()
                        return _cmd

                    if prev_col:
                        tk.Button(btn_row, text="< " + prev_col,
                                  command=_make_move_cmd(i, col_num, "prev"),
                                  bg=C["card"], fg=C["text_sub"],
                                  relief="flat", bd=0,
                                  font=FONT_SMALL, cursor="hand2", padx=6, pady=2,
                                  activebackground=C["card_h"],
                                  activeforeground=C["text"],
                                  ).pack(side="right", padx=(2, 0))
                    if next_col:
                        tk.Button(btn_row, text=next_col + " >",
                                  command=_make_move_cmd(i, col_num, "next"),
                                  bg=C["card"], fg=C["text_sub"],
                                  relief="flat", bd=0,
                                  font=FONT_SMALL, cursor="hand2", padx=6, pady=2,
                                  activebackground=C["card_h"],
                                  activeforeground=C["text"],
                                  ).pack(side="right")

                    _bind_scroll(card)

    def _task_quick_edit(self, task_idx: int):
        """Open the task edit dialog for the given task index."""
        self._edit_task(task_idx)

    def _render_task_list(self):
        # configure Treeview style to match theme
        style = ttk.Style()
        style.configure("TaskTree.Treeview",
                        background=C["card"], foreground=C["text"],
                        fieldbackground=C["card"], rowheight=26, font=FONT)
        style.configure("TaskTree.Treeview.Heading",
                        background=C["tab_inact"], foreground=C["text"],
                        font=FONT_BOLD, relief="flat", padding=4)
        style.map("TaskTree.Treeview.Heading",
                  background=[("active", C["card_h"]), ("!active", C["tab_inact"])],
                  foreground=[("active", C["text"]),   ("!active", C["text"])])
        style.map("TaskTree.Treeview",
                  background=[("selected", C["card_h"])],
                  foreground=[("selected", C["text"])])

        # 上部ツールバー（Summary / Kanban toggle）
        toolbar = tk.Frame(self._list_frame, bg=C["bg"])
        toolbar.pack(fill="x", padx=2, pady=(2, 0))
        tk.Button(toolbar, text="Work Summary",
                  command=self._open_work_summary,
                  bg=C["card"], fg=C["text_sub"], relief="flat", bd=0,
                  font=FONT_SMALL, cursor="hand2", padx=8, pady=3,
                  activebackground=C["card_h"], activeforeground=C["text"],
                  ).pack(side="right")

        def _toggle_view():
            self._task_view = "kanban" if self._task_view == "list" else "list"
            self._render_list()

        kanban_btn_bg = C["accent_lt"] if self._task_view == "kanban" else C["card"]
        tk.Button(toolbar, text="Kanban",
                  command=_toggle_view,
                  bg=kanban_btn_bg, fg=C["text_sub"], relief="flat", bd=0,
                  font=FONT_SMALL, cursor="hand2", padx=8, pady=3,
                  activebackground=C["card_h"], activeforeground=C["text"],
                  ).pack(side="right", padx=(0, 2))

        if self._task_view == "kanban":
            self._render_kanban()
            return

        # 作業中バー
        self._work_bar_lbl = None
        if self._work_active is not None:
            wa   = self._work_active
            task = self._tasks[wa["task_idx"]]
            elapsed = (datetime.datetime.now() - wa["start"]).total_seconds()
            bar = tk.Frame(self._list_frame, bg=C["accent_lt"])
            bar.pack(fill="x", padx=2, pady=(2, 0))
            self._work_bar_lbl = tk.Label(
                bar,
                text=f"{task.get('process', '')}  作業中...  {_fmt_duration(elapsed)}",
                bg=C["accent_lt"], fg=C["accent_dk"], font=FONT_BOLD, anchor="w",
            )
            self._work_bar_lbl.pack(side="left", padx=10, pady=5)
            tk.Button(bar, text="Stop Work",
                      command=lambda: self._stop_work(wa["task_idx"]),
                      bg=C["btn_del"], fg="white", relief="flat", bd=0,
                      font=FONT, cursor="hand2", padx=10, pady=3,
                      activebackground=C["btn_del_h"], activeforeground="white",
                      ).pack(side="right", padx=8, pady=4)
            self._work_anim_dots = 0
            self._work_anim_step()

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
                return label + (" v" if self._task_sort["reverse"] else " ^")
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
        _dark = self._theme in ("dark", "claude", "scarlet", "ocean")
        if _dark:
            tree.tag_configure("p_red",    background="#5C1A20", foreground="#FFB0B8")
            tree.tag_configure("p_yellow", background="#4A3A00", foreground="#FFE680")
            tree.tag_configure("p_green",  background="#1A3C24", foreground="#80DDA0")
            tree.tag_configure("done",     background="#163020", foreground="#60CC80")
        else:
            tree.tag_configure("p_red",    background="#FFCCCC", foreground="#7A1A1A")
            tree.tag_configure("p_yellow", background="#FFF3BC", foreground="#6B4E00")
            tree.tag_configure("p_green",  background="#C8EDD4", foreground="#1A5C2E")
            tree.tag_configure("done",     background="#A8DDB8", foreground="#0F4020")

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
                _recur_badge = {
                    "daily": "[D]", "weekly": "[W]", "biweekly": "[2W]",
                    "monthly": "[M]", "yearly": "[Y]",
                }.get(task.get("recur", "none"), "")
                process_disp = task.get("process", "")
                if _recur_badge:
                    process_disp = f"{_recur_badge} {process_disp}"
                tree.insert(parent, "end", iid=str(i), text="",
                            tags=(_progress_tag(pct),),
                            values=(process_disp, content,
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
        memo_row.pack(fill="x", padx=6, pady=(0, 2))
        work_row = tk.Frame(detail_bg, bg=C["card"])
        work_row.pack(fill="x", padx=6, pady=(0, 4))

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

            # Memo row (rebuild each time)
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

            # 作業時間ログ行（毎回再構築）
            for w in work_row.winfo_children():
                w.destroy()
            logs = task.get("work_logs", [])
            log_count = len(logs)
            total_sec = sum(
                (datetime.datetime.fromisoformat(lg["end"]) -
                 datetime.datetime.fromisoformat(lg["start"])).total_seconds()
                for lg in logs if lg.get("end")
            )
            is_running = (
                self._work_active is not None and
                self._work_active["task_idx"] == idx
            )
            if is_running:
                elapsed = (datetime.datetime.now() -
                           self._work_active["start"]).total_seconds()
                tk.Label(work_row,
                         text=f"Working...  {_fmt_duration(elapsed)}",
                         bg=C["card"], fg=C["accent"], font=FONT_SMALL,
                         anchor="w").pack(side="left")
                tk.Button(work_row, text="Stop Work",
                          command=lambda i=idx: self._stop_work(i),
                          bg=C["btn_del"], fg="white", relief="flat", bd=0,
                          font=FONT, cursor="hand2", padx=10, pady=4,
                          activebackground=C["btn_del_h"], activeforeground="white",
                          ).pack(side="right", padx=(4, 0))
            else:
                if total_sec:
                    tk.Label(work_row,
                             text=f"Total: {_fmt_duration(total_sec)}",
                             bg=C["card"], fg=C["text_sub"], font=FONT_SMALL,
                             anchor="w").pack(side="left")
                tk.Button(work_row, text="Start Work",
                          command=lambda i=idx: self._start_work(i),
                          bg=C["accent"], fg="white", relief="flat", bd=0,
                          font=FONT, cursor="hand2", padx=10, pady=4,
                          activebackground=C["accent_dk"], activeforeground="white",
                          ).pack(side="right", padx=(4, 0))
            if log_count:
                tk.Button(work_row, text=f"Log ({log_count})",
                          command=lambda i=idx: self._open_work_log(i),
                          bg=C["card"], fg=C["text_sub"], relief="flat", bd=0,
                          font=FONT_SMALL, cursor="hand2", padx=8, pady=4,
                          activebackground=C["card_h"], activeforeground=C["text"],
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
            is_running = (self._work_active is not None and
                          self._work_active["task_idx"] == idx)
            if is_running:
                menu.add_command(label="Stop Work",
                                 command=lambda: self._stop_work(idx))
            else:
                menu.add_command(label="Start Work",
                                 command=lambda: self._start_work(idx))
            menu.add_separator()
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
        prev_progress = self._tasks[idx].get("progress", 0)
        # 既存フィールド（memos, created_at 等）を保持しつつ上書き
        merged = dict(self._tasks[idx])
        merged.update(dlg.result)
        merged["updated"] = datetime.date.today().isoformat()
        self._tasks[idx] = merged
        # 繰り返しタスク：完了時に次回分を生成
        if merged.get("recur", "none") != "none" and merged.get("progress", 0) == 100 and prev_progress < 100:
            self._spawn_recurring(merged)
        self._save_tasks()
        self._render_list()

    # ── Recurring tasks ────────────────────────────────────

    @staticmethod
    def _next_recur_date(base: str, recur: str) -> str:
        """繰り返し種別に応じて次回の締め切り日を返す。"""
        try:
            d = datetime.date.fromisoformat(base) if base else datetime.date.today()
        except ValueError:
            d = datetime.date.today()
        if recur == "daily":
            d += datetime.timedelta(days=1)
        elif recur == "weekly":
            d += datetime.timedelta(weeks=1)
        elif recur == "biweekly":
            d += datetime.timedelta(weeks=2)
        elif recur == "monthly":
            month = d.month + 1
            year  = d.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            day   = min(d.day, [31,28+int((year%4==0 and year%100!=0)or year%400==0),
                                 31,30,31,30,31,31,30,31,30,31][month-1])
            d = d.replace(year=year, month=month, day=day)
        elif recur == "yearly":
            try:
                d = d.replace(year=d.year + 1)
            except ValueError:
                d = d.replace(year=d.year + 1, day=28)
        return d.isoformat()

    def _spawn_recurring(self, source: dict):
        """完了した繰り返しタスクの次回分を生成して追加する。"""
        recur = source.get("recur", "none")
        if recur == "none":
            return
        next_dl = self._next_recur_date(source.get("deadline", ""), recur)
        new_task = {
            "event":        source["event"],
            "process":      source.get("process", ""),
            "content":      source.get("content", ""),
            "progress":     0,
            "deadline":     next_dl,
            "recur":        recur,
            "work_folders": list(source.get("work_folders", [])),
            "created_at":   datetime.date.today().isoformat(),
            "updated":      datetime.date.today().isoformat(),
        }
        self._tasks.append(new_task)

    def _check_recurring_tasks(self):
        """起動時に繰り返しタスクの未生成分を補完する。"""
        today = datetime.date.today()
        to_add = []
        for task in self._tasks:
            recur = task.get("recur", "none")
            if recur == "none" or task.get("progress", 0) < 100:
                continue
            dl = task.get("deadline", "")
            next_dl = self._next_recur_date(dl, recur)
            try:
                next_date = datetime.date.fromisoformat(next_dl)
            except ValueError:
                continue
            if next_date > today:
                continue
            # 同じ event+process+recur で未完了のものがなければ生成
            exists = any(
                t.get("recur") == recur
                and t.get("event") == task["event"]
                and t.get("process") == task.get("process")
                and t.get("progress", 0) < 100
                for t in self._tasks
            )
            if not exists:
                to_add.append(task)
        for t in to_add:
            self._spawn_recurring(t)
        if to_add:
            self._save_tasks()

    def _remove_task(self, idx: int):
        name = self._tasks[idx]["event"]
        if messagebox.askyesno("Remove", f"Remove \"{name}\"?", parent=self):
            self._tasks.pop(idx)
            self._save_tasks()
            self._render_list()

    def _open_gantt(self):
        GanttWindow(self, self._tasks)

    # ── Work time tracking ────────────────────────────────

    def _work_anim_step(self):
        """作業中バーのドットアニメーションを更新する。"""
        if self._work_anim_id is not None:
            self.after_cancel(self._work_anim_id)
            self._work_anim_id = None
        if self._work_active is None:
            return
        lbl = self._work_bar_lbl
        if lbl is None or not lbl.winfo_exists():
            return
        self._work_anim_dots = (self._work_anim_dots + 1) % 4
        dots = ("." * self._work_anim_dots).ljust(3)
        wa   = self._work_active
        task = self._tasks[wa["task_idx"]]
        elapsed = (datetime.datetime.now() - wa["start"]).total_seconds()
        lbl.configure(
            text=f"{task.get('process', '')}  作業中{dots}  {_fmt_duration(elapsed)}"
        )
        self._work_anim_id = self.after(500, self._work_anim_step)

    def _start_work(self, task_idx: int):
        """作業開始：現在時刻を記録する。"""
        if self._work_active is not None:
            if not messagebox.askyesno(
                "作業中",
                "別のタスクの作業中です。切り替えますか？",
                parent=self,
            ):
                return
            self._stop_work(self._work_active["task_idx"])
        self._work_active = {
            "task_idx": task_idx,
            "start": datetime.datetime.now(),
        }
        self._render_list()

    def _stop_work(self, task_idx: int):
        """作業終了：ログに記録して保存する。"""
        if self._work_active is None:
            return
        start_dt = self._work_active["start"]
        end_dt   = datetime.datetime.now()
        self._work_active = None
        task = self._tasks[task_idx]
        task.setdefault("work_logs", []).append({
            "start": start_dt.isoformat(timespec="seconds"),
            "end":   end_dt.isoformat(timespec="seconds"),
        })
        self._save_tasks()
        self._render_list()

    # ── System tray ───────────────────────────────────────

    def _on_unmap(self, event):
        if event.widget is self and self.state() == "iconic":
            self._minimize_to_tray()

    def _on_close(self):
        self.destroy()

    def _set_card_size(self, size: str):
        self._card_size = size
        self._save_config()
        self._render_list()

    def _open_transparency_dialog(self):
        """Show a slider dialog to adjust window transparency."""
        win = tk.Toplevel(self)
        win.title("Transparency")
        win.configure(bg=C["bg"])
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="Window transparency",
                 bg=C["bg"], fg=C["text"], font=FONT).pack(padx=20, pady=(16, 4))

        current = int(self.attributes("-alpha") * 100)
        val_var = tk.StringVar(value=f"{current}%")

        tk.Label(win, textvariable=val_var,
                 bg=C["bg"], fg=C["accent"], font=FONT_BOLD).pack()

        def _on_slide(v):
            alpha = int(float(v)) / 100
            self.attributes("-alpha", alpha)
            val_var.set(f"{int(float(v))}%")

        scale = tk.Scale(win, from_=30, to=100, orient="horizontal",
                         length=200, command=_on_slide,
                         bg=C["bg"], fg=C["text"],
                         troughcolor=C["card"], activebackground=C["accent"],
                         highlightthickness=0, bd=0, showvalue=False)
        scale.set(current)
        scale.pack(padx=20, pady=(4, 12))

        btn_row = tk.Frame(win, bg=C["bg"])
        btn_row.pack(padx=20, pady=(0, 16))

        def _ok():
            self._save_config()
            win.destroy()

        def _cancel():
            self.attributes("-alpha", self._alpha_cfg)
            win.destroy()

        tk.Button(btn_row, text="OK", command=_ok,
                  bg=C["accent"], fg="white", relief="flat", bd=0,
                  font=FONT_BOLD, cursor="hand2", padx=20, pady=4,
                  activebackground=C["accent_dk"], activeforeground="white",
                  ).pack(side="left", padx=(0, 6))
        tk.Button(btn_row, text="Cancel", command=_cancel,
                  bg=C["card"], fg=C["text"], relief="flat", bd=0,
                  font=FONT, cursor="hand2", padx=12, pady=4,
                  activebackground=C["card_h"], activeforeground=C["text"],
                  ).pack(side="left")

        win.update_idletasks()
        wx = self.winfo_rootx() + (self.winfo_width()  - win.winfo_width())  // 2
        wy = self.winfo_rooty() + (self.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{wx}+{wy}")
        win.protocol("WM_DELETE_WINDOW", _cancel)

    def _show_startup_summary(self):
        """Show a startup popup summarising tasks due today and overdue."""
        today = datetime.date.today().isoformat()

        due_today = [t for t in self._tasks
                     if t.get("due") == today and t.get("status") != "done"]
        overdue   = [t for t in self._tasks
                     if t.get("due") and t.get("due") < today
                     and t.get("status") != "done"]

        if not due_today and not overdue:
            return

        win = tk.Toplevel(self)
        win.title("Today's Summary")
        win.configure(bg=C["bg"])
        win.resizable(False, False)
        win.attributes("-topmost", True)

        # Header
        tk.Label(win, text="Today's Summary",
                 bg=C["accent"], fg="white",
                 font=FONT_BOLD, anchor="w", padx=12, pady=6
                 ).pack(fill="x")

        body = tk.Frame(win, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=14, pady=10)

        def _section(title, tasks, fg_title):
            if not tasks:
                return
            tk.Label(body, text=title,
                     bg=C["bg"], fg=fg_title,
                     font=FONT_BOLD, anchor="w").pack(fill="x", pady=(4, 2))
            for t in tasks[:8]:
                name = t.get("event", "") or t.get("process", "—")
                due  = t.get("due", "")
                line = f"  {name}" + (f"  ({due})" if due else "")
                tk.Label(body, text=line,
                         bg=C["bg"], fg=C["text"],
                         font=FONT_SMALL, anchor="w").pack(fill="x")
            if len(tasks) > 8:
                tk.Label(body, text=f"  ... and {len(tasks) - 8} more",
                         bg=C["bg"], fg=C["text_sub"],
                         font=FONT_SMALL, anchor="w").pack(fill="x")

        _section(f"Due today  ({len(due_today)})", due_today, C["accent"])
        _section(f"Overdue  ({len(overdue)})",     overdue,   "#C84040")

        # Footer: countdown + close button
        footer = tk.Frame(win, bg=C["bg"])
        footer.pack(fill="x", padx=14, pady=(4, 10))

        count_var = tk.StringVar()
        tk.Label(footer, textvariable=count_var,
                 bg=C["bg"], fg=C["text_sub"], font=FONT_SMALL).pack(side="left")
        tk.Button(footer, text="Close", command=win.destroy,
                  bg=C["accent"], fg="white", relief="flat", bd=0,
                  font=FONT_SMALL, cursor="hand2", padx=12, pady=3,
                  activebackground=C["accent_dk"], activeforeground="white",
                  ).pack(side="right")

        # Auto-close countdown
        _remaining = [10]
        def _tick():
            if not win.winfo_exists():
                return
            count_var.set(f"Closing in {_remaining[0]} s")
            if _remaining[0] <= 0:
                win.destroy()
                return
            _remaining[0] -= 1
            win.after(1000, _tick)
        _tick()

        # Position: bottom-right of main window
        win.update_idletasks()
        wx = self.winfo_rootx() + self.winfo_width()  - win.winfo_width()  - 10
        wy = self.winfo_rooty() + self.winfo_height() - win.winfo_height() - 10
        win.geometry(f"+{wx}+{wy}")

    def _minimize_to_tray(self):
        self.withdraw()
        if self._tray_icon is not None:
            return  # already running

        png_data = base64.b64decode(_make_icon_png(
            ICON_PALETTES.get(self._theme, ICON_PALETTES["violet"])
        ))
        img = Image.open(io.BytesIO(png_data)).convert("RGBA")

        menu = pystray.Menu(
            pystray.MenuItem("Show Gem", self._restore_from_tray, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._quit_from_tray),
        )
        self._tray_icon = pystray.Icon("Gem", img, "Gem", menu)
        threading.Thread(target=self._tray_icon.run, daemon=True).start()

    def _restore_from_tray(self, icon=None, item=None):
        self.after(0, self._do_restore)

    def _do_restore(self):
        if self._tray_icon is not None:
            self._tray_icon.stop()
            self._tray_icon = None
        self.deiconify()
        self.lift()
        self.focus_force()

    def _quit_from_tray(self, icon=None, item=None):
        self.after(0, self._do_quit)

    def _do_quit(self):
        if self._tray_icon is not None:
            self._tray_icon.stop()
            self._tray_icon = None
        self.destroy()

    def _open_sleep_screen(self, fullscreen: bool = False):
        """Sleep overlay showing clock and active task."""
        if self._sleep_win and self._sleep_win.winfo_exists():
            return

        BG      = C["card"]
        FG      = C["text"]
        ACCENT  = C["accent"]
        DIM     = C["text_sub"]
        BORDER  = C["border"]

        win = tk.Toplevel(self)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=BG)

        if fullscreen:
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            win.geometry(f"{sw}x{sh}+0+0")
            clock_size, date_size, task_size, elapsed_size, hint_size = 80, 16, 18, 13, 9
        else:
            self.update_idletasks()
            wx = self.winfo_rootx()
            wy = self.winfo_rooty()
            ww = self.winfo_width()
            wh = self.winfo_height()
            win.geometry(f"{ww}x{wh}+{wx}+{wy}")

        _follow_bid = [None]
        if not fullscreen:
            def _follow(e=None):
                if not win.winfo_exists():
                    return
                win.geometry(f"{self.winfo_width()}x{self.winfo_height()}"
                             f"+{self.winfo_rootx()}+{self.winfo_rooty()}")
            _follow_bid[0] = self.bind("<Configure>", _follow)
            clock_size, date_size, task_size, elapsed_size, hint_size = 48, 12, 14, 11, 8

        self._sleep_win = win

        tk.Frame(win, bg=BORDER, height=2).place(relx=0, rely=0, relwidth=1)

        clock_lbl = tk.Label(win, text="", bg=BG, fg=FG,
                             font=("Segoe UI", clock_size, "bold"))
        clock_lbl.place(relx=0.5, rely=0.38, anchor="center")

        date_lbl = tk.Label(win, text="", bg=BG, fg=DIM,
                            font=("Segoe UI", date_size))
        date_lbl.place(relx=0.5, rely=0.54, anchor="center")

        task_lbl = tk.Label(win, text="", bg=BG, fg=ACCENT,
                            font=("Segoe UI", task_size, "bold"))
        task_lbl.place(relx=0.5, rely=0.65, anchor="center")

        elapsed_lbl = tk.Label(win, text="", bg=BG, fg=DIM,
                               font=("Segoe UI", elapsed_size))
        elapsed_lbl.place(relx=0.5, rely=0.74, anchor="center")

        hint_lbl = tk.Label(win, text="Click or press any key to wake",
                            bg=BG, fg=DIM, font=("Segoe UI", hint_size))
        hint_lbl.place(relx=0.5, rely=0.93, anchor="center")

        def _wake(e=None):
            if self._sleep_tick_id:
                self.after_cancel(self._sleep_tick_id)
                self._sleep_tick_id = None
            if _follow_bid[0] is not None:
                try:
                    self.unbind("<Configure>", _follow_bid[0])
                except Exception:
                    pass
            win.destroy()
            self._sleep_win = None

        def _tick_sleep():
            if not win.winfo_exists():
                return
            now = datetime.datetime.now()
            clock_lbl.configure(text=now.strftime("%H:%M"))
            date_lbl.configure(text=now.strftime("%Y-%m-%d  %A"))
            if self._work_active is not None:
                wa      = self._work_active
                task    = self._tasks[wa["task_idx"]]
                name    = task.get("process", "Task")
                elapsed = (now - wa["start"]).total_seconds()
                task_lbl.configure(text=f"Working on:  {name}")
                elapsed_lbl.configure(text=_fmt_duration(elapsed))
            else:
                task_lbl.configure(text="")
                elapsed_lbl.configure(text="")
            self._sleep_tick_id = self.after(1000, _tick_sleep)

        win.bind("<Button-1>", _wake)
        win.bind("<Key>",      _wake)
        win.focus_set()
        _tick_sleep()

    def _open_work_log(self, task_idx: int):
        """作業ログ一覧・削除ダイアログを開く。"""
        task = self._tasks[task_idx]
        logs = task.get("work_logs", [])

        dlg = tk.Toplevel(self)
        dlg.title(f"Work Log — {task.get('process', '')}")
        dlg.configure(bg=C["bg"])
        dlg.resizable(False, False)
        dlg.grab_set()

        # ヘッダー
        tk.Label(dlg, text=f"Work Log  [{task.get('event', '')}] {task.get('process', '')}",
                 bg=C["bg"], fg=C["text"], font=FONT_BOLD).pack(padx=16, pady=(12, 4), anchor="w")

        # ログ一覧フレーム
        frame = tk.Frame(dlg, bg=C["bg"])
        frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        def _refresh():
            for w in frame.winfo_children():
                w.destroy()
            logs = task.get("work_logs", [])
            if not logs:
                tk.Label(frame, text="記録なし", bg=C["bg"], fg=C["text_sub"],
                         font=FONT_SMALL).pack(pady=8)
                return
            total_sec = 0
            for i, lg in enumerate(logs):
                start_s = lg.get("start", "")
                end_s   = lg.get("end", "")
                try:
                    dt_s = datetime.datetime.fromisoformat(start_s)
                    dt_e = datetime.datetime.fromisoformat(end_s)
                    dur  = (dt_e - dt_s).total_seconds()
                    total_sec += dur
                    dur_str  = _fmt_duration(dur)
                    date_str = dt_s.strftime("%Y-%m-%d  %H:%M") + "  -  " + dt_e.strftime("%H:%M")
                except Exception:
                    dur_str  = "-"
                    date_str = f"{start_s} - {end_s}"

                row = tk.Frame(frame, bg=C["card"],
                               highlightthickness=1, highlightbackground=C["border"])
                row.pack(fill="x", pady=2)
                tk.Label(row, text=date_str, bg=C["card"], fg=C["text"],
                         font=FONT_SMALL, anchor="w").pack(side="left", padx=8, pady=4)
                tk.Label(row, text=dur_str, bg=C["card"], fg=C["accent"],
                         font=FONT_BOLD, anchor="e").pack(side="left", padx=(0, 12))
                tk.Button(row, text="x", command=lambda i=i: _delete(i),
                          bg=C["card"], fg=C["text_sub"], relief="flat", bd=0,
                          font=FONT_SMALL, cursor="hand2",
                          activebackground=C["btn_del"], activeforeground="white",
                          ).pack(side="right", padx=4)

            tk.Frame(frame, bg=C["border"], height=1).pack(fill="x", pady=(4, 0))
            tk.Label(frame, text=f"合計  {_fmt_duration(total_sec)}",
                     bg=C["bg"], fg=C["text"], font=FONT_BOLD,
                     anchor="e").pack(fill="x", pady=(2, 0))

        def _delete(i: int):
            task["work_logs"].pop(i)
            self._save_tasks()
            _refresh()

        _refresh()
        tk.Button(dlg, text="Close", command=dlg.destroy,
                  bg=C["accent_lt"], fg=C["text"], relief="flat", bd=0,
                  font=FONT, cursor="hand2", padx=16, pady=4,
                  activebackground=C["border"], activeforeground=C["text"],
                  ).pack(pady=(0, 12))

        dlg.update_idletasks()
        px = self.winfo_x() + (self.winfo_width()  - dlg.winfo_width())  // 2
        py = self.winfo_y() + (self.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{px}+{py}")
        dlg.wait_window()

    def _open_work_summary(self):
        """日別・タスク別の作業時間サマリーウィンドウを開く。"""
        win = tk.Toplevel(self)
        win.title("Work Summary")
        win.configure(bg=C["bg"])
        win.grab_set()

        # 全ログを日付ごとに集計
        # records: [(date_str, event, process, seconds)]
        records = []
        for task in self._tasks:
            for lg in task.get("work_logs", []):
                if not lg.get("end"):
                    continue
                try:
                    dt_s = datetime.datetime.fromisoformat(lg["start"])
                    dt_e = datetime.datetime.fromisoformat(lg["end"])
                    sec  = (dt_e - dt_s).total_seconds()
                    records.append((
                        dt_s.strftime("%Y-%m-%d"),
                        task.get("event", ""),
                        task.get("process", ""),
                        sec,
                        dt_s.strftime("%H:%M"),
                        dt_e.strftime("%H:%M"),
                    ))
                except Exception:
                    pass

        # ── Treeview ──
        style = ttk.Style()
        style.configure("SummaryTree.Treeview",
                        background=C["card"], foreground=C["text"],
                        fieldbackground=C["card"], rowheight=24, font=FONT)
        style.configure("SummaryTree.Treeview.Heading",
                        background=C["tab_inact"], foreground=C["text"],
                        font=FONT_BOLD, relief="flat")
        style.map("SummaryTree.Treeview.Heading",
                  background=[("active", C["card_h"]), ("!active", C["tab_inact"])],
                  foreground=[("active", C["text"]),   ("!active", C["text"])])
        style.map("SummaryTree.Treeview",
                  background=[("selected", C["card_h"])],
                  foreground=[("selected", C["text"])])

        tk.Label(win, text="Work Summary", bg=C["bg"], fg=C["text"],
                 font=FONT_BOLD).pack(padx=16, pady=(12, 4), anchor="w")

        frame = tk.Frame(win, bg=C["bg"])
        frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        cols = ("event", "process", "time", "duration")
        tree = ttk.Treeview(frame, columns=cols, show="tree headings",
                            style="SummaryTree.Treeview", height=16)
        tree.heading("#0",       text="Date",     anchor="w")
        tree.heading("event",    text="Event",    anchor="w")
        tree.heading("process",  text="Process",  anchor="w")
        tree.heading("time",     text="Time",     anchor="center")
        tree.heading("duration", text="Duration", anchor="center")
        tree.column("#0",       width=140, minwidth=100)
        tree.column("event",    width=110, minwidth=70)
        tree.column("process",  width=150, minwidth=90)
        tree.column("time",     width=110, minwidth=90)
        tree.column("duration", width=75,  minwidth=55)

        vsb = tk.Scrollbar(frame, command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        if not records:
            tree.insert("", "end", text="記録なし", values=("", "", "", ""))
        else:
            # 日付ごとにグループ化
            from collections import defaultdict
            by_date: dict[str, list] = defaultdict(list)
            for date, ev, proc, sec, t_s, t_e in sorted(records):
                by_date[date].append((ev, proc, sec, t_s, t_e))

            for date, items in sorted(by_date.items(), reverse=True):
                day_total = sum(s for _, _, s, _, _ in items)
                parent = tree.insert("", "end",
                                     text=f"{date}  ({_fmt_duration(day_total)})",
                                     values=("", "", "", ""), open=True)
                for ev, proc, sec, t_s, t_e in items:
                    tree.insert(parent, "end", text="",
                                values=(ev, proc, f"{t_s} - {t_e}", _fmt_duration(sec)))

        tk.Button(win, text="Close", command=win.destroy,
                  bg=C["accent_lt"], fg=C["text"], relief="flat", bd=0,
                  font=FONT, cursor="hand2", padx=16, pady=4,
                  activebackground=C["border"], activeforeground=C["text"],
                  ).pack(pady=(0, 12))

        win.update_idletasks()
        px = self.winfo_x() + (self.winfo_width()  - win.winfo_width())  // 2
        py = self.winfo_y() + (self.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{px}+{py}")

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

        today     = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        yesterday_str = yesterday.isoformat()

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
        SEP1 = "━" * 50
        SEP2 = "-" * 50

        # ── 前日作業実績セクション ──────────────────────────
        lines.append(SEP1)
        lines.append(f"前日作業実績  {yesterday_str}")
        lines.append(SEP1)

        # 前日ログを (event, process) キーで集計
        prev_groups: dict[tuple, list] = {}
        for task in self._tasks:
            for lg in task.get("work_logs", []):
                if not lg.get("end"):
                    continue
                try:
                    dt_s = datetime.datetime.fromisoformat(lg["start"])
                    dt_e = datetime.datetime.fromisoformat(lg["end"])
                    if dt_s.date().isoformat() != yesterday_str:
                        continue
                    key = (task.get("event", ""), task.get("process", ""))
                    prev_groups.setdefault(key, []).append((dt_s, dt_e))
                except Exception:
                    pass

        if prev_groups:
            day_total_sec = 0.0
            # タスク名列の幅を最長に合わせる
            label_width = max(
                len(f"  [{ev}] {proc}") for (ev, proc) in prev_groups
            )
            for (ev, proc), entries in sorted(prev_groups.items()):
                task_sec = sum((e - s).total_seconds() for s, e in entries)
                day_total_sec += task_sec
                h, m = divmod(int(task_sec) // 60, 60)
                label = f"  [{ev}] {proc}".ljust(label_width)
                lines.append(f"{label}  ({h}時間{m:02d}分)")
                for s, e in sorted(entries):
                    lines.append(f"    {s.strftime('%H:%M')} - {e.strftime('%H:%M')}")
            dh, dm = divmod(int(day_total_sec) // 60, 60)
            lines.append("")
            lines.append(f"  合計: {dh}時間{dm:02d}分")
        else:
            lines.append("  （記録なし）")

        lines.append("")

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
                bar = "#" * bar_filled + "-" * (20 - bar_filled)

                lines.append(f"  {process}")
                lines.append(f"    Progress : [{bar}] {pct}%")

                if deadline:
                    dl_note = days_left(deadline)
                    lines.append(f"    Deadline : {deadline}  {dl_note}")
                if updated:
                    lines.append(f"    Updated  : {updated}")
                if content:
                    # Wrap content for display
                    for line in content.splitlines():
                        if line.strip():
                            lines.append(f"    Content  : {line}")
                if wfs:
                    for wf in wfs:
                        lines.append(f"    Folder   : {wf}")
                if memos:
                    for memo in memos:
                        m_title   = memo.get("title", "Untitled")
                        m_content = memo.get("content", "").strip()
                        lines.append(f"    Memo [{m_title}]")
                        for ml in m_content.splitlines():
                            if ml.strip():
                                lines.append(f"      {ml}")
                lines.append("")

        Path(save_path).write_text("\n".join(lines), encoding="utf-8-sig")
        subprocess.Popen(["notepad", save_path])

    def _open_memo(self, task_idx: int):
        """Memo list and edit window for a task (supports multiple memos)."""
        task = self._tasks[task_idx]

        # Migrate legacy "memo" (str) → "memos" (list) format
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

        # ── Left pane (memo list) ──────────────────────────
        left = tk.Frame(win, bg=C["bg"], width=170)
        left.pack(side="left", fill="y", padx=(10, 0), pady=10)
        left.pack_propagate(False)

        tk.Label(left, text="Memos", bg=C["bg"], fg=C["text"],
                 font=FONT_BOLD, anchor="w").pack(fill="x", pady=(0, 4))

        lb = tk.Listbox(left, font=FONT_SMALL,
                        bg=C["card"], fg=C["text"],
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
                               bg=C["card"], fg=C["text"], relief="flat", bd=1,
                               insertbackground=C["accent"])
        title_entry.pack(fill="x", pady=(0, 6))

        tk.Label(right, text="Content", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="w").pack(fill="x")
        txt = tk.Text(right, font=FONT, bg=C["card"], fg=C["text"],
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

            arrow  = "v" if self._notify_past_open else ">"
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
                    lbl.configure(text=f"v  Past  ({len(past)})")
                    frame.pack(fill="x")
                else:
                    lbl.configure(text=f">  Past  ({len(past)})")
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
            card, text="x",
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
        labels = {"violet": "Violet", "dark": "Dark", "light": "Light", "gemini": "Gemini", "claude": "Claude", "scarlet": "Scarlet", "ocean": "Ocean", "rose": "Rose", "mint": "Mint"}
        for key, label in labels.items():
            prefix = "* " if self._theme == key else "  "
            menu.add_command(
                label=prefix + label,
                command=lambda k=key: self._apply_theme(k),
            )
        menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())

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

        # Windows のネイティブ ttk テーマは Treeview 見出し等の背景色を無視するため
        # clam テーマに切り替えてカスタムカラーを有効にする
        ttk.Style(self).theme_use("clam")

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
        inner = tk.Frame(self, bg=C["bg"])
        inner.pack(fill="x", padx=24, pady=(24, 8))

        def _field(label_text, var, show=None):
            tk.Label(inner, text=label_text, bg=C["bg"], fg=C["text_sub"],
                     font=FONT_SMALL, anchor="w").pack(fill="x")
            kw = {"show": show} if show else {}
            e = tk.Entry(inner, textvariable=var, font=FONT,
                         bg=C["card"], fg=C["text"], relief="flat", bd=1,
                         insertbackground=C["accent"], width=22, **kw)
            e.pack(fill="x", pady=(2, 10), ipady=4)
            return e

        self._user_var = tk.StringVar()
        user_e = _field("Username", self._user_var)
        user_e.focus_set()

        self._pw_var = tk.StringVar()
        pw_e = _field("Password", self._pw_var, show="*")
        pw_e.bind("<Return>", lambda e: self._login())

        self._err_var = tk.StringVar()
        tk.Label(self, textvariable=self._err_var,
                 bg=C["bg"], fg="#B84060",
                 font=FONT_SMALL).pack()

        btn = tk.Button(self, text="Login", command=self._login,
                        bg=C["accent"], fg="white", relief="flat", bd=0,
                        font=FONT_BOLD, cursor="hand2",
                        padx=28, pady=6,
                        activebackground=C["accent_dk"], activeforeground="white")
        btn.pack(pady=(8, 20))
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
            self._err_var.set("Invalid username or password")
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


def _preload_theme():
    """起動前に config.json からテーマだけ読み込んで C を更新する。"""
    try:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        theme = cfg.get("theme", "violet")
        if theme in THEMES:
            C.update(THEMES[theme])
    except Exception:
        pass


if __name__ == "__main__":
    _preload_theme()
    login = LoginWindow()
    login.mainloop()
    if login.authenticated:
        app = FolderLauncher()
        app.mainloop()
