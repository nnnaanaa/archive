"""
Lavender-themed folder launcher
Manage folders organized by category tabs
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import json
import subprocess
import zlib
import struct
import base64
import ctypes
import datetime
import tempfile
from ctypes import wintypes
from pathlib import Path
from PIL import ImageGrab

CONFIG_FILE   = Path(__file__).parent / "folders.json"
TERM_CONFIG   = Path(__file__).parent / "terminals.json"
TASKS_CONFIG  = Path(__file__).parent / "tasks.json"
TERATERM_LINK = r"C:\Users\nanahira\Desktop\Tera Term 5.lnk"

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

FONT       = ("Segoe UI", 10)
FONT_BOLD  = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 8)


# ── Icon generation ───────────────────────────────────────

def _make_icon_png() -> str:
    W, H = 32, 32
    T  = (  0,   0,   0,   0)
    B  = (106,  91, 168, 255)
    F  = (139, 124, 200, 255)
    HL = (196, 184, 232, 255)

    def px(x, y):
        if 4 <= y <= 8 and 2 <= x <= 12:
            if y == 4 and (x == 2 or x == 12):
                return T
            return B
        if 7 <= y <= 26 and 2 <= x <= 29:
            if (y == 7 and x == 2) or (y == 7 and x == 29): return T
            if (y == 26 and x == 2) or (y == 26 and x == 29): return T
            if y == 7: return HL
            return F
        return T

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

def _get_teraterm_exe() -> str:
    """Get Tera Term executable path from shortcut."""
    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
    lnk = shell.CreateShortCut(TERATERM_LINK)
    return lnk.TargetPath


def _encode_pw(pw: str) -> str:
    return base64.b64encode(pw.encode()).decode()

def _decode_pw(enc: str) -> str:
    try:
        return base64.b64decode(enc.encode()).decode()
    except Exception:
        return ""


def _launch_teraterm(conn: dict):
    """Launch Tera Term with auto-login and command execution."""
    exe   = _get_teraterm_exe()
    host  = conn["host"]
    port  = int(conn.get("port", 22 if conn["protocol"] == "SSH" else 23))
    user  = conn.get("user", "")
    pw    = _decode_pw(conn.get("password", ""))
    proto = conn["protocol"]
    cmds  = [c for c in conn.get("commands", []) if c.strip()]

    PROMPT = "wait '$' '#' '%' '>'"

    if cmds:
        # if commands exist, use TTL script to wait for prompt and send them
        ttl_lines = [
            "timeout = 30",  # prompt wait timeout (seconds)
            PROMPT,
        ]
        for cmd in cmds:
            ttl_lines.append(f"sendln '{cmd}'")
            ttl_lines.append(PROMPT)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl",
                                         delete=False, encoding="utf-8") as f:
            f.write("\n".join(ttl_lines) + "\n")
            ttl_path = f.name
        ttl_arg = [f"/M={ttl_path}"]  # /L= is log file, /M= is macro file
    else:
        ttl_arg = []

    # pass connection info directly via CLI args (more reliable than TTL connect)
    if proto == "SSH":
        args = [
            exe,
            f"{host}:{port}",
            "/ssh", "/2",
            "/auth=password",
            f"/user={user}",
            f"/passwd={pw}",
        ] + ttl_arg
    else:  # Telnet
        args = [
            exe,
            f"{host}:{port}",
            "/telnet",
            f"/user={user}",
            f"/passwd={pw}",
        ] + ttl_arg

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


class ConnectionDialog(tk.Toplevel):
    """Dialog for adding/editing connections."""

    def __init__(self, parent, initial: dict | None = None):
        super().__init__(parent)
        self.title("Add Connection" if initial is None else "Edit Connection")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.result: dict | None = None

        d = initial or {}
        self._name_var = tk.StringVar(value=d.get("name", ""))
        self._proto = tk.StringVar(value=d.get("protocol", "SSH"))
        self._host  = tk.StringVar(value=d.get("host", ""))
        self._port  = tk.StringVar(value=str(d.get("port", 22)))
        self._user  = tk.StringVar(value=d.get("user", ""))
        self._pw    = tk.StringVar(value=_decode_pw(d.get("password", "")))
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
        tk.Label(self._form, text=label, bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="e", width=10).grid(
                     row=row, column=0, padx=(12, 4), pady=3, sticky="e")
        e = tk.Entry(self._form, textvariable=var, font=FONT,
                     bg="#F0EBF8", fg=C["text"], relief="flat", bd=1,
                     insertbackground=C["accent"], width=width, show=show)
        e.grid(row=row, column=1, padx=(0, 12), pady=3, sticky="ew")
        return e

    def _build(self):
        self._form = tk.Frame(self, bg=C["bg"])
        self._form.pack(padx=4, pady=(12, 4))

        self._row("Name",     0, self._name_var)
        # Protocol dropdown
        tk.Label(self._form, text="Protocol", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="e", width=10).grid(
                     row=1, column=0, padx=(12, 4), pady=3, sticky="e")
        combo = ttk.Combobox(self._form, textvariable=self._proto,
                             values=["SSH", "Telnet", "RDP"], state="readonly",
                             font=FONT, width=20)
        combo.grid(row=1, column=1, padx=(0, 12), pady=3, sticky="ew")

        self._row("Host",     2, self._host)
        self._port_entry = self._row("Port", 3, self._port, width=8)
        self._row("Username", 4, self._user)
        self._row("Password", 5, self._pw, show="●")

        # command input area
        tk.Label(self._form, text="Commands", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="ne", width=10).grid(
                     row=6, column=0, padx=(12, 4), pady=(6, 3), sticky="ne")
        self._cmd_text = tk.Text(
            self._form, font=("Consolas", 9),
            bg="#F0EBF8", fg=C["text"], relief="flat", bd=1,
            insertbackground=C["accent"],
            width=24, height=5,
            wrap="none",
        )
        self._cmd_text.insert("1.0", self._init_cmds)
        self._cmd_text.grid(row=6, column=1, padx=(0, 12), pady=(6, 3), sticky="ew")
        tk.Label(self._form, text="One command per line\nExecuted after login",
                 bg=C["bg"], fg=C["text_sub"],
                 font=("Segoe UI", 7), justify="left").grid(
                     row=7, column=1, padx=(0, 12), sticky="w")

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
        defaults = {"SSH": "22", "Telnet": "23", "RDP": "3389"}
        default = defaults.get(self._proto.get(), "22")
        if self._port.get() in ("22", "23", "3389"):
            self._port.set(default)

    def _ok(self):
        if not self._name_var.get().strip() or not self._host.get().strip():
            messagebox.showwarning("Input Error",
                                   "Name and Host are required.", parent=self)
            return
        cmds = [l.strip() for l in self._cmd_text.get("1.0", "end").splitlines()
                if l.strip()]
        self.result = {
            "name":     self._name_var.get().strip(),
            "protocol": self._proto.get(),
            "host":     self._host.get().strip(),
            "port":     int(self._port.get() or 22),
            "user":     self._user.get().strip(),
            "password": _encode_pw(self._pw.get()),
            "commands": cmds,
        }
        self.destroy()


# ── Task dialog ───────────────────────────────────────────

class TaskDialog(tk.Toplevel):
    """Dialog for adding/editing tasks."""

    def __init__(self, parent, initial: dict | None = None):
        super().__init__(parent)
        self.title("Add Task" if initial is None else "Edit Task")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.result: dict | None = None

        d = initial or {}
        self._event_var    = tk.StringVar(value=d.get("event", ""))
        self._process_var  = tk.StringVar(value=d.get("process", ""))
        self._progress_var = tk.IntVar(value=d.get("progress", 0))
        self._deadline_var = tk.StringVar(value=d.get("deadline", ""))
        self._init_content = d.get("content", "")

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

        self._entry_row("Event",   0, self._event_var)
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

        # deadline input
        tk.Label(self._form, text="Deadline", bg=C["bg"], fg=C["text_sub"],
                 font=FONT_SMALL, anchor="e", width=9).grid(
                     row=4, column=0, padx=(12, 4), pady=(6, 3), sticky="e")
        dl_frame = tk.Frame(self._form, bg=C["bg"])
        dl_frame.grid(row=4, column=1, padx=(0, 12), pady=(6, 3), sticky="ew")
        tk.Entry(dl_frame, textvariable=self._deadline_var, font=FONT,
                 bg="#F0EBF8", fg=C["text"], relief="flat", bd=1,
                 insertbackground=C["accent"], width=14).pack(side="left")
        tk.Label(dl_frame, text="YYYY-MM-DD  (optional)",
                 bg=C["bg"], fg=C["text_sub"], font=FONT_SMALL).pack(side="left", padx=(6, 0))

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

    def _ok(self):
        if not self._event_var.get().strip():
            messagebox.showwarning("Input Error", "Event name is required.", parent=self)
            return
        deadline = self._deadline_var.get().strip()
        if deadline:
            try:
                datetime.date.fromisoformat(deadline)
            except ValueError:
                messagebox.showwarning("Input Error",
                                       "Deadline must be YYYY-MM-DD format.", parent=self)
                return
        self.result = {
            "event":    self._event_var.get().strip(),
            "process":  self._process_var.get().strip(),
            "content":  self._content_text.get("1.0", "end").strip(),
            "progress": self._progress_var.get(),
            "deadline": deadline,
        }
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

    def __init__(self):
        super().__init__()
        self.title("Folder Launcher")
        self.geometry("480x480")
        self.resizable(True, True)
        self.configure(bg=C["bg"])
        self.minsize(320, 300)

        self._icon = tk.PhotoImage(data=_make_icon_png())
        self.wm_iconphoto(True, self._icon)

        # folder data: [{"category": "name", "folders": [{"name":..,"path":..}]}, ...]
        self._data: list[dict] = []
        self._active: int = 0   # -1 = Terminal tab
        self._load()

        # terminal connection data
        self._conns: list[dict] = []
        self._load_conns()

        # task data
        self._tasks: list[dict] = []
        self._load_tasks()
        self._task_sort: dict = {"col": None, "reverse": False}

        self._build_ui()
        self._render_tabs()
        self._render_list()

    # ── Folder config read/write ──────────────────────────

    def _load(self):
        if not CONFIG_FILE.exists():
            self._data = [{"category": "General", "folders": []}]
            return
        try:
            raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            # convert old format (flat folder list)
            if raw and isinstance(raw[0], (str, dict)) and "category" not in raw[0]:
                folders = []
                for item in raw:
                    if isinstance(item, str):
                        folders.append({"name": os.path.basename(item) or item, "path": item})
                    else:
                        folders.append(item)
                self._data = [{"category": "General", "folders": folders}]
            else:
                self._data = raw
        except Exception:
            self._data = [{"category": "General", "folders": []}]

        if not self._data:
            self._data = [{"category": "General", "folders": []}]

    def _save(self):
        CONFIG_FILE.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ── Terminal connection config read/write ─────────────

    def _load_conns(self):
        if TERM_CONFIG.exists():
            try:
                self._conns = json.loads(TERM_CONFIG.read_text(encoding="utf-8"))
            except Exception:
                self._conns = []

    def _save_conns(self):
        TERM_CONFIG.write_text(
            json.dumps(self._conns, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ── Task data read/write ───────────────────────────────

    def _load_tasks(self):
        if TASKS_CONFIG.exists():
            try:
                self._tasks = json.loads(TASKS_CONFIG.read_text(encoding="utf-8"))
            except Exception:
                self._tasks = []

    def _save_tasks(self):
        TASKS_CONFIG.write_text(
            json.dumps(self._tasks, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @property
    def _current(self) -> dict:
        return self._data[self._active]

    # ── UI construction ───────────────────────────────────

    def _build_ui(self):
        # header
        hdr = tk.Frame(self, bg=C["accent"], height=36)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Folder Launcher",
                 bg=C["accent"], fg="white", font=FONT_BOLD,
                 ).pack(side="left", padx=12, pady=6)

        self._clock_var = tk.StringVar()
        tk.Label(hdr, textvariable=self._clock_var,
                 bg=C["accent"], fg=C["accent_lt"],
                 font=("Consolas", 9)).pack(side="left", padx=8)
        self._tick()

        tk.Button(hdr, text="Screenshot",
                  command=self._open_screenshot,
                  bg=C["accent_dk"], fg="white", relief="flat", bd=0,
                  font=FONT, cursor="hand2",
                  activebackground=C["accent_lt"], activeforeground=C["text"],
                  padx=10, pady=2).pack(side="right", padx=(0, 8))

        self._show_options = tk.BooleanVar(value=False)
        tk.Checkbutton(hdr, text="Options",
                       variable=self._show_options,
                       bg=C["accent"], fg="white",
                       activebackground=C["accent"], activeforeground="white",
                       selectcolor=C["accent_dk"],
                       relief="flat", bd=0, font=FONT_SMALL,
                       ).pack(side="right", padx=(0, 4))

        # tab bar
        self._tab_bar = tk.Frame(self, bg=C["tab_inact"])
        self._tab_bar.pack(fill="x")

        # scrollable list
        wrapper = tk.Frame(self, bg=C["bg"])
        wrapper.pack(fill="both", expand=True, padx=8, pady=6)

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
        footer = tk.Frame(self, bg=C["bg"], pady=6)
        footer.pack(fill="x", padx=8)
        self._footer_btn = tk.Button(
            footer, text="+ Add Folder",
            command=self._add_folder,
            bg=C["accent"], fg="white", relief="flat", bd=0,
            font=FONT_BOLD, cursor="hand2", padx=12, pady=6,
            activebackground=C["accent_dk"], activeforeground="white",
        )
        self._footer_btn.pack(fill="x")
        _hover(self._footer_btn, C["accent_dk"], C["accent"])

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
                cursor="hand2", padx=10, pady=5,
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
            font=FONT, cursor="hand2", padx=4, pady=5,
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

    def _switch_tab(self, idx: int):
        self._active = idx
        self._render_tabs()
        self._update_footer()
        self._render_list()

    def _update_footer(self):
        """Update footer button text/command based on active tab."""
        if self._active == -1:
            self._footer_btn.configure(text="+ Add Connection", command=self._add_conn)
        elif self._active == -2:
            self._footer_btn.configure(text="+ Add Task", command=self._add_task)
        else:
            self._footer_btn.configure(text="+ Add Folder", command=self._add_folder)

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

    # ── List render (folder/terminal/task switch) ──────────

    def _render_list(self):
        for w in self._list_frame.winfo_children():
            w.destroy()

        if self._active == -1:
            self._render_terminal_list()
        elif self._active == -2:
            self._render_task_list()
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
            ).pack(pady=30)
            return

        for i, entry in enumerate(folders):
            self._make_card(i, entry["name"], entry["path"])

    def _make_card(self, idx: int, name: str, path: str):
        card = tk.Frame(self._list_frame, bg=C["card"],
                        pady=6, padx=10, relief="flat", bd=0,
                        highlightthickness=1, highlightbackground=C["border"])
        card.pack(fill="x", pady=3, padx=2)

        left = tk.Frame(card, bg=C["card"])
        left.pack(side="left", fill="both", expand=True)
        tk.Label(left, text=name,
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

        for widget in (card, left) + tuple(left.winfo_children()):
            widget.bind("<Button-1>", lambda e, p=path: self._open_folder(p))
            widget.bind("<Enter>",    lambda e, f=card: _set_bg(f, C["card_h"]))
            widget.bind("<Leave>",    lambda e, f=card: _set_bg(f, C["card"]))
            widget.configure(cursor="hand2")

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

    # ── Terminal list ─────────────────────────────────────

    def _render_terminal_list(self):
        if not self._conns:
            tk.Label(
                self._list_frame,
                text="No connections registered.\nClick \"+ Add Connection\".",
                bg=C["bg"], fg=C["text_sub"],
                font=FONT_SMALL, justify="center",
            ).pack(pady=30)
            return

        for i, conn in enumerate(self._conns):
            self._make_conn_card(i, conn)

    def _make_conn_card(self, idx: int, conn: dict):
        card = tk.Frame(self._list_frame, bg=C["card"],
                        pady=6, padx=10, relief="flat", bd=0,
                        highlightthickness=1, highlightbackground=C["border"])
        card.pack(fill="x", pady=3, padx=2)

        left = tk.Frame(card, bg=C["card"])
        left.pack(side="left", fill="both", expand=True)

        proto_color = {"SSH": C["accent"], "RDP": C["accent_dk"]}.get(conn["protocol"], C["text_sub"])
        tk.Label(left, text=f"  {conn['name']}",
                 bg=C["card"], fg=C["text"],
                 font=FONT_BOLD, anchor="w").pack(fill="x")
        ncmds = len(conn.get("commands", []))
        cmd_str = f"  {ncmds} cmd{'s' if ncmds != 1 else ''}" if ncmds else ""
        tk.Label(left,
                 text=f"{conn['protocol']}  {conn['user']}@{conn['host']}:{conn.get('port', 22)}{cmd_str}",
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
        dlg = ConnectionDialog(self)
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
        dlg = ConnectionDialog(self, initial=self._conns[idx])
        if dlg.result is None:
            return
        self._conns[idx] = dlg.result
        self._save_conns()
        self._render_list()

    def _connect_server(self, conn: dict):
        try:
            if conn["protocol"] == "RDP":
                _launch_rdp(conn)
            else:
                _launch_teraterm(conn)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect:\n{e}", parent=self)

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
            ).pack(pady=30)
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
        tree.column("process",   width=80,  minwidth=50,  stretch=False)
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
        detail_lbl.pack(padx=8, pady=6, fill="x")

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
            # task rows only (same event group)
            if not _is_task_row(target):
                return
            if tree.parent(src) != tree.parent(target):
                return
            tgt_idx = tree.index(target)
            # insert after if mouse is in lower half of row
            bbox = tree.bbox(target)
            if bbox and e.y >= bbox[1] + bbox[3] // 2:
                tgt_idx += 1
            tree.move(src, tree.parent(src), tgt_idx)
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
        except ValueError:
            return  # skip event parent rows
        self._edit_task(idx)

    def _task_tree_menu(self, event, tree):
        row = tree.identify_row(event.y)
        if not row:
            return
        try:
            idx = int(row)
        except ValueError:
            return  # skip event parent rows
        tree.selection_set(row)
        menu = tk.Menu(self, tearoff=0,
                       bg=C["card"], fg=C["text"],
                       activebackground=C["card_h"], activeforeground=C["text"],
                       relief="flat", font=FONT)
        menu.add_command(label="Edit",   command=lambda: self._edit_task(idx))
        menu.add_separator()
        menu.add_command(label="Delete", command=lambda: self._remove_task(idx))
        menu.tk_popup(event.x_root, event.y_root)

    # ── Task operations ───────────────────────────────────

    def _add_task(self):
        dlg = TaskDialog(self)
        if dlg.result is None:
            return
        dlg.result["updated"] = datetime.date.today().isoformat()
        self._tasks.append(dlg.result)
        self._save_tasks()
        self._render_list()

    def _edit_task(self, idx: int):
        dlg = TaskDialog(self, initial=self._tasks[idx])
        if dlg.result is None:
            return
        dlg.result["updated"] = datetime.date.today().isoformat()
        self._tasks[idx] = dlg.result
        self._save_tasks()
        self._render_list()

    def _remove_task(self, idx: int):
        name = self._tasks[idx]["event"]
        if messagebox.askyesno("Remove", f"Remove \"{name}\"?", parent=self):
            self._tasks.pop(idx)
            self._save_tasks()
            self._render_list()

    # ── Other ─────────────────────────────────────────────

    def _tick(self):
        self._clock_var.set(datetime.datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self._tick)

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
    app = FolderLauncher()
    app.mainloop()
