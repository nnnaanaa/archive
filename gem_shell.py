"""
gem_shell.py - Gem interactive shell
Dedicated REPL for the Gem folder/file launcher.
"""

import base64
import cmd
import ctypes
import datetime
import json
import os
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

# Enable ANSI escape codes on Windows
os.system("")

# Tab completion support (pyreadline3 on Windows)
try:
    import readline
except ImportError:
    try:
        import pyreadline3 as readline  # noqa: F401
    except ImportError:
        readline = None


def _set_console_icon(ico_path: str):
    """Set the console window icon to the specified .ico file."""
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if not hwnd:
            return
        hicon = ctypes.windll.user32.LoadImageW(
            None, ico_path,
            1,           # IMAGE_ICON
            0, 0,
            0x10 | 0x40, # LR_LOADFROMFILE | LR_DEFAULTSIZE
        )
        if hicon:
            ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, hicon)  # WM_SETICON SMALL
            ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, hicon)  # WM_SETICON BIG
    except Exception:
        pass

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_BASE_DIR    = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
CONFIG_FILE  = _BASE_DIR / "config.json"
LOG_DIR      = _BASE_DIR / "logs"
TERATERM_EXE = r"C:\Program Files\teraterm5\ttermpro.exe"

# ── ANSI colors ────────────────────────────────────────────────
R      = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"

ACCENT   = "\033[38;2;139;124;200m"   # #8B7CC8  lavender
ACCENT2  = "\033[38;2;106;91;170m"    # #6A5BAA  darker lavender
HL       = "\033[38;2;220;210;250m"   # #DCD2FA  very light lavender
TEXT_SUB = "\033[38;2;123;109;176m"   # #7B6DB0
SUCCESS  = "\033[38;2;80;180;120m"    # green
WARN     = "\033[38;2;200;160;80m"    # amber
ERR      = "\033[38;2;200;80;80m"     # red
CAT_CLR  = "\033[38;2;196;184;232m"   # category header
FILE_CLR = "\033[38;2;100;190;150m"   # file type tag

# ── Theme definitions (shared palette with gem.py) ──────────────

def _h(hex_color: str) -> str:
    """Convert a hex color (#RRGGBB) to an ANSI foreground escape."""
    c = hex_color.lstrip("#")
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m"

# Import the THEMES palette from gem.py
_GEM_PALETTES: dict[str, dict[str, str]] = {
    "violet": {
        "accent": "#8B7CC8", "accent_dk": "#6A5BAA", "accent_lt": "#C4B8E8",
        "text_sub": "#7B6DB0",
    },
    "dark": {
        "accent": "#7C6FBD", "accent_dk": "#5A4FA0", "accent_lt": "#9A8ED4",
        "text_sub": "#A09CC0",
    },
    "light": {
        "accent": "#6655BB", "accent_dk": "#4A3DA0", "accent_lt": "#A89DD4",
        "text_sub": "#666699",
    },
    "gemini": {
        "accent": "#1B6EF3", "accent_dk": "#1251B5", "accent_lt": "#A8C7FA",
        "text_sub": "#5F6368",
    },
    "claude": {
        "accent": "#DA7756", "accent_dk": "#B85C3C", "accent_lt": "#E89A7A",
        "text_sub": "#9E9890",
    },
    "scarlet": {
        "accent": "#CC2244", "accent_dk": "#991833", "accent_lt": "#E06078",
        "text_sub": "#C09098",
    },
    "ocean": {
        "accent": "#2196C4", "accent_dk": "#1570A0", "accent_lt": "#5BB8D4",
        "text_sub": "#7AAFC8",
    },
    "rose": {
        "accent": "#E0608A", "accent_dk": "#C0407A", "accent_lt": "#F0A0BC",
        "text_sub": "#A06080",
    },
    "mint": {
        "accent": "#3DAA78", "accent_dk": "#2A8A60", "accent_lt": "#80CCA8",
        "text_sub": "#5A8A70",
    },
    "peach": {
        "accent": "#E8845A", "accent_dk": "#C86030", "accent_lt": "#F5C0A0",
        "text_sub": "#A06848",
    },
    "sky": {
        "accent": "#4DA8DA", "accent_dk": "#2A88BE", "accent_lt": "#9DD4F0",
        "text_sub": "#4A80A8",
    },
    "lemon": {
        "accent": "#C8A800", "accent_dk": "#A08800", "accent_lt": "#E8D870",
        "text_sub": "#787040",
    },
    "lavender": {
        "accent": "#9B88D8", "accent_dk": "#7A66C0", "accent_lt": "#C8BCEE",
        "text_sub": "#7868B0",
    },
    "sakura": {
        "accent": "#E87898", "accent_dk": "#C85878", "accent_lt": "#F5B0C8",
        "text_sub": "#A06888",
    },
    "plush": {
        "accent": "#9E92D6", "accent_dk": "#7C6FBF", "accent_lt": "#C6BEE8",
        "text_sub": "#6E65A5",
    },
}

THEMES: dict[str, dict[str, str]] = {
    name: {
        "ACCENT":   _h(p["accent"]),
        "ACCENT2":  _h(p["accent_dk"]),
        "HL":       _h(p["accent_lt"]),
        "TEXT_SUB": _h(p["text_sub"]),
        "CAT_CLR":  _h(p["accent_lt"]),
        "FILE_CLR": _h(p["accent_lt"]),
    }
    for name, p in _GEM_PALETTES.items()
}


def _apply_theme(name: str) -> bool:
    """Overwrite global color variables with the specified theme."""
    global ACCENT, ACCENT2, HL, TEXT_SUB, CAT_CLR, FILE_CLR
    t = THEMES.get(name)
    if not t:
        return False
    ACCENT   = t["ACCENT"]
    ACCENT2  = t["ACCENT2"]
    HL       = t["HL"]
    TEXT_SUB = t["TEXT_SUB"]
    CAT_CLR  = t["CAT_CLR"]
    FILE_CLR = t["FILE_CLR"]
    return True


# ── Terminal helpers ───────────────────────────────────────────

def _decode_pw(enc: str) -> str:
    try:
        return base64.b64decode(enc.encode()).decode()
    except Exception:
        return ""


