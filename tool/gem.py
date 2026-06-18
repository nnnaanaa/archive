"""
Gem — Lavender-toned multi-hub
Unified management of folders, terminal connections, and tasks
"""

import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
from tkinter import font as tkfont
import os
import json
import subprocess
import zlib
import struct
import base64
import ctypes
import datetime
import tempfile
import threading
import socket
import time
import io
import re
import math
import calendar
import webbrowser
from collections import deque
from ctypes import wintypes
from pathlib import Path
from PIL import ImageGrab, Image
import pystray

try:
    # optional: Explorer drag&drop support (pip install tkinterdnd2)
    from tkinterdnd2 import TkinterDnD, DND_FILES
except ImportError:
    TkinterDnD, DND_FILES = None, None

# When frozen with cx_Freeze, use the parent of sys.executable as base
_BASE_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent

CONFIG_FILE   = _BASE_DIR / "config.json"
LOG_DIR       = _BASE_DIR / "logs"
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
    "violet": {   # default (same as base C)
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
    "gemini": {   # Gemini style: clean white + Google blue to violet
        "bg": "#F8F9FA", "card": "#FFFFFF", "card_h": "#E8F0FE",
        "accent": "#1B6EF3", "accent_dk": "#1251B5", "accent_lt": "#A8C7FA",
        "text": "#202124", "text_sub": "#5F6368", "border": "#DADCE0",
        "tab_act": "#FFFFFF", "tab_inact": "#F1F3F4",
        "btn_del": "#D93025", "btn_del_h": "#A50E0E",
    },
    "claude": {   # Claude Code style: near-black + coral orange
        "bg": "#1A1A1A", "card": "#242424", "card_h": "#2E2E2E",
        "accent": "#DA7756", "accent_dk": "#B85C3C", "accent_lt": "#E89A7A",
        "text": "#F0EDE8", "text_sub": "#9E9890", "border": "#383838",
        "tab_act": "#242424", "tab_inact": "#1E1E1E",
        "btn_del": "#8B3A3A", "btn_del_h": "#B04848",
    },
    "scarlet": {   # Imp: jet black + crimson red
        "bg": "#1A0A0E", "card": "#240F14", "card_h": "#331520",
        "accent": "#CC2244", "accent_dk": "#991833", "accent_lt": "#E06078",
        "text": "#F5E8EA", "text_sub": "#C09098", "border": "#4A1A25",
        "tab_act": "#240F14", "tab_inact": "#1E0B10",
        "btn_del": "#882030", "btn_del_h": "#BB3045",
    },
    "ocean": {   # deep sea blue
        "bg": "#0D1B2A", "card": "#1A2940", "card_h": "#243550",
        "accent": "#2196C4", "accent_dk": "#1570A0", "accent_lt": "#5BB8D4",
        "text": "#C8E8F5", "text_sub": "#7AAFC8", "border": "#2A4060",
        "tab_act": "#1A2940", "tab_inact": "#152030",
        "btn_del": "#8B3A3A", "btn_del_h": "#B04848",
    },
    "rose": {   # rose pink
        "bg": "#FDF0F3", "card": "#FFFFFF", "card_h": "#FFE4EC",
        "accent": "#E0608A", "accent_dk": "#C0407A", "accent_lt": "#F0A0BC",
        "text": "#4A1A2A", "text_sub": "#A06080", "border": "#F0C0D0",
        "tab_act": "#FFFFFF", "tab_inact": "#FAE0E8",
        "btn_del": "#E06080", "btn_del_h": "#C04060",
    },
    "mint": {   # mint green
        "bg": "#F0FAF5", "card": "#FFFFFF", "card_h": "#D8F5E8",
        "accent": "#3DAA78", "accent_dk": "#2A8A60", "accent_lt": "#80CCA8",
        "text": "#1A3A28", "text_sub": "#5A8A70", "border": "#B0E0C8",
        "tab_act": "#FFFFFF", "tab_inact": "#E0F5EC",
        "btn_del": "#C06060", "btn_del_h": "#A04040",
    },
    "peach": {   # peach: warm orange to pink pastel
        "bg": "#FFF5EE", "card": "#FFFAF7", "card_h": "#FFE8D8",
        "accent": "#E8845A", "accent_dk": "#C86030", "accent_lt": "#F5C0A0",
        "text": "#4A2010", "text_sub": "#A06848", "border": "#F5D0B8",
        "tab_act": "#FFFAF7", "tab_inact": "#FFE8D8",
        "btn_del": "#D05050", "btn_del_h": "#A83030",
    },
    "sky": {   # sky blue: refreshing light blue pastel
        "bg": "#EEF7FF", "card": "#F5FBFF", "card_h": "#D4EDFF",
        "accent": "#4DA8DA", "accent_dk": "#2A88BE", "accent_lt": "#9DD4F0",
        "text": "#0C2C44", "text_sub": "#4A80A8", "border": "#B0D8F0",
        "tab_act": "#F5FBFF", "tab_inact": "#DCF0FF",
        "btn_del": "#C05870", "btn_del_h": "#A03858",
    },
    "lemon": {   # lemon: bright and cheerful yellow pastel
        "bg": "#FDFCE8", "card": "#FFFFF0", "card_h": "#F5F0B8",
        "accent": "#C8A800", "accent_dk": "#A08800", "accent_lt": "#E8D870",
        "text": "#383000", "text_sub": "#787040", "border": "#E8DC90",
        "tab_act": "#FFFFF0", "tab_inact": "#F5EEC0",
        "btn_del": "#C06040", "btn_del_h": "#A04020",
    },
    "lavender": {   # lavender: soft purple pastel (lighter than violet)
        "bg": "#F3F0FF", "card": "#FAF8FF", "card_h": "#E4DEFF",
        "accent": "#9B88D8", "accent_dk": "#7A66C0", "accent_lt": "#C8BCEE",
        "text": "#2E2460", "text_sub": "#7868B0", "border": "#D0C8F0",
        "tab_act": "#FAF8FF", "tab_inact": "#E8E0FF",
        "btn_del": "#C888B0", "btn_del_h": "#A86898",
    },
    "sakura": {   # sakura: cherry blossom soft pink
        "bg": "#FFF0F5", "card": "#FFF8FA", "card_h": "#FFD8E8",
        "accent": "#E87898", "accent_dk": "#C85878", "accent_lt": "#F5B0C8",
        "text": "#4A1828", "text_sub": "#A06888", "border": "#F0C0D4",
        "tab_act": "#FFF8FA", "tab_inact": "#FFE0EC",
        "btn_del": "#D05878", "btn_del_h": "#B03858",
    },
    "plush": {   # soft periwinkle lavender
        "bg": "#EAE5F8", "card": "#F5F2FF", "card_h": "#DAD2F8",
        "accent": "#9E92D6", "accent_dk": "#7C6FBF", "accent_lt": "#C6BEE8",
        "text": "#2A2055", "text_sub": "#6E65A5", "border": "#C8C0E8",
        "tab_act": "#F5F2FF", "tab_inact": "#E0DAF8",
        "btn_del": "#C88AB8", "btn_del_h": "#A86898",
    },
    "cyber": {   # near-black blue + neon cyan
        "bg": "#0A0E16", "card": "#0F1620", "card_h": "#15202E",
        "accent": "#00C2E0", "accent_dk": "#0094AC", "accent_lt": "#46DCF5",
        "text": "#D8F4FF", "text_sub": "#6FA8C0", "border": "#1C3A4A",
        "tab_act": "#0F1620", "tab_inact": "#0C1118",
        "btn_del": "#B03060", "btn_del_h": "#E04880",
    },
    "synthwave": {   # deep violet night + neon magenta
        "bg": "#16102A", "card": "#1E1638", "card_h": "#2A1E4C",
        "accent": "#E83E9C", "accent_dk": "#B82578", "accent_lt": "#F570BE",
        "text": "#F2E6FF", "text_sub": "#A98CC8", "border": "#3C2A60",
        "tab_act": "#1E1638", "tab_inact": "#181230",
        "btn_del": "#8B3A5A", "btn_del_h": "#C04878",
    },
    "matrix": {   # black + terminal green
        "bg": "#060A06", "card": "#0C140C", "card_h": "#142014",
        "accent": "#22CC55", "accent_dk": "#189940", "accent_lt": "#55E882",
        "text": "#CCF5D6", "text_sub": "#5FA873", "border": "#1A3A22",
        "tab_act": "#0C140C", "tab_inact": "#080F08",
        "btn_del": "#A03838", "btn_del_h": "#CC4848",
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
    "plush": {
        "BDR": ( 50,  40, 100, 255), "HL": (232, 228, 245, 255),
        "LT":  (208, 202, 234, 255), "F":  (181, 173, 220, 255),
        "MD":  (144, 136, 190, 255), "DK": (104,  96, 160, 255),
        "SP":  (210, 205, 238, 210),
    },
    "cyber": {
        "BDR": (  5,  35,  48, 255), "HL": (140, 235, 250, 255),
        "LT":  ( 70, 220, 245, 255), "F":  (  0, 194, 224, 255),
        "MD":  (  0, 148, 172, 255), "DK": (  0,  90, 110, 255),
        "SP":  (160, 240, 252, 200),
    },
    "synthwave": {
        "BDR": ( 60,  15,  45, 255), "HL": (250, 160, 215, 255),
        "LT":  (245, 112, 190, 255), "F":  (232,  62, 156, 255),
        "MD":  (184,  37, 120, 255), "DK": (110,  20,  75, 255),
        "SP":  (250, 170, 220, 200),
    },
    "matrix": {
        "BDR": (  8,  40,  16, 255), "HL": (150, 245, 180, 255),
        "LT":  ( 85, 232, 130, 255), "F":  ( 34, 204,  85, 255),
        "MD":  ( 24, 153,  64, 255), "DK": ( 12,  90,  40, 255),
        "SP":  (160, 245, 190, 200),
    },
}

# ── Font hierarchy ───────────────────────────────────────
# A single consistent scale derived from the configurable base size.
# Route all widget fonts through these constants (never hardcode tuples)
# so the whole UI stays visually consistent and scales together.
FONT_BASE       = 11  # base font size (configurable)
FONT            = ("Segoe UI", 11)            # body text
FONT_BOLD       = ("Segoe UI", 11, "bold")    # emphasis / titles
FONT_SMALL      = ("Segoe UI", 9)             # secondary text, captions
FONT_SMALL_BOLD = ("Segoe UI", 9, "bold")     # small headers / badges
FONT_TINY       = ("Segoe UI", 8)             # hints, dense sub-labels
FONT_MONO       = ("Consolas", 10)            # clock, logs, command text


FONT_FAMILY = "Segoe UI"   # configurable UI font family


def _update_fonts(size: int, family: str | None = None):
    """Update global fonts to match the base size and family
    (keeps the scale consistent)."""
    global FONT_BASE, FONT_FAMILY, FONT, FONT_BOLD, FONT_SMALL, \
        FONT_SMALL_BOLD, FONT_TINY, FONT_MONO
    if family:
        FONT_FAMILY = family
    fam = FONT_FAMILY
    FONT_BASE       = size
    FONT            = (fam, size)
    FONT_BOLD       = (fam, size, "bold")
    FONT_SMALL      = (fam, max(7, size - 2))
    FONT_SMALL_BOLD = (fam, max(7, size - 2), "bold")
    FONT_TINY       = (fam, max(7, size - 3))
    FONT_MONO       = ("Consolas", max(8, size - 1))


# ── Spacing scale ────────────────────────────────────────
# Shared insets/gaps so list rows line up consistently across every tab.
PAD_ROW_X = 2   # left/right inset of a list row (card) within the list
PAD_ROW_Y = 2   # vertical gap between consecutive list rows


def _fmt_duration(seconds: float) -> str:
    """Convert seconds to a string in '2h 30m' format."""
    seconds = int(seconds)
    h, m = divmod(seconds // 60, 60)
    if h:
        return f"{h}h {m:02d}m"
    return f"{m}m"


def _fuzzy_score(query: str, text: str) -> int | None:
    """Rank text against query for the command palette.

    Lower is better; None = no match. Each query word must match as a
    prefix (best), substring, or in-order subsequence (worst).
    """
    q = query.lower().strip()
    if not q:
        return 1000
    t = text.lower()
    total = 0
    for word in q.split():
        pos = t.find(word)
        if pos == 0:
            continue
        if pos > 0:
            total += 10 + min(pos, 80)
            continue
        p = 0
        for ch in word:
            p = t.find(ch, p)
            if p < 0:
                return None
            p += 1
        total += 200
    return total


def _log_task_progress(task: dict, new_pct: int, created: bool = False):
    """Record a day-level progress change on the task.

    Call BEFORE updating task["progress"] so the previous value is captured.
    One entry per day: repeated changes on the same day keep the first
    'from' and the final 'to' (the day's net change). from=None marks
    task creation.
    """
    prev = None if created else task.get("progress", 0)
    if not created and prev == new_pct:
        return
    today = datetime.date.today().isoformat()
    log = task.setdefault("progress_log", [])
    if log and log[-1].get("date") == today:
        log[-1]["to"] = new_pct
    else:
        log.append({"date": today, "from": prev, "to": new_pct})


def _draw_rounded_rect(canvas, x1, y1, x2, y2, r, **kw):
    """Draw a filled rounded rectangle on a Canvas."""
    kw.setdefault("outline", "")
    r = max(1, min(r, (x2 - x1) // 2, (y2 - y1) // 2))
    for ax, ay, start in (
        (x1,      y1,      90),
        (x2-2*r,  y1,       0),
        (x1,      y2-2*r, 180),
        (x2-2*r,  y2-2*r, 270),
    ):
        canvas.create_arc(ax, ay, ax+2*r, ay+2*r,
                          start=start, extent=90, style="pieslice", **kw)
    canvas.create_rectangle(x1+r, y1, x2-r, y2, **kw)
    canvas.create_rectangle(x1, y1+r, x2, y2-r, **kw)


def _autohide_scrollbar(sb, lo, hi, pack_kw):
    """yscrollcommand handler that hides a packed scrollbar when not needed.

    Works for both tk.Scrollbar and ttk.Scrollbar. Pass the same pack()
    keyword args used to place the scrollbar so it can be re-shown on demand.
    """
    lo_f, hi_f = float(lo), float(hi)
    if lo_f <= 0.0 and hi_f >= 1.0:
        sb.pack_forget()
    elif not sb.winfo_ismapped():
        sb.pack(**pack_kw)
    sb.set(lo, hi)


def _blend_hex(c1: str, c2: str, t: float) -> str:
    """Linearly blend two #RRGGBB colors (t=0 -> c1, t=1 -> c2)."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


# Port used to probe connection latency via a plain TCP connect.
_PING_PORTS = {"SSH": 22, "Telnet": 23, "RDP": 3389, "SMB": 445}


def _style_flat_scrollbars(root) -> None:
    """Configure thin, flat, arrow-less ttk scrollbar styles in theme colors.

    Defines Gem.Vertical.TScrollbar / Gem.Horizontal.TScrollbar on the
    root's shared style database; call again after a theme change.
    """
    style = ttk.Style(root)
    for orient, sticky in (("Vertical", "ns"), ("Horizontal", "ew")):
        name = f"Gem.{orient}.TScrollbar"
        style.layout(name, [
            (f"{orient}.Scrollbar.trough",
             {"children": [(f"{orient}.Scrollbar.thumb",
                            {"expand": "1", "sticky": "nswe"})],
              "sticky": sticky}),
        ])
        style.configure(name,
                        troughcolor=C["bg"], background=C["accent"],
                        bordercolor=C["bg"],
                        lightcolor=C["accent"], darkcolor=C["accent"],
                        gripcount=0, relief="flat", width=8)
        style.map(name,
                  background=[("pressed", C["accent_dk"]),
                              ("active", C["accent_lt"])])


# ── System stats (CPU/RAM via Win32, no extra deps) ──────

_cpu_prev: tuple[int, int] | None = None   # (idle, kernel+user) cumulative times


def _sample_cpu() -> float | None:
    """Return system CPU usage 0-100 since the previous call (None on the first)."""
    global _cpu_prev
    try:
        idle, kern, user = wintypes.FILETIME(), wintypes.FILETIME(), wintypes.FILETIME()
        if not ctypes.windll.kernel32.GetSystemTimes(
                ctypes.byref(idle), ctypes.byref(kern), ctypes.byref(user)):
            return None
        def _q(ft): return (ft.dwHighDateTime << 32) | ft.dwLowDateTime
        i, t = _q(idle), _q(kern) + _q(user)   # kernel time includes idle
        prev, _cpu_prev = _cpu_prev, (i, t)
        if prev is None:
            return None
        di, dt = i - prev[0], t - prev[1]
        if dt <= 0:
            return None
        return max(0.0, min(100.0, 100.0 * (1.0 - di / dt)))
    except Exception:
        return None


def _sample_ram() -> float | None:
    """Return physical memory load 0-100 (GlobalMemoryStatusEx)."""
    try:
        class _MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [("dwLength", wintypes.DWORD),
                        ("dwMemoryLoad", wintypes.DWORD),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        ms = _MEMORYSTATUSEX()
        ms.dwLength = ctypes.sizeof(ms)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
            return None
        return float(ms.dwMemoryLoad)
    except Exception:
        return None


# ── Search tab helpers ────────────────────────────────────

# Directories the Search tab never descends into (noise / huge).
# Dot-prefixed dirs (.git, .venv, ...) are skipped separately.
_GREP_SKIP_DIRS = {"__pycache__", "node_modules", "venv",
                   "$recycle.bin", "system volume information"}

_vscode_cmd: str | None = None   # resolved on first use; "" = not installed


def _open_in_editor(path: str, lineno: int = 1) -> None:
    """Open a file at a line in VS Code when available, else the default app."""
    global _vscode_cmd
    if _vscode_cmd is None:
        import shutil
        _vscode_cmd = shutil.which("code") or ""
    if _vscode_cmd:
        try:
            subprocess.Popen([_vscode_cmd, "-g", f"{path}:{lineno}"],
                             creationflags=subprocess.CREATE_NO_WINDOW)
            return
        except OSError:
            pass
    try:
        os.startfile(path)
    except OSError:
        pass


# ── Icon generation ───────────────────────────────────────

def _icon_png_jelly(palette: dict | None = None) -> str:
    """Generate the rabbit-ear jellyfish icon PNG and return it as Base64."""
    p = palette or ICON_PALETTES["violet"]
    W, H = 32, 32
    T   = (  0,   0,   0,   0)
    BDR = p["BDR"]
    HL  = p["HL"]
    LT  = p["LT"]
    F   = p["F"]
    MD  = p["MD"]

    # ── Bell (head): circle center=(15,16) r=10 (shifted 4px down) ──
    BELL = {
         7: (11, 19),
         8: ( 9, 21),
         9: ( 8, 22),
        10: ( 7, 23),
        11: ( 6, 24),
        12: ( 6, 24),
        13: ( 5, 25),
        14: ( 5, 25),
        15: ( 5, 25),
        16: ( 5, 25),
        17: ( 5, 25),
        18: ( 5, 25),
        19: ( 5, 25),
        20: ( 6, 24),
        21: ( 6, 24),
        22: ( 7, 23),
        23: ( 8, 22),
        24: ( 9, 21),
        25: (11, 19),
    }

    def _in_d(d, x, y):
        if y not in d: return False
        lo, hi = d[y]; return lo <= x <= hi

    def in_bell(x, y):  return _in_d(BELL, x, y)
    def is_bell_edge(x, y):
        if not in_bell(x, y): return False
        return any(not in_bell(x+dx, y+dy) for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)))

    # ── Ears (wide rounded, shifted 2px down) ──────────────────────
    L_EAR    = {4: ( 8,12), 5: ( 7,13), 6: ( 7,13), 7: ( 7,13), 8: ( 8,12)}
    R_EAR    = {4: (18,22), 5: (17,23), 6: (17,23), 7: (17,23), 8: (18,22)}
    L_EAR_IN = {4: ( 9,11), 5: ( 8,12), 6: ( 8,12), 7: ( 8,12)}
    R_EAR_IN = {4: (19,21), 5: (18,22), 6: (18,22), 7: (18,22)}

    def in_ear(x, y):    return _in_d(L_EAR, x, y) or _in_d(R_EAR, x, y)
    def ear_inner(x, y): return _in_d(L_EAR_IN, x, y) or _in_d(R_EAR_IN, x, y)
    def is_ear_edge(x, y):
        if not in_ear(x, y): return False
        return any(not in_ear(x+dx, y+dy) and not in_bell(x+dx, y+dy)
                   for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)))

    # ── Tentacles (5, short, slightly spreading) ───────────────────
    TENTACLE: set[tuple[int, int]] = set()
    TENTACLE_EDGE: set[tuple[int, int]] = set()
    for base_x, drift in ((7, -1), (12, 0), (17, 0), (22, 1)):
        for dy in range(5):
            y = 26 + dy
            if y >= H: break
            x = base_x + drift * (dy // 3)
            TENTACLE.add((x, y))
            TENTACLE.add((x + 1, y))
    for tx, ty in TENTACLE:
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = tx+dx, ty+dy
            if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in TENTACLE:
                TENTACLE_EDGE.add((nx, ny))

    def px(x, y):
        if (x, y) in TENTACLE:
            return F
        if (x, y) in TENTACLE_EDGE and not in_bell(x, y) and not in_ear(x, y):
            return BDR
        # Ears (flat: edge=BDR, inner=LT, fill=F)
        if in_ear(x, y):
            if is_ear_edge(x, y): return BDR
            if ear_inner(x, y):   return LT
            return F
        if not in_bell(x, y):
            return T
        # Bell (subtle 3D: highlight top-center/left, light shadow bottom)
        if is_bell_edge(x, y): return BDR
        dx = x - 15
        if y <= 16 and dx <= 1:
            return LT
        if y >= 22:
            return MD
        return F

    # Draw at 32x32 then scale up 2x to 64x64
    OUT = 2
    W_OUT, H_OUT = W * OUT, H * OUT
    pixels = [[px(x, y) for x in range(W)] for y in range(H)]

    raw = b''
    for oy in range(H_OUT):
        raw += b'\x00'
        for ox in range(W_OUT):
            raw += bytes(pixels[oy // OUT][ox // OUT])

    def chunk(tag, data):
        c = tag + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)

    png = (
        b'\x89PNG\r\n\x1a\n'
        + chunk(b'IHDR', struct.pack('>IIBBBBB', W_OUT, H_OUT, 8, 6, 0, 0, 0))
        + chunk(b'IDAT', zlib.compress(raw, 9))
        + chunk(b'IEND', b'')
    )
    return base64.b64encode(png).decode()


# ── Modern icon shapes (gradient fill + soft gloss, palette-tinted) ──
# Each "mask" drawer paints the silhouette in white on an L-mode image; the
# renderer fills it with a vertical accent gradient and adds a top gloss for
# a flat-but-glossy, app-tile look. Supersampled then downscaled for crisp
# edges.

def _mask_rounded(md, S):
    m = int(S * 0.09)
    md.rounded_rectangle([m, m, S - m, S - m], radius=int(S * 0.27), fill=255)


def _mask_ring(md, S):
    m = int(S * 0.09)
    md.ellipse([m, m, S - m, S - m], fill=255)
    im = int(S * 0.31)
    md.ellipse([im, im, S - im, S - im], fill=0)


def _mask_hexagon(md, S):
    import math
    c, R = S / 2, S * 0.44
    pts = [(c + R * math.cos(-math.pi / 2 + i * math.pi / 3),
            c + R * math.sin(-math.pi / 2 + i * math.pi / 3)) for i in range(6)]
    md.polygon(pts, fill=255)


def _mask_spark(md, S):
    import math
    c, R, r = S / 2, S * 0.48, S * 0.13
    pts = []
    for i in range(8):
        a = -math.pi / 2 + i * math.pi / 4
        rad = R if i % 2 == 0 else r
        pts.append((c + rad * math.cos(a), c + rad * math.sin(a)))
    md.polygon(pts, fill=255)


def _mask_drop(md, S):
    c = S / 2
    md.ellipse([S * 0.20, S * 0.40, S * 0.80, S * 0.93], fill=255)
    md.polygon([(c, S * 0.07), (S * 0.77, S * 0.56), (S * 0.23, S * 0.56)], fill=255)


def _mask_heart(md, S):
    # two round lobes + V bottom
    md.ellipse([S * 0.08, S * 0.14, S * 0.56, S * 0.62], fill=255)
    md.ellipse([S * 0.44, S * 0.14, S * 0.92, S * 0.62], fill=255)
    md.polygon([(S * 0.115, S * 0.46), (S * 0.885, S * 0.46),
                (S * 0.50, S * 0.92)], fill=255)


def _mask_star(md, S):
    import math
    c, R, r = S / 2, S * 0.48, S * 0.22   # plump inner radius = cute
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rad = R if i % 2 == 0 else r
        pts.append((c + rad * math.cos(a), c + rad * math.sin(a)))
    md.polygon(pts, fill=255)


def _mask_moon(md, S):
    m = int(S * 0.08)
    md.ellipse([m, m, S - m, S - m], fill=255)
    # bite out the upper-right to leave a crescent
    md.ellipse([S * 0.30, -S * 0.18, S * 1.12, S * 0.64], fill=0)


def _mask_cloud(md, S):
    md.ellipse([S * 0.06, S * 0.38, S * 0.50, S * 0.80], fill=255)
    md.ellipse([S * 0.26, S * 0.20, S * 0.74, S * 0.70], fill=255)
    md.ellipse([S * 0.50, S * 0.38, S * 0.94, S * 0.80], fill=255)
    md.rounded_rectangle([S * 0.14, S * 0.52, S * 0.86, S * 0.80],
                         radius=int(S * 0.14), fill=255)


_ICON_MASKS = {
    "rounded": _mask_rounded,
    "ring":    _mask_ring,
    "hexagon": _mask_hexagon,
    "spark":   _mask_spark,
    "drop":    _mask_drop,
    "heart":   _mask_heart,
    "star":    _mask_star,
    "moon":    _mask_moon,
    "cloud":   _mask_cloud,
}

# Selectable icon designs (key, label) shown in the settings menu.
ICON_SHAPES = [
    ("rounded", "Rounded"),
    ("ring",    "Ring"),
    ("hexagon", "Hexagon"),
    ("spark",   "Spark"),
    ("drop",    "Drop"),
    ("jelly",   "Jelly"),
    ("heart",   "Heart"),
    ("star",    "Star"),
    ("moon",    "Moon"),
    ("cloud",   "Cloud"),
]


def _icon_png_modern(palette: dict | None, mask_fn) -> str:
    """Render a gradient-filled, glossy icon shape as a Base64 PNG (64x64)."""
    from PIL import Image, ImageDraw, ImageChops
    p = palette or ICON_PALETTES["violet"]
    S = 256
    top, bot = tuple(p["DK"])[:3], tuple(p["F"])[:3]

    # vertical accent gradient
    grad = Image.new("RGB", (S, S))
    gd = ImageDraw.Draw(grad)
    for y in range(S):
        t = y / (S - 1)
        gd.line([(0, y), (S, y)], fill=(
            int(top[0] + (bot[0] - top[0]) * t),
            int(top[1] + (bot[1] - top[1]) * t),
            int(top[2] + (bot[2] - top[2]) * t)))

    # silhouette mask
    mask = Image.new("L", (S, S), 0)
    mask_fn(ImageDraw.Draw(mask), S)

    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.paste(grad, (0, 0), mask)

    # soft top gloss, clipped to the shape
    gloss = Image.new("L", (S, S), 0)
    ImageDraw.Draw(gloss).ellipse([S * 0.10, -S * 0.30, S * 0.90, S * 0.46], fill=70)
    out.paste((255, 255, 255, 255), (0, 0), ImageChops.darker(gloss, mask))

    out = out.resize((64, 64), Image.LANCZOS)
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _make_icon_png(palette: dict | None = None, shape: str = "jelly") -> str:
    """Return the Base64 PNG for the chosen icon design (default: jelly)."""
    mask_fn = _ICON_MASKS.get(shape)
    if mask_fn is None:
        return _icon_png_jelly(palette)
    try:
        return _icon_png_modern(palette, mask_fn)
    except Exception:
        return _icon_png_jelly(palette)


def _add_tray_badge(img: Image, color: str) -> Image:
    """Return a copy of img with a small status dot in the bottom-right corner."""
    from PIL import ImageDraw
    img = img.convert("RGBA").copy()
    w, h = img.size
    r = int(w * 0.20)
    cx, cy = w - r, h - r
    d = ImageDraw.Draw(img)
    d.ellipse([cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2], fill="#1a1a2e")  # halo for contrast
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    return img


_gem_ico_path: str | None = None  # retained for automatic application to all Toplevels


def _setup_taskbar_icon(root: tk.Tk, palette: dict | None = None,
                        shape: str = "jelly") -> None:
    """Set AppUserModelID and apply the taskbar icon from an ICO file."""
    global _gem_ico_path
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Gem.Launcher.1")
    except Exception:
        pass

    ico_path = _BASE_DIR / "gem.ico"
    # Always regenerate when a palette is specified (theme change); on first run only if the script was updated
    force = palette is not None
    if not force:
        if getattr(sys, "frozen", False):
            # Skip mtime check when running as a frozen executable
            force = not ico_path.exists()
        else:
            script_mtime = Path(__file__).stat().st_mtime
            ico_mtime    = ico_path.stat().st_mtime if ico_path.exists() else 0
            force = not ico_path.exists() or script_mtime > ico_mtime
    if force:
        try:
            from PIL import Image
            png_data = base64.b64decode(_make_icon_png(palette, shape))
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
        # Re-apply after window is shown to handle timing issues
        root.after(200, _apply)


def _apply_titlebar_theme(win) -> None:
    """Color the native title bar / window border to match the theme.

    Uses DWM attributes available on Windows 11 (caption color 35, caption
    text color 36, border color 34); silently no-ops on older Windows and
    on frameless (overrideredirect) windows.
    """
    try:
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
        if not hwnd:
            return

        def cref(hex_color: str) -> int:   # "#RRGGBB" -> COLORREF (0x00BBGGRR)
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            return (b << 16) | (g << 8) | r

        dwm = ctypes.windll.dwmapi
        dwm.DwmSetWindowAttribute.argtypes = [
            wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
        for attr, val in ((35, cref(C["accent"])),       # DWMWA_CAPTION_COLOR
                          (36, cref("#FFFFFF")),         # DWMWA_TEXT_COLOR
                          (34, cref(C["accent_dk"]))):   # DWMWA_BORDER_COLOR
            v = wintypes.DWORD(val)
            dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(v),
                                      ctypes.sizeof(v))
    except Exception:
        pass


# Monkey-patch to automatically apply the icon and themed title bar
# when a Toplevel is created
_orig_toplevel_init = tk.Toplevel.__init__

def _patched_toplevel_init(self, master=None, **kwargs):
    _orig_toplevel_init(self, master, **kwargs)
    if _gem_ico_path:
        try:
            self.wm_iconbitmap(_gem_ico_path)
        except Exception:
            pass
    try:
        # deferred: the WM frame window exists only after mapping
        self.after(20, lambda: _apply_titlebar_theme(self))
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
        wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC,
        ctypes.POINTER(wintypes.RECT), wintypes.LPARAM,
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

    # Auto-generate log file
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"{timestamp}_{host}.log"
    log_arg = [f"/L={log_path}"]

    PROMPT = "wait '$' '#' '%' '>'"

    def _ttl_sendln(s: str) -> list[str]:
        """Generate TTL sendln code. Handles strings containing single quotes correctly."""
        if "'" not in s:
            return [f"sendln '{s}'"]
        # Build the string with single quotes using strconcat + char2str(39)
        parts = s.split("'")
        lines = [f"_s = '{parts[0]}'"]
        for part in parts[1:]:
            lines += ["char2str _c 39", "strconcat _s _c"]
            if part:
                lines.append(f"strconcat _s '{part}'")
        lines.append("sendln _s")
        return lines

    def _write_ttl(lines: list[str]) -> str:
        """Write a TTL script to a temporary file and return its path."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl",
                                         delete=False, encoding="utf-8") as f:
            f.write("\r\n".join(lines) + "\r\n")
            return f.name

    if proto == "SSH":
        # SSH: pass user/pass via CLI arguments; use TTL to wait for prompt if commands are specified
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
    else:  # Telnet: auto-fill login/password prompts via TTL script
        ttl_lines = [
            "timeout = 30",
            # Handles various device prompts: login: / Login: / Username: / User:
            "wait 'ogin:' 'sername:' 'ser:'",
            "mpause 300",   # Wait a moment after receiving the prompt for the device to be ready for input
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
    unc  = conn["host"]   # \\server\share format
    user = conn.get("user", "")
    pw   = _decode_pw(conn.get("password", ""))

    if user and pw:
        # Temporarily register credentials before accessing
        subprocess.run(
            ["net", "use", unc, pw, f"/user:{user}"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            capture_output=True,
        )
    os.startfile(unc)


class ConnectionDialog(tk.Toplevel):
    """Dialog for adding/editing connections.
    Multiple protocols can be selected when adding. result is list[dict].
    """

    # Default port per protocol
    _PROTO_PORT = {"SSH": 22, "Telnet": 23, "RDP": 3389, "SMB": 0}

    def __init__(self, parent, initial: dict | None = None,
                 groups: list[str] | None = None):
        super().__init__(parent)
        self._edit_mode = initial is not None
        self.title("Edit Connection" if self._edit_mode else "Add Connection")
        self.configure(bg=C["bg"])
        self.resizable(True, False)
        self.grab_set()
        self.result: list[dict] = []
        self._groups = groups or []

        d = initial or {}
        self._name_var  = tk.StringVar(value=d.get("name", ""))
        self._host      = tk.StringVar(value=d.get("host", ""))
        self._user      = tk.StringVar(value=d.get("user", ""))
        self._pw        = tk.StringVar(value=_decode_pw(d.get("password", "")))
        self._group_var = tk.StringVar(value=d.get("group", ""))

        # Per-protocol settings (add: multi-select / edit: single)
        init_proto = d.get("protocol", "SSH")
        self._proto_enabled: dict[str, tk.BooleanVar] = {}
        self._proto_port:    dict[str, tk.StringVar]  = {}
        self._proto_charset: dict[str, tk.StringVar]  = {}
        for p, dp in self._PROTO_PORT.items():
            enabled = (p == init_proto) if self._edit_mode else (p == "SSH")
            self._proto_enabled[p] = tk.BooleanVar(value=enabled)
            port_val = str(d.get("port", dp)) if p == init_proto else str(dp)
            self._proto_port[p]    = tk.StringVar(value=port_val)
            cs_val = d.get("charset", "UTF-8") if p == init_proto else "UTF-8"
            self._proto_charset[p] = tk.StringVar(value=cs_val)

        # SMB-specific: UNC path (\\server\share format)
        smb_unc_init = d.get("host", "") if init_proto == "SMB" else ""
        self._smb_unc = tk.StringVar(value=smb_unc_init)

        self._init_cmds = "\n".join(d.get("commands", []))
        self._show_pw   = False

        self._build()
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")
        self.wait_window()

    # ── Helpers ─────────────────────────────────────────────
    def _lbl(self, parent, text: str, width: int = 10) -> tk.Label:
        return tk.Label(parent, text=text, bg=C["bg"], fg=C["text_sub"],
                        font=FONT_SMALL, anchor="e", width=width)

    def _entry(self, parent, var: tk.StringVar, show: str = "",
               width: int = 22) -> tk.Entry:
        return tk.Entry(parent, textvariable=var, font=FONT,
                        bg=C["card"], fg=C["text"], relief="flat", bd=1,
                        insertbackground=C["accent"], width=width, show=show)

    # ── UI build ────────────────────────────────────────────
    def _build(self):
        form = tk.Frame(self, bg=C["bg"])
        form.pack(fill="x", padx=12, pady=(12, 4))
        form.columnconfigure(1, weight=1)

        def _row(label, var, r, show=""):
            self._lbl(form, label).grid(row=r, column=0, padx=(0, 6), pady=3, sticky="e")
            e = self._entry(form, var, show=show)
            e.grid(row=r, column=1, columnspan=2, pady=3, sticky="ew")
            return e

        _row("Name",     self._name_var, 0)
        _row("Host",     self._host,     1)
        _row("Username", self._user,     2)
        pw_e = _row("Password", self._pw, 3, show="*")
        self._pw_entry = pw_e
        self._pw_toggle = tk.Button(
            form, text="show", font=FONT_TINY,
            bg=C["bg"], fg=C["text_sub"], relief="flat", bd=0,
            cursor="hand2", command=self._toggle_pw,
        )
        self._pw_toggle.grid(row=3, column=3, padx=(2, 0), pady=3)

        self._lbl(form, "Group").grid(row=4, column=0, padx=(0, 6), pady=3, sticky="e")
        ttk.Combobox(form, textvariable=self._group_var,
                     values=self._groups, font=FONT, width=20
                     ).grid(row=4, column=1, columnspan=2, pady=3, sticky="ew")

        # ── Protocol section ─────────────────────────────────
        sep = tk.Frame(self, bg=C["border"], height=1)
        sep.pack(fill="x", padx=12, pady=(6, 0))
        tk.Label(self, text="Protocols", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="w").pack(fill="x", padx=14, pady=(4, 2))

        proto_frame = tk.Frame(self, bg=C["bg"])
        proto_frame.pack(fill="x", padx=12, pady=(0, 4))
        self._proto_rows: dict[str, tk.Frame] = {}
        for p in ("SSH", "Telnet", "RDP", "SMB"):
            self._build_proto_row(proto_frame, p)

        # ── Commands (shared for SSH/Telnet/RDP) ─────────────
        self._cmd_section = tk.Frame(self, bg=C["bg"])
        self._cmd_section.pack(fill="x", padx=12, pady=(0, 4))
        tk.Label(self._cmd_section, text="Commands", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="w").pack(fill="x")
        self._cmd_text = tk.Text(
            self._cmd_section, font=FONT_MONO,
            bg=C["card"], fg=C["text"], relief="flat", bd=1,
            insertbackground=C["accent"], width=34, height=4, wrap="none",
        )
        self._cmd_text.insert("1.0", self._init_cmds)
        self._cmd_text.pack(fill="x")
        hint_row = tk.Frame(self._cmd_section, bg=C["bg"])
        hint_row.pack(fill="x", pady=(2, 0))
        tk.Label(hint_row, text="One command per line  /  Executed after login",
                 bg=C["bg"], fg=C["text_sub"],
                 font=FONT_TINY).pack(side="left")
        tk.Button(hint_row, text="Import...", command=self._import_cmd_file,
                  bg=C["card"], fg=C["text_sub"], relief="flat", bd=0,
                  font=FONT_TINY, cursor="hand2", padx=6, pady=1,
                  activebackground=C["card_h"], activeforeground=C["text"],
                  ).pack(side="right")

        self._update_cmd_section()

        # ── Button row ───────────────────────────────────────
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", padx=0, pady=(4, 0))
        btn_frame = tk.Frame(self, bg=C["bg"])
        btn_frame.pack(fill="x", padx=16, pady=(6, 14))
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

    def _build_proto_row(self, parent: tk.Frame, proto: str):
        """Build one protocol row (checkbox + port + charset)."""
        row = tk.Frame(parent, bg=C["bg"])
        row.pack(fill="x", pady=1)
        self._proto_rows[proto] = row

        cb = tk.Checkbutton(
            row, text=proto, variable=self._proto_enabled[proto],
            bg=C["bg"], fg=C["text"], selectcolor=C["card"],
            activebackground=C["bg"], activeforeground=C["text"],
            font=FONT_SMALL, width=6, anchor="w", cursor="hand2",
            command=self._update_cmd_section,
        )
        cb.pack(side="left")

        # Lock checkbox in edit mode
        if self._edit_mode:
            cb.configure(state="disabled")

        # Port (not shown for SMB)
        if proto != "SMB":
            tk.Label(row, text="Port:", bg=C["bg"], fg=C["text_sub"],
                     font=FONT_SMALL).pack(side="left", padx=(8, 2))
            tk.Entry(row, textvariable=self._proto_port[proto],
                     font=FONT, bg=C["card"], fg=C["text"],
                     relief="flat", bd=1, insertbackground=C["accent"],
                     width=6).pack(side="left")

        # Charset (SSH / Telnet only)
        if proto in ("SSH", "Telnet"):
            tk.Label(row, text="Charset:", bg=C["bg"], fg=C["text_sub"],
                     font=FONT_SMALL).pack(side="left", padx=(10, 2))
            ttk.Combobox(row, textvariable=self._proto_charset[proto],
                         values=["UTF-8", "SJIS", "EUC", "JIS"],
                         state="readonly", font=FONT, width=8,
                         ).pack(side="left")

        # SMB-specific: UNC Path field (visible only when SMB is checked)
        if proto == "SMB":
            unc_row = tk.Frame(parent, bg=C["bg"])
            tk.Label(unc_row, text="UNC Path:", bg=C["bg"], fg=C["text_sub"],
                     font=FONT_SMALL).pack(side="left", padx=(22, 4))
            tk.Entry(unc_row, textvariable=self._smb_unc,
                     font=FONT, bg=C["card"], fg=C["text"],
                     relief="flat", bd=1, insertbackground=C["accent"],
                     width=26).pack(side="left", fill="x", expand=True)
            tk.Label(unc_row, text="Leave blank to use \\\\{Host}",
                     bg=C["bg"], fg=C["text_sub"],
                     font=FONT_TINY).pack(side="left", padx=(6, 0))

            def _toggle_unc_row(*_):
                if self._proto_enabled["SMB"].get():
                    unc_row.pack(fill="x", pady=(0, 2))
                else:
                    unc_row.pack_forget()

            self._proto_enabled["SMB"].trace_add("write", _toggle_unc_row)
            _toggle_unc_row()  # apply initial state

    def _update_cmd_section(self):
        """Show Commands section only when SSH, Telnet, or RDP is enabled."""
        show = any(self._proto_enabled[p].get() for p in ("SSH", "Telnet", "RDP"))
        if show:
            self._cmd_section.pack(fill="x", padx=12, pady=(0, 4))
        else:
            self._cmd_section.pack_forget()

    def _import_cmd_file(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Select command file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            messagebox.showerror("Import Error", str(e), parent=self)
            return
        current = self._cmd_text.get("1.0", "end-1c").rstrip("\n")
        merged = (current + "\n" + text.rstrip("\n")) if current else text.rstrip("\n")
        self._cmd_text.delete("1.0", "end")
        self._cmd_text.insert("1.0", merged)

    def _toggle_pw(self):
        self._show_pw = not self._show_pw
        self._pw_entry.config(show="" if self._show_pw else "*")
        self._pw_toggle.config(
            text="hide" if self._show_pw else "show",
            fg=C["accent"] if self._show_pw else C["text_sub"],
        )

    def _ok(self):
        name = self._name_var.get().strip()
        host = self._host.get().strip()
        if not name or not host:
            messagebox.showwarning("Input Error",
                                   "Name and Host are required.", parent=self)
            return
        selected = [p for p in ("SSH", "Telnet", "RDP", "SMB")
                    if self._proto_enabled[p].get()]
        if not selected:
            messagebox.showwarning("Input Error",
                                   "Select at least one protocol.", parent=self)
            return

        cmds = [l.strip() for l in self._cmd_text.get("1.0", "end").splitlines()
                if l.strip()]
        base = {
            "host":     host,
            "user":     self._user.get().strip(),
            "password": _encode_pw(self._pw.get()),
            "group":    self._group_var.get().strip(),
        }
        multi = len(selected) > 1
        for proto in selected:
            entry = dict(base)
            entry["protocol"] = proto
            entry["name"] = f"{name} ({proto})" if multi else name
            port_str = self._proto_port[proto].get().strip()
            entry["port"] = int(port_str) if port_str and proto != "SMB" else 0
            entry["charset"] = (self._proto_charset[proto].get()
                                 if proto in ("SSH", "Telnet") else "")
            entry["commands"] = cmds if proto != "SMB" else []
            if proto == "SMB":
                # UNC Path 欄が空なら \\{host} を自動生成
                unc = self._smb_unc.get().strip()
                if not unc:
                    unc = f"\\\\{host}"
                entry["host"] = unc
            self.result.append(entry)

        self.destroy()


# ── Bookmark dialog ───────────────────────────────────────

class BookmarkDialog(tk.Toplevel):
    """Dialog for adding/editing bookmarks."""

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

        # deadline spinbox initial values
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

        # Event: combobox (select from existing event names or type directly)
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

        # deadline input (split spinboxes + checkbox)
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

        # work folders (multiple)
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
        _wf_sb = ttk.Scrollbar(wf_lb_frame, orient="vertical",
                               style="Gem.Vertical.TScrollbar",
                               command=self._wf_lb.yview)
        _wf_sb_pack = dict(side="right", fill="y")
        self._wf_lb.configure(yscrollcommand=lambda lo, hi:
                              _autohide_scrollbar(_wf_sb, lo, hi, _wf_sb_pack))
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


# ── Subtask dialog ─────────────────────────────────────────

class SubtaskDialog(tk.Toplevel):
    """Dialog for adding/editing subtasks."""

    def __init__(self, parent, initial: dict | None = None):
        super().__init__(parent)
        self.title("Add Subtask" if initial is None else "Edit Subtask")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.result: dict | None = None

        d = initial or {}
        self._title_var    = tk.StringVar(value=d.get("title", ""))
        self._progress_var = tk.IntVar(value=d.get("progress", 0))
        self._done_var     = tk.BooleanVar(value=d.get("done", False))

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

    def _build(self):
        form = tk.Frame(self, bg=C["bg"])
        form.pack(padx=4, pady=(12, 4))

        def _lbl(text, row):
            tk.Label(form, text=text, bg=C["bg"], fg=C["text_sub"],
                     font=FONT_SMALL, anchor="e", width=9).grid(
                         row=row, column=0, padx=(12, 4), pady=3, sticky="e")

        # title
        _lbl("Title", 0)
        e = tk.Entry(form, textvariable=self._title_var, font=FONT,
                     bg=C["card"], fg=C["text"], relief="flat", bd=1,
                     insertbackground=C["accent"], width=26)
        e.grid(row=0, column=1, padx=(0, 12), pady=3, sticky="ew")
        e.focus_set()

        # Done checkbox
        _lbl("Done", 1)
        def _on_done():
            if self._done_var.get():
                self._progress_var.set(100)
                self._pct_label.configure(text="100%")
            else:
                if self._progress_var.get() == 100:
                    self._progress_var.set(0)
                    self._pct_label.configure(text="0%")
        tk.Checkbutton(form, variable=self._done_var, command=_on_done,
                       bg=C["bg"], fg=C["text"], selectcolor=C["bg"],
                       activebackground=C["bg"], cursor="hand2",
                       ).grid(row=1, column=1, padx=(0, 12), pady=3, sticky="w")

        # progress slider
        _lbl("Progress", 2)
        slider_frame = tk.Frame(form, bg=C["bg"])
        slider_frame.grid(row=2, column=1, padx=(0, 12), pady=3, sticky="ew")
        self._pct_label = tk.Label(slider_frame, text=f"{self._progress_var.get()}%",
                                   bg=C["bg"], fg=C["accent"], font=FONT_BOLD, width=4)
        self._pct_label.pack(side="right")
        def _on_scale(v):
            pct = int(float(v))
            self._pct_label.configure(text=f"{pct}%")
            self._done_var.set(pct == 100)
        tk.Scale(slider_frame, variable=self._progress_var,
                 from_=0, to=100, orient="horizontal", command=_on_scale,
                 bg=C["bg"], fg=C["text"], troughcolor=C["border"],
                 activebackground=C["accent_lt"],
                 highlightthickness=0, bd=0, showvalue=False, resolution=5,
                 ).pack(side="left", fill="x", expand=True)

        # deadline
        _lbl("Deadline", 3)
        dl_outer = tk.Frame(form, bg=C["bg"])
        dl_outer.grid(row=3, column=1, padx=(0, 12), pady=3, sticky="ew")
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

        # buttons
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
        state, bg = ("normal", C["card"]) if self._use_deadline.get() else ("disabled", C["border"])
        for sp in self._dl_spinboxes:
            sp.configure(state=state, bg=bg)

    def _ok(self):
        title = self._title_var.get().strip()
        if not title:
            messagebox.showwarning("Input Error", "Title is required.", parent=self)
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
            "title":    title,
            "progress": self._progress_var.get(),
            "done":     self._done_var.get(),
            "deadline": deadline,
        }
        self.destroy()


# ── MJPEG AVI writer ──────────────────────────────────────

def _avi_chunk(fourcc: bytes, data: bytes) -> bytes:
    if len(data) % 2:
        data += b"\x00"
    return fourcc + struct.pack("<I", len(data)) + data


def _avi_list(fourcc: bytes, data: bytes) -> bytes:
    return b"LIST" + struct.pack("<I", 4 + len(data)) + fourcc + data


class _MjpegAviWriter:
    """Incremental MJPEG AVI writer.

    Frames are appended to a temp file as they are captured, so a long
    recording keeps only the per-frame sizes in memory instead of every
    JPEG (30 min of full-screen frames can be several GB). Call finalize()
    to assemble the playable AVI, or abort() to discard the temp file.
    """

    def __init__(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".mjpeg", delete=False)
        self._sizes: list[int] = []   # full '00dc' chunk sizes (header + padded data)
        self.width  = 0
        self.height = 0

    @property
    def frame_count(self) -> int:
        return len(self._sizes)

    def add_frame(self, jpeg: bytes):
        if not self._sizes:
            # frame dimensions come from the first frame
            from PIL import Image
            with Image.open(io.BytesIO(jpeg)) as im:
                self.width, self.height = im.size
        chunk = _avi_chunk(b"00dc", jpeg)
        self._tmp.write(chunk)
        self._sizes.append(len(chunk))

    def abort(self):
        """Discard the recording and remove the temp file."""
        try:
            self._tmp.close()
            os.unlink(self._tmp.name)
        except OSError:
            pass

    def finalize(self, out_path: Path, fps: int):
        """Assemble the AVI at out_path by streaming the buffered frames."""
        n = len(self._sizes)
        if n == 0:
            self.abort()
            return
        self._tmp.flush()

        width, height = self.width, self.height
        max_f = max(self._sizes) - 8

        # idx1 — frame offset index (offsets relative to just after 'movi')
        offset = 4
        idx_parts = []
        for sz in self._sizes:
            idx_parts.append(b"00dc" + struct.pack("<III", 0x10, offset, sz - 8))
            offset += sz
        idx1 = _avi_chunk(b"idx1", b"".join(idx_parts))

        # strf: BITMAPINFOHEADER (40 bytes)
        strf_data = (
            struct.pack("<IiiHH", 40, width, height, 1, 24)  # biSize/biWidth/biHeight/biPlanes/biBitCount
            + b"MJPG"                                         # biCompression
            + struct.pack("<i", width * height * 3)           # biSizeImage
            + struct.pack("<iiII", 0, 0, 0, 0)               # xPPM/yPPM/clrUsed/clrImportant
        )

        # strh: AVISTREAMHEADER (60 bytes data)
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

        strl = _avi_list(b"strl", _avi_chunk(b"strh", strh_data)
                         + _avi_chunk(b"strf", strf_data))

        # avih: AVIMAINHEADER (56 bytes data)
        avih_data = (
            struct.pack("<IIIIIIIIII",
                1000000 // fps, max_f * fps, 0, 0x10,  # microSecPerFrame, maxBytesPerSec, padding, flags
                n, 0, 1, max_f, width, height,         # totalFrames, initialFrames, streams, bufSize, W, H
            )
            + struct.pack("<IIII", 0, 0, 0, 0)         # dwReserved[4]
        )

        hdrl = _avi_list(b"hdrl", _avi_chunk(b"avih", avih_data) + strl)

        movi_size = 4 + sum(self._sizes)   # 'movi' fourcc + frame chunks
        riff_size = 4 + len(hdrl) + 8 + movi_size + len(idx1)

        import shutil
        with open(out_path, "wb") as out:
            out.write(b"RIFF" + struct.pack("<I", riff_size) + b"AVI " + hdrl)
            out.write(b"LIST" + struct.pack("<I", movi_size) + b"movi")
            self._tmp.seek(0)
            shutil.copyfileobj(self._tmp, out)
            out.write(idx1)
        self._tmp.close()
        try:
            os.unlink(self._tmp.name)
        except OSError:
            pass


# ── Recording window ───────────────────────────────────────

class RecordingWindow(tk.Toplevel):
    MAX_FRAMES = 18000  # up to 30 minutes at 10fps

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
        self._writer: _MjpegAviWriter | None = None
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
        # ── Monitor selection ──
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

        # ── JPEG Quality ──
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

        # ── Save destination ──
        tk.Label(self, text="Save to", bg=C["bg"], fg=C["text"],
                 font=FONT_BOLD).pack(anchor="w", padx=14)
        dir_frame = tk.Frame(self, bg=C["bg"])
        dir_frame.pack(fill="x", padx=14, pady=(4, 0))
        tk.Entry(dir_frame, textvariable=self._save_dir,
                 font=FONT_MONO, bg=C["card"], fg=C["text"],
                 relief="flat", bd=1, width=28,
                 insertbackground=C["accent"]).pack(side="left", fill="x", expand=True)
        tk.Button(dir_frame, text="...", command=self._browse_dir,
                  bg=C["accent_lt"], fg=C["text"], relief="flat", bd=0,
                  font=FONT, cursor="hand2", padx=6, pady=1,
                  activebackground=C["border"]).pack(side="left", padx=(4, 0))

        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", pady=8)

        # ── Options ──
        tk.Checkbutton(self, text="Hide launcher while recording",
                       variable=self._hide_var,
                       bg=C["bg"], fg=C["text"], font=FONT,
                       activebackground=C["bg"], activeforeground=C["text"],
                       selectcolor=C["accent_lt"], relief="flat", bd=0,
                       ).pack(anchor="w", padx=14)

        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", pady=(8, 0))

        # ── Button & Status ──
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

        # Determine capture region (truncate to even size)
        idx = self._monitor_var.get()
        if idx == -1:
            self._bbox = None
        else:
            m = self._monitors[idx]
            self._bbox = (m["left"], m["top"], m["right"], m["bottom"])

        with self._lock:
            if self._writer is not None:
                self._writer.abort()
            self._writer = _MjpegAviWriter()
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
                # Crop to even dimensions (recommended for MJPEG)
                w = img.width  & ~1
                h = img.height & ~1
                if w != img.width or h != img.height:
                    img = img.crop((0, 0, w, h))

                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=quality, optimize=False)
                jpeg = buf.getvalue()

                with self._lock:
                    if self._writer is None:
                        break
                    self._writer.add_frame(jpeg)
                    count = self._writer.frame_count

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
            fc = self._writer.frame_count if self._writer else 0
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

        # Run the save process on a background thread (to prevent UI freeze)
        fps = self._fps_var.get()

        def _save():
            with self._lock:
                writer, self._writer = self._writer, None
            count = writer.frame_count if writer else 0
            if writer is not None:
                if count:
                    writer.finalize(self._output_path, fps)
                else:
                    writer.abort()
            self.after(0, self._on_save_done, count)

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
                # Wrap on_save_done to auto-close after saving
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
                 font=FONT_MONO, bg=C["card"], fg=C["text"],
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


# ── File Scanner ──────────────────────────────────────────

class FileScanWindow(tk.Toplevel):
    """Displays a list of files (name, size, timestamp) under a specified folder.
    Recursively scans subdirectories."""

    _COL_DEFS = [
        ("path",    "Path",             320),
        ("size",    "Size",              90),
        ("mtime",   "Modified",         150),
    ]

    def __init__(self, parent: tk.Misc, folder_path: str = ""):
        super().__init__(parent)
        self._parent = parent
        self.title("File Scanner")
        self.configure(bg=C["bg"])
        self.resizable(True, True)
        self.minsize(600, 400)

        self._folder_var = tk.StringVar(value=folder_path)
        self._status_var = tk.StringVar(value="Select a folder and click Scan.")
        self._sort_col   = "path"
        self._sort_rev   = False
        self._rows: list[tuple] = []   # (rel_path, size_bytes, mtime_dt)
        self._scanning   = False
        self._cancel     = False

        self._build()
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        self.geometry(f"700x500+{px + (pw - 700) // 2}+{py + (ph - 500) // 2}")

        if folder_path and os.path.isdir(folder_path):
            self.after(100, self._start_scan)

    def _build(self):
        top = tk.Frame(self, bg=C["bg"])
        top.pack(fill="x", padx=12, pady=(12, 6))

        tk.Label(top, text="Folder", bg=C["bg"], fg=C["text"],
                 font=FONT_BOLD).pack(side="left")

        entry = tk.Entry(top, textvariable=self._folder_var,
                         font=FONT_MONO, bg=C["card"], fg=C["text"],
                         relief="flat", bd=1, insertbackground=C["accent"])
        entry.pack(side="left", fill="x", expand=True, padx=(6, 4))
        entry.bind("<Return>", lambda _: self._start_scan())

        tk.Button(top, text="…", command=self._browse,
                  bg=C["accent_lt"], fg=C["text"], relief="flat", bd=0,
                  font=FONT, cursor="hand2", padx=6, pady=1,
                  activebackground=C["border"]).pack(side="left", padx=(0, 4))

        self._scan_btn = tk.Button(top, text="Scan", command=self._start_scan,
                                   bg=C["accent"], fg="white", relief="flat", bd=0,
                                   font=FONT_BOLD, cursor="hand2", padx=10, pady=2,
                                   activebackground=C["accent_dk"])
        self._scan_btn.pack(side="left")

        tree_frame = tk.Frame(self, bg=C["bg"])
        tree_frame.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        cols = [c[0] for c in self._COL_DEFS]
        style = ttk.Style(self)
        style.configure("FileScan.Treeview",
                        background=C["card"], foreground=C["text"],
                        fieldbackground=C["card"], rowheight=22,
                        font=FONT)
        style.configure("FileScan.Treeview.Heading",
                        background=C["accent_lt"], foreground=C["text"],
                        relief="flat", font=FONT_BOLD)
        style.map("FileScan.Treeview",
                  background=[("selected", C["card_h"])],
                  foreground=[("selected", C["text"])])

        self._tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                  style="FileScan.Treeview", selectmode="extended")

        for key, label, width in self._COL_DEFS:
            self._tree.heading(key, text=label,
                               command=lambda k=key: self._sort_by(k))
            anchor = "w" if key == "path" else "e"
            self._tree.column(key, width=width, anchor=anchor, stretch=(key == "path"))

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                            style="Gem.Vertical.TScrollbar", command=self._tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal",
                            style="Gem.Horizontal.TScrollbar", command=self._tree.xview)
        _vpack = dict(side="right",  fill="y")
        _hpack = dict(side="bottom", fill="x")
        self._tree.configure(
            yscrollcommand=lambda lo, hi: _autohide_scrollbar(vsb, lo, hi, _vpack),
            xscrollcommand=lambda lo, hi: _autohide_scrollbar(hsb, lo, hi, _hpack),
        )
        self._tree.pack(side="left", fill="both", expand=True)
        # vsb/hsb are shown by _autohide_scrollbar only when content overflows

        bot = tk.Frame(self, bg=C["bg"])
        bot.pack(fill="x", padx=12, pady=(0, 10))

        self._status_lbl = tk.Label(bot, textvariable=self._status_var,
                                    bg=C["bg"], fg=C["text_sub"], font=FONT,
                                    anchor="w")
        self._status_lbl.pack(side="left", fill="x", expand=True)

        tk.Button(bot, text="Export CSV", command=self._export_csv,
                  bg=C["accent_lt"], fg=C["text"], relief="flat", bd=0,
                  font=FONT, cursor="hand2", padx=8, pady=2,
                  activebackground=C["border"]).pack(side="right")

    def _browse(self):
        path = filedialog.askdirectory(title="Select folder", parent=self)
        if path:
            self._folder_var.set(os.path.normpath(path))

    def _start_scan(self):
        folder = self._folder_var.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("Error", "Please specify a valid folder.", parent=self)
            return
        if self._scanning:
            self._cancel = True
            return
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._rows.clear()
        self._scanning = True
        self._cancel   = False
        self._scan_btn.configure(text="Cancel", bg=C["btn_del"],
                                 activebackground=C["btn_del_h"])
        self._status_var.set("Scanning...")
        threading.Thread(target=self._scan_worker, args=(folder,), daemon=True).start()

    def _scan_worker(self, folder: str):
        rows: list[tuple] = []
        try:
            for root, _dirs, files in os.walk(folder):
                if self._cancel:
                    break
                for fname in files:
                    if self._cancel:
                        break
                    full = os.path.join(root, fname)
                    try:
                        stat = os.stat(full)
                        rel  = os.path.relpath(full, folder)
                        size = stat.st_size
                        mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                        rows.append((rel, size, mtime))
                    except OSError:
                        pass
        finally:
            self.after(0, self._scan_done, rows)

    def _scan_done(self, rows: list[tuple]):
        self._rows = rows
        self._scanning = False
        self._scan_btn.configure(text="Scan", bg=C["accent"],
                                 activebackground=C["accent_dk"])
        if self._cancel:
            self._status_var.set(f"Cancelled. ({len(rows)} files retrieved)")
            self._cancel = False
        else:
            self._status_var.set(f"{len(rows)} file(s) found.")
        self._refresh_tree()

    def _refresh_tree(self):
        for item in self._tree.get_children():
            self._tree.delete(item)

        rows = sorted(
            self._rows,
            key=lambda r: (r[0].lower() if self._sort_col == "path"
                           else r[1] if self._sort_col == "size"
                           else r[2]),
            reverse=self._sort_rev,
        )
        for rel, size, mtime in rows:
            self._tree.insert("", "end", values=(
                rel,
                self._fmt_size(size),
                mtime.strftime("%Y-%m-%d %H:%M:%S"),
            ))

    def _sort_by(self, col: str):
        if self._sort_col == col:
            self._sort_rev = not self._sort_rev
        else:
            self._sort_col = col
            self._sort_rev = False
        self._refresh_tree()

    def _export_csv(self):
        if not self._rows:
            messagebox.showinfo("Info", "No data to export.", parent=self)
            return
        save_path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="file_scan.csv",
        )
        if not save_path:
            return
        import csv
        try:
            with open(save_path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["Path", "Size (bytes)", "Modified"])
                for rel, size, mtime in self._rows:
                    w.writerow([rel, size, mtime.strftime("%Y-%m-%d %H:%M:%S")])
            self._status_var.set(f"Saved: {save_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    @staticmethod
    def _fmt_size(size: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# ── Notification popup ────────────────────────────────────



def _get_monitor_work_area(widget: tk.Misc) -> tuple[int, int, int, int]:
    """Return the work area (left, top, right, bottom) of the monitor where the widget is displayed.
    The area excludes the taskbar. Falls back to primary monitor size on failure."""
    try:
        class _RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

        class _MONITORINFO(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.DWORD),
                        ("rcMonitor", _RECT), ("rcWork", _RECT),
                        ("dwFlags", wintypes.DWORD)]

        # identify monitor by widget center coordinates. While withdrawn/
        # minimized to tray, winfo_rootx/y no longer reflect the window's
        # on-screen position, so fall back to the last known normal
        # geometry (kept up to date by _on_window_resize) to still target
        # the monitor the window was last shown on.
        if widget.winfo_viewable():
            cx = widget.winfo_rootx() + widget.winfo_width() // 2
            cy = widget.winfo_rooty() + widget.winfo_height() // 2
        else:
            m = re.match(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", getattr(widget, "_geometry_cfg", "") or "")
            if m:
                w, h, x, y = map(int, m.groups())
                cx, cy = x + w // 2, y + h // 2
            else:
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
    """Bottom-right fade-in notification popup with progress bar"""

    FADE_MS    = 350    # fade in/out duration (ms)
    FADE_STEPS = 14     # number of fade steps
    SLIDE_PX   = 46     # horizontal slide-in distance (px)

    def __init__(self, parent, task: dict, display_ms: int = 8000):
        super().__init__(parent)
        self._display_ms = display_ms
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)
        self.configure(bg=C["accent"])   # outer border: accent color 2px

        # ── calculate remaining time ──
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

        # ── main container (2px border padding) ──
        inner = tk.Frame(self, bg=C["card"])
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        # ── header strip ──────────────────────────────────
        hdr = tk.Frame(inner, bg=C["accent_lt"])
        hdr.pack(fill="x")

        # left: "Notify" label + recurrence badge
        hdr_l = tk.Frame(hdr, bg=C["accent_lt"])
        hdr_l.pack(side="left", padx=(10, 4), pady=(7, 5))
        tk.Label(hdr_l, text="Notify",
                 bg=C["accent_lt"], fg=C["accent_dk"],
                 font=FONT_SMALL_BOLD).pack(side="left")
        if recur_text:
            tk.Label(hdr_l, text=recur_text,
                     bg=C["accent"], fg="white",
                     font=FONT_SMALL_BOLD,
                     padx=5, pady=1).pack(side="left", padx=(6, 0))

        # right: decorative circles + close button
        hdr_r = tk.Frame(hdr, bg=C["accent_lt"])
        hdr_r.pack(side="right", padx=(0, 8), pady=6)

        # 4-point star resembling the Claude logo
        star_cv = tk.Canvas(hdr_r, bg=C["accent_lt"], width=14, height=14,
                            highlightthickness=0)
        star_cv.pack(side="left")
        star_cv.create_polygon(
            7, 1,  8, 6,  13, 7,  8, 8,  7, 13,  6, 8,  1, 7,  6, 6,
            fill=C["accent"], outline="",
        )

        close = tk.Label(hdr_r, text=" x ",
                         bg=C["accent_lt"], fg=C["accent_dk"],
                         font=FONT_SMALL_BOLD, cursor="hand2")
        close.pack(side="left", padx=(6, 0))
        close.bind("<Button-1>", lambda e: self.destroy())
        close.bind("<Enter>",    lambda e: close.configure(bg=C["accent"], fg="white"))
        close.bind("<Leave>",    lambda e: close.configure(bg=C["accent_lt"], fg=C["accent_dk"]))

        # thin accent line below header
        tk.Frame(inner, bg=C["accent"], height=1).pack(fill="x")

        # ── content area ────────────────────────────────
        content = tk.Frame(inner, bg=C["card"])
        content.pack(fill="both", expand=True, padx=14, pady=(10, 12))

        # title
        title = task.get("title", "")
        tk.Label(content, text=title,
                 bg=C["card"], fg=C["text"],
                 font=FONT_BOLD, anchor="w",
                 wraplength=240, justify="left").pack(fill="x", pady=(0, 6))

        # datetime pill
        if time_str:
            pill = tk.Frame(content, bg=C["accent_lt"])
            pill.pack(anchor="w", pady=(0, 3))
            tk.Label(pill, text=time_str,
                     bg=C["accent_lt"], fg=C["accent_dk"],
                     font=FONT_SMALL, padx=8, pady=2).pack()

        # remaining time
        if remain_str:
            tk.Label(content, text=remain_str,
                     bg=C["card"], fg=C["accent"],
                     font=FONT_SMALL_BOLD, anchor="w").pack(fill="x")

        # launch path
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

        # notes
        notes = task.get("notes", "")
        if notes:
            tk.Frame(content, bg=C["border"], height=1).pack(fill="x", pady=(6, 0))
            tk.Label(content, text=notes,
                     bg=C["card"], fg=C["text_sub"],
                     font=FONT_SMALL, anchor="w",
                     wraplength=240, justify="left").pack(fill="x", pady=(4, 0))

        # ── progress bar (bottom, 6px) ──────────────────────
        self._pb = tk.Canvas(self, height=6, bg=C["accent_lt"],
                             highlightthickness=0)
        self._pb.pack(fill="x", side="bottom")

        # ── position at bottom-right of the monitor where the app is shown ──
        self.update_idletasks()
        w  = max(self.winfo_reqwidth(), 280)
        h  = max(self.winfo_reqheight(), 80)
        ml, mt, mr, mb = _get_monitor_work_area(parent)
        self._fx = mr - w - 20   # final position; slide in from the right
        self._fy = mb - h - 12
        self.geometry(f"{w}x{h}+{self._fx + self.SLIDE_PX}+{self._fy}")

        # click to close
        for widget in (self, inner, content, hdr, hdr_l, hdr_r):
            widget.bind("<Button-1>", lambda e: self.destroy())

        # start animation
        self._start  = time.monotonic()
        self._pb_rect = None
        self._anim_step = 0
        self._fade_in()

    def _fade_in(self):
        # slide in from the right (ease-out) while fading in
        self._anim_step += 1
        k = min(1.0, self._anim_step / self.FADE_STEPS)
        ease = 1 - (1 - k) ** 3
        self.geometry(f"+{round(self._fx + (1 - ease) * self.SLIDE_PX)}+{self._fy}")
        self.attributes("-alpha", k)
        if k < 1.0:
            self.after(self.FADE_MS // self.FADE_STEPS, self._fade_in)
        else:
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
        # slide back toward the edge (ease-in) while fading out
        a = float(self.attributes("-alpha")) - 1.0 / self.FADE_STEPS
        self.attributes("-alpha", max(0.0, a))
        ease = (1.0 - max(0.0, a)) ** 2
        self.geometry(f"+{round(self._fx + ease * self.SLIDE_PX)}+{self._fy}")
        if a > 0:
            self.after(self.FADE_MS // self.FADE_STEPS, self._fade_out)
        else:
            self.destroy()


# ── Notify item dialog ─────────────────────────────────────

class NotifyDialog(tk.Toplevel):
    """Dialog for adding/editing a notification item"""

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
        # open_paths: new list format; legacy open_path string is also migrated
        _op = d.get("open_paths", [])
        if not _op and d.get("open_path"):
            _op = [d["open_path"]]
        self._open_paths_list: list = list(_op)
        self._notes_init    = d.get("notes", "")

        # parse existing scheduled_at to set spinbox initial values
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

        # scheduled input (split spinboxes)
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

        # open paths (multiple)
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
        _sb = ttk.Scrollbar(lb_frame, orient="vertical",
                            style="Gem.Vertical.TScrollbar",
                            command=self._paths_lb.yview)
        _sb_pack = dict(side="right", fill="y")
        self._paths_lb.configure(yscrollcommand=lambda lo, hi:
                                 _autohide_scrollbar(_sb, lo, hi, _sb_pack))
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

class FolderLauncher(TkinterDnD.Tk if TkinterDnD is not None else tk.Tk):
    # _active >= 0  : folder category index
    # _active == -1 : Terminal tab

    # system tab definitions (key, display name, _active value)
    _SYSTEM_TABS = [
        ("auto",      "Auto",      -9),
        ("terminal",  "Terminal",  -1),
        ("tasks",     "Tasks",     -2),
        ("notify",    "Notify",    -3),
        ("web",       "Web",       -4),
        ("grep",      "Search",   -12),
        ("console",   "Console",  -13),
    ]
    _DEFAULT_PINS = ["terminal", "tasks", "notify"]

    def __init__(self):
        super().__init__()
        self.title("Gem")
        self.geometry("480x400")
        self.resizable(True, True)
        self.configure(bg=C["bg"])
        self.minsize(320, 260)

        # The native Windows ttk theme ignores background colors for Treeview headers etc.,
        # so switch to the clam theme to enable custom colors.
        ttk.Style(self).theme_use("clam")

        # Load all settings at once from config.json (theme is resolved first)
        self._data: list[dict] = []
        self._conns: list[dict] = []
        self._tasks: list[dict] = []
        self._notify_items: list[dict] = []
        self._terminal_groups: list[str] = []
        self._selected_group: str | None = None   # None = All
        self._bookmarks: list[dict] = []
        self._bm_selected: int = 0
        self._active: int = 0   # -1=Terminal, -2=Tasks, -3=Notify, -4=Web
        self._pinned_tabs: list[str] = list(self._DEFAULT_PINS)
        self._tab_offset: int = 0   # category tab scroll position
        self._work_active: dict | None = None  # {"task_idx": int, "start": datetime}
        self._tray_icon: pystray.Icon | None = None
        self._tray_notify_pending: bool = False  # unread notification while minimized to tray
        self._work_anim_id = None
        self._work_anim_dots = 0
        self._work_bar_lbl: tk.Label | None = None
        self._theme: str = "plush"   # overwritten by _load_config()
        self._tick_id = None             # after ID for _tick() (cancelled on rebuild)
        # Auto tab: rule management
        self._rules: list[dict] = []
        self._rule_fired: set[str] = set()
        self._file_mtimes: dict[str, float | None] = {}
        self._file_watcher_started: bool = False
        self._conn_ping_cache:   dict[str, str | None] = {}  # host -> "ok"|"fail"|None
        self._conn_ping_dots:    dict[str, list]        = {}  # host -> [Canvas, ...]
        self._conn_ping_running: set[str]               = set()   # after IDs for dashboard auto-refresh
        self._conn_ping_enabled: bool = True   # Terminal ping dot ON/OFF
        self._hud_cpu: deque = deque(maxlen=60)   # last 60s of CPU samples (%)
        self._hud_ram: deque = deque(maxlen=60)   # last 60s of RAM load (%)
        self._save_after_id = None             # after ID for debounced config save
        self._pill_font_cache: dict = {}       # (font tuple) -> tkfont.Font, for tab width measurement
        self._load_config()
        self._backup_config_daily()
        self._cleanup_old_logs()
        _style_flat_scrollbars(self)   # theme colors are resolved above

        # generate icon after theme is resolved
        palette = ICON_PALETTES.get(self._theme)
        self._icon = tk.PhotoImage(data=_make_icon_png(palette, self._icon_shape))
        _setup_taskbar_icon(self, palette, self._icon_shape)
        self._task_sort: dict = {"col": None, "reverse": False}
        self._conn_sort: dict = {"col": None, "reverse": False}
        self._conn_search = tk.StringVar()
        self._conn_search_after = None   # debounce: re-render shortly after the last keystroke
        self._conn_search.trace_add("write", self._on_conn_search_changed)

        self._notified: set[str] = set()  # tracks already-notified keys
        self._notify_past_open: bool = False  # open/close state of past notifications section
        self._task_archive_open: bool = False        # archived tasks section open/close
        self._task_select_pending: int | None = None # task to select after next render (palette)
        self._palette_win: tk.Toplevel | None = None # command palette window (Ctrl+K)
        self._prev_bp: str = "md"  # responsive: previous breakpoint
        self._grep_folder: str = ""
        self._grep_query:  str = ""
        self._grep_ext:    str = ""
        self._grep_history: list[str] = []   # recent queries, newest first
        self._grep_running: bool = False
        self._grep_cancel:  bool = False
        self._log_tail_file: str | None = None  # Console tab: selected log filename
        self._log_tail_pos:  int = 0            # Console tab: byte offset already read

        self._restore_geometry()
        self._build_ui()
        # restore the last active tab (validated against current data)
        self._active = self._validate_active_tab(self._active_cfg)
        if self._active == -9:
            self._ensure_file_watcher()
        self._render_tabs()
        self._update_footer()
        self._render_list()
        self._check_schedule()
        self.after(30_000, self._check_rules)
        self.after(600, self._show_startup_summary)
        self._check_recurring_tasks()
        self.bind("<Control-k>", self._open_command_palette)
        self._setup_win_integration()
        # deferred: the WM frame window exists only after mapping
        self.after(50, lambda: _apply_titlebar_theme(self))
        self._pulse_loop()   # ping-dot glow animation (independent of _tick)

    # ── Config read/write (unified in config.json) ─────────────────

    def _load_config(self):
        migrated = False
        if not CONFIG_FILE.exists():
            # auto-migrate from legacy individual files if they exist
            old_folders   = _BASE_DIR / "folders.json"
            old_terminals = _BASE_DIR / "terminals.json"
            old_tasks     = _BASE_DIR / "tasks.json"
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
                self._font_size = 11
                self._font_family = "Segoe UI"
                self._grep_folder = ""
                self._grep_query  = ""
                self._grep_ext    = ""
                self._icon_shape  = "jelly"
                self._geometry_cfg = ""
                self._active_cfg   = 0
                self._export_lang  = "en"
                self._task_hide_done = False
                self._log_keep_days = 30
                self._hud_enabled = True
                C.update(THEMES.get(self._theme, THEMES["plush"]))
                return
            migrated = True  # migration successful
        else:
            try:
                cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            except Exception:
                # Corrupt/partial config: preserve it for recovery instead of
                # silently resetting to defaults (which a later save could
                # then persist over the only copy of the data).
                try:
                    import shutil
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    shutil.copy2(CONFIG_FILE, CONFIG_FILE.with_name(f"config.corrupt-{ts}.json"))
                except Exception:
                    pass
                cfg = {}

        # folder settings (auto-convert from legacy format)
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

        # terminal connection settings
        self._conns = cfg.get("terminals", [])
        self._terminal_groups = cfg.get("terminal_groups", [])
        self._bookmarks = cfg.get("bookmarks", [])

        # task data
        self._tasks = cfg.get("tasks", [])

        # restore an in-progress work timer (matched by event+process)
        aw = cfg.get("active_work")
        if aw:
            for i, t in enumerate(self._tasks):
                if (t.get("event") == aw.get("event")
                        and t.get("process") == aw.get("process")):
                    try:
                        self._work_active = {
                            "task_idx": i,
                            "start": datetime.datetime.fromisoformat(aw["start"]),
                        }
                    except (KeyError, ValueError):
                        pass
                    break

        # notification items
        self._notify_items = cfg.get("notifications", [])

        self._conn_ping_enabled = cfg.get("conn_ping_enabled", True)

        # header HUD (CPU/MEM readout) visibility
        self._hud_enabled = bool(cfg.get("hud_enabled", True))

        # tab pin settings
        self._pinned_tabs = cfg.get("pinned_tabs", list(self._DEFAULT_PINS))

        # automation rules
        self._rules = cfg.get("rules", [])

        # banner display settings
        self._banner_enabled_cfg: bool = cfg.get("banner_enabled", True)
        self._notify_display_sec_cfg: int = cfg.get("notify_display_sec", 8)
        self._topmost_cfg: bool = cfg.get("topmost", False)
        self._alpha_cfg: float = float(cfg.get("alpha", 1.0))
        self._card_size: str = cfg.get("card_size", "normal")
        self._font_size: int = int(cfg.get("font_size", 11))
        self._font_family: str = cfg.get("font_family", "Segoe UI")
        _update_fonts(self._font_size, self._font_family)
        self._grep_folder = cfg.get("grep_folder", "")
        self._grep_query  = cfg.get("grep_query",  "")
        self._grep_ext    = cfg.get("grep_ext",    "")
        self._grep_history = [str(x) for x in cfg.get("grep_history", [])][:10]

        # theme settings
        self._theme = cfg.get("theme", "plush")
        C.update(THEMES.get(self._theme, THEMES["plush"]))

        # icon design
        self._icon_shape = cfg.get("icon_shape", "jelly")

        # window geometry & last active tab (restored on next launch)
        self._geometry_cfg = cfg.get("geometry", "")
        self._active_cfg   = cfg.get("active_tab", 0)

        # export report language ("en" | "ja")
        self._export_lang = cfg.get("export_lang", "en")

        # Tasks tab: hide completed tasks
        self._task_hide_done = bool(cfg.get("task_hide_done", False))

        # terminal log auto-cleanup: keep logs for N days (0 = disabled)
        try:
            self._log_keep_days = max(0, int(cfg.get("log_keep_days", 30)))
        except (TypeError, ValueError):
            self._log_keep_days = 30

        # save to config.json when migrating from legacy files
        if migrated:
            self._save_config()

    def _save_config(self):
        """Debounced save: coalesce rapid changes into a single disk write.

        Many call sites (work timer, edits, etc.) call this in
        bursts; writing the full config.json (tens of KB) each time is wasteful.
        Schedule the write shortly after the last change instead. A flush runs
        on close/quit so nothing is lost on normal exit.
        """
        if self._save_after_id is not None:
            try:
                self.after_cancel(self._save_after_id)
            except Exception:
                pass
        self._save_after_id = self.after(800, self._flush_config)

    def _flush_config(self):
        """Write pending config changes to disk immediately."""
        self._save_after_id = None
        self._save_config_now()

    def _save_config_now(self):
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
            "icon_shape":      getattr(self, "_icon_shape", "jelly"),
            "geometry":        getattr(self, "_geometry_cfg", ""),
            "active_tab":      getattr(self, "_active", 0),
            "export_lang":     getattr(self, "_export_lang", "en"),
            "conn_ping_enabled": self._conn_ping_enabled,
            "hud_enabled":     getattr(self, "_hud_enabled", True),
            "topmost":         self.attributes("-topmost"),
            "alpha":           self.attributes("-alpha"),
            "card_size":       self._card_size,
            "font_size":       self._font_size,
            "font_family":     getattr(self, "_font_family", "Segoe UI"),
            "grep_folder":     self._grep_folder,
            "grep_query":      self._grep_query,
            "grep_ext":        self._grep_ext,
            "grep_history":    getattr(self, "_grep_history", []),
            "task_hide_done":  getattr(self, "_task_hide_done", False),
            "log_keep_days":   getattr(self, "_log_keep_days", 30),
            "pinned_tabs":   self._pinned_tabs,
            "rules":         self._rules,
            "active_work":   self._active_work_record(),
        }
        # ── Safety guard ──────────────────────────────────────────
        # Never let an all-empty config silently clobber a populated one
        # (this happens if a previous launch loaded a corrupt/partial file
        # and reset everything to defaults). If the new config has no folders,
        # terminals, tasks, bookmarks, notifications or rules, but the file on
        # disk still holds data, refuse to overwrite and keep a backup.
        primary_empty = not any([
            any(c.get("folders") for c in self._data if isinstance(c, dict)),
            self._conns, self._tasks, self._bookmarks,
            self._notify_items, self._rules,
        ])
        if primary_empty and CONFIG_FILE.exists():
            try:
                existing = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                had_data = any([
                    any(c.get("folders") for c in existing.get("folders", [])
                        if isinstance(c, dict)),
                    existing.get("terminals"), existing.get("tasks"),
                    existing.get("bookmarks"), existing.get("notifications"),
                    existing.get("rules"),
                ])
            except Exception:
                # unparseable but non-trivial → assume it held data
                had_data = CONFIG_FILE.stat().st_size > 200
            if had_data:
                try:
                    import shutil
                    shutil.copy2(CONFIG_FILE, CONFIG_FILE.with_suffix(".bak"))
                except Exception:
                    pass
                return   # don't wipe real data with an empty config

        data = json.dumps(cfg, ensure_ascii=False, indent=2)
        try:
            # keep a one-generation backup of the current good config
            if CONFIG_FILE.exists() and CONFIG_FILE.stat().st_size > 0:
                import shutil
                shutil.copy2(CONFIG_FILE, CONFIG_FILE.with_suffix(".bak"))
            # atomic write: write to a temp file then replace, so an
            # interrupted/killed write can never leave a truncated config
            tmp = CONFIG_FILE.with_suffix(".tmp")
            tmp.write_text(data, encoding="utf-8")
            os.replace(tmp, CONFIG_FILE)
        except Exception:
            CONFIG_FILE.write_text(data, encoding="utf-8")

    def _save(self):
        self._save_config()

    def _save_conns(self):
        self._save_config()

    def _save_tasks(self):
        self._save_config()

    def _save_notify(self):
        self._save_config()

    def _popup_menu(self, menu, x, y):
        """Show a popup menu at (x, y).

        While the window is pinned on top (-topmost), cascade submenus render
        *behind* the window on Windows; temporarily drop topmost during the
        popup so submenus appear in front. No-op when not pinned.
        """
        try:
            was_top = bool(self.attributes("-topmost"))
        except Exception:
            was_top = False
        if was_top:
            self.attributes("-topmost", False)
        try:
            menu.tk_popup(x, y)
        finally:
            try:
                menu.grab_release()
            except Exception:
                pass
            if was_top:
                self.attributes("-topmost", True)

    @property
    def _current(self) -> dict:
        return self._data[self._active]

    # ── Responsive layout ────────────────────────────────

    def _width_bp(self) -> str:
        """Return the current width breakpoint name (xs/sm/md)."""
        try:
            w = self.winfo_width()
        except Exception:
            return "md"
        if w < 360:
            return "xs"
        if w < 480:
            return "sm"
        return "md"

    def _restore_geometry(self):
        """Apply the saved window geometry, dropping an off-screen position."""
        geo = getattr(self, "_geometry_cfg", "") or ""
        m = re.match(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)$", geo)
        if not m:
            if re.match(r"\d+x\d+$", geo):
                self.geometry(geo)   # size only
            return
        w, h, x, y = map(int, m.groups())
        try:
            mons = _get_monitors()
        except Exception:
            mons = []
        on_screen = (not mons) or any(
            mon["left"] - 50 <= x <= mon["right"] - 50 and
            mon["top"] - 50 <= y <= mon["bottom"] - 50 for mon in mons)
        self.geometry(f"{w}x{h}+{x}+{y}" if on_screen else f"{w}x{h}")

    def _validate_active_tab(self, idx) -> int:
        """Return a safe active-tab index (folder index or known system tab)."""
        try:
            idx = int(idx)
        except (TypeError, ValueError):
            return 0
        if idx >= 0:
            return idx if idx < len(self._data) else 0
        valid = {v for _, _, v in self._SYSTEM_TABS}
        return idx if idx in valid else 0

    def _on_window_resize(self, event):
        """Handle responsive layout on window resize."""
        if event.widget is not self:
            return

        # remember the current window geometry (persisted for next launch)
        try:
            if self.state() == "normal":
                new_geo = self.geometry()
                if new_geo != getattr(self, "_geometry_cfg", "") and hasattr(self, "_footer"):
                    self._geometry_cfg = new_geo
                    self._save_config()   # debounced; coalesces rapid resizes
        except Exception:
            pass

        # Hide header banner when width < 400
        if hasattr(self, "_banner_lbl"):
            try:
                w = self.winfo_width()
                if w < 400:
                    self._banner_lbl.pack_forget()
                elif not self._banner_lbl.winfo_ismapped():
                    self._banner_lbl.pack(side="left", padx=(4, 0))
            except Exception:
                pass

        # Re-render only when the breakpoint changes
        bp = self._width_bp()
        if bp == self._prev_bp:
            return
        self._prev_bp = bp
        self._render_tabs()
        self._render_list()

    # ── UI construction ───────────────────────────────────

    def _build_ui(self):
        # header
        hdr = tk.Frame(self, bg=C["accent"], height=40)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        # 1px border below header
        tk.Frame(self, bg=C["accent_dk"], height=1).pack(fill="x")

        # instrument-panel clock: time + date/weekday in mono, stacked
        self._clock_var = tk.StringVar()
        self._date_var  = tk.StringVar()
        _clk = tk.Frame(hdr, bg=C["accent"])
        _clk.pack(side="left", padx=(6, 0))
        tk.Label(_clk, textvariable=self._clock_var,
                 bg=C["accent"], fg="white",
                 font=FONT_MONO, anchor="w").pack(fill="x")
        tk.Label(_clk, textvariable=self._date_var,
                 bg=C["accent"], fg=C["accent_lt"],
                 font=(FONT_MONO[0], max(7, FONT_BASE - 3)),
                 anchor="w").pack(fill="x")

        # HUD: CPU/RAM sparkline + readout (fed by _tick)
        self._hud_cv = tk.Canvas(hdr, width=56, height=24,
                                 bg=C["accent"], highlightthickness=0)
        self._hud_cv.pack(side="left", padx=(8, 0))
        self._hud_lbl = tk.Label(hdr, text="", justify="left", anchor="w",
                                 bg=C["accent"], fg=C["accent_lt"],
                                 font=(FONT_MONO[0], max(7, FONT_BASE - 3)))
        self._hud_lbl.pack(side="left", padx=(3, 0))

        # Banner notification label
        self._banner_lbl = tk.Label(
            hdr, text="",
            bg=C["accent_dk"], fg="white",
            font=FONT_SMALL, padx=8, pady=0, anchor="w",
        )
        self._banner_lbl.pack(side="left", padx=(4, 0))

        # Setup vars (must be before _tick())
        self._hud_enabled_var = tk.BooleanVar(value=self._hud_enabled)
        self._hud_enabled_var.trace_add("write", self._on_toggle_hud)
        self._apply_hud_visibility()
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
                        padx=10, pady=3)

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
            for key, label in [("plush","Plush"),("violet","Violet"),("dark","Dark"),("light","Light"),
                                ("gemini","Gemini"),("claude","Claude"),("scarlet","Scarlet"),
                                ("ocean","Ocean"),("rose","Rose"),("mint","Mint"),
                                ("peach","Peach"),("sky","Sky"),("lemon","Lemon"),
                                ("lavender","Lavender"),("sakura","Sakura"),
                                ("cyber","Cyber"),("synthwave","Synthwave"),("matrix","Matrix")]:
                prefix = "* " if self._theme == key else "  "
                theme_sub.add_command(label=prefix + label,
                                      command=lambda k=key: self._apply_theme(k))
            m.add_cascade(label="Theme", menu=theme_sub)

            # Icon submenu
            icon_sub = tk.Menu(m, tearoff=0,
                               bg=C["card"], fg=C["text"],
                               activebackground=C["card_h"], activeforeground=C["text"],
                               relief="flat", font=FONT_SMALL)
            for key, label in ICON_SHAPES:
                prefix = "* " if getattr(self, "_icon_shape", "jelly") == key else "  "
                icon_sub.add_command(label=prefix + label,
                                     command=lambda k=key: self._set_icon_shape(k))
            m.add_cascade(label="Icon", menu=icon_sub)

            # Export language submenu
            exp_sub = tk.Menu(m, tearoff=0,
                              bg=C["card"], fg=C["text"],
                              activebackground=C["card_h"], activeforeground=C["text"],
                              relief="flat", font=FONT_SMALL)
            for key, label in [("en", "English"), ("ja", "日本語")]:
                prefix = "* " if getattr(self, "_export_lang", "en") == key else "  "
                exp_sub.add_command(label=prefix + label,
                                    command=lambda k=key: self._set_export_lang(k))
            m.add_cascade(label="Export language", menu=exp_sub)
            m.add_separator()

            # Banner toggle
            m.add_checkbutton(label="Banner notifications",
                              variable=self._banner_enabled,
                              onvalue=True, offvalue=False)

            # CPU/MEM HUD toggle
            m.add_checkbutton(label="CPU/MEM monitor",
                              variable=self._hud_enabled_var,
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

            # Terminal log auto-cleanup
            log_sub = tk.Menu(m, tearoff=0,
                              bg=C["card"], fg=C["text"],
                              activebackground=C["card_h"], activeforeground=C["text"],
                              relief="flat", font=FONT_SMALL)
            for d in (0, 7, 14, 30, 90):
                prefix = "* " if getattr(self, "_log_keep_days", 30) == d else "  "
                label = "Off" if d == 0 else f"Keep {d} days"
                log_sub.add_command(label=prefix + label,
                                    command=lambda v=d: self._set_log_keep_days(v))
            m.add_cascade(label="Log cleanup", menu=log_sub)
            m.add_separator()

            # Pin on top
            is_top = bool(self.attributes("-topmost"))
            def _toggle_topmost():
                self.attributes("-topmost", not bool(self.attributes("-topmost")))
                self._save_config()
            m.add_command(label=("* " if is_top else "  ") + "Pin on top",
                          command=_toggle_topmost)

            # Start with Windows (HKCU Run key)
            in_startup = self._is_startup_enabled()
            m.add_command(label=("* " if in_startup else "  ") + "Start with Windows",
                          command=self._toggle_startup)
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

            # Font size submenu
            font_sub = tk.Menu(m, tearoff=0,
                               bg=C["card"], fg=C["text"],
                               activebackground=C["card_h"], activeforeground=C["text"],
                               relief="flat", font=FONT_SMALL)
            for pt in [9, 10, 11, 12, 13, 14]:
                prefix = "* " if self._font_size == pt else "  "
                font_sub.add_command(
                    label=f"{prefix}{pt}pt",
                    command=lambda p=pt: self._set_font_size(p))
            m.add_cascade(label="Font size", menu=font_sub)

            # Font family submenu
            fam_sub = tk.Menu(m, tearoff=0,
                              bg=C["card"], fg=C["text"],
                              activebackground=C["card_h"], activeforeground=C["text"],
                              relief="flat", font=FONT_SMALL)
            for fam in ("Segoe UI", "Bahnschrift", "Consolas"):
                prefix = "* " if self._font_family == fam else "  "
                fam_sub.add_command(
                    label=f"{prefix}{fam}",
                    command=lambda f=fam: self._set_font_family(f))
            m.add_cascade(label="Font family", menu=fam_sub)

            # Transparency
            m.add_command(label="Transparency...", command=self._open_transparency_dialog)

            self._popup_menu(m, _cfg_btn.winfo_rootx(),
                         _cfg_btn.winfo_rooty() + _cfg_btn.winfo_height())

        _cfg_btn = tk.Button(hdr, text="...", command=_show_settings, **_btn_cfg)
        _cfg_btn.pack(side="right", padx=(0, 6))

        # Record
        tk.Button(hdr, text="Record", command=self._open_recording,
                  **_btn_cfg).pack(side="right", padx=(0, 2))

        # Screenshot
        tk.Button(hdr, text="Screenshot", command=self._open_screenshot,
                  **_btn_cfg).pack(side="right", padx=(0, 2))


        # Minimize to tray
        self.bind("<Unmap>", self._on_unmap)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Responsive: monitor window resize
        self.bind("<Configure>", self._on_window_resize)

        # tab bar
        self._tab_bar = tk.Frame(self, bg=C["bg"], pady=2)
        self._tab_bar.pack(fill="x")

        # Separator line between tab bar and content
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")

        # Path bar — packed with side="bottom" before canvas to reserve space
        self._pathbar_var = tk.StringVar()
        self._pathbar = tk.Label(
            self,
            textvariable=self._pathbar_var,
            bg=C["bg"], fg=C["text_sub"],
            font=FONT_TINY,
            anchor="w", padx=10, pady=2,
        )
        self._pathbar.pack(fill="x", side="bottom")

        # scrollable list
        wrapper = tk.Frame(self, bg=C["bg"])
        wrapper.pack(fill="both", expand=True, padx=4, pady=3)

        canvas = tk.Canvas(wrapper, bg=C["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(wrapper, orient="vertical",
                                  style="Gem.Vertical.TScrollbar",
                                  command=canvas.yview)
        self._list_frame = tk.Frame(canvas, bg=C["bg"])
        self._list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        _win_id = canvas.create_window((0, 0), window=self._list_frame, anchor="nw")
        _sb_pack = dict(side="right", fill="y")
        canvas.configure(yscrollcommand=lambda lo, hi:
                         _autohide_scrollbar(scrollbar, lo, hi, _sb_pack))
        canvas.pack(side="left", fill="both", expand=True)
        # scrollbar is shown by _autohide_scrollbar only when content overflows
        # sync _list_frame width with canvas width on resize
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfigure(_win_id, width=e.width))
        def _on_wheel(e):
            # bind_all fires for every widget; scroll the nearest scrollable
            # ancestor of the pointer so Treeview/Text/Listbox keep their
            # native wheel handling, nested canvases (e.g. search results)
            # scroll themselves, and dialogs don't scroll the list behind.
            w = e.widget
            if isinstance(w, str):   # widget already destroyed
                return
            while w is not None:
                if isinstance(w, (ttk.Treeview, tk.Listbox, tk.Text)):
                    return
                if isinstance(w, tk.Canvas) and w.cget("yscrollcommand"):
                    w.yview_scroll(-1 * (e.delta // 120), "units")
                    return
                w = getattr(w, "master", None)

        canvas.bind_all("<MouseWheel>", _on_wheel)
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

        # "Add File" button for folder tabs only
        self._footer_btn2 = tk.Button(
            self._footer, text="+ Add File",
            command=self._add_file,
            bg=C["accent_lt"], fg=C["text"], relief="flat", bd=0,
            font=FONT_BOLD, cursor="hand2", padx=12, pady=4,
            activebackground=C["border"], activeforeground=C["text"],
        )
        self._footer_btn2.pack(side="left", fill="x", expand=True, padx=(2, 0))
        _hover(self._footer_btn2, C["border"], C["accent_lt"])

        # "Export" button for Tasks tab only
        self._footer_btn3 = tk.Button(
            self._footer, text="Export",
            command=self._export_tasks,
            bg=C["accent_lt"], fg=C["text"], relief="flat", bd=0,
            font=FONT_BOLD, cursor="hand2", padx=12, pady=4,
            activebackground=C["border"], activeforeground=C["text"],
        )
        _hover(self._footer_btn3, C["border"], C["accent_lt"])

    # ── Tab bar ───────────────────────────────────────────

    # maximum number of category tabs shown in the tab bar at once
    _MAX_CAT_TABS = 7

    def _render_tabs(self):
        for w in self._tab_bar.winfo_children():
            w.destroy()

        # Responsive: determine visible tab count based on window width
        try:
            win_w = self.winfo_width()
        except Exception:
            win_w = 480
        max_cat_tabs = (3 if win_w < 360 else
                        5 if win_w < 480 else
                        self._MAX_CAT_TABS)

        # ── category tabs (left side) ──────────────────────────────
        total = len(self._data)

        # clamp offset to safe range
        max_offset = max(0, total - max_cat_tabs)
        self._tab_offset = max(0, min(self._tab_offset, max_offset))

        # auto-scroll so the active category tab is within the visible range
        if 0 <= self._active < total:
            if self._active < self._tab_offset:
                self._tab_offset = self._active
            elif self._active >= self._tab_offset + max_cat_tabs:
                self._tab_offset = self._active - max_cat_tabs + 1

        # ◀ scroll button (shown only when offset is greater than 0)
        if self._tab_offset > 0:
            tk.Button(
                self._tab_bar, text="◀",
                command=self._scroll_tabs_left,
                bg=C["bg"], fg=C["text_sub"],
                relief="flat", bd=0,
                font=FONT, cursor="hand2", padx=4, pady=3,
                activebackground=C["card_h"],
                activeforeground=C["text"],
            ).pack(side="left")

        # Pill-style tab builder
        def _pill(parent, text, active, cmd, ctx_cmd=None, side="left"):
            font_val = FONT_BOLD if active else FONT
            bg_act   = C["accent"]
            bg_idle  = C["bg"]
            bg_hov   = C["card_h"]
            fg_act   = "white"
            fg_idle  = C["text_sub"]
            # Measure text via a cached font object instead of creating a
            # throwaway Label + update_idletasks() per pill (called for every
            # tab on each render — tab switch, resize).
            fnt = self._pill_font_cache.get(font_val)
            if fnt is None:
                fnt = tkfont.Font(family=font_val[0], size=font_val[1],
                                  weight="bold" if len(font_val) > 2 else "normal")
                self._pill_font_cache[font_val] = fnt
            tw = fnt.measure(text) + 20   # matches Label padx=10 (both sides)
            th = fnt.metrics("linespace") + 8   # matches Label pady=4
            r = min(th // 2, 10)
            fill = [bg_act if active else bg_idle]
            cv = tk.Canvas(parent, width=tw, height=th,
                           bg=C["bg"], highlightthickness=0, cursor="hand2")
            cv.pack(side=side, padx=1, pady=2)
            def _draw(f):
                fill[0] = f
                cv.delete("all")
                _draw_rounded_rect(cv, 0, 0, tw, th, r, fill=f, outline="")
                fg = fg_act if f == bg_act else (C["text"] if f == bg_hov else fg_idle)
                cv.create_text(tw//2, th//2, text=text, font=font_val, fill=fg)
            _draw(fill[0])
            cv.bind("<Button-1>", lambda e: cmd())
            if ctx_cmd:
                cv.bind("<Button-3>", ctx_cmd)
            if not active:
                cv.bind("<Enter>", lambda e: _draw(bg_hov))
                cv.bind("<Leave>", lambda e: _draw(bg_idle))
            return cv

        # show category tabs within the visible range
        end = min(self._tab_offset + max_cat_tabs, total)
        for i in range(self._tab_offset, end):
            cat = self._data[i]
            is_active = (i == self._active)
            _pill(
                self._tab_bar, cat["category"], is_active,
                cmd=lambda i=i: self._switch_tab(i),
                ctx_cmd=lambda e, i=i: self._tab_context_menu(e, i),
                side="left",
            )

        # ▶ scroll button (shown only when there are still tabs to the right)
        if end < total:
            tk.Button(
                self._tab_bar, text="▶",
                command=self._scroll_tabs_right,
                bg=C["bg"], fg=C["text_sub"],
                relief="flat", bd=0,
                font=FONT, cursor="hand2", padx=4, pady=3,
                activebackground=C["card_h"],
                activeforeground=C["text"],
            ).pack(side="left")

        # '+' category add button
        tk.Button(
            self._tab_bar, text="+",
            command=self._add_category,
            bg=C["bg"], fg=C["text_sub"],
            relief="flat", bd=0,
            font=FONT, cursor="hand2", padx=6, pady=3,
            activebackground=C["card_h"],
            activeforeground=C["text"],
        ).pack(side="left", padx=(2, 0))

        # separator (spacer)
        tk.Frame(self._tab_bar, bg=C["bg"]).pack(side="left", fill="x", expand=True)

        # ≡ menu button (rightmost)
        self._menu_btn = tk.Button(
            self._tab_bar, text="≡",
            command=self._show_tabs_menu,
            bg=C["bg"], fg=C["text_sub"],
            relief="flat", bd=0,
            font=FONT, cursor="hand2", padx=8, pady=3,
            activebackground=C["card_h"],
            activeforeground=C["text"],
        )
        self._menu_btn.pack(side="right")

        # show only pinned system tabs (packed in reverse order from the right)
        for key, label, idx in reversed(self._SYSTEM_TABS):
            if key not in self._pinned_tabs:
                continue
            is_active = (self._active == idx)
            _pill(
                self._tab_bar, label, is_active,
                cmd=lambda idx=idx: self._switch_tab(idx),
                ctx_cmd=lambda e, k=key: self._unpin_tab(k),
                side="right",
            )

    def _switch_tab(self, idx: int):
        # Cancel search when leaving Grep tab
        if self._active == -12 and idx != -12:
            self._grep_cancel = True
        self._active = idx
        self._render_tabs()
        self._update_footer()
        self._render_list()
        self._save_config()   # remember the active tab for next launch
        # Start file watcher when entering the Auto tab
        if idx == -9:
            self._ensure_file_watcher()

    def _update_footer(self):
        """Update footer button text/command based on active tab."""
        self._footer_btn3.pack_forget()
        if self._active == -1:
            self._footer_btn.configure(text="+ Add Connection", command=self._add_conn)
            self._footer_btn2.pack_forget()
        elif self._active == -2:
            self._footer_btn.configure(text="+ Add Task", command=self._add_task)
            self._footer_btn2.pack_forget()
            self._footer_btn3.pack(side="left", fill="x", expand=True, padx=(2, 0))
        elif self._active == -3:
            self._footer_btn.configure(text="+ Add Notification", command=self._add_notify_item)
            self._footer_btn2.pack_forget()
        elif self._active == -4:
            self._footer_btn.configure(text="+ Add Bookmark", command=self._add_bookmark)
            self._footer_btn2.configure(text="+ Add Category", command=self._add_bm_category)
            self._footer_btn2.pack(side="left", fill="x", expand=True, padx=(2, 0))
        elif self._active == -9:
            self._footer_btn.configure(text="+ Add Rule", command=self._add_rule)
            self._footer_btn2.pack_forget()
        elif self._active == -12:
            self._footer_btn.configure(text="Search", command=lambda: None)
            self._footer_btn2.pack_forget()
        elif self._active == -13:
            self._footer_btn.configure(text="Open Logs Folder",
                                        command=self._open_logs_folder)
            self._footer_btn2.pack_forget()
        else:
            self._footer_btn.configure(text="+ Add Folder", command=self._add_folder)
            self._footer_btn2.configure(text="+ Add File", command=self._add_file)
            self._footer_btn2.pack(side="left", fill="x", expand=True, padx=(2, 0))

    def _show_tabs_menu(self):
        """Show the drop-down menu for the ≡ button."""
        menu = tk.Menu(self, tearoff=0,
                       bg=C["card"], fg=C["text"],
                       activebackground=C["card_h"],
                       activeforeground=C["text"],
                       relief="flat", font=FONT)

        # if there are many category tabs, show them in a submenu
        if len(self._data) > self._MAX_CAT_TABS:
            cat_menu = tk.Menu(menu, tearoff=0,
                               bg=C["card"], fg=C["text"],
                               activebackground=C["card_h"],
                               activeforeground=C["text"],
                               relief="flat", font=FONT)
            for i, cat in enumerate(self._data):
                is_active = (i == self._active)
                cat_menu.add_command(
                    label=("▸ " if is_active else "  ") + cat["category"],
                    command=lambda i=i: self._switch_tab(i),
                )
            menu.add_cascade(label="Categories...", menu=cat_menu)
            menu.add_separator()

        # list all system tabs (pinned ones get a leading "+" mark)
        for key, label, idx in self._SYSTEM_TABS:
            pinned = key in self._pinned_tabs
            prefix = "+ " if pinned else "  "
            menu.add_command(
                label=f"{prefix}{label}",
                command=lambda idx=idx: self._switch_tab(idx),
            )

        menu.add_separator()

        # pin management submenu
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
        self._popup_menu(menu, btn.winfo_rootx(), btn.winfo_rooty() + btn.winfo_height())

    def _toggle_pin(self, key: str):
        """Toggle the pin state of a tab."""
        if key in self._pinned_tabs:
            self._pinned_tabs.remove(key)
        else:
            self._pinned_tabs.append(key)
        self._save_config()
        self._render_tabs()

    def _scroll_tabs_left(self):
        """Scroll the category tabs to the left."""
        self._tab_offset = max(0, self._tab_offset - 1)
        self._render_tabs()

    def _scroll_tabs_right(self):
        """Scroll the category tabs to the right."""
        self._tab_offset = min(len(self._data) - 1, self._tab_offset + 1)
        self._render_tabs()

    def _unpin_tab(self, key: str):
        """Unpin a tab from the tab bar via right-click."""
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
        self._popup_menu(menu, event.x_root, event.y_root)

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
        elif self._active == -9:
            self._render_rules_list()
        elif self._active == -12:
            self._render_grep_list()
        elif self._active == -13:
            self._render_log_console()
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

        size = self._card_size
        if size == "large":
            # large: single-column layout
            for i, entry in enumerate(folders):
                self._make_card(i, entry["name"], entry["path"],
                                entry.get("type", "folder"))
            return

        # compact / normal: responsive grid layout
        bp = self._width_bp()
        cols = ({"xs": 1, "sm": 2, "md": 3} if size == "compact"
                else {"xs": 1, "sm": 1, "md": 2})[bp]

        grid_wrap = tk.Frame(self._list_frame, bg=C["bg"])
        grid_wrap.pack(fill="x", padx=2, pady=2)
        for c in range(cols):
            grid_wrap.columnconfigure(c, weight=1, uniform="card")

        for i, entry in enumerate(folders):
            r, c = divmod(i, cols)
            self._make_card(i, entry["name"], entry["path"],
                            entry.get("type", "folder"),
                            grid_parent=grid_wrap, grid_pos=(r, c))

    def _make_card(self, idx: int, name: str, path: str, item_type: str = "folder",
                   grid_parent: tk.Frame | None = None,
                   grid_pos: tuple[int, int] | None = None):
        size = self._card_size
        pad_y = {"compact": 1, "normal": 4, "large": 8}.get(size, 4)
        pad_x = {"compact": 6, "normal": 8, "large": 12}.get(size, 8)
        name_font = FONT_SMALL if size == "compact" else FONT_BOLD

        in_grid = grid_parent is not None
        parent = grid_parent if in_grid else self._list_frame
        outer = tk.Frame(parent, bg=C["bg"], highlightthickness=0)
        if in_grid:
            r, c = grid_pos
            gpad = 1 if size == "compact" else 2
            outer.grid(row=r, column=c, sticky="nsew", padx=gpad, pady=gpad)
        else:
            outer.pack(fill="x", pady=(1 if size == "compact" else PAD_ROW_Y),
                       padx=PAD_ROW_X)
        card = tk.Frame(outer, bg=C["card"],
                        pady=pad_y, padx=pad_x, relief="flat", bd=0,
                        highlightthickness=1, highlightbackground=C["border"])
        card.pack(fill="both", expand=True)

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
            card, text="✕",
            command=lambda i=idx: self._remove_folder(i),
            bg=C["card"], fg=C["btn_del"],
            relief="flat", bd=0,
            font=FONT, cursor="hand2",
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

        def _on_enter(e, f=card):
            _set_bg(f, C["card_h"])
            f.configure(highlightbackground=C["accent"])

        def _on_leave(e, f=card):
            _set_bg(f, C["card"])
            f.configure(highlightbackground=C["border"])

        def _bind_open(w):
            if w in extra_btns:
                return
            w.bind("<Button-1>", lambda e, p=path, t=item_type: self._open_item(p, t))
            w.bind("<Button-3>", _show_ctx)
            w.bind("<Enter>",    _on_enter)
            w.bind("<Leave>",    _on_leave)
            w.configure(cursor="hand2")
            for child in w.winfo_children():
                _bind_open(child)

        _bind_open(card)

        # Show hovered path in the bottom status bar
        card.bind("<Enter>", lambda e: self._pathbar_var.set(path), add="+")
        card.bind("<Leave>", lambda e: self._pathbar_var.set(""),   add="+")
        for child in tuple(card.winfo_children()):
            if child not in extra_btns:
                child.bind("<Enter>", lambda e, p=path: self._pathbar_var.set(p), add="+")
                child.bind("<Leave>", lambda e: self._pathbar_var.set(""),        add="+")

    def _card_context_menu(self, event, idx: int, name: str, path: str):
        folders = self._current["folders"]
        menu = tk.Menu(self, tearoff=0,
                       bg=C["card"], fg=C["text"],
                       activebackground=C["card_h"], activeforeground=C["text"],
                       relief="flat", font=FONT)

        # reorder
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

        # Folder entries only: file list scan
        if os.path.isdir(path):
            menu.add_separator()
            menu.add_command(label="Scan Files",
                             command=lambda: FileScanWindow(self, path))

        self._popup_menu(menu, event.x_root, event.y_root)

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

    def _on_conn_search_changed(self, *_):
        """Debounce search-box re-renders: rebuilding every card per
        keystroke is wasteful, so wait until typing pauses."""
        if self._active != -1:
            return
        if self._conn_search_after is not None:
            self.after_cancel(self._conn_search_after)
        self._conn_search_after = self.after(200, self._apply_conn_search)

    def _apply_conn_search(self):
        self._conn_search_after = None
        if self._active == -1:
            self._render_list()

    def _render_terminal_list(self):
        # ── 2-pane layout (left: group sidebar, right: connection list) ──
        pane = tk.Frame(self._list_frame, bg=C["bg"])
        pane.pack(fill="both", expand=True)

        # left sidebar (responsive width: xs=70 / sm=90 / md=110)
        _tw = self._width_bp()
        _sidebar_w = 70 if _tw == "xs" else 90 if _tw == "sm" else 110
        sidebar = tk.Frame(pane, bg=C["card"], width=_sidebar_w,
                           highlightthickness=1, highlightbackground=C["border"])
        sidebar.pack(side="left", fill="y", padx=(0, 4))
        self._render_group_sidebar(sidebar)

        # right main area
        main_frame = tk.Frame(pane, bg=C["bg"])
        main_frame.pack(side="left", fill="both", expand=True)

        # ── toolbar (search / sort) ──────────────────────
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

        # Terminal ping dot ON/OFF toggle
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

        # ── filtering & sorting ──────────────────────
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

        # start reachability probe for each displayed host (if enabled)
        if self._conn_ping_enabled:
            for _, conn in conns_idx:
                host = conn.get("host", "")
                if not host:
                    continue
                port = conn.get("port") or _PING_PORTS.get(conn["protocol"], 0)
                if host not in self._conn_ping_running:
                    self._conn_ping_probe(host, port)

        # ── drag & drop (enabled only when no sort/search/group filter is active) ──
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
            # check if dropped onto a group button in the sidebar
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
        """Render group buttons in the left sidebar."""
        self._sidebar_group_btns: dict = {}

        inner = parent

        def _select_group(grp: str | None):
            self._selected_group = grp
            self._render_list()

        def _make_grp_btn(label: str, grp: str | None):
            is_active = (self._selected_group == grp)
            bg_c = C["accent"] if is_active else C["card"]
            fg_c = "white" if is_active else C["text_sub"]
            b = tk.Button(inner, text=label,
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
            # right-click menu (Rename / Delete)
            menu = tk.Menu(parent, tearoff=0)
            menu.add_command(label="Rename",
                             command=lambda g=grp: self._rename_terminal_group(g))
            menu.add_command(label="Delete",
                             command=lambda g=grp: self._delete_terminal_group(g))
            b.bind("<Button-3>", lambda e, m=menu: self._popup_menu(m, e.x_root, e.y_root))

        # ── drag reordering of group buttons ──────────────────
        dnd: dict = {"src": None, "moved": False}

        def _grp_btns_now() -> list[tk.Button]:
            """Return group buttons in pack order within parent."""
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
            # finalize drop target and reorder data
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

        # + group add button
        add_btn = tk.Button(inner, text="+ Add Group",
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
        card._conn_orig_idx = idx   # retain original index for drag & drop
        card.pack(fill="x", pady=PAD_ROW_Y, padx=PAD_ROW_X)

        left = tk.Frame(card, bg=C["card"])
        left.pack(side="left", fill="both", expand=True)

        proto_color = {"SSH": C["accent"], "RDP": C["accent_dk"],
                       "SMB": C["text_sub"]}.get(conn["protocol"], C["text_sub"])
        # group badge (hidden if not in any group)
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
        # connection statistics
        cnt = conn.get("connect_count", 0)
        last = conn.get("last_connected")
        stats_parts = []
        if cnt:
            stats_parts.append(f"{cnt}x")
        if last:
            stats_parts.append(last[:10])  # date part only from ISO format
        if stats_parts:
            sub_text += "  |  " + "  ".join(stats_parts)
        tk.Label(left, text=sub_text,
                 bg=C["card"], fg=proto_color,
                 font=FONT_SMALL, anchor="w").pack(fill="x")

        del_btn = tk.Button(card, text="x",
                            command=lambda i=idx: self._remove_conn(i),
                            bg=C["card"], fg=C["btn_del"],
                            relief="flat", bd=0,
                            font=FONT, cursor="hand2",
                            activebackground=C["card"], activeforeground=C["btn_del_h"])
        del_btn.pack(side="right", padx=(6, 0))

        edit_btn = tk.Button(card, text="Edit",
                             command=lambda i=idx: self._edit_conn(i),
                             bg=C["card"], fg=C["text_sub"],
                             relief="flat", bd=0,
                             font=FONT_SMALL, cursor="hand2",
                             activebackground=C["card"], activeforeground=C["text"])
        edit_btn.pack(side="right", padx=(0, 2))

        # reachability dot (reflects background probe; hidden when disabled)
        host = conn.get("host", "")
        if self._conn_ping_enabled:
            status = self._conn_ping_cache.get(host)
            dot_color = {"ok": "#4caf50", "fail": C["btn_del"]}.get(status, C["border"])
            dot_cv = tk.Canvas(card, width=12, height=12, bg=C["card"], highlightthickness=0)
            dot_cv.pack(side="right", padx=(0, 6))
            dot_cv.create_oval(1, 1, 11, 11, fill=dot_color, outline="", tags="dot")
            self._conn_ping_dots.setdefault(host, []).append(dot_cv)

        for widget in (card, left) + tuple(left.winfo_children()):
            widget.bind("<Button-1>", lambda e, c=conn: self._connect_server(c))
            widget.bind("<Enter>",    lambda e, f=card: _set_bg(f, C["card_h"]))
            widget.bind("<Leave>",    lambda e, f=card: _set_bg(f, C["card"]))
            widget.configure(cursor="hand2")

    def _conn_ping_probe(self, host: str, port: int):
        """Check TCP reachability in the background and update the dot color."""
        self._conn_ping_running.add(host)

        def _probe():
            try:
                with socket.create_connection((host, port), timeout=1.5):
                    ok = True
            except OSError:
                ok = False
            self._conn_ping_cache[host] = "ok" if ok else "fail"
            self.after(0, lambda: self._conn_ping_update_dots(host))

        threading.Thread(target=_probe, daemon=True).start()

    def _conn_ping_update_dots(self, host: str):
        """Update the dot canvas color based on the probe result."""
        self._conn_ping_running.discard(host)
        status = self._conn_ping_cache.get(host)
        color = "#4caf50" if status == "ok" else C["btn_del"]
        for cv in self._conn_ping_dots.get(host, []):
            try:
                cv.delete("all")
                cv.create_oval(1, 1, 11, 11, fill=color, outline="", tags="dot")
            except tk.TclError:
                pass  # widget already destroyed

    # ── Terminal connection operations ────────────────────

    def _add_conn(self):
        dlg = ConnectionDialog(self, groups=self._terminal_groups)
        if not dlg.result:
            return
        self._conns.extend(dlg.result)
        self._save_conns()
        self._render_list()
        # Connect immediately when only one entry was added
        if len(dlg.result) == 1:
            self._connect_server(dlg.result[0])

    def _remove_conn(self, idx: int):
        name = self._conns[idx]["name"]
        if messagebox.askyesno("Remove", f"Remove \"{name}\"?", parent=self):
            self._conns.pop(idx)
            self._save_conns()
            self._render_list()

    def _edit_conn(self, idx: int):
        dlg = ConnectionDialog(self, initial=self._conns[idx],
                               groups=self._terminal_groups)
        if not dlg.result:
            return
        # Carry over connection statistics
        prev = self._conns[idx]
        result = dlg.result[0]
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
            # update connection statistics (update the actual self._conns entry)
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
        card.pack(fill="x", pady=PAD_ROW_Y, padx=PAD_ROW_X)

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
                  font=FONT, cursor="hand2",
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
            today = datetime.date.today().isoformat()
            task = {
                "event":        action.get("task_event", "Auto Task"),
                "process":      action.get("task_process", ""),
                "content":      f"Auto rule: {rule.get('name', '')}",
                "progress":     0,
                "deadline":     "",
                "work_folders": [],
                "recur":        "none",
                "created_at":   today,
                "updated":      today,
            }
            _log_task_progress(task, 0, created=True)
            self._tasks.append(task)
            self._save_config()
            if self._active == -2:
                self._render_list()

        elif atype == "notify":
            item = {
                "title":        action.get("title", rule.get("name", "Rule Fired")),
                "notes":        action.get("message", ""),
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

    def _render_bookmark_list(self):
        pane = tk.Frame(self._list_frame, bg=C["bg"])
        pane.pack(fill="both", expand=True)

        if not self._bookmarks:
            tk.Label(pane,
                     text="No categories.\nClick \"+ Add Category\" to start.",
                     bg=C["bg"], fg=C["text_sub"],
                     font=FONT_SMALL, justify="center").pack(pady=20)
            return

        # left sidebar
        sidebar = tk.Frame(pane, bg=C["card"], width=110,
                           highlightthickness=1, highlightbackground=C["border"])
        sidebar.pack(side="left", fill="y", padx=(0, 4))
        self._render_bm_sidebar(sidebar)

        # right main area
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
            b.bind("<Button-3>", lambda e, m=menu: self._popup_menu(m, e.x_root, e.y_root))

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
        card.pack(fill="x", pady=PAD_ROW_Y, padx=PAD_ROW_X)

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
                            font=FONT, cursor="hand2",
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

    # ── Grep（ファイル全文検索） ───────────────────────────

    def _render_grep_list(self):
        """Full-text file search UI."""
        import queue as _queue
        f = self._list_frame

        top = tk.Frame(f, bg=C["bg"])
        top.pack(fill="x", padx=6, pady=4)

        # Folder row
        row1 = tk.Frame(top, bg=C["bg"])
        row1.pack(fill="x", pady=(0, 3))
        tk.Label(row1, text="Folder", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, width=7, anchor="w").pack(side="left")
        folder_var = tk.StringVar(value=self._grep_folder)
        tk.Entry(row1, textvariable=folder_var, font=FONT,
                 bg=C["card"], fg=C["text"], relief="flat", bd=1,
                 insertbackground=C["accent"]).pack(side="left", fill="x", expand=True, padx=(0, 4))
        def _browse():
            from tkinter import filedialog
            d = filedialog.askdirectory(initialdir=folder_var.get() or ".")
            if d:
                folder_var.set(d)
        tk.Button(row1, text="Browse", command=_browse,
                  bg=C["card"], fg=C["text_sub"], relief="flat", bd=0,
                  font=FONT_SMALL, cursor="hand2", padx=8, pady=2,
                  activebackground=C["card_h"], activeforeground=C["text"],
                  ).pack(side="left")

        # Query row
        row2 = tk.Frame(top, bg=C["bg"])
        row2.pack(fill="x", pady=(0, 3))
        tk.Label(row2, text="Query", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, width=7, anchor="w").pack(side="left")
        query_var = tk.StringVar(value=self._grep_query)
        query_e = ttk.Combobox(row2, textvariable=query_var, font=FONT,
                               values=self._grep_history)
        query_e.pack(side="left", fill="x", expand=True, padx=(0, 4))
        case_var = tk.BooleanVar(value=True)
        tk.Checkbutton(row2, text="Ignore case", variable=case_var,
                       bg=C["bg"], fg=C["text_sub"], font=FONT_SMALL,
                       selectcolor=C["card"], activebackground=C["bg"],
                       cursor="hand2").pack(side="left")

        # Match mode row
        row_mode = tk.Frame(top, bg=C["bg"])
        row_mode.pack(fill="x", pady=(0, 3))
        tk.Label(row_mode, text="Match", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, width=7, anchor="w").pack(side="left")
        mode_var = tk.StringVar(value="contains")
        _rb_cfg = dict(bg=C["bg"], fg=C["text_sub"], font=FONT_SMALL,
                       selectcolor=C["card"], activebackground=C["bg"],
                       cursor="hand2", variable=mode_var)
        tk.Radiobutton(row_mode, text="Contains",   value="contains",  **_rb_cfg).pack(side="left")
        tk.Radiobutton(row_mode, text="Starts with", value="starts",   **_rb_cfg).pack(side="left", padx=(8, 0))
        tk.Radiobutton(row_mode, text="Ends with",   value="ends",     **_rb_cfg).pack(side="left", padx=(8, 0))

        # Extension filter row
        row_ext = tk.Frame(top, bg=C["bg"])
        row_ext.pack(fill="x", pady=(0, 3))
        tk.Label(row_ext, text="Ext", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, width=7, anchor="w").pack(side="left")
        ext_var = tk.StringVar(value=self._grep_ext)
        tk.Entry(row_ext, textvariable=ext_var, font=FONT,
                 bg=C["card"], fg=C["text"], relief="flat", bd=1,
                 insertbackground=C["accent"]).pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Label(row_ext, text="e.g.  .py .txt .md  (blank = all)",
                 bg=C["bg"], fg=C["text_sub"], font=FONT_SMALL).pack(side="left")

        # Button / status row
        row3 = tk.Frame(top, bg=C["bg"])
        row3.pack(fill="x")
        status_var = tk.StringVar(value="Enter folder and query, then press Search.")
        tk.Label(row3, textvariable=status_var, bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="w").pack(side="left", fill="x", expand=True)

        tk.Frame(f, bg=C["border"], height=1).pack(fill="x")

        # Results scroll area
        res_outer = tk.Frame(f, bg=C["bg"])
        res_outer.pack(fill="both", expand=True)
        res_cv = tk.Canvas(res_outer, bg=C["bg"], highlightthickness=0)
        res_vsb = ttk.Scrollbar(res_outer, orient="vertical",
                                style="Gem.Vertical.TScrollbar",
                                command=res_cv.yview)
        res_frame = tk.Frame(res_cv, bg=C["bg"])
        res_frame.bind("<Configure>",
                       lambda e: res_cv.configure(scrollregion=res_cv.bbox("all")))
        _win = res_cv.create_window((0, 0), window=res_frame, anchor="nw")
        _res_sb_pack = dict(side="right", fill="y")
        res_cv.configure(yscrollcommand=lambda lo, hi:
                         _autohide_scrollbar(res_vsb, lo, hi, _res_sb_pack))
        res_cv.bind("<Configure>", lambda e: res_cv.itemconfigure(_win, width=e.width))
        # wheel scrolling is handled by the global <MouseWheel> handler,
        # which scrolls the nearest scrollable canvas under the pointer
        res_cv.pack(side="left", fill="both", expand=True)
        # res_vsb is shown by _autohide_scrollbar only when results overflow

        q = _queue.Queue()
        self._grep_cancel = False
        results: list[dict] = []   # all matches of the last run (for export)

        def _copy(text: str):
            self.clipboard_clear()
            self.clipboard_append(text)

        def _result_menu(parent, items):
            menu = tk.Menu(parent, tearoff=0, bg=C["card"], fg=C["text"],
                           activebackground=C["card_h"], activeforeground=C["text"],
                           relief="flat", font=FONT_SMALL)
            for label, cmd in items:
                menu.add_command(label=label, command=cmd)
            return menu

        def _append_file_header(rel_path, abs_path):
            hdr = tk.Frame(res_frame, bg=C["bg"])
            hdr.pack(fill="x", padx=4, pady=(8, 1))
            lbl = tk.Label(hdr, text=rel_path, bg=C["bg"], fg=C["accent"],
                           font=FONT_BOLD, anchor="w", cursor="hand2")
            lbl.pack(side="left", fill="x", expand=True)
            menu = _result_menu(hdr, [
                ("Open folder", lambda: os.startfile(os.path.dirname(abs_path))),
                ("Copy path",   lambda: _copy(abs_path)),
            ])
            lbl.bind("<Button-1>", lambda e: _open_in_editor(abs_path))
            lbl.bind("<Button-3>", lambda e: self._popup_menu(menu, e.x_root, e.y_root))

        def _append_match(m: dict):
            text, mstart, mlen = m["text"], m["mstart"], m["mlen"]
            # window long lines so the hit stays visible
            if mstart > 60:
                cut = mstart - 40
                text = "…" + text[cut:]
                mstart -= cut - 1
            prefix = text[:mstart]
            hit    = text[mstart:mstart + mlen]
            suffix = text[mstart + mlen:][:160]

            row = tk.Frame(res_frame, bg=C["card"],
                           highlightthickness=1, highlightbackground=C["border"])
            row.pack(fill="x", padx=4, pady=1)
            mono = ("Consolas", max(7, FONT_BASE - 2))
            tk.Label(row, text=f"{m['lineno']:5d}", bg=C["card"], fg=C["text_sub"],
                     font=mono, anchor="e", width=6).pack(side="left")
            tk.Frame(row, bg=C["border"], width=1).pack(side="left", fill="y")
            tk.Label(row, text=prefix, bg=C["card"], fg=C["text"],
                     font=mono, anchor="w").pack(side="left", padx=(6, 0))
            if hit:
                tk.Label(row, text=hit, bg=C["accent"], fg="white",
                         font=mono, anchor="w").pack(side="left")
            tk.Label(row, text=suffix, bg=C["card"], fg=C["text"],
                     font=mono, anchor="w").pack(side="left", fill="x", expand=True)

            path, ln = m["abs"], m["lineno"]
            menu = _result_menu(row, [
                ("Copy line",      lambda: _copy(m["text"])),
                ("Copy path:line", lambda: _copy(f"{path}:{ln}")),
                ("Open folder",    lambda: os.startfile(os.path.dirname(path))),
            ])
            for w in (row,) + tuple(row.winfo_children()):
                w.bind("<Button-1>", lambda e: _open_in_editor(path, ln))
                w.bind("<Button-3>", lambda e: self._popup_menu(menu, e.x_root, e.y_root))
                w.configure(cursor="hand2")

        def _poll():
            try:
                while True:
                    item = q.get_nowait()
                    kind = item[0]
                    if kind == "file":
                        _append_file_header(item[1], item[2])
                    elif kind == "match":
                        results.append(item[1])
                        _append_match(item[1])
                    elif kind == "status":
                        status_var.set(item[1])
                    elif kind == "done":
                        _on_done(item[1], item[2], item[3], item[4])
                        return
            except _queue.Empty:
                pass
            if self._grep_running:
                self.after(60, _poll)

        def _on_done(cancelled: bool, file_count: int, match_count: int,
                     limited: bool):
            self._grep_running = False
            search_btn.configure(text="Search", command=_start_search,
                                 bg=C["accent"])
            export_btn.configure(state="normal" if results else "disabled")
            if cancelled:
                status_var.set(f"Cancelled — {file_count} file(s), {match_count} match(es)")
            elif match_count == 0:
                status_var.set("No matches found.")
                tk.Label(res_frame, text="No matches found.",
                         bg=C["bg"], fg=C["text_sub"], font=FONT_SMALL).pack(pady=20)
            elif limited:
                status_var.set(f"Stopped at {match_count} matches (limit) — "
                               f"{file_count} file(s)")
            else:
                status_var.set(f"Done — {file_count} file(s), {match_count} match(es)")

        def _parse_exts(raw: str) -> set[str]:
            """Parse extension filter string into a set of lowercased dotted exts."""
            exts = set()
            for token in raw.replace(",", " ").split():
                token = token.lower()
                if not token.startswith("."):
                    token = "." + token
                exts.add(token)
            return exts

        MAX_MATCHES   = 500                 # widget count stays bounded
        MAX_FILE_SIZE = 10 * 1024 * 1024    # skip files larger than 10MB

        def _search_thread(folder: str, query: str, ignore_case: bool,
                           exts: set[str], mode: str):
            file_count = 0
            match_count = 0
            limited = False
            cq = query.lower() if ignore_case else query
            try:
                for root, dirs, files in os.walk(folder):
                    if self._grep_cancel or limited:
                        break
                    dirs[:] = sorted(d for d in dirs
                                     if not d.startswith('.')
                                     and d.lower() not in _GREP_SKIP_DIRS)
                    for filename in sorted(files):
                        if self._grep_cancel or limited:
                            break
                        # Extension filter
                        if exts:
                            _, ext = os.path.splitext(filename)
                            if ext.lower() not in exts:
                                continue
                        filepath = os.path.join(root, filename)
                        try:
                            if os.path.getsize(filepath) > MAX_FILE_SIZE:
                                continue
                            with open(filepath, "rb") as fh:
                                # NUL byte in the head = binary; latin-1 below
                                # would otherwise happily "decode" any file
                                if b"\x00" in fh.read(8192):
                                    continue
                        except OSError:
                            continue
                        rel = os.path.relpath(filepath, folder)
                        file_matches: list[dict] = []
                        try:
                            lines = None
                            for enc in ("utf-8", "shift-jis", "latin-1"):
                                try:
                                    with open(filepath, "r", encoding=enc, errors="strict") as fh:
                                        lines = fh.readlines()
                                    break
                                except (UnicodeDecodeError, LookupError, OSError):
                                    continue
                            if lines is None:
                                continue
                            for lineno, line in enumerate(lines, 1):
                                raw = line.rstrip("\r\n")
                                cl  = raw.lower() if ignore_case else raw
                                mstart = -1
                                if mode == "starts":
                                    ls = cl.lstrip()
                                    if ls.startswith(cq):
                                        mstart = len(cl) - len(ls)
                                elif mode == "ends":
                                    rs = cl.rstrip()
                                    if rs.endswith(cq):
                                        mstart = len(rs) - len(cq)
                                else:
                                    mstart = cl.find(cq)
                                if mstart >= 0:
                                    file_matches.append(
                                        {"rel": rel, "abs": filepath,
                                         "lineno": lineno, "text": raw,
                                         "mstart": mstart, "mlen": len(cq)})
                        except Exception:
                            continue
                        if file_matches:
                            room = MAX_MATCHES - match_count
                            if len(file_matches) >= room:
                                file_matches = file_matches[:room]
                                limited = True
                            file_count += 1
                            match_count += len(file_matches)
                            q.put(("file", rel, filepath))
                            for m in file_matches:
                                q.put(("match", m))
                            q.put(("status", f"Searching… {file_count} file(s), {match_count} match(es)"))
            finally:
                q.put(("done", self._grep_cancel, file_count, match_count, limited))

        def _start_search():
            folder = folder_var.get().strip()
            query  = query_var.get()
            if not folder:
                status_var.set("Please specify a folder.")
                return
            if not query:
                status_var.set("Please enter a search query.")
                return
            if not os.path.isdir(folder):
                status_var.set("Folder does not exist.")
                return
            self._grep_folder = folder
            self._grep_query  = query
            self._grep_ext    = ext_var.get().strip()
            # query history: newest first, deduplicated, max 10
            h = self._grep_history
            if query in h:
                h.remove(query)
            h.insert(0, query)
            del h[10:]
            query_e["values"] = h
            self._save_config()
            for w in res_frame.winfo_children():
                w.destroy()
            results.clear()
            export_btn.configure(state="disabled")
            self._grep_cancel  = False
            self._grep_running = True
            search_btn.configure(text="Cancel", command=_cancel_search,
                                 bg=C["btn_del"])
            status_var.set("Searching…")
            exts = _parse_exts(self._grep_ext)
            threading.Thread(target=_search_thread,
                             args=(folder, query, case_var.get(), exts, mode_var.get()),
                             daemon=True).start()
            self.after(60, _poll)

        def _cancel_search():
            self._grep_cancel = True
            status_var.set("Cancelling…")

        def _export_results():
            if not results:
                return
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = filedialog.asksaveasfilename(
                parent=self, title="Export search results",
                defaultextension=".txt",
                initialfile=f"search_{ts}.txt",
                filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"),
                           ("All files", "*.*")])
            if not path:
                return
            if path.lower().endswith(".csv"):
                import csv
                with open(path, "w", newline="", encoding="utf-8-sig") as fh:
                    w = csv.writer(fh)
                    w.writerow(["file", "line", "text"])
                    for m in results:
                        w.writerow([m["abs"], m["lineno"], m["text"]])
            else:
                out = [f"Query : {self._grep_query}",
                       f"Folder: {self._grep_folder}",
                       f"Date  : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
                       ""]
                cur = None
                for m in results:
                    if m["rel"] != cur:
                        cur = m["rel"]
                        out.append(cur)
                    out.append(f"  {m['lineno']:5d}: {m['text']}")
                Path(path).write_text("\n".join(out), encoding="utf-8-sig")
            status_var.set(f"Exported {len(results)} match(es).")

        search_btn = tk.Button(row3, text="Search", command=_start_search,
                               bg=C["accent"], fg="white", relief="flat", bd=0,
                               font=FONT_BOLD, cursor="hand2", padx=16, pady=3,
                               activebackground=C["accent_dk"], activeforeground="white")
        search_btn.pack(side="right")
        export_btn = tk.Button(row3, text="Export", command=_export_results,
                               state="disabled",
                               bg=C["card"], fg=C["text_sub"], relief="flat", bd=0,
                               font=FONT_SMALL, cursor="hand2", padx=10, pady=4,
                               activebackground=C["card_h"], activeforeground=C["text"])
        export_btn.pack(side="right", padx=(0, 6))
        query_e.bind("<Return>", lambda e: _start_search())
        query_e.focus_set()

    # ── Log console (real-time tail viewer) ────────────────

    def _open_logs_folder(self):
        LOG_DIR.mkdir(exist_ok=True)
        os.startfile(LOG_DIR)

    def _render_log_console(self):
        """Tail the selected terminal session log, highlighting error/warning lines."""
        f = self._list_frame

        log_files = (sorted(LOG_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
                     if LOG_DIR.exists() else [])
        names = [p.name for p in log_files]

        if not names:
            tk.Label(f, text="No logs found.", bg=C["bg"], fg=C["text_sub"],
                     font=FONT_SMALL, justify="center").pack(pady=20)
            return

        if self._log_tail_file not in names:
            self._log_tail_file = names[0]
            self._log_tail_pos = 0

        top = tk.Frame(f, bg=C["bg"])
        top.pack(fill="x", padx=6, pady=4)
        tk.Label(top, text="Log", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="w").pack(side="left", padx=(0, 4))
        file_var = tk.StringVar(value=self._log_tail_file)
        combo = ttk.Combobox(top, textvariable=file_var, values=names,
                              state="readonly", font=FONT_SMALL)
        combo.pack(side="left", fill="x", expand=True)

        tk.Frame(f, bg=C["border"], height=1).pack(fill="x")

        txt_frame = tk.Frame(f, bg=C["bg"])
        txt_frame.pack(fill="both", expand=True)
        txt = tk.Text(txt_frame, bg=C["card"], fg=C["text"], font=FONT_MONO,
                       wrap="none", state="disabled", relief="flat", bd=0,
                       padx=6, pady=4)
        vsb = ttk.Scrollbar(txt_frame, orient="vertical",
                            style="Gem.Vertical.TScrollbar", command=txt.yview)
        txt.configure(yscrollcommand=lambda lo, hi:
                      _autohide_scrollbar(vsb, lo, hi, dict(side="right", fill="y")))
        txt.pack(side="left", fill="both", expand=True)
        txt.tag_configure("err", foreground=C["btn_del"])
        txt.tag_configure("warn", foreground="#FFB74D")

        ansi_re = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

        def _append(chunk: str):
            txt.configure(state="normal")
            for line in chunk.splitlines(True):
                low = line.lower()
                if "error" in low or "fatal" in low or "traceback" in low:
                    txt.insert("end", line, "err")
                elif "warn" in low:
                    txt.insert("end", line, "warn")
                else:
                    txt.insert("end", line)
            txt.see("end")
            txt.configure(state="disabled")

        def _reload():
            txt.configure(state="normal")
            txt.delete("1.0", "end")
            txt.configure(state="disabled")
            path = LOG_DIR / self._log_tail_file
            try:
                data = path.read_text(encoding="utf-8", errors="replace")
                self._log_tail_pos = path.stat().st_size
            except OSError:
                self._log_tail_pos = 0
                return
            _append(ansi_re.sub("", data))

        def _on_select(_e=None):
            self._log_tail_file = file_var.get()
            self._log_tail_pos = 0
            _reload()

        combo.bind("<<ComboboxSelected>>", _on_select)

        def _poll():
            if self._active != -13 or not txt.winfo_exists():
                return   # tab left or widget destroyed: stop polling
            path = LOG_DIR / self._log_tail_file
            try:
                size = path.stat().st_size
                if size < self._log_tail_pos:
                    self._log_tail_pos = 0   # file truncated or rotated
                if size > self._log_tail_pos:
                    with open(path, "r", encoding="utf-8", errors="replace") as fh:
                        fh.seek(self._log_tail_pos)
                        chunk = fh.read()
                    self._log_tail_pos = size
                    _append(ansi_re.sub("", chunk))
            except OSError:
                pass
            self.after(1000, _poll)

        _reload()
        _poll()

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
        style.map("TaskTree.Treeview.Heading",
                  background=[("active", C["card_h"]), ("!active", C["tab_inact"])],
                  foreground=[("active", C["text"]),   ("!active", C["text"])])
        style.map("TaskTree.Treeview",
                  background=[("selected", C["card_h"])],
                  foreground=[("selected", C["text"])])


        # ── Quick add row (list view only) ──
        # A single rounded "card" holding an event selector, a task entry
        # (with placeholder) and a pill-shaped add button. Type a task and
        # press Enter to add instantly; the full TaskDialog stays for details.
        qa_outer = tk.Frame(self._list_frame, bg=C["bg"])
        qa_outer.pack(fill="x", padx=4, pady=(6, 4))

        card = tk.Frame(qa_outer, bg=C["card"],
                        highlightthickness=1, highlightbackground=C["border"])
        card.pack(fill="x")

        existing_events = self._event_names()
        default_event = (getattr(self, "_task_quick_event", "")
                         or (self._tasks[-1]["event"] if self._tasks else ""))
        qa_event   = tk.StringVar(value=default_event)
        qa_content = tk.StringVar()

        style = ttk.Style()
        style.configure("QuickAdd.TCombobox",
                        fieldbackground=C["card"], background=C["card"],
                        foreground=C["text"], arrowcolor=C["text_sub"])
        ev_cb = ttk.Combobox(card, textvariable=qa_event, values=existing_events,
                             width=10, font=FONT, style="QuickAdd.TCombobox")
        ev_cb.pack(side="left", padx=(8, 8), pady=6)

        # thin vertical divider between the event selector and the entry
        tk.Frame(card, bg=C["border"], width=1).pack(side="left", fill="y", pady=7)

        content_entry = tk.Entry(card, textvariable=qa_content, font=FONT,
                                 bg=C["card"], fg=C["text"], relief="flat", bd=0,
                                 insertbackground=C["accent"])
        content_entry.pack(side="left", fill="x", expand=True,
                           padx=(10, 8), pady=6, ipady=2)

        # ── placeholder text (tk.Entry has no native placeholder) ──
        PLACEHOLDER = "Type a task and press Enter to add"

        def _show_ph():
            qa_content.set(PLACEHOLDER)
            content_entry.configure(fg=C["text_sub"])
            content_entry._ph = True

        def _clear_ph(_e=None):
            if getattr(content_entry, "_ph", False):
                qa_content.set("")
                content_entry.configure(fg=C["text"])
                content_entry._ph = False

        def _restore_ph(_e=None):
            if not qa_content.get():
                _show_ph()

        _show_ph()
        content_entry.bind("<FocusIn>", _clear_ph, add="+")
        content_entry.bind("<FocusOut>", _restore_ph, add="+")

        # ── focus ring: highlight the card border while editing ──
        def _focus_on(_e=None):
            card.configure(highlightbackground=C["accent"])

        def _focus_off(_e=None):
            card.configure(highlightbackground=C["border"])

        for w in (ev_cb, content_entry):
            w.bind("<FocusIn>",  _focus_on,  add="+")
            w.bind("<FocusOut>", _focus_off, add="+")

        def _quick_add(_e=None):
            if getattr(content_entry, "_ph", False):
                return
            txt = qa_content.get().strip()
            if not txt:
                return
            ev = qa_event.get().strip() or "General"
            self._task_quick_event = ev   # remember group for the next add
            today = datetime.date.today().isoformat()
            new_task = {
                "event":        ev,
                "process":      txt,
                "content":      "",
                "progress":     0,
                "deadline":     "",
                "work_folders": [],
                "recur":        "none",
                "created_at":   today,
                "updated":      today,
            }
            _log_task_progress(new_task, 0, created=True)
            self._tasks.append(new_task)
            self._save_tasks()
            self._task_quick_focus = True   # refocus entry after re-render
            self._render_list()

        content_entry.bind("<Return>", _quick_add)
        ev_cb.bind("<Return>", lambda e: content_entry.focus_set())

        # ── pill-shaped add button (rounded canvas) ──
        _btxt  = "+ Add"
        _bfont = FONT_SMALL_BOLD
        _bm    = tkfont.Font(family=_bfont[0], size=_bfont[1], weight="bold")
        _bw    = _bm.measure(_btxt) + 26
        _bh    = _bm.metrics("linespace") + 12
        add_cv = tk.Canvas(card, width=_bw, height=_bh, bg=C["card"],
                           highlightthickness=0, cursor="hand2")
        add_cv.pack(side="left", padx=(0, 8), pady=6)

        def _draw_add(fill):
            add_cv.delete("all")
            _draw_rounded_rect(add_cv, 0, 0, _bw, _bh, min(_bh // 2, 12),
                               fill=fill, outline="")
            add_cv.create_text(_bw // 2, _bh // 2, text=_btxt,
                               font=_bfont, fill="white")

        _draw_add(C["accent"])
        add_cv.bind("<Button-1>", lambda e: _quick_add())
        add_cv.bind("<Enter>",    lambda e: _draw_add(C["accent_dk"]))
        add_cv.bind("<Leave>",    lambda e: _draw_add(C["accent"]))

        if getattr(self, "_task_quick_focus", False):
            self._task_quick_focus = False
            content_entry.focus_set()

        # ── visibility filter (archived always hidden; done optional) ──
        active_tasks = [(i, t) for i, t in enumerate(self._tasks)
                        if not t.get("archived")]
        done_count = sum(1 for _, t in active_tasks
                         if t.get("progress", 0) >= 100)
        visible = ([(i, t) for i, t in active_tasks
                    if t.get("progress", 0) < 100]
                   if self._task_hide_done else active_tasks)

        if self._tasks:
            filter_row = tk.Frame(self._list_frame, bg=C["bg"])
            filter_row.pack(fill="x", padx=6)

            tk.Button(filter_row, text="History",
                      command=self._open_task_history,
                      bg=C["tab_inact"], fg=C["text_sub"], relief="flat", bd=0,
                      font=FONT_SMALL, cursor="hand2", padx=8, pady=1,
                      activebackground=C["card_h"], activeforeground=C["text"],
                      ).pack(side="right")

            if active_tasks:
                hd_var = tk.BooleanVar(value=self._task_hide_done)

                def _toggle_hide_done():
                    self._task_hide_done = hd_var.get()
                    self._save_config()
                    self._render_list()

                hd_text = "Hide done"
                if self._task_hide_done and done_count:
                    hd_text += f"  ({done_count} hidden)"
                tk.Checkbutton(filter_row, text=hd_text, variable=hd_var,
                               command=_toggle_hide_done,
                               bg=C["bg"], fg=C["text_sub"], selectcolor=C["card"],
                               activebackground=C["bg"], font=FONT_SMALL,
                               cursor="hand2").pack(side="left")

        # work-in-progress bar
        self._work_bar_lbl = None
        if self._work_active is not None:
            wa   = self._work_active
            task = self._tasks[wa["task_idx"]]
            elapsed = (datetime.datetime.now() - wa["start"]).total_seconds()
            bar = tk.Frame(self._list_frame, bg=C["accent_lt"])
            bar.pack(fill="x", padx=2, pady=(2, 0))
            self._work_bar_lbl = tk.Label(
                bar,
                text=f"{task.get('process', '')}  Working...  {_fmt_duration(elapsed)}",
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

        if not visible:
            msg = ("All tasks are done (hidden)."
                   if self._task_hide_done and done_count
                   else "No tasks to show.")
            tk.Label(self._list_frame, text=msg,
                     bg=C["bg"], fg=C["text_sub"],
                     font=FONT_SMALL, justify="center").pack(pady=20)
            self._render_task_archived_section()
            return

        # group by event name (preserve insertion order)
        groups: dict[str, list[tuple[int, dict]]] = {}
        for i, task in visible:
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

        n_rows = len(visible) + len(groups)
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
                            selectmode="extended")   # Ctrl/Shift-click for multi-select

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

        def _resize_tree_cols(w: int):
            """Switch Treeview columns based on widget width."""
            if w < 340:
                # xs: Event + Process only
                tree["displaycolumns"] = ("process",)
                tree.column("#0",      width=max(60, w // 2), stretch=True)
                tree.column("process", width=max(60, w // 2), stretch=True)
            elif w < 480:
                # sm: Event + Process + Progress + Deadline
                tree["displaycolumns"] = ("process", "progress", "deadline")
                tree.column("#0",       width=max(70, w // 3), stretch=True)
                tree.column("process",  width=max(70, w // 2), stretch=False)
                tree.column("progress", width=55, stretch=False)
                tree.column("deadline", width=76, stretch=False)
            else:
                # md: all columns visible
                tree["displaycolumns"] = cols
                tree.column("#0",        width=100, minwidth=70,  stretch=True)
                tree.column("process",   width=170, minwidth=70,  stretch=False)
                tree.column("content",   width=120, minwidth=60,  stretch=True)
                tree.column("progress",  width=58,  minwidth=45,  stretch=False)
                tree.column("deadline",  width=82,  minwidth=70,  stretch=False)
                tree.column("remaining", width=68,  minwidth=55,  stretch=False)
                tree.column("updated",   width=82,  minwidth=70,  stretch=False)

        vsb = ttk.Scrollbar(tree_wrap, orient="vertical",
                            style="Gem.Vertical.TScrollbar", command=tree.yview)
        _vsb_pack = dict(side="right", fill="y")
        tree.configure(yscrollcommand=lambda lo, hi:
                       _autohide_scrollbar(vsb, lo, hi, _vsb_pack))
        tree.pack(side="left", fill="both", expand=True)
        # vsb is shown by _autohide_scrollbar only when rows overflow

        # Re-adjust columns on widget width change
        tree_wrap.bind("<Configure>", lambda e: _resize_tree_cols(e.width))
        # Apply initial column layout
        try:
            _resize_tree_cols(self.winfo_width())
        except Exception:
            pass

        # row color by progress (red=critical / yellow=caution / green=ok)
        _dark = self._theme in ("dark", "claude", "scarlet", "ocean",
                                "cyber", "synthwave", "matrix")
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
                _subtasks = task.get("subtasks", [])
                task_iid = str(i)
                tree.insert(parent, "end", iid=task_iid,
                            text="", open=bool(_subtasks),
                            tags=(_progress_tag(pct),),
                            values=(process_disp, content,
                                    f"{pct}%", deadline, remaining, updated))
                # insert subtasks as child rows
                for si, sub in enumerate(_subtasks):
                    sub_pct = 100 if sub.get("done") else sub.get("progress", 0)
                    sub_dl  = sub.get("deadline", "")
                    sub_rem = _days_left_str(sub_dl)
                    # title goes in the process column (under the parent's
                    # name), not in #0 which sits left of the parent
                    tree.insert(task_iid, "end", iid=f"{i}.{si}",
                                text="",
                                tags=(_progress_tag(sub_pct),),
                                values=(f"└ {sub.get('title', '')}", "",
                                        f"{sub_pct}%", sub_dl, sub_rem, ""))

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

        def _clear_detail():
            for fr in (folder_frame, memo_row, work_row):
                for w in fr.winfo_children():
                    w.destroy()

        def on_select(_e):
            sel = tree.selection()
            if not sel:
                return
            iid = sel[0]

            # ── when a subtask row is selected ──────────────────────
            if "." in iid:
                task_idx, sub_idx = map(int, iid.split("."))
                sub = self._tasks[task_idx]["subtasks"][sub_idx]
                sub_dl  = sub.get("deadline", "")
                sub_rem = _days_left_str(sub_dl)
                dl_part = f"  Deadline: {sub_dl}  ({sub_rem})" if sub_dl else ""
                pct     = 100 if sub.get("done") else sub.get("progress", 0)
                done_str = "  ✓ Done" if sub.get("done") else ""
                detail_lbl.configure(fg=C["text"], text=(
                    f"[subtask]  {sub.get('title', '')}"
                    f"  {pct}%{dl_part}{done_str}"
                ))
                _clear_detail()
                return

            # ── skip non-task rows (event parent rows) ────────────
            try:
                idx = int(iid)
            except ValueError:
                return

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

            # work folder buttons (rebuilt each time)
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

            # work time log row (rebuilt each time)
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
        tree.bind("<Double-1>",  lambda e: self._task_tree_edit(tree, e))
        tree.bind("<Button-3>",  lambda e: self._task_tree_menu(e, tree))
        tree.bind("<Delete>",    lambda e: self._task_tree_delete(tree))

        # ── Drag & drop reordering ──
        dnd: dict = {"src": None, "moved": False}

        def _row_type(iid: str) -> str:
            """Return the type of iid: 'event' | 'task' | 'subtask'"""
            if "." in iid:
                return "subtask"
            try:
                int(iid)
                return "task"
            except ValueError:
                return "event"

        def on_dnd_press(e):
            region = tree.identify_region(e.x, e.y)
            if region not in ("cell", "tree"):
                return
            item = tree.identify_row(e.y)
            dnd["src"] = item if (item and _row_type(item) != "event") else None
            dnd["moved"] = False

        def on_dnd_motion(e):
            src = dnd["src"]
            if not src:
                return
            target = tree.identify_row(e.y)
            if not target or target == src:
                return
            src_type = _row_type(src)
            tgt_type = _row_type(target)
            bbox = tree.bbox(target)
            if not bbox:
                return
            tgt_idx = tree.index(target)
            if e.y >= bbox[1] + bbox[3] // 2:
                tgt_idx += 1
            if src_type == "task" and tgt_type == "task":
                # task row → move only within the same group
                if tree.parent(src) != tree.parent(target):
                    return
                tree.move(src, tree.parent(src), tgt_idx)
                dnd["moved"] = True
            elif src_type == "subtask" and tgt_type == "subtask":
                # subtask row → move only within the same task
                if tree.parent(src) != tree.parent(target):
                    return
                tree.move(src, tree.parent(src), tgt_idx)
                dnd["moved"] = True
            elif src_type == "event" and tgt_type == "event":
                # event row → reorder whole groups
                tree.move(src, "", tgt_idx)
                dnd["moved"] = True

        def on_dnd_release(e):
            src = dnd["src"]
            dnd["src"] = None
            if not src or not dnd["moved"]:
                return
            src_type = _row_type(src)
            if src_type == "subtask":
                # rebuild subtask order
                task_iid = tree.parent(src)
                task_idx = int(task_iid)
                old_subs = self._tasks[task_idx].get("subtasks", [])
                new_subs = []
                for sub_iid in tree.get_children(task_iid):
                    _, si = map(int, sub_iid.split("."))
                    new_subs.append(old_subs[si])
                self._tasks[task_idx]["subtasks"] = new_subs
                self._save_tasks()
                self._render_list()
            else:
                # rebuild task/event order from the tree; tasks not shown
                # there (archived / hidden done) must be kept, appended at
                # the end in their original order
                vis_idx = []
                for ev_row in tree.get_children():
                    for child in tree.get_children(ev_row):
                        vis_idx.append(int(child))
                vis_set = set(vis_idx)
                new_tasks = [self._tasks[i] for i in vis_idx]
                new_tasks += [t for j, t in enumerate(self._tasks)
                              if j not in vis_set]
                self._tasks[:] = new_tasks
                self._task_sort = {"col": None, "reverse": False}
                self._save_tasks()
                self._render_list()

        tree.bind("<ButtonPress-1>",   on_dnd_press)
        tree.bind("<B1-Motion>",       on_dnd_motion)
        tree.bind("<ButtonRelease-1>", on_dnd_release)

        # select the task requested from the command palette, if any
        pending = self._task_select_pending
        if pending is not None:
            self._task_select_pending = None
            if tree.exists(str(pending)):
                tree.selection_set(str(pending))
                tree.see(str(pending))

        self._render_task_archived_section()

    def _task_tree_edit(self, tree, event=None):
        if event is not None:
            # rapid clicks on the expand/collapse arrow arrive as Double-1;
            # they must not open an editor for whatever row was selected
            if "indicator" in tree.identify("element", event.x, event.y):
                return "break"
            row = tree.identify_row(event.y)
            if not row:
                return   # double-click on empty space below the rows
            iid = row    # edit the row under the cursor, not a stale selection
        else:
            sel = tree.selection()
            if not sel:
                return
            iid = sel[0]
        if "." in iid:
            task_idx, sub_idx = map(int, iid.split("."))
            self._edit_subtask(task_idx, sub_idx)
            return
        try:
            idx = int(iid)
            self._edit_task(idx)
        except ValueError:
            # double-click on event parent row → rename
            self._rename_event(tree.item(iid, "text"))

    def _task_tree_delete(self, tree):
        """Delete all selected tasks/subtasks at once (Delete key or menu).

        Supports multi-select (Ctrl/Shift-click): collect every selected row,
        confirm once, then remove them in a single batch.
        """
        sel = tree.selection()
        if not sel:
            return
        task_idxs: set[int] = set()
        sub_pairs: list[tuple[int, int]] = []   # (task_idx, sub_idx)
        for iid in sel:
            if "." in iid:
                ti, si = map(int, iid.split("."))
                sub_pairs.append((ti, si))
            else:
                try:
                    task_idxs.add(int(iid))
                except ValueError:
                    pass   # event parent row — skip
        # subtasks whose parent task is also being deleted are redundant
        sub_pairs = [(ti, si) for (ti, si) in sub_pairs if ti not in task_idxs]
        if not task_idxs and not sub_pairs:
            return

        parts = []
        if task_idxs:
            parts.append(f"{len(task_idxs)} task(s)")
        if sub_pairs:
            parts.append(f"{len(sub_pairs)} subtask(s)")
        if not messagebox.askyesno(
                "Remove", f"Remove {' and '.join(parts)}?", parent=self):
            return

        # delete subtasks first (descending per task, original indices still valid)
        by_task: dict[int, list[int]] = {}
        for ti, si in sub_pairs:
            by_task.setdefault(ti, []).append(si)
        for ti, sis in by_task.items():
            subs = self._tasks[ti].get("subtasks", [])
            for si in sorted(sis, reverse=True):
                if 0 <= si < len(subs):
                    subs.pop(si)
        # then delete whole tasks (descending index so earlier indices stay valid)
        for ti in sorted(task_idxs, reverse=True):
            if 0 <= ti < len(self._tasks):
                self._tasks.pop(ti)

        self._save_tasks()
        self._render_list()

    def _task_tree_menu(self, event, tree):
        row = tree.identify_row(event.y)
        if not row:
            return
        # keep an existing multi-selection; only reset when right-clicking
        # outside the current selection
        if row not in tree.selection():
            tree.selection_set(row)
        sel = tree.selection()
        menu = tk.Menu(self, tearoff=0,
                       bg=C["card"], fg=C["text"],
                       activebackground=C["card_h"], activeforeground=C["text"],
                       relief="flat", font=FONT)

        # multiple rows selected → offer a single batch-delete action
        if len(sel) > 1:
            menu.add_command(label=f"Delete {len(sel)} selected",
                             command=lambda: self._task_tree_delete(tree))
            self._popup_menu(menu, event.x_root, event.y_root)
            return

        if "." in row:
            # subtask row
            task_idx, sub_idx = map(int, row.split("."))
            sub = self._tasks[task_idx]["subtasks"][sub_idx]
            is_done = sub.get("done", False)
            menu.add_command(label="Edit Subtask",
                             command=lambda: self._edit_subtask(task_idx, sub_idx))
            menu.add_separator()
            menu.add_command(
                label="Mark Undone" if is_done else "Mark Done",
                command=lambda: self._toggle_subtask_done(task_idx, sub_idx))
            menu.add_separator()
            menu.add_command(label="Delete Subtask",
                             command=lambda: self._remove_subtask(task_idx, sub_idx))
        else:
            try:
                idx = int(row)
                # task row
                is_running = (self._work_active is not None and
                              self._work_active["task_idx"] == idx)
                if is_running:
                    menu.add_command(label="Stop Work",
                                     command=lambda: self._stop_work(idx))
                else:
                    menu.add_command(label="Start Work",
                                     command=lambda: self._start_work(idx))
                menu.add_separator()
                menu.add_command(label="Add Subtask",
                                 command=lambda: self._add_subtask(idx))
                menu.add_separator()

                # quick Deadline submenu
                _submenu_cfg = dict(tearoff=0, bg=C["card"], fg=C["text"],
                                    activebackground=C["card_h"],
                                    activeforeground=C["text"],
                                    relief="flat", font=FONT)
                dl_menu = tk.Menu(menu, **_submenu_cfg)
                for lbl, key in [("Today", "today"), ("Tomorrow", "tomorrow"),
                                 ("+3 days", "3days"), ("+1 week", "1week"),
                                 ("+2 weeks", "2weeks"), ("+1 month", "1month")]:
                    dl_menu.add_command(
                        label=lbl,
                        command=lambda k=key, i=idx: self._quick_set_deadline(i, k))
                dl_menu.add_separator()
                dl_menu.add_command(label="Custom date...",
                                    command=lambda i=idx: self._quick_set_deadline(i, "custom"))
                dl_menu.add_command(label="Clear",
                                    command=lambda i=idx: self._quick_set_deadline(i, "clear"))
                cur_dl = self._tasks[idx].get("deadline", "")
                menu.add_cascade(label=f"Deadline ({cur_dl})" if cur_dl else "Deadline",
                                 menu=dl_menu)

                # quick Progress submenu
                pg_menu = tk.Menu(menu, **_submenu_cfg)
                cur_pct = self._tasks[idx].get("progress", 0)
                for pct in (0, 25, 50, 75, 100):
                    mark = "* " if cur_pct == pct else "  "
                    pg_menu.add_command(
                        label=f"{mark}{pct}%",
                        command=lambda p=pct, i=idx: self._quick_set_progress(i, p))
                menu.add_cascade(label=f"Progress ({cur_pct}%)", menu=pg_menu)
                menu.add_separator()
                menu.add_command(label="Edit",    command=lambda: self._edit_task(idx))
                menu.add_command(label="Archive", command=lambda: self._archive_task(idx))
                menu.add_separator()
                menu.add_command(label="Delete",  command=lambda: self._remove_task(idx))
            except ValueError:
                # event parent row
                ev_name = tree.item(row, "text")
                menu.add_command(label="Rename",
                                 command=lambda: self._rename_event(ev_name))
        self._popup_menu(menu, event.x_root, event.y_root)

    # ── Quick task edits (from the right-click menu) ──────

    def _quick_set_deadline(self, idx: int, key: str):
        """Set a task's deadline from a relative shortcut, a custom date, or clear it."""
        today = datetime.date.today()
        if key == "clear":
            new = ""
        elif key == "custom":
            cur = self._tasks[idx].get("deadline", "") or today.isoformat()
            dlg = InputDialog(self, "Deadline", "Date (YYYY-MM-DD):", default=cur)
            if not dlg.result:
                return
            try:
                new = datetime.date.fromisoformat(dlg.result.strip()).isoformat()
            except ValueError:
                messagebox.showwarning("Deadline", "Invalid date (use YYYY-MM-DD).",
                                       parent=self)
                return
        elif key == "1month":
            mo = today.month + 1
            yr = today.year + (mo - 1) // 12
            mo = (mo - 1) % 12 + 1
            day = min(today.day, calendar.monthrange(yr, mo)[1])
            new = datetime.date(yr, mo, day).isoformat()
        else:
            days = {"today": 0, "tomorrow": 1, "3days": 3, "1week": 7, "2weeks": 14}
            new = (today + datetime.timedelta(days=days[key])).isoformat()
        self._tasks[idx]["deadline"] = new
        self._tasks[idx]["updated"]  = today.isoformat()
        self._save_tasks()
        self._render_list()

    def _quick_set_progress(self, idx: int, pct: int):
        """Set a task's progress directly; spawn the next occurrence if it completes a recurring task."""
        task = self._tasks[idx]
        prev = task.get("progress", 0)
        _log_task_progress(task, pct)
        task["progress"] = pct
        task["updated"]  = datetime.date.today().isoformat()
        if task.get("recur", "none") != "none" and pct == 100 and prev < 100:
            self._spawn_recurring(task)
        self._save_tasks()
        self._render_list()

    # ── Subtask operations ─────────────────────────────────

    def _add_subtask(self, task_idx: int):
        dlg = SubtaskDialog(self)
        if dlg.result is None:
            return
        self._tasks[task_idx].setdefault("subtasks", []).append(dlg.result)
        self._save_tasks()
        self._render_list()

    def _edit_subtask(self, task_idx: int, sub_idx: int):
        sub = self._tasks[task_idx]["subtasks"][sub_idx]
        dlg = SubtaskDialog(self, initial=sub)
        if dlg.result is None:
            return
        self._tasks[task_idx]["subtasks"][sub_idx] = dlg.result
        self._save_tasks()
        self._render_list()

    def _remove_subtask(self, task_idx: int, sub_idx: int):
        self._tasks[task_idx].get("subtasks", []).pop(sub_idx)
        self._save_tasks()
        self._render_list()

    def _toggle_subtask_done(self, task_idx: int, sub_idx: int):
        sub = self._tasks[task_idx]["subtasks"][sub_idx]
        sub["done"] = not sub.get("done", False)
        sub["progress"] = 100 if sub["done"] else sub.get("progress", 0)
        self._save_tasks()
        self._render_list()

    # ── Task operations ───────────────────────────────────

    def _event_names(self) -> list:
        return sorted(set(t["event"] for t in self._tasks if t.get("event")))

    def _add_task(self):
        dlg = TaskDialog(self, event_names=self._event_names())
        if dlg.result is None:
            return
        today = datetime.date.today().isoformat()
        dlg.result["created_at"] = today   # creation date
        dlg.result["updated"]    = today   # last updated date
        _log_task_progress(dlg.result, dlg.result.get("progress", 0), created=True)
        self._tasks.append(dlg.result)
        self._save_tasks()
        self._render_list()

    def _edit_task(self, idx: int):
        dlg = TaskDialog(self, initial=self._tasks[idx],
                         event_names=self._event_names())
        if dlg.result is None:
            return
        prev_progress = self._tasks[idx].get("progress", 0)
        # record before merging: dict() copies the progress_log reference,
        # so the entry written here carries over into the merged task
        _log_task_progress(self._tasks[idx], dlg.result.get("progress", 0))
        # overwrite while preserving existing fields (memos, created_at, etc.)
        merged = dict(self._tasks[idx])
        merged.update(dlg.result)
        merged["updated"] = datetime.date.today().isoformat()
        self._tasks[idx] = merged
        # recurring task: spawn the next occurrence when completed
        if merged.get("recur", "none") != "none" and merged.get("progress", 0) == 100 and prev_progress < 100:
            self._spawn_recurring(merged)
        self._save_tasks()
        self._render_list()

    # ── Recurring tasks ────────────────────────────────────

    @staticmethod
    def _next_recur_date(base: str, recur: str) -> str:
        """Return the next deadline date according to the recurrence type."""
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
        """Generate and append the next occurrence of a completed recurring task."""
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
        _log_task_progress(new_task, 0, created=True)
        self._tasks.append(new_task)

    def _check_recurring_tasks(self):
        """Fill in any ungenerated recurring task occurrences at startup."""
        today = datetime.date.today()
        to_add = []
        for task in self._tasks:
            recur = task.get("recur", "none")
            if (recur == "none" or task.get("progress", 0) < 100
                    or task.get("archived")):
                continue
            dl = task.get("deadline", "")
            next_dl = self._next_recur_date(dl, recur)
            try:
                next_date = datetime.date.fromisoformat(next_dl)
            except ValueError:
                continue
            if next_date > today:
                continue
            # spawn only if no incomplete task with the same event+process+recur exists
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

    # ── Task archive ──────────────────────────────────────

    def _archive_task(self, idx: int):
        """Move a task to the archived section (kept in data, hidden from the tree)."""
        self._tasks[idx]["archived"] = True
        self._tasks[idx]["updated"]  = datetime.date.today().isoformat()
        self._save_tasks()
        self._render_list()

    def _unarchive_task(self, idx: int):
        self._tasks[idx]["archived"] = False
        self._tasks[idx]["updated"]  = datetime.date.today().isoformat()
        self._save_tasks()
        self._render_list()

    def _render_task_archived_section(self):
        """Collapsible list of archived tasks at the bottom of the Tasks tab."""
        archived = [(i, t) for i, t in enumerate(self._tasks)
                    if t.get("archived")]
        if not archived:
            return
        tk.Frame(self._list_frame, bg=C["border"], height=1).pack(
            fill="x", padx=2, pady=(8, 0))

        arch_frame = tk.Frame(self._list_frame, bg=C["bg"])
        arrow  = "v" if self._task_archive_open else ">"
        toggle = tk.Label(self._list_frame,
                          text=f"{arrow}  Archived  ({len(archived)})",
                          bg=C["bg"], fg=C["text_sub"],
                          font=FONT_SMALL, cursor="hand2", anchor="w")
        toggle.pack(fill="x", padx=6, pady=(2, 0))

        def _toggle(_e=None):
            self._task_archive_open = not self._task_archive_open
            if self._task_archive_open:
                toggle.configure(text=f"v  Archived  ({len(archived)})")
                arch_frame.pack(fill="x")
            else:
                toggle.configure(text=f">  Archived  ({len(archived)})")
                arch_frame.pack_forget()

        toggle.bind("<Button-1>", _toggle)

        for i, task in archived:
            card = tk.Frame(arch_frame, bg=C["bg"], pady=3, padx=8,
                            highlightthickness=1, highlightbackground=C["border"])
            card.pack(fill="x", pady=PAD_ROW_Y, padx=PAD_ROW_X)
            label = (f"[{task.get('event', '')}]  {task.get('process', '')}"
                     f"  {task.get('progress', 0)}%")
            tk.Label(card, text=label, bg=C["bg"], fg=C["text_sub"],
                     font=FONT_SMALL, anchor="w").pack(
                         side="left", fill="x", expand=True)
            tk.Button(card, text="x",
                      command=lambda i=i: self._remove_task(i),
                      bg=C["bg"], fg=C["btn_del"], relief="flat", bd=0,
                      font=FONT_SMALL, cursor="hand2",
                      activebackground=C["bg"], activeforeground=C["btn_del_h"],
                      ).pack(side="right", padx=(6, 0))
            tk.Button(card, text="Restore",
                      command=lambda i=i: self._unarchive_task(i),
                      bg=C["bg"], fg=C["accent"], relief="flat", bd=0,
                      font=FONT_SMALL, cursor="hand2",
                      activebackground=C["bg"], activeforeground=C["accent_dk"],
                      ).pack(side="right")

        if self._task_archive_open:
            arch_frame.pack(fill="x")

    # ── Work time tracking ────────────────────────────────

    def _work_anim_step(self):
        """Update the dot animation on the work-in-progress bar."""
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
            text=f"{task.get('process', '')}  Working{dots}  {_fmt_duration(elapsed)}"
        )
        self._work_anim_id = self.after(500, self._work_anim_step)

    def _active_work_record(self) -> dict | None:
        """Return the active work info as a dict for config persistence."""
        if self._work_active is None:
            return None
        task = self._tasks[self._work_active["task_idx"]]
        return {
            "event":   task.get("event", ""),
            "process": task.get("process", ""),
            "start":   self._work_active["start"].isoformat(timespec="seconds"),
        }

    def _start_work(self, task_idx: int):
        """Start work: record the current time."""
        if self._work_active is not None:
            if not messagebox.askyesno(
                "Working",
                "Another task is in progress. Switch to this one?",
                parent=self,
            ):
                return
            self._stop_work(self._work_active["task_idx"])
        self._work_active = {
            "task_idx": task_idx,
            "start": datetime.datetime.now(),
        }
        self._save_config()
        self._render_list()
        self._update_tray_badge()

    def _stop_work(self, task_idx: int):
        """Stop work: record to log and save."""
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
        self._save_config()  # save with active_work set to None
        self._render_list()
        self._update_tray_badge()

    # ── System tray ───────────────────────────────────────

    def _on_unmap(self, event):
        if event.widget is self and self.state() == "iconic":
            self._minimize_to_tray()

    def _on_close(self):
        self._flush_config_on_exit()
        self.destroy()

    def _set_card_size(self, size: str):
        self._card_size = size
        self._save_config()
        self._render_list()

    def _set_font_size(self, size: int):
        """Change the font size and rebuild the UI."""
        self._font_size = size
        _update_fonts(size)
        self._save_config()
        self._rebuild_ui()

    def _set_font_family(self, family: str):
        """Change the UI font family and rebuild the UI."""
        self._font_family = family
        _update_fonts(self._font_size, family)
        self._save_config()
        self._rebuild_ui()

    def _rebuild_ui(self):
        """Destroy all widgets and rebuild (font/theme change)."""
        if self._tick_id is not None:
            self.after_cancel(self._tick_id)
            self._tick_id = None
        self._pill_font_cache.clear()   # measured with the old fonts
        for w in self.winfo_children():
            w.destroy()
        self.configure(bg=C["bg"])
        self._build_ui()
        self._render_tabs()
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
                     if t.get("deadline") == today and t.get("progress", 0) < 100]
        overdue   = [t for t in self._tasks
                     if t.get("deadline") and t.get("deadline") < today
                     and t.get("progress", 0) < 100]

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
                name = t.get("process", "") or t.get("event", "—")
                due  = t.get("deadline", "")
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

    def _build_tray_image(self) -> Image:
        """Render the tray icon, with a status dot if work is active or a
        notification fired while minimized."""
        png_data = base64.b64decode(_make_icon_png(
            ICON_PALETTES.get(self._theme, ICON_PALETTES["violet"]),
            getattr(self, "_icon_shape", "jelly"),
        ))
        img = Image.open(io.BytesIO(png_data)).convert("RGBA")
        if self._work_active is not None:
            img = _add_tray_badge(img, "#4caf50")   # work timer running
        elif self._tray_notify_pending:
            img = _add_tray_badge(img, C["btn_del"])  # unread notification
        return img

    def _update_tray_badge(self):
        """Refresh the tray icon image to reflect the current status badge."""
        if self._tray_icon is None:
            return
        self._tray_icon.icon = self._build_tray_image()

    def _minimize_to_tray(self):
        self.withdraw()
        if self._tray_icon is not None:
            return  # already running

        menu = pystray.Menu(
            pystray.MenuItem("Show Gem", self._restore_from_tray, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._quit_from_tray),
        )
        self._tray_icon = pystray.Icon("Gem", self._build_tray_image(), "Gem", menu)
        threading.Thread(target=self._tray_icon.run, daemon=True).start()

    def _restore_from_tray(self, icon=None, item=None):
        self.after(0, self._do_restore)

    def _do_restore(self):
        self._tray_notify_pending = False
        if self._tray_icon is not None:
            self._tray_icon.stop()
            self._tray_icon = None
        self.deiconify()
        self.lift()
        self.focus_force()

    def _quit_from_tray(self, icon=None, item=None):
        self.after(0, self._do_quit)

    def _do_quit(self):
        self._flush_config_on_exit()
        if self._tray_icon is not None:
            self._tray_icon.stop()
            self._tray_icon = None
        self.destroy()

    def _flush_config_on_exit(self):
        """Commit any pending debounced config write before shutting down."""
        if self._save_after_id is not None:
            try:
                self.after_cancel(self._save_after_id)
            except Exception:
                pass
            self._save_after_id = None
            try:
                self._save_config_now()
            except Exception:
                pass

    # ── Command palette (Ctrl+K) ──────────────────────────

    def _palette_items(self) -> list[tuple[str, str, str, object]]:
        """Collect all launchable items as (kind, label, search_text, action)."""
        items: list[tuple[str, str, str, object]] = []
        for cat in self._data:
            for entry in cat.get("folders", []):
                kind = "File" if entry.get("type") == "file" else "Folder"
                name, path = entry.get("name", ""), entry.get("path", "")
                items.append((kind, name, f"{name} {path}",
                              lambda p=path, t=entry.get("type", "folder"):
                                  self._open_item(p, t)))
        for conn in self._conns:
            name = conn.get("name") or conn.get("host", "")
            items.append(("Conn", f"{name}  ({conn.get('protocol', '')})",
                          f"{name} {conn.get('host', '')} {conn.get('protocol', '')}",
                          lambda c=conn: self._connect_server(c)))
        for i, task in enumerate(self._tasks):
            if task.get("archived"):
                continue
            label = f"[{task.get('event', '')}] {task.get('process', '')}"
            items.append(("Task", label,
                          f"{task.get('event', '')} {task.get('process', '')} "
                          f"{task.get('content', '')}",
                          lambda idx=i: self._palette_goto_task(idx)))
        for cat in self._bookmarks:
            for bm in cat.get("items", []):
                items.append(("Web", bm.get("name", ""),
                              f"{bm.get('name', '')} {bm.get('url', '')}",
                              lambda u=bm.get("url", ""): webbrowser.open(u)))
        for key, label, idx in self._SYSTEM_TABS:
            items.append(("Tab", label, f"tab {label} {key}",
                          lambda i2=idx: self._switch_tab(i2)))
        for ci, cat in enumerate(self._data):
            items.append(("Tab", cat["category"], f"tab {cat['category']}",
                          lambda i2=ci: self._switch_tab(i2)))
        return items

    def _palette_goto_task(self, idx: int):
        """Jump to the Tasks tab and select the given task."""
        self._task_select_pending = idx
        self._switch_tab(-2)

    def _open_command_palette(self, _e=None):
        # toggle: a second Ctrl+K closes the palette
        if self._palette_win is not None:
            try:
                self._palette_win.destroy()
            except Exception:
                pass
            self._palette_win = None
            return "break"
        # don't fire while typing in an input (Entry/Text bind Ctrl+K natively)
        try:
            f = self.focus_get()
        except Exception:
            f = None
        if isinstance(f, (tk.Entry, tk.Text, tk.Spinbox)):
            return

        win = tk.Toplevel(self)
        self._palette_win = win
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=C["accent"])
        inner = tk.Frame(win, bg=C["card"])
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        var = tk.StringVar()
        entry = tk.Entry(inner, textvariable=var, font=FONT,
                         bg=C["card"], fg=C["text"], relief="flat", bd=0,
                         insertbackground=C["accent"])
        entry.pack(fill="x", padx=10, pady=(10, 6), ipady=3)
        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x")
        lb = tk.Listbox(inner, height=10, font=FONT,
                        bg=C["card"], fg=C["text"],
                        selectbackground=C["accent_lt"],
                        selectforeground=C["accent_dk"],
                        relief="flat", bd=0, activestyle="none",
                        highlightthickness=0)
        lb.pack(fill="both", expand=True, padx=6, pady=6)

        items = self._palette_items()
        matches: list = []

        def _refresh(*_):
            q = var.get()
            scored = []
            for it in items:
                s = _fuzzy_score(q, it[2])
                if s is not None:
                    scored.append((s, it))
            scored.sort(key=lambda x: x[0])
            matches[:] = [it for _, it in scored[:12]]
            lb.delete(0, "end")
            for kind, label, _t, _a in matches:
                lb.insert("end", f" [{kind}]  {label}")
            if matches:
                lb.selection_set(0)

        var.trace_add("write", _refresh)
        _refresh()

        def _close(_e=None):
            self._palette_win = None
            try:
                win.destroy()
            except Exception:
                pass

        def _run(_e=None):
            sel = lb.curselection()
            i = sel[0] if sel else 0
            if i >= len(matches):
                _close()
                return
            action = matches[i][3]
            _close()
            self.after(10, action)   # run after the palette is gone

        def _move(d):
            cur = lb.curselection()
            cur = cur[0] if cur else 0
            nxt = max(0, min(len(matches) - 1, cur + d))
            lb.selection_clear(0, "end")
            lb.selection_set(nxt)
            lb.see(nxt)
            return "break"

        entry.bind("<Return>",  _run)
        entry.bind("<Escape>",  _close)
        entry.bind("<Down>",    lambda e: _move(1))
        entry.bind("<Up>",      lambda e: _move(-1))
        lb.bind("<Return>",          _run)
        lb.bind("<Double-Button-1>", _run)
        lb.bind("<Escape>",          _close)

        # close when focus leaves the palette (click elsewhere / Alt-Tab)
        def _maybe_close(_e=None):
            def _check():
                if self._palette_win is not win or not win.winfo_exists():
                    return
                try:
                    f2 = win.focus_get()
                except Exception:
                    f2 = None
                if f2 is None or f2.winfo_toplevel() is not win:
                    _close()
            win.after(120, _check)
        entry.bind("<FocusOut>", _maybe_close)
        lb.bind("<FocusOut>",    _maybe_close)

        self.update_idletasks()
        w = max(360, min(520, self.winfo_width() - 40))
        x = self.winfo_rootx() + (self.winfo_width() - w) // 2
        y = self.winfo_rooty() + 60
        win.geometry(f"{w}x320+{x}+{y}")
        entry.focus_force()
        return "break"

    # ── Windows shell integration (drag&drop / global hotkey) ──

    def _setup_win_integration(self):
        """Global hotkey (Win+Shift+G) and Explorer drag&drop.

        Both deliberately avoid subclassing the Tk window procedure: running
        a Python WNDPROC for every window message crashes CPython inside
        Tk's event loop (fatal "PyEval_RestoreThread" GIL error). The hotkey
        therefore lives on its own thread with its own message queue, and
        drag&drop uses the optional tkinterdnd2 package (native Tcl side)
        when installed.
        """
        # ── global hotkey: dedicated thread + thread message queue ──
        self._hotkey_event = threading.Event()

        def _hotkey_loop():
            user32 = ctypes.windll.user32
            user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int,
                                              wintypes.UINT, wintypes.UINT]
            # MOD_SHIFT | MOD_WIN | MOD_NOREPEAT,  VK 'G'
            # hwnd=None: WM_HOTKEY is posted to this thread's message queue
            if not user32.RegisterHotKey(None, 1, 0x4 | 0x8 | 0x4000, 0x47):
                return   # taken by another app — feature silently off
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == 0x0312:   # WM_HOTKEY
                    self._hotkey_event.set()

        threading.Thread(target=_hotkey_loop, daemon=True).start()
        self._poll_hotkey()

        # ── drag&drop: only when tkinterdnd2 is available ──
        if DND_FILES is not None:
            try:
                self.drop_target_register(DND_FILES)
                self.dnd_bind("<<Drop>>", self._on_dnd_drop)
            except Exception:
                pass

    def _poll_hotkey(self):
        """Relay hotkey presses from the worker thread to the UI thread.
        Polling an Event avoids calling any Tk API off the main thread."""
        if self._hotkey_event.is_set():
            self._hotkey_event.clear()
            self._on_global_hotkey()
        self.after(150, self._poll_hotkey)

    def _on_dnd_drop(self, event):
        try:
            # Tcl list: paths with spaces arrive wrapped in braces
            paths = list(self.tk.splitlist(event.data))
        except Exception:
            paths = [event.data]
        self._handle_dropped_paths(paths)

    def _handle_dropped_paths(self, paths: list):
        """Register Explorer-dropped files/folders into the active folder tab."""
        if self._active < 0:
            self._pathbar_var.set(
                "Drop ignored — switch to a folder tab to register items")
            return
        folders = self._current["folders"]
        existing = {e.get("path") for e in folders}
        added = 0
        for p in paths:
            p = os.path.normpath(p)
            if p in existing:
                continue
            entry = {"name": os.path.basename(p) or p, "path": p}
            if os.path.isfile(p):
                entry["type"] = "file"
            folders.append(entry)
            existing.add(p)
            added += 1
        if added:
            self._save()
            self._render_list()
            self._pathbar_var.set(f"Added {added} item(s) by drag && drop")

    def _on_global_hotkey(self):
        """Win+Shift+G: bring Gem to the front; hide to tray if already focused."""
        try:
            if self.state() in ("withdrawn", "iconic"):
                self._do_restore()
            elif self.focus_displayof() is not None:
                self._minimize_to_tray()   # already in front → toggle hide
            else:
                self.deiconify()
                self.lift()
                self.focus_force()
        except Exception:
            pass

    # ── Config daily backup ───────────────────────────────

    def _backup_config_daily(self):
        """Keep a rolling 7-day backup of config.json under backups/."""
        try:
            if not CONFIG_FILE.exists() or CONFIG_FILE.stat().st_size == 0:
                return
            bdir = _BASE_DIR / "backups"
            bdir.mkdir(exist_ok=True)
            dst = bdir / f"config-{datetime.date.today().strftime('%Y%m%d')}.json"
            if not dst.exists():
                import shutil
                shutil.copy2(CONFIG_FILE, dst)
            for old in sorted(bdir.glob("config-*.json"))[:-7]:
                old.unlink()
        except Exception:
            pass

    def _cleanup_old_logs(self):
        """Delete terminal logs in LOG_DIR older than _log_keep_days (by mtime).

        0 days = disabled. Runs in a background thread so a slow/locked
        disk never delays startup; files in use are silently skipped.
        """
        days = getattr(self, "_log_keep_days", 0)
        if days <= 0 or not LOG_DIR.exists():
            return

        def _work():
            cutoff = time.time() - days * 86400
            for f in LOG_DIR.glob("*.log"):
                try:
                    if f.stat().st_mtime < cutoff:
                        f.unlink()
                except OSError:
                    pass   # locked by a live Tera Term session, etc.

        threading.Thread(target=_work, daemon=True).start()

    def _set_log_keep_days(self, days: int):
        self._log_keep_days = days
        self._save_config()
        self._cleanup_old_logs()   # apply the new retention immediately

    # ── Start with Windows ────────────────────────────────

    _RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

    def _is_startup_enabled(self) -> bool:
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._RUN_KEY) as k:
                winreg.QueryValueEx(k, "Gem")
            return True
        except OSError:
            return False

    def _toggle_startup(self):
        import winreg
        enable = not self._is_startup_enabled()
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._RUN_KEY, 0,
                                winreg.KEY_SET_VALUE) as k:
                if enable:
                    if getattr(sys, "frozen", False):
                        cmd = f'"{sys.executable}"'
                    else:
                        # prefer pythonw.exe so no console window appears
                        pyw = Path(sys.executable).with_name("pythonw.exe")
                        py  = pyw if pyw.exists() else Path(sys.executable)
                        cmd = f'"{py}" "{Path(__file__).resolve()}"'
                    winreg.SetValueEx(k, "Gem", 0, winreg.REG_SZ, cmd)
                else:
                    winreg.DeleteValue(k, "Gem")
        except OSError as e:
            messagebox.showerror("Start with Windows", str(e), parent=self)


    def _open_task_history(self):
        """Daily digest of task progress changes (newest day first)."""
        # date -> [(task, log entry), ...] in task order; archived included
        by_date: dict[str, list[tuple[dict, dict]]] = {}
        for task in self._tasks:
            for entry in task.get("progress_log", []):
                if entry.get("from") == entry.get("to"):
                    continue   # same-day change that was reverted — no net change
                by_date.setdefault(entry.get("date", ""), []).append((task, entry))

        win = tk.Toplevel(self)
        win.title("Progress History")
        win.configure(bg=C["bg"])
        win.geometry("420x480")
        win.minsize(320, 240)
        win.resizable(True, True)

        tk.Label(win, text="Progress History",
                 bg=C["accent"], fg="white",
                 font=FONT_BOLD, anchor="w", padx=12, pady=6).pack(fill="x")

        wrapper = tk.Frame(win, bg=C["bg"])
        wrapper.pack(fill="both", expand=True, padx=8, pady=6)
        cv = tk.Canvas(wrapper, bg=C["bg"], highlightthickness=0)
        sb = ttk.Scrollbar(wrapper, orient="vertical",
                           style="Gem.Vertical.TScrollbar", command=cv.yview)
        body = tk.Frame(cv, bg=C["bg"])
        body.bind("<Configure>",
                  lambda e: cv.configure(scrollregion=cv.bbox("all")))
        _win_id = cv.create_window((0, 0), window=body, anchor="nw")
        _sb_pack = dict(side="right", fill="y")
        cv.configure(yscrollcommand=lambda lo, hi:
                     _autohide_scrollbar(sb, lo, hi, _sb_pack))
        cv.bind("<Configure>", lambda e: cv.itemconfigure(_win_id, width=e.width))
        cv.pack(side="left", fill="both", expand=True)
        # wheel scrolling comes from the global <MouseWheel> handler, which
        # scrolls the nearest scrollable canvas under the pointer

        if not by_date:
            tk.Label(body,
                     text="No history yet.\nProgress changes are recorded from now on.",
                     bg=C["bg"], fg=C["text_sub"], font=FONT_SMALL,
                     justify="center").pack(pady=24)
        else:
            MAX_DAYS = 30
            dates = sorted(by_date.keys(), reverse=True)
            for d in dates[:MAX_DAYS]:
                try:
                    hdr = f"{d} ({datetime.date.fromisoformat(d).strftime('%a')})"
                except ValueError:
                    hdr = d
                tk.Label(body, text=hdr, bg=C["bg"], fg=C["text"],
                         font=FONT_BOLD, anchor="w").pack(
                             fill="x", padx=4, pady=(8, 2))
                for task, entry in by_date[d]:
                    row = tk.Frame(body, bg=C["card"], highlightthickness=1,
                                   highlightbackground=C["border"])
                    row.pack(fill="x", padx=4, pady=1)
                    name = f"[{task.get('event', '')}] {task.get('process', '')}"
                    if task.get("archived"):
                        name += "  (archived)"
                    tk.Label(row, text=name, bg=C["card"], fg=C["text"],
                             font=FONT_SMALL, anchor="w").pack(
                                 side="left", fill="x", expand=True,
                                 padx=(8, 4), pady=3)
                    frm, to = entry.get("from"), entry.get("to", 0)
                    chg = f"created ({to}%)" if frm is None else f"{frm}% → {to}%"
                    fg = "#4caf50" if to == 100 else C["accent_dk"]
                    tk.Label(row, text=chg, bg=C["card"], fg=fg,
                             font=FONT_SMALL_BOLD, anchor="e").pack(
                                 side="right", padx=(4, 8), pady=3)
            if len(dates) > MAX_DAYS:
                tk.Label(body,
                         text=f"({len(dates) - MAX_DAYS} older day(s) omitted)",
                         bg=C["bg"], fg=C["text_sub"], font=FONT_TINY,
                         anchor="w").pack(fill="x", padx=4, pady=(8, 4))

        tk.Button(win, text="Close", command=win.destroy,
                  bg=C["accent_lt"], fg=C["text"], relief="flat", bd=0,
                  font=FONT, cursor="hand2", padx=16, pady=4,
                  activebackground=C["border"], activeforeground=C["text"],
                  ).pack(pady=(0, 10))

        win.update_idletasks()
        px = self.winfo_x() + (self.winfo_width()  - win.winfo_width())  // 2
        py = self.winfo_y() + (self.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{px}+{py}")

    def _open_work_log(self, task_idx: int):
        """Open the work log list and delete dialog."""
        task = self._tasks[task_idx]
        logs = task.get("work_logs", [])

        dlg = tk.Toplevel(self)
        dlg.title(f"Work Log — {task.get('process', '')}")
        dlg.configure(bg=C["bg"])
        dlg.resizable(False, False)
        dlg.grab_set()

        # header
        tk.Label(dlg, text=f"Work Log  [{task.get('event', '')}] {task.get('process', '')}",
                 bg=C["bg"], fg=C["text"], font=FONT_BOLD).pack(padx=16, pady=(12, 4), anchor="w")

        # log list frame
        frame = tk.Frame(dlg, bg=C["bg"])
        frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        def _refresh():
            for w in frame.winfo_children():
                w.destroy()
            logs = task.get("work_logs", [])
            if not logs:
                tk.Label(frame, text="No records", bg=C["bg"], fg=C["text_sub"],
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
            tk.Label(frame, text=f"Total  {_fmt_duration(total_sec)}",
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

    def _export_tasks(self):
        """Export the task list to a human-readable text report (EN or JA)."""
        ja = (getattr(self, "_export_lang", "en") == "ja")

        if not self._tasks:
            messagebox.showinfo(
                "エクスポート" if ja else "Export",
                "登録されたタスクがありません。" if ja else "No tasks registered.",
                parent=self)
            return

        include_prev = messagebox.askyesno(
            "昨日の作業ログ" if ja else "Yesterday's Work Log",
            "昨日の作業ログもレポートに含めますか？" if ja
            else "Include yesterday's work log in the report?",
            parent=self,
        )

        save_path = filedialog.asksaveasfilename(
            parent=self,
            title="タスク一覧を書き出す" if ja else "Export Tasks",
            defaultextension=".txt",
            initialfile=("タスク一覧_" if ja else "tasks_")
                        + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + ".txt",
            filetypes=([("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")] if ja
                       else [("Text files", "*.txt"), ("All files", "*.*")]),
        )
        if not save_path:
            return

        today     = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        yesterday_str = yesterday.isoformat()

        def fmt_date(s: str) -> str:
            try:
                return datetime.date.fromisoformat(s).strftime("%Y/%m/%d")
            except ValueError:
                return s

        def deadline_note(dl_str: str) -> str:
            try:
                d = datetime.date.fromisoformat(dl_str)
            except ValueError:
                return ""
            delta = (d - today).days
            if ja:
                if delta > 0:  return f"あと{delta}日"
                if delta == 0: return "本日締切"
                return f"{abs(delta)}日超過"
            if delta > 0:  return f"{delta} day{'s' if delta != 1 else ''} left"
            if delta == 0: return "due today"
            n = abs(delta)
            return f"{n} day{'s' if n != 1 else ''} overdue"

        def fmt_dur(sec: float) -> str:
            h, m = divmod(int(sec) // 60, 60)
            if ja:
                return f"{h}時間{m:02d}分" if h else f"{m}分"
            return f"{h}h {m:02d}m" if h else f"{m}m"

        def status_label(pct: int) -> str:
            if pct >= 100: return "完了" if ja else "Done"
            if pct <= 0:   return "未着手" if ja else "Not started"
            return "進行中" if ja else "In progress"

        _JA_LABELS = {"Progress": "進捗　　", "Deadline": "期限　　",
                      "Updated": "更新日　", "Content": "内容　　", "Folder": "フォルダ"}

        def field(label: str, value: str) -> str:
            if ja:
                return f"　　{_JA_LABELS[label]}：{value}"
            return f"    {label:<9}: {value}"

        CONT_INDENT = "　" * 7 if ja else ("    " + " " * 9 + "  ")

        # group by event (preserve insertion order; archived tasks excluded)
        groups: dict[str, list[dict]] = {}
        for task in self._tasks:
            if task.get("archived"):
                continue
            if self._task_hide_done and task.get("progress", 0) >= 100:
                continue
            groups.setdefault(task["event"], []).append(task)

        lines: list[str] = []
        SEP = "=" * 42

        # ── yesterday's work log section ──────────────────────────
        if include_prev:
            lines.append(SEP)
            lines.append((f"昨日の作業ログ（{fmt_date(yesterday_str)}）" if ja
                          else f"Yesterday's Work Log ({fmt_date(yesterday_str)})"))
            lines.append(SEP)

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
                for (ev, proc), entries in sorted(prev_groups.items()):
                    task_sec = sum((e - s).total_seconds() for s, e in entries)
                    day_total_sec += task_sec
                    sep_dot = "…" if ja else "..."
                    lines.append(f"{'　' if ja else '  '}[{ev}] {proc} {sep_dot} {fmt_dur(task_sec)}")
                    for s, e in sorted(entries):
                        lines.append(f"{'　　' if ja else '    '}{s.strftime('%H:%M')} - {e.strftime('%H:%M')}")
                lines.append("")
                lines.append((f"　合計：{fmt_dur(day_total_sec)}" if ja
                              else f"  Total: {fmt_dur(day_total_sec)}"))
            else:
                lines.append("　（記録なし）" if ja else "  (no records)")

            lines.append("")

        # ── tasks grouped by event (with a per-event summary) ─────
        for event_name, task_list in groups.items():
            ev_total = len(task_list)
            ev_done  = sum(1 for t in task_list if t.get("progress", 0) >= 100)
            ev_avg   = (sum(t.get("progress", 0) for t in task_list) // ev_total
                        if ev_total else 0)
            lines.append("")
            lines.append(SEP)
            lines.append(event_name)
            if ja:
                lines.append(f"　タスク数:{ev_total}  完了:{ev_done}  "
                             f"進行中:{ev_total - ev_done}  平均進捗:{ev_avg}%")
            else:
                lines.append(f"  Tasks:{ev_total}  Done:{ev_done}  "
                             f"In progress:{ev_total - ev_done}  Avg:{ev_avg}%")
            lines.append(SEP)

            for task in task_list:
                pct      = task.get("progress", 0)
                process  = task.get("process", "（プロセス名なし）" if ja else "(no process name)")
                content  = task.get("content", "").strip()
                deadline = task.get("deadline", "")
                updated  = task.get("updated", "")
                wfs      = task.get("work_folders", [])
                if not wfs and task.get("work_folder"):
                    wfs = [task["work_folder"]]
                memos = task.get("memos", [])
                if not memos and task.get("memo"):
                    memos = [{"title": "メモ" if ja else "Memo", "content": task["memo"]}]

                lines.append("")
                lines.append(process)
                lines.append(field("Progress", f"{pct}%（{status_label(pct)}）" if ja
                                   else f"{pct}% ({status_label(pct)})"))
                if deadline:
                    lines.append(field("Deadline", (f"{fmt_date(deadline)}（{deadline_note(deadline)}）" if ja
                                                     else f"{fmt_date(deadline)} ({deadline_note(deadline)})")))
                if updated:
                    lines.append(field("Updated", fmt_date(updated)))
                if content:
                    first = True
                    for line in content.splitlines():
                        if line.strip():
                            lines.append(field("Content", line) if first
                                         else f"{CONT_INDENT}{line}")
                            first = False
                if wfs:
                    for i, wf in enumerate(wfs):
                        lines.append(field("Folder", wf) if i == 0
                                     else f"{CONT_INDENT}{wf}")
                if memos:
                    for memo in memos:
                        m_title   = memo.get("title", "無題" if ja else "Untitled")
                        m_content = memo.get("content", "").strip()
                        lines.append(f"　　メモ［{m_title}］" if ja else f"    Memo [{m_title}]")
                        for ml in m_content.splitlines():
                            if ml.strip():
                                lines.append(f"　　　　{ml}" if ja else f"      {ml}")
                subs = task.get("subtasks", [])
                if subs:
                    done_n = sum(1 for s in subs if s.get("done"))
                    lines.append(f"　　サブタスク（{done_n}/{len(subs)} 完了）" if ja
                                 else f"    Subtasks ({done_n}/{len(subs)} done)")
                    for sub in subs:
                        mark  = "[x]" if sub.get("done") else "[ ]"
                        s_dl  = sub.get("deadline", "")
                        info  = []
                        if not sub.get("done"):
                            info.append(f"{sub.get('progress', 0)}%")
                        if s_dl:
                            info.append(f"{fmt_date(s_dl)}（{deadline_note(s_dl)}）" if ja
                                        else f"{fmt_date(s_dl)} ({deadline_note(s_dl)})")
                        suffix = ((("　" + "・".join(info)) if ja
                                   else ("  " + ", ".join(info))) if info else "")
                        lines.append((f"　　　{mark} {sub.get('title', '')}{suffix}") if ja
                                     else f"      {mark} {sub.get('title', '')}{suffix}")
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

        # ── separator line ────────────────────────────────────────
        tk.Frame(win, bg=C["border"], width=1).pack(
            side="left", fill="y", padx=(8, 0))

        # ── right pane (edit area) ───────────────────────────
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

        # ── logic ────────────────────────────────────────
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

        # classify into Upcoming / Past
        # Past = time is in the past AND recurrence == "none"
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

        # ── Past (collapsible) ──
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
        card.pack(fill="x", pady=PAD_ROW_Y, padx=PAD_ROW_X)

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
            font=FONT, cursor="hand2",
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

    def _set_export_lang(self, lang: str):
        """Set the language used for the exported task report (en | ja)."""
        if lang not in ("en", "ja"):
            return
        self._export_lang = lang
        self._save_config()

    def _set_icon_shape(self, shape: str):
        """Switch the app icon design and re-apply it everywhere."""
        if shape == getattr(self, "_icon_shape", "jelly"):
            return
        self._icon_shape = shape
        self._save_config()
        palette = ICON_PALETTES.get(self._theme)
        png_b64 = _make_icon_png(palette, shape)
        self._icon = tk.PhotoImage(data=png_b64)
        try:
            self.wm_iconphoto(True, self._icon)
        except Exception:
            pass
        _setup_taskbar_icon(self, palette, shape)
        # update the tray icon image if currently minimized to tray
        self._update_tray_badge()

    def _apply_theme(self, theme_name: str):
        if theme_name not in THEMES:
            return
        self._theme = theme_name
        C.update(THEMES[theme_name])
        _style_flat_scrollbars(self)
        self._save_config()

        # cancel the _tick() after loop (prevent double loop)
        if self._tick_id is not None:
            self.after_cancel(self._tick_id)
            self._tick_id = None

        # regenerate icon with theme colors
        palette = ICON_PALETTES.get(theme_name)
        png_b64 = _make_icon_png(palette, getattr(self, "_icon_shape", "jelly"))
        self._icon = tk.PhotoImage(data=png_b64)
        self.wm_iconphoto(True, self._icon)
        _setup_taskbar_icon(self, palette, getattr(self, "_icon_shape", "jelly"))
        self._update_tray_badge()

        # destroy all widgets and rebuild, with a soft alpha cross-fade
        def _do_rebuild():
            for w in self.winfo_children():
                w.destroy()
            self.configure(bg=C["bg"])
            self._build_ui()
            self._render_tabs()
            self._render_list()
            _apply_titlebar_theme(self)
        self._fade_transition(_do_rebuild)

    def _fade_transition(self, rebuild_fn):
        """Dip the window alpha around a full rebuild for a cross-fade feel.

        Blocks the UI thread for ~200ms, which is acceptable for a
        user-initiated theme switch; restores the user's configured alpha.
        """
        try:
            base = float(self.attributes("-alpha"))
        except tk.TclError:
            base = 1.0
        steps = 5
        try:
            for i in range(1, steps + 1):
                self.attributes("-alpha", base * (1 - 0.75 * i / steps))
                self.update_idletasks()
                time.sleep(0.018)
            rebuild_fn()
            self.update_idletasks()
            for i in range(1, steps + 1):
                self.attributes("-alpha", base * (0.25 + 0.75 * i / steps))
                self.update_idletasks()
                time.sleep(0.018)
        finally:
            self.attributes("-alpha", base)

    # ── Other ─────────────────────────────────────────────

    def _tick(self):
        now = datetime.datetime.now()
        self._clock_var.set(now.strftime("%H:%M:%S"))
        self._date_var.set(now.strftime("%m/%d %a").upper())
        self._update_hud()
        self._update_banner()
        self._tick_id = self.after(1000, self._tick)

    def _is_visible(self) -> bool:
        """False while minimized or hidden in the tray."""
        try:
            return self.state() in ("normal", "zoomed")
        except tk.TclError:
            return False

    def _apply_hud_visibility(self):
        """Show/hide the header CPU/MEM HUD per self._hud_enabled."""
        if self._hud_enabled:
            self._hud_cv.pack(side="left", padx=(8, 0), before=self._banner_lbl)
            self._hud_lbl.pack(side="left", padx=(3, 0), before=self._banner_lbl)
        else:
            self._hud_cv.pack_forget()
            self._hud_lbl.pack_forget()

    def _on_toggle_hud(self, *_):
        self._hud_enabled = self._hud_enabled_var.get()
        self._apply_hud_visibility()
        self._save_config()

    def _update_hud(self):
        """Sample CPU/RAM and redraw the header sparkline + readout."""
        if not self._hud_enabled or not self._is_visible():
            return   # nobody is looking; GetSystemTimes is cumulative, so
                     # the first sample after restore averages the gap
        cpu, ram = _sample_cpu(), _sample_ram()
        if cpu is not None:
            self._hud_cpu.append(cpu)
        if ram is not None:
            self._hud_ram.append(ram)
        self._draw_hud()

    def _draw_hud(self, pulse: float = 0.35):
        """Redraw the header sparkline + readout with a neon glow halo.

        pulse (0-1) sets the glow bloom intensity; _pulse_hud() animates
        it while CPU/RAM usage is high for an alarm-like effect.
        """
        cv = getattr(self, "_hud_cv", None)
        if cv is None or not cv.winfo_exists():
            return
        c = int(self._hud_cpu[-1]) if self._hud_cpu else 0
        r = int(self._hud_ram[-1]) if self._hud_ram else 0
        hot = c >= 80 or r >= 80
        self._hud_lbl.configure(
            text=f"CPU{c:3d}%\nMEM{r:3d}%",
            fg=_blend_hex(C["accent_lt"], C["btn_del_h"], pulse) if hot else C["accent_lt"],
        )

        cv.delete("all")
        w = cv.winfo_width() or 56
        h = cv.winfo_height() or 24
        bg = C["accent"]

        def _spark(data, color, glow_t):
            if len(data) < 2:
                return
            n, ln = data.maxlen, len(data)
            pts = []
            for i, v in enumerate(data):
                pts.append(1 + (w - 2) * (n - ln + i) / (n - 1))      # x: anchored right
                pts.append(h - 2 - (h - 4) * v / 100.0)               # y: 0-100%
            cv.create_line(*pts, fill=_blend_hex(bg, color, glow_t), width=3, smooth=True)
            cv.create_line(*pts, fill=color, width=1, smooth=True)

        _spark(self._hud_ram, C["accent_dk"], pulse if r >= 80 else 0.35)
        _spark(self._hud_cpu, "#FFFFFF",      pulse if c >= 80 else 0.35)

    def _pulse_loop(self):
        """~8fps loop that animates Terminal-tab ping dots and the HUD glow (alarm)."""
        visible = self._is_visible()
        try:
            if visible:
                self._pulse_ping_dots()
                self._pulse_hud()
        finally:
            # fewer event-loop wake-ups while minimized / in the tray
            self.after(120 if visible else 800, self._pulse_loop)

    def _pulse_hud(self):
        """Pulse the HUD glow while CPU or RAM usage is high (>= 80%)."""
        if not self._hud_enabled:
            return
        c = int(self._hud_cpu[-1]) if self._hud_cpu else 0
        r = int(self._hud_ram[-1]) if self._hud_ram else 0
        if c < 80 and r < 80:
            return
        t = time.monotonic()
        pulse = 0.35 + 0.55 * (0.5 + 0.5 * math.sin(t * 4.0))
        self._draw_hud(pulse)

    def _pulse_ping_dots(self):
        if not self._conn_ping_enabled or not self._conn_ping_dots:
            return
        t = time.monotonic()
        ok_col   = _blend_hex("#2E8033", "#6FE87E", 0.5 + 0.5 * math.sin(t * 2.0))
        fail_col = _blend_hex(C["btn_del"], C["card"], 0.3 + 0.3 * math.sin(t * 5.0))
        for host, cvs in self._conn_ping_dots.items():
            status = self._conn_ping_cache.get(host)
            if status == "ok":
                color = ok_col
            elif status == "fail":
                color = fail_col
            else:
                continue
            for cv in cvs:
                try:
                    cv.itemconfigure("dot", fill=color)
                except tk.TclError:
                    pass   # widget already destroyed

    def _update_banner(self):
        """Display the next notification in the banner label."""
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
        """Periodically check scheduled notifications (every 30 seconds)"""
        now = datetime.datetime.now()
        updated = False
        for item in self._notify_items:
            sched_str = item.get("scheduled_at", "")
            if not sched_str:
                continue
            try:
                sched = datetime.datetime.fromisoformat(sched_str)
            except ValueError:
                continue
            notify_before = item.get("notify_before", 5)
            notify_at = sched - datetime.timedelta(minutes=notify_before)
            # key by identity (title + time), not list index: deleting an
            # item must not shift another item's "already notified" state
            key = f"{item.get('title', '')}|{sched_str}"
            if notify_at <= now < sched and key not in self._notified:
                self._notified.add(key)
                NotificationPopup(self, item, self._notify_display_sec.get() * 1000)
                if not self._is_visible():
                    self._tray_notify_pending = True
                    self._update_tray_badge()
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
            # if past the scheduled time, update to the next datetime per recurrence setting
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
                    # month-end handling: cap day to the last day of next month
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
    """Load only the theme from config.json before startup and update C."""
    try:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        theme = cfg.get("theme", "violet")
        if theme in THEMES:
            C.update(THEMES[theme])
    except Exception:
        pass


if __name__ == "__main__":
    _preload_theme()
    app = FolderLauncher()
    app.mainloop()