def _launch_connection(conn: dict):
    """Launch a connection (SSH/Telnet via Tera Term, RDP, SMB)."""
    proto = conn.get("protocol", "SSH")

    if proto == "RDP":
        host = conn["host"]
        port = int(conn.get("port", 3389))
        user = conn.get("user", "")
        pw   = _decode_pw(conn.get("password", ""))
        target = f"TERMSRV/{host}"
        subprocess.run(
            ["cmdkey", f"/generic:{target}", f"/user:{user}", f"/pass:{pw}"],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        address = f"{host}:{port}" if port != 3389 else host
        subprocess.Popen(["mstsc", f"/v:{address}"])
        return

    if proto == "SMB":
        unc  = conn["host"]
        user = conn.get("user", "")
        pw   = _decode_pw(conn.get("password", ""))
        if user and pw:
            subprocess.run(
                ["net", "use", unc, pw, f"/user:{user}"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                capture_output=True,
            )
        os.startfile(unc)
        return

    # SSH / Telnet via Tera Term
    host    = conn["host"]
    port    = int(conn.get("port", 22 if proto == "SSH" else 23))
    user    = conn.get("user", "")
    pw      = _decode_pw(conn.get("password", ""))
    cmds    = [c for c in conn.get("commands", []) if c.strip()]
    charset = conn.get("charset", "UTF-8")
    charset_arg = [f"/KT={charset}"] if charset else []

    LOG_DIR.mkdir(exist_ok=True)
    ts      = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_arg = [f"/L={LOG_DIR / f'{ts}_{host}.log'}"]

    PROMPT = "wait '$' '#' '%' '>'"

    def _ttl_sendln(s: str) -> list[str]:
        if "'" not in s:
            return [f"sendln '{s}'"]
        parts = s.split("'")
        lines = [f"_s = '{parts[0]}'"]
        for part in parts[1:]:
            lines += ["char2str _c 39", "strconcat _s _c"]
            if part:
                lines.append(f"strconcat _s '{part}'")
        lines.append("sendln _s")
        return lines

    def _write_ttl(lines: list[str]) -> str:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl",
                                         delete=False, encoding="utf-8") as f:
            f.write("\r\n".join(lines) + "\r\n")
            return f.name

    if proto == "SSH":
        if cmds:
            ttl_lines = ["timeout = 30", PROMPT]
            for c in cmds:
                ttl_lines += ["timeout = 60", "mpause 300"] + _ttl_sendln(c) + [PROMPT]
            ttl_arg = [f"/M={_write_ttl(ttl_lines)}"]
        else:
            ttl_arg = []
        args = [
            TERATERM_EXE, f"{host}:{port}",
            "/ssh", "/2", "/auth=password",
            f"/user={user}", f"/passwd={pw}",
        ] + charset_arg + log_arg + ttl_arg
    else:  # Telnet
        ttl_lines = [
            "timeout = 30",
            "wait 'ogin:' 'sername:' 'ser:'",
            "mpause 300",
        ] + _ttl_sendln(user) + [
            "wait 'assword:'", "mpause 300",
        ] + _ttl_sendln(pw) + [PROMPT]
        for c in cmds:
            ttl_lines += ["timeout = 60", "mpause 300"] + _ttl_sendln(c) + [PROMPT]
        args = [
            TERATERM_EXE, f"{host}:{port}", "/telnet",
        ] + charset_arg + log_arg + [f"/M={_write_ttl(ttl_lines)}"]

    subprocess.Popen(args)


# ── Data helpers ───────────────────────────────────────────────

def _load_folders() -> list[dict]:
    if not CONFIG_FILE.exists():
        return [{"category": "General", "folders": []}]
    try:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return [{"category": "General", "folders": []}]

    raw = cfg.get("folders", [])
    # Convert legacy format (no category)
    if raw and isinstance(raw[0], (str, dict)) and "category" not in raw[0]:
        items = []
        for item in raw:
            if isinstance(item, str):
                items.append({"name": os.path.basename(item) or item, "path": item})
            else:
                items.append(item)
        return [{"category": "General", "folders": items}]
    return raw or [{"category": "General", "folders": []}]


def _load_conns() -> list[dict]:
    """Load terminal connection list from config.json."""
    if not CONFIG_FILE.exists():
        return []
    try:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return cfg.get("terminals", [])
    except Exception:
        return []


def _load_tasks() -> list[dict]:
    """Load task list from config.json."""
    if not CONFIG_FILE.exists():
        return []
    try:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return cfg.get("tasks", [])
    except Exception:
        return []


def _load_bookmarks() -> list[dict]:
    """Load bookmark categories from config.json."""
    if not CONFIG_FILE.exists():
        return []
    try:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return cfg.get("bookmarks", [])
    except Exception:
        return []


def _all_entries(data: list[dict]) -> list[tuple[str, str, str]]:
    entries = []
    for cat in data:
        category = cat.get("category", "")
        for f in cat.get("folders", []):
            entries.append((category, f.get("name", ""), f.get("path", "")))
    return entries


def _type_tag(path: str) -> str:
    """Return a colored type tag: [dir], [file], or [miss]."""
    if os.path.isdir(path):
        return f"{ACCENT}[dir ]{R}"
    elif os.path.isfile(path):
        return f"{FILE_CLR}[file]{R}"
    else:
        return f"{ERR}[miss]{R}"




def _wcswidth(s: str) -> int:
    """Return terminal display width of a string (fullwidth=2, halfwidth=1)."""
    w = 0
    for c in s:
        ew = unicodedata.east_asian_width(c)
        w += 2 if ew in ("W", "F") else 1
    return w


def _trunc_path(path: str, max_cols: int) -> str:
    """Truncate a path with '...' if its display width exceeds max_cols."""
    if _wcswidth(path) <= max_cols:
        return path
    result = ""
    used = 0
    ellipsis_w = 3  # display width of "..."
    budget = max_cols - ellipsis_w
    for c in path:
        cw = 2 if unicodedata.east_asian_width(c) in ("W", "F") else 1
        if used + cw > budget:
            break
        result += c
        used += cw
    return result + "..."


def _open_path(path: str) -> bool:
    if os.path.isdir(path):
        os.startfile(os.path.normpath(path))
        print(f"  {SUCCESS}opened folder:{R} {path}")
        return True
    elif os.path.isfile(path):
        os.startfile(path)
        print(f"  {SUCCESS}opened file:{R} {path}")
        return True
    else:
        print(f"  {ERR}path does not exist:{R} {path}")
        return False


def _getch_nav() -> str:
    """Read a single keypress and return 'up'/'down'/'enter'/'back'/'quit'/'menu'."""
    try:
        import msvcrt
        ch = msvcrt.getch()
        if ch in (b'\x00', b'\xe0'):   # special key (arrow keys etc.)
            ch2 = msvcrt.getch()
            if ch2 == b'H':
                return 'up'
            if ch2 == b'P':
                return 'down'
            if ch2 == b'M':            # right arrow -> show path
                return 'menu'
            return 'enter'
        if ch == b'\x1b':              # Esc -> go back
            return 'back'
        if ch == b'\x08':              # Backspace -> go back
            return 'back'
        if ch.lower() in (b'q', b'\x03'):   # q / Ctrl+C -> quit
            return 'quit'
        return 'enter'
    except Exception:
        try:
            line = input().strip().lower()
            return 'quit' if line == 'q' else 'enter'
        except Exception:
            return 'quit'


# ── Shell ──────────────────────────────────────────────────────

class GemShell(cmd.Cmd):
    intro = ""
    prompt = f"{ACCENT}{BOLD}cmd{R} {ACCENT2}>{R} "

    def __init__(self, quiet: bool = False):
        super().__init__()
        self._quiet = quiet
        self._data: list[dict] = []
        self._entries: list[tuple[str, str, str]] = []
        self._watchers: dict[str, "threading.Event"] = {}  # path → stop_event
        self._reload()
        # Load and apply theme and prompt label
        cfg_theme = self._load_cfg_str("theme") or "claude"
        _apply_theme(cfg_theme)
        self._prompt_label = self._load_cfg_str("prompt_label")
        self._update_prompt()

    def _update_prompt(self):
        if self._prompt_label:
            self.prompt = f"{ACCENT}{BOLD}{self._prompt_label}{R} {ACCENT2}❯{R} "
        else:
            self.prompt = f"{ACCENT2}❯{R} "

    def _load_cfg_str(self, key: str) -> str:
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return cfg.get(key, "")
        except Exception:
            return ""

    def _save_cfg(self, key: str, value: str):
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8")) if CONFIG_FILE.exists() else {}
            cfg[key] = value
            CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _reload(self):
        self._data = _load_folders()
        self._entries = _all_entries(self._data)
        self._conns = _load_conns()
        self._tasks = _load_tasks()
        self._bookmarks = _load_bookmarks()

    # ── Display helpers ────────────────────────────────────────

    def _print_banner(self):
        # Colors matching gem.ico pixel art
        O = "\033[38;2;42;32;88m"       # outline (dark navy)
        H = "\033[38;2;210;200;240m"    # bright highlight
        L = "\033[38;2;178;165;220m"    # light body
        M = "\033[38;2;120;108;190m"    # medium body
        D = "\033[38;2;88;78;158m"      # dark body

        def row(*cols):
            out = "  "
            for c in cols:
                out += " " if c is None else (c + "█" + R)
            return out

        _ = None

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        char = [
            row(_,_,_,O,D,O,_,_,_,O,D,O,_,_),
            row(_,_,O,H,H,H,L,L,L,L,L,O,_,_),
            row(_,O,H,H,H,L,L,M,M,M,L,L,O,_),
        ]

        title = [
            "",
            f"   {DIM}v1.0.0{R}",
            f"   {TEXT_SUB}started at {now}{R}",
        ]

        print()
        for body, side in zip(char, title):
            print(body + side)
        print()

    def _print_help_hint(self):
        cmds = [
            ("list", "folders"),
            ("open <#|name>", "open"),
            ("tasks", "tasks"),
            ("connect <#|name>", "terminal"),
            ("web [<query>]", "browser"),
            ("help", "help"),
            ("exit", "quit"),
        ]
        sep = f"  {DIM}·{R}  "
        parts = [f"{ACCENT}{BOLD}{c}{R} {DIM}{TEXT_SUB}{d}{R}" for c, d in cmds]
        print(f"  {sep.join(parts)}\n")

    def _print_list(self, filter_cat: str = "", filter_kw: str = ""):
        if not self._entries:
            print(f"  {WARN}No entries registered.{R}")
            return

        # Collect filtered entries
        filtered: list[tuple[int, str, str, str]] = []
        for idx, (cat, name, path) in enumerate(self._entries, 1):
            if filter_cat and filter_cat.lower() not in cat.lower():
                continue
            if filter_kw and filter_kw.lower() not in name.lower() and filter_kw.lower() not in path.lower():
                continue
            filtered.append((idx, cat, name, path))

        if not filtered:
            print(f"  {WARN}No matching entries.{R}")
            return

        self._interactive_list(filtered)

    def _interactive_list(self, filtered: list):
        """Two-level interactive list: category -> item selection."""
        # Group items by category (preserve insertion order)
        groups: dict[str, list[tuple]] = {}
        for entry in filtered:
            idx, cat, name, path = entry
            groups.setdefault(cat, []).append(entry)
        cats = list(groups.keys())

        try:
            term_h = os.get_terminal_size().lines
        except OSError:
            term_h = 24
        visible = max(3, term_h - 7)

        # ── Level 1: category selection ─────────────────────
        def select_category() -> str | None:
            """Display category list; return selected name or None on q."""
            sel = 0
            top = 0
            n   = len(cats)
            while True:
                os.system("cls")
                print(f"\n  {DIM}Select category  up/down=move  Enter=select  Esc/q=quit{R}\n")
                if top > 0:
                    print(f"  {DIM}  ︙{R}")
                for i in range(top, min(top + visible, n)):
                    cat   = cats[i]
                    count = len(groups[cat])
                    if i == sel:
                        print(f"  {ACCENT}{BOLD}▶ [{cat}]{R}  {DIM}{count} items{R}")
                    else:
                        print(f"    {CAT_CLR}[{cat}]{R}  {DIM}{count} items{R}")
                if top + visible < n:
                    print(f"  {DIM}  ︙{R}")

                try:
                    key = _getch_nav()
                except KeyboardInterrupt:
                    return None

                if key in ('quit', 'back'):
                    return None
                elif key == 'up' and sel > 0:
                    sel -= 1
                    if sel < top:
                        top = sel
                elif key == 'down' and sel < n - 1:
                    sel += 1
                    if sel >= top + visible:
                        top += 1
                elif key == 'enter':
                    return cats[sel]

        # ── Level 2: item selection ──────────────────────────
        def select_item(cat: str) -> bool:
            """Display items; Esc/Backspace returns to category; False=quit."""
            items     = groups[cat]
            n         = len(items)
            sel       = 0
            top       = 0
            show_path = False
            while True:
                os.system("cls")
                print(f"\n  {CAT_CLR}{BOLD}[{cat}]{R}  {DIM}{n} items  up/down=move  Enter=open  →=path  Esc=back  q=quit{R}\n")
                if top > 0:
                    print(f"  {DIM}  ︙{R}")
                for i in range(top, min(top + visible, n)):
                    idx, _, name, path = items[i]
                    tag = _type_tag(path)
                    if i == sel:
                        print(f"  {ACCENT}{BOLD}▶{R} {DIM}{idx:3d}.{R} {tag} {ACCENT}{BOLD}{name}{R}")
                        if show_path:
                            full = str(Path(path).resolve())
                            print(f"       {DIM}path:{R} {HL}{full}{R}")
                    else:
                        print(f"     {DIM}{idx:3d}.{R} {tag} {name}")
                if top + visible < n:
                    print(f"  {DIM}  ︙{R}")

                try:
                    key = _getch_nav()
                except KeyboardInterrupt:
                    return False

                if key == 'quit':
                    return False
                elif key == 'back':
                    return True   # return to category selection
                elif key == 'up' and sel > 0:
                    sel -= 1
                    if sel < top:
                        top = sel
                elif key == 'down' and sel < n - 1:
                    sel += 1
                    if sel >= top + visible:
                        top += 1
                elif key == 'menu':
                    show_path = not show_path
                elif key == 'enter':
                    _, _, name, path = items[sel]
                    _open_path(path)

        # ── Main loop ────────────────────────────────────────
        while True:
            cat = select_category()
            if cat is None:
                break
            if not select_item(cat):
                break

        os.system("cls")

    # ── Commands ───────────────────────────────────────────────

    def do_list(self, arg: str):
        """List entries.  list [-c CATEGORY] [-f KEYWORD]"""
        tokens = arg.split()
        cat_f = kw_f = ""
        i = 0
        while i < len(tokens):
            if tokens[i] == "-c" and i + 1 < len(tokens):
                cat_f = tokens[i + 1]; i += 2
            elif tokens[i] == "-f" and i + 1 < len(tokens):
                kw_f = tokens[i + 1]; i += 2
            else:
                kw_f = tokens[i]; i += 1
        self._print_list(cat_f, kw_f)

    def do_open(self, arg: str):
        """Open a folder or file.  open <#|name> [--all]"""
        tokens = arg.split()
        if not tokens:
            print(f"  {WARN}Usage: open <index|name>{R}")
            return

        open_all = "--all" in tokens
        tokens = [t for t in tokens if t != "--all"]
        query = " ".join(tokens)

        if query.isdigit():
            idx = int(query) - 1
            if 0 <= idx < len(self._entries):
                _, name, path = self._entries[idx]
                print(f"  {TEXT_SUB}[{name}]{R} opening...")
                _open_path(path)
            else:
                print(f"  {ERR}Index {query} out of range (1-{len(self._entries)}){R}")
            return

        q = query.lower()
        matched = [(cat, name, path) for cat, name, path in self._entries
                   if q in name.lower() or q in path.lower()]

        if not matched:
            print(f"  {ERR}No match for '{query}'.{R}")
            print(f"  {DIM}Hint: run 'list' to see all entries.{R}")
            return

        if len(matched) == 1 or open_all:
            for _, name, path in matched:
                _open_path(path)
            return

        print(f"  {WARN}Multiple matches:{R}")
        for i, (cat, name, path) in enumerate(matched, 1):
            tag = _type_tag(path)
            print(f"  {ACCENT}{i}.{R} {tag} [{cat}] {BOLD}{name}{R}  {DIM}{path}{R}")
        try:
            choice = input(f"\n  {ACCENT2}Enter number (a = open all, Enter = cancel):{R} ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if choice.lower() == "a":
            for _, name, path in matched:
                _open_path(path)
        elif choice.isdigit():
            c = int(choice) - 1
            if 0 <= c < len(matched):
                _open_path(matched[c][2])
            else:
                print(f"  {ERR}Invalid number.{R}")

    def do_find(self, arg: str):
        """Search entries without opening.  find <keyword>"""
        if not arg.strip():
            print(f"  {WARN}Usage: find <keyword>{R}")
            return
        q = arg.strip().lower()
        matched = [(cat, name, path) for cat, name, path in self._entries
                   if q in name.lower() or q in path.lower()]
        if not matched:
            print(f"  {WARN}No matches for '{arg.strip()}'.{R}")
            return
        print(f"\n  {ACCENT}Results for '{arg.strip()}' ({len(matched)} found){R}")
        for cat, name, path in matched:
            tag = _type_tag(path)
            print(f"  {tag} {DIM}[{cat}]{R} {BOLD}{name}{R}  {TEXT_SUB}{path}{R}")

    def do_tasks(self, arg: str):
        """Show task list.  tasks [-e EVENT] [--done] [--todo] [--content] [--recur] [--folders]"""
        tokens = arg.split()
        event_f = ""
        show_done = show_todo = False
        show_content = show_recur = show_folders = False
        i = 0
        while i < len(tokens):
            if tokens[i] == "-e" and i + 1 < len(tokens):
                event_f = tokens[i + 1]; i += 2
            elif tokens[i] == "--done":
                show_done = True; i += 1
            elif tokens[i] == "--todo":
                show_todo = True; i += 1
            elif tokens[i] == "--content":
                show_content = True; i += 1
            elif tokens[i] == "--recur":
                show_recur = True; i += 1
            elif tokens[i] == "--folders":
                show_folders = True; i += 1
            else:
                event_f = tokens[i]; i += 1

        tasks = self._tasks
        if not tasks:
            print(f"  {WARN}No tasks registered.{R}")
            return

        # Filter
        if event_f:
            tasks = [t for t in tasks if event_f.lower() in t.get("event", "").lower()]
        if show_done:
            tasks = [t for t in tasks if t.get("done") or t.get("progress", 0) >= 100]
        elif show_todo:
            tasks = [t for t in tasks if not t.get("done") and t.get("progress", 0) < 100]

        if not tasks:
            print(f"  {WARN}No matching tasks.{R}")
            return

        today = datetime.date.today()

        # Group by event
        groups: dict[str, list[dict]] = {}
        for t in tasks:
            groups.setdefault(t.get("event", ""), []).append(t)

        for event, group in groups.items():
            print(f"\n  {CAT_CLR}{BOLD}[{event}]{R}")
            for t in group:
                prog   = t.get("progress", 0)
                done   = t.get("done", False) or prog >= 100
                name   = t.get("process", "(no title)")
                dl_str = t.get("deadline", "")

                # Status indicator
                if done:
                    status = f"{SUCCESS}[x]{R}"
                elif prog >= 50:
                    status = f"{ACCENT}[/]{R}"
                else:
                    status = f"{DIM}[ ]{R}"

                # Progress bar (10 cells) + percentage
                filled = round(prog / 10)
                bar = f"{ACCENT}{'█' * filled}{DIM}{'░' * (10 - filled)}{R} {BOLD}{prog:3d}%{R}"

                # Deadline
                dl_part = ""
                if dl_str:
                    try:
                        dl = datetime.date.fromisoformat(dl_str)
                        diff = (dl - today).days
                        if done:
                            dl_part = f"  {DIM}{dl_str}{R}"
                        elif diff < 0:
                            dl_part = f"  {ERR}overdue {dl_str}{R}"
                        elif diff == 0:
                            dl_part = f"  {WARN}due today{R}"
                        elif diff <= 3:
                            dl_part = f"  {WARN}due {dl_str}{R}"
                        else:
                            dl_part = f"  {TEXT_SUB}{dl_str}{R}"
                    except ValueError:
                        dl_part = f"  {TEXT_SUB}{dl_str}{R}"

                print(f"  {status} {bar} {BOLD}{name}{R}{dl_part}")

                if show_recur:
                    recur = t.get("recur", "none")
                    if recur and recur != "none":
                        print(f"         {DIM}recur:{R} {TEXT_SUB}{recur}{R}")

                if show_folders:
                    folders = t.get("work_folders") or ([t["work_folder"]] if t.get("work_folder") else [])
                    for f in folders:
                        print(f"         {DIM}folder:{R} {TEXT_SUB}{f}{R}")

                if show_content:
                    content = t.get("content", "").strip()
                    if content:
                        for line in content.splitlines():
                            print(f"         {DIM}│{R} {TEXT_SUB}{line}{R}")

    def _confirm_and_launch(self, c: dict) -> bool:
        """Show connection info, ask y/N, then launch if confirmed. Returns True if launched."""
        proto = c.get("protocol", "SSH")
        name  = c.get("name", c["host"])
        host  = c.get("host", "")
        print(f"\n  {BOLD}{name}{R}  {DIM}[{proto}]  {host}{R}")
        try:
            ans = input(f"  {ACCENT2}Connect? [y/N]:{R} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return False
        if ans == "y":
            _launch_connection(c)
            print(f"  {SUCCESS}Launched.{R}")
            return True
        print(f"  {DIM}Cancelled.{R}")
        return False

    def do_connect(self, arg: str):
        """Connect to a terminal.  connect [<#|name>]"""
        if not arg.strip():
            self._interactive_connect()
            return

        query = arg.strip()

        if query.isdigit():
            idx = int(query) - 1
            if 0 <= idx < len(self._conns):
                c = self._conns[idx]
                self._confirm_and_launch(c)
            else:
                print(f"  {ERR}Index {query} out of range (1-{len(self._conns)}){R}")
            return

        q = query.lower()
        matched = [c for c in self._conns
                   if q in c.get("name", "").lower() or q in c.get("host", "").lower()]

        if not matched:
            print(f"  {ERR}No connection matching '{query}'.{R}")
            print(f"  {DIM}Hint: run 'connect' to see all connections.{R}")
            return

        if len(matched) == 1:
            c = matched[0]
            self._confirm_and_launch(c)
            return

        print(f"  {WARN}Multiple matches:{R}")
        for i, c in enumerate(matched, 1):
            proto = c.get("protocol", "SSH")
            print(f"  {ACCENT}{i}.{R} [{proto}] {BOLD}{c.get('name', c['host'])}{R}  {DIM}{c['host']}{R}")
        try:
            choice = input(f"\n  {ACCENT2}Enter number (Enter = cancel):{R} ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if choice.isdigit():
            c_idx = int(choice) - 1
            if 0 <= c_idx < len(matched):
                c = matched[c_idx]
                self._confirm_and_launch(c)
            else:
                print(f"  {ERR}Invalid number.{R}")

    def _interactive_connect(self):
        """2-level interactive connect: group -> connection."""
        if not self._conns:
            print(f"  {WARN}No connections registered.{R}")
            return

        # Group connections by group name (empty -> "(ungrouped)")
        groups: dict[str, list[dict]] = {}
        for c in self._conns:
            grp = c.get("group", "") or "(ungrouped)"
            groups.setdefault(grp, []).append(c)
        grp_names = list(groups.keys())

        try:
            term_h = os.get_terminal_size().lines
        except OSError:
            term_h = 24
        visible = max(3, term_h - 7)

        # ── Level 1: group selection ──────────────────────────
        def select_group() -> str | None:
            sel = 0
            top = 0
            n   = len(grp_names)
            while True:
                os.system("cls")
                print(f"\n  {DIM}Select group  up/down=move  Enter=select  Esc/q=quit{R}\n")
                if top > 0:
                    print(f"  {DIM}  ︙{R}")
                for i in range(top, min(top + visible, n)):
                    grp   = grp_names[i]
                    count = len(groups[grp])
                    if i == sel:
                        print(f"  {ACCENT}{BOLD}▶ [{grp}]{R}  {DIM}{count} items{R}")
                    else:
                        print(f"    {CAT_CLR}[{grp}]{R}  {DIM}{count} items{R}")
                if top + visible < n:
                    print(f"  {DIM}  ︙{R}")

                try:
                    key = _getch_nav()
                except KeyboardInterrupt:
                    return None

                if key in ('quit', 'back'):
                    return None
                elif key == 'up' and sel > 0:
                    sel -= 1
                    if sel < top:
                        top = sel
                elif key == 'down' and sel < n - 1:
                    sel += 1
                    if sel >= top + visible:
                        top += 1
                elif key == 'enter':
                    return grp_names[sel]

        # ── Level 2: connection selection ─────────────────────
        def select_conn(grp: str) -> bool:
            conns       = groups[grp]
            n           = len(conns)
            sel         = 0
            top         = 0
            show_detail = False
            while True:
                os.system("cls")
                print(f"\n  {CAT_CLR}{BOLD}[{grp}]{R}  {DIM}{n} items  up/down=move  Enter=connect  →=detail  Esc=back  q=quit{R}\n")
                if top > 0:
                    print(f"  {DIM}  ︙{R}")
                for i in range(top, min(top + visible, n)):
                    c     = conns[i]
                    proto = c.get("protocol", "SSH")
                    host  = c.get("host", "")
                    port  = c.get("port", 22 if proto == "SSH" else 23 if proto == "Telnet" else "")
                    user  = c.get("user", "")
                    name  = c.get("name", host)
                    tag   = f"{ACCENT}[{proto:<6}]{R}"
                    if i == sel:
                        print(f"  {ACCENT}{BOLD}▶{R} {tag} {ACCENT}{BOLD}{name}{R}  {DIM}{host}{R}")
                        if show_detail:
                            detail = f"{host}:{port}" if port else host
                            if user:
                                detail += f"  {DIM}user:{R} {HL}{user}{R}"
                            print(f"       {DIM}host:{R} {HL}{detail}{R}")
                    else:
                        print(f"     {tag} {name}  {TEXT_SUB}{host}{R}")
                if top + visible < n:
                    print(f"  {DIM}  ︙{R}")

                try:
                    key = _getch_nav()
                except KeyboardInterrupt:
                    return False

                if key == 'quit':
                    return False
                elif key == 'back':
                    return True
                elif key == 'menu':
                    show_detail = not show_detail
                elif key == 'up' and sel > 0:
                    sel -= 1
                    if sel < top:
                        top = sel
                elif key == 'down' and sel < n - 1:
                    sel += 1
                    if sel >= top + visible:
                        top += 1
                elif key == 'enter':
                    c = conns[sel]
                    self._confirm_and_launch(c)

        while True:
            grp = select_group()
            if grp is None:
                break
            if not select_conn(grp):
                break

        os.system("cls")

    def do_web(self, arg: str):
        """Open a bookmark in the browser.  web [<query>]"""
        if not self._bookmarks:
            print(f"  {WARN}No bookmarks registered.{R}")
            return

        # Flatten all items with their category for search
        all_items: list[tuple[str, dict]] = [
            (cat["category"], item)
            for cat in self._bookmarks
            for item in cat.get("items", [])
        ]

        if arg.strip():
            q = arg.strip().lower()
            matched = [
                (cat, item) for cat, item in all_items
                if q in item.get("name", "").lower() or q in item.get("url", "").lower()
            ]
            if not matched:
                print(f"  {ERR}No bookmark matching '{arg.strip()}'.{R}")
                print(f"  {DIM}Hint: run 'web' to browse all bookmarks.{R}")
                return
            if len(matched) == 1:
                cat, item = matched[0]
                self._open_bookmark(cat, item)
                return
            print(f"\n  {WARN}Multiple matches:{R}\n")
            for i, (cat, item) in enumerate(matched, 1):
                print(f"  {ACCENT}{i}.{R} {BOLD}{item['name']}{R}  "
                      f"{DIM}{cat}{R}  {ACCENT2}{item['url']}{R}")
            try:
                choice = input(f"\n  {ACCENT2}Enter number (Enter = cancel):{R} ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return
            if choice.isdigit():
                c_idx = int(choice) - 1
                if 0 <= c_idx < len(matched):
                    cat, item = matched[c_idx]
                    self._open_bookmark(cat, item)
                else:
                    print(f"  {ERR}Invalid number.{R}")
            return

        # Interactive 2-level: category → item
        self._interactive_web()

    def _open_bookmark(self, category: str, item: dict):
        """Print bookmark info and open in browser."""
        import webbrowser
        name = item.get("name", item["url"])
        url  = item["url"]
        print(f"\n  {BOLD}{name}{R}  {DIM}[{category}]{R}")
        print(f"  {ACCENT2}{url}{R}")
        try:
            ans = input(f"  {ACCENT2}Open in browser? [y/N]:{R} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if ans == "y":
            webbrowser.open(url)
            print(f"  {SUCCESS}Opened.{R}")
        else:
            print(f"  {DIM}Cancelled.{R}")

    def _interactive_web(self):
        """2-level interactive browser: category -> bookmark."""
        all_items: list[tuple[str, dict]] = [
            (cat["category"], item)
            for cat in self._bookmarks
            for item in cat.get("items", [])
        ]
        if not all_items:
            print(f"  {WARN}No bookmarks registered.{R}")
            return

        # Group by category (preserve order)
        cat_order: list[str] = []
        cat_map: dict[str, list[dict]] = {}
        for cat in self._bookmarks:
            name = cat["category"]
            items = cat.get("items", [])
            if items:
                cat_order.append(name)
                cat_map[name] = items

        if not cat_order:
            print(f"  {WARN}No bookmarks registered.{R}")
            return

        visible = 12

        def select_category() -> str | None:
            """Display category list; return selected name or None on q."""
            cats = cat_order
            n = len(cats)
            sel = 0
            top = 0
            while True:
                os.system("cls")
                print(f"\n  {ACCENT}{BOLD}Web — Select Category{R}\n")
                end = min(top + visible, n)
                for i in range(top, end):
                    bar = f"{ACCENT}▌{R} " if i == sel else "  "
                    active = BOLD if i == sel else ""
                    count = len(cat_map[cats[i]])
                    print(f"  {bar}{active}{cats[i]}{R}  {DIM}({count}){R}")
                print(f"\n  {DIM}↑↓ move  Enter select  q quit{R}")
                key = _getch_nav()
                if key == 'up'   and sel > 0:
                    sel -= 1
                    if sel < top:
                        top -= 1
                elif key == 'down' and sel < n - 1:
                    sel += 1
                    if sel >= top + visible:
                        top += 1
                elif key == 'enter':
                    return cats[sel]
                elif key in ('quit', 'back'):
                    return None

        def select_item(cat_name: str) -> bool:
            """Display items in category; Esc/Backspace returns to category; False=quit."""
            items = cat_map[cat_name]
            n = len(items)
            sel = 0
            top = 0
            while True:
                os.system("cls")
                print(f"\n  {ACCENT}{BOLD}Web — {cat_name}{R}\n")
                end = min(top + visible, n)
                for i in range(top, end):
                    bar = f"{ACCENT}▌{R} " if i == sel else "  "
                    active = BOLD if i == sel else ""
                    item = items[i]
                    print(f"  {bar}{active}{item.get('name', item['url'])}{R}  "
                          f"{DIM}{item['url']}{R}")
                print(f"\n  {DIM}↑↓ move  Enter open  Esc/← back  q quit{R}")
                key = _getch_nav()
                if key == 'up'   and sel > 0:
                    sel -= 1
                    if sel < top:
                        top -= 1
                elif key == 'down' and sel < n - 1:
                    sel += 1
                    if sel >= top + visible:
                        top += 1
                elif key == 'enter':
                    self._open_bookmark(cat_name, items[sel])
                    return True
                elif key == 'back':
                    return True  # return to category selection
                elif key == 'quit':
                    return False

        while True:
            cat = select_category()
            if cat is None:
                break
            if not select_item(cat):
                break

        os.system("cls")

    def do_theme(self, arg: str):
        """Switch theme.  theme [name]"""
        name = arg.strip().lower()
        if not name:
            current = self._load_cfg_str("theme") or "lavender"
            print(f"\n  {ACCENT}Available themes:{R}\n")
            for t in THEMES:
                marker = f"  {SUCCESS}←{R}" if t == current else ""
                swatch = THEMES[t]["ACCENT"] + "██" + R
                print(f"  {swatch}  {BOLD}{t}{R}{marker}")
            print(f"\n  {DIM}Usage: theme <name>{R}\n")
            return
        if not _apply_theme(name):
            print(f"  {ERR}Unknown theme '{name}'.{R}  {DIM}Available: {', '.join(THEMES)}{R}")
            return
        self._update_prompt()
        self._save_cfg("theme", name)
        print(f"  {SUCCESS}Theme changed to '{name}'.{R}")

    def do_prompt(self, arg: str):
        """Change the prompt label.  prompt [label]"""
        label = arg.strip()
        if not label:
            print(f"  {DIM}current:{R} {ACCENT}{BOLD}{self._prompt_label}{R} {ACCENT2}>{R}")
            print(f"  {DIM}Usage: prompt <label>   reset: prompt cmd{R}")
            return
        self._prompt_label = label
        self._update_prompt()
        self._save_cfg("prompt_label", label)
        print(f"  {SUCCESS}Prompt changed to '{label}'.{R}")

    def _resolve_path(self, query: str) -> tuple[str, str] | None:
        """Resolve a query (index/name/path) to a folder (name, path)."""
        if query.isdigit():
            idx = int(query) - 1
            if not (0 <= idx < len(self._entries)):
                print(f"  {ERR}Index {query} out of range.{R}")
                return None
            _, name, path = self._entries[idx]
            return name, path
        if os.path.isdir(query.rstrip("\\/")):
            path = query.rstrip("\\/")
            return os.path.basename(path) or path, path
        q = query.lower()
        matched = [(n, p) for _, n, p in self._entries if q in n.lower() or q in p.lower()]
        if not matched:
            print(f"  {ERR}No match for '{query}'.{R}")
            return None
        return matched[0]

    def do_watch(self, arg: str):
        """Watch a folder for changes in the background.  watch <#|name|path> [-r]"""
        import threading

        tokens = arg.split()
        if not tokens:
            # Show list of watched folders
            if not self._watchers:
                print(f"  {DIM}No folders being watched.{R}")
            else:
                print(f"\n  {ACCENT}Watching:{R}")
                for p in self._watchers:
                    print(f"  {DIM}·{R} {p}")
                print()
            return

        recursive = "-r" in tokens
        tokens = [t for t in tokens if t != "-r"]
        query = " ".join(tokens)

        result = self._resolve_path(query)
        if result is None:
            return
        name, path = result

        if not os.path.isdir(path):
            print(f"  {ERR}'{path}' is not a directory.{R}")
            return

        if path in self._watchers:
            print(f"  {WARN}'{name}' is already being watched.{R}")
            return

        try:
            import win32file, win32con
        except ImportError:
            print(f"  {ERR}pywin32 is required.{R}")
            return

        _ACTIONS = {
            1: (SUCCESS, "added "),
            2: (ERR,     "removed"),
            3: (WARN,    "modified"),
            4: (DIM,     "renamed"),
            5: (ACCENT,  "→     "),
        }

        stop_event = threading.Event()
        self._watchers[path] = stop_event

        def _watcher():
            flags = (
                win32con.FILE_NOTIFY_CHANGE_FILE_NAME  |
                win32con.FILE_NOTIFY_CHANGE_DIR_NAME   |
                win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
                win32con.FILE_NOTIFY_CHANGE_SIZE
            )
            try:
                hdir = win32file.CreateFile(
                    path, win32con.GENERIC_READ,
                    win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
                    None, win32con.OPEN_EXISTING, win32con.FILE_FLAG_BACKUP_SEMANTICS, None,
                )
                while not stop_event.is_set():
                    results = win32file.ReadDirectoryChangesW(hdir, 65536, recursive, flags, None, None)
                    if stop_event.is_set():
                        break
                    ts = datetime.datetime.now().strftime("%H:%M:%S")
                    for action, fname in results:
                        clr, label = _ACTIONS.get(action, (DIM, "?     "))
                        sys.stdout.write(f"\n  {clr}{BOLD}{label}{R}  {DIM}[{ts}] [{name}]{R}  {fname}\n")
                        sys.stdout.flush()
                win32file.CloseHandle(hdir)
            except Exception:
                pass
            finally:
                self._watchers.pop(path, None)

        threading.Thread(target=_watcher, daemon=True).start()
        rec_label = "(recursive)" if recursive else ""
        print(f"  {SUCCESS}Watching:{R} {name}  {DIM}{rec_label}  use 'unwatch' to stop{R}")

    def do_unwatch(self, arg: str):
        """Stop watching a folder.  unwatch <#|name|path|all>"""
        query = arg.strip()

        if not self._watchers:
            print(f"  {DIM}No folders being watched.{R}")
            return

        if query.lower() == "all":
            for ev in self._watchers.values():
                ev.set()
            self._watchers.clear()
            print(f"  {SUCCESS}All watchers stopped.{R}")
            return

        if not query:
            print(f"  {WARN}Usage: unwatch <index|name|path|all>{R}")
            return

        # Resolve path (direct path or entry name)
        if os.path.isdir(query.rstrip("\\/")):
            path = query.rstrip("\\/")
        else:
            q = query.lower()
            matched = [p for p in self._watchers if q in p.lower() or q in os.path.basename(p).lower()]
            if not matched:
                # Resolve from entry name
                result = self._resolve_path(query)
                if result:
                    path = result[1]
                else:
                    return
            else:
                path = matched[0]

        if path not in self._watchers:
            print(f"  {WARN}'{path}' is not being watched.{R}")
            return

        self._watchers[path].set()
        print(f"  {SUCCESS}Stopped watching:{R} {path}")

    def do_gem(self, _):
        """Launch gem.py or bring the tray window to the foreground.  gem"""
        hwnd = ctypes.windll.user32.FindWindowW(None, "Gem")
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 9)   # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            print(f"  {SUCCESS}Gem brought to foreground.{R}")
        else:
            gem_path = _BASE_DIR / "gem.py"
            subprocess.Popen(
                [sys.executable, str(gem_path)],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            )
            print(f"  {SUCCESS}Gem launched.{R}")

    def do_reload(self, _):
        """Reload config.json."""
        self._reload()
        if not self._quiet:
            self._print_banner()
        self._print_help_hint()
        print(f"  {SUCCESS}Reloaded.{R} ({len(self._entries)} folders, {len(self._conns)} connections, {len(self._tasks)} tasks)")
        self._print_wip_tasks()

    def do_help(self, arg: str):
        """Show help."""
        print(f"""
  {ACCENT}{BOLD}Commands{R}

  {ACCENT}list{R}                     Show all registered entries
  {ACCENT}list -c{R} <category>       Filter by category
  {ACCENT}list -f{R} <keyword>        Filter by name/path keyword

  {ACCENT}open{R} <#|name>            Open by index or name
  {ACCENT}open{R} <name> {DIM}--all{R}        Open all matches

  {ACCENT}find{R} <keyword>           Search without opening

  {ACCENT}watch{R} <#|name|path>       Watch folder changes in background
  {ACCENT}watch{R} <#|name|path> {DIM}-r{R}   Watch recursively (include subfolders)
  {ACCENT}watch{R}                    List active watchers
  {ACCENT}unwatch{R} <#|name|path>    Stop watching a folder
  {ACCENT}unwatch all{R}              Stop all watchers

  {ACCENT}tasks{R}                    Show all tasks
  {ACCENT}tasks -e{R} <event>         Filter by event/category
  {ACCENT}tasks --todo{R}             Show incomplete tasks only
  {ACCENT}tasks --done{R}             Show completed tasks only
  {ACCENT}tasks --content{R}          Show memo/notes
  {ACCENT}tasks --recur{R}            Show recurrence setting
  {ACCENT}tasks --folders{R}          Show work folders

  {ACCENT}connect{R}                  List terminal connections
  {ACCENT}connect{R} <#|name>         Connect to a terminal

  {ACCENT}theme{R}                    List available themes
  {ACCENT}theme{R} <name>             Switch theme  {DIM}({', '.join(THEMES)}){R}

  {ACCENT}prompt{R}                   Show current prompt label
  {ACCENT}prompt{R} <label>           Change prompt label  {DIM}(e.g. prompt ★  prompt gem){R}

  {ACCENT}gem{R}                      Launch Gem / restore from tray

  {ACCENT}reload{R}                   Reload config.json
  {ACCENT}!{R}<command>               Run a system command  {DIM}(e.g. !dir  !ipconfig){R}

  {ACCENT}exit{R} / {ACCENT}quit{R}               Quit the shell

  {DIM}Type indicators:{R}
  {ACCENT}[dir ]{R}  folder    {FILE_CLR}[file]{R}  file    {ERR}[miss]{R}  not found
""")

    def do_keytest(self, _):
        """Key inspector: shows hex codes for pressed keys. Ctrl+C to exit."""
        import msvcrt
        print(f"  {DIM}Press any key (Ctrl+C to exit)...{R}")
        try:
            while True:
                ch = msvcrt.getch()
                if ch == b'\x03':
                    break
                if ch in (b'\x00', b'\xe0'):
                    ch2 = msvcrt.getch()
                    print(f"  {ACCENT}special:{R} {ch!r} + {ch2!r}  (hex: {ch.hex()} {ch2.hex()})")
                else:
                    print(f"  {ACCENT}key:{R} {ch!r}  (hex: {ch.hex()})")
        except KeyboardInterrupt:
            pass
        print(f"  {DIM}done{R}")

    def do_exit(self, _):
        """Exit the shell."""
        print(f"\n  {TEXT_SUB}Bye!{R}\n")
        return True

    def do_quit(self, _):
        """Exit the shell."""
        return self.do_exit(_)

    def default(self, line: str):
        if line.startswith("!"):
            cmd = line[1:].strip()
            if cmd:
                subprocess.run(cmd, shell=True)
            return
        print(f"  {ERR}Unknown command:{R} {line}  {DIM}(type 'help' for list){R}")

    def emptyline(self):
        pass

    def cmdloop(self, intro=None):
        """Override cmdloop to print a colored prompt while preserving tab completion."""
        _rl = readline  # module-level readline (pyreadline3 fallback already applied)
        if self.completekey and _rl is not None:
            self._old_completer = _rl.get_completer()
            _rl.set_completer(self.complete)
            _rl.parse_and_bind(self.completekey + ": complete")
        try:
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    now = datetime.datetime.now().strftime("%H:%M")
                    time_prefix = f"{TEXT_SUB}{now}{R} "
                    sys.stdout.write(time_prefix + self.prompt)
                    sys.stdout.flush()
                    try:
                        line = input()
                    except EOFError:
                        line = "EOF"
                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
            self.postloop()
        finally:
            if self.completekey and _rl is not None:
                _rl.set_completer(self._old_completer)

    def _print_wip_tasks(self):
        """Display the currently active task (started via StartWork) at startup."""
        if not CONFIG_FILE.exists():
            return
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return
        aw = cfg.get("active_work")
        if not aw:
            return

        # Find the task matching active_work by event+process
        t = next(
            (x for x in self._tasks
             if x.get("event") == aw.get("event") and x.get("process") == aw.get("process")),
            None,
        )
        name  = aw.get("process", "(no title)")
        event = aw.get("event", "")
        start_str = aw.get("start", "")

        # Elapsed time
        elapsed_part = ""
        if start_str:
            try:
                start_dt = datetime.datetime.fromisoformat(start_str)
                secs = int((datetime.datetime.now() - start_dt).total_seconds())
                h, m = divmod(secs // 60, 60)
                elapsed_part = f"  {DIM}elapsed {h}h {m:02d}m{R}"
            except ValueError:
                pass

        # Progress bar (only when the matching task is found)
        bar_part = ""
        dl_part  = ""
        if t:
            prog   = t.get("progress", 0)
            filled = round(prog / 10)
            bar_part = f" {ACCENT}{'█' * filled}{DIM}{'░' * (10 - filled)}{R} {BOLD}{prog:3d}%{R}"
            dl_str = t.get("deadline", "")
            if dl_str:
                try:
                    diff = (datetime.date.fromisoformat(dl_str) - datetime.date.today()).days
                    if diff < 0:
                        dl_part = f"  {ERR}overdue {dl_str}{R}"
                    elif diff == 0:
                        dl_part = f"  {WARN}due today{R}"
                    elif diff <= 3:
                        dl_part = f"  {WARN}due {dl_str}{R}"
                    else:
                        dl_part = f"  {TEXT_SUB}{dl_str}{R}"
                except ValueError:
                    dl_part = f"  {TEXT_SUB}{dl_str}{R}"

        event_part = f"  {DIM}[{event}]{R}" if event else ""
        print(f"  {WARN}{BOLD}▶ Working:{R}{bar_part} {BOLD}{name}{R}{event_part}{elapsed_part}{dl_part}")
        print()

    def cmdloop_with_banner(self, quiet: bool = False):
        if not quiet:
            self._print_banner()
        self._print_help_hint()
        self._print_wip_tasks()
        try:
            self.cmdloop()
        except KeyboardInterrupt:
            self.do_exit("")

    # Tab completion
    def complete_open(self, text, line, begidx, endidx):
        names = [name for _, name, _ in self._entries]
        nums  = [str(i) for i in range(1, len(self._entries) + 1)]
        return [c for c in names + nums if c.lower().startswith(text.lower())]

    def complete_find(self, text, line, begidx, endidx):
        return self.complete_open(text, line, begidx, endidx)

    def complete_connect(self, text, line, begidx, endidx):
        names = [c.get("name", c.get("host", "")) for c in self._conns]
        nums  = [str(i) for i in range(1, len(self._conns) + 1)]
        return [c for c in names + nums if c.lower().startswith(text.lower())]


def main():
    quiet = "-q" in sys.argv
    _set_console_icon(str(_BASE_DIR / "gem.ico"))
    shell = GemShell(quiet=quiet)
    shell.cmdloop_with_banner(quiet=quiet)


if __name__ == "__main__":
    main()
