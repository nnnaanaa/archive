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


def _open_path(path: str) -> bool:
    if os.path.isdir(path):
        subprocess.Popen(["explorer", os.path.normpath(path)])
        print(f"  {SUCCESS}opened folder:{R} {path}")
        return True
    elif os.path.isfile(path):
        os.startfile(path)
        print(f"  {SUCCESS}opened file:{R} {path}")
        return True
    else:
        print(f"  {ERR}path does not exist:{R} {path}")
        return False


# ── Shell ──────────────────────────────────────────────────────

class GemShell(cmd.Cmd):
    intro = ""
    prompt = f"{ACCENT}{BOLD}cmd{R} {ACCENT2}>{R} "

    def __init__(self):
        super().__init__()
        self._data: list[dict] = []
        self._entries: list[tuple[str, str, str]] = []
        self._reload()

    def _reload(self):
        self._data = _load_folders()
        self._entries = _all_entries(self._data)
        self._conns = _load_conns()
        self._tasks = _load_tasks()

    # ── Display helpers ────────────────────────────────────────

    def _print_banner(self):
        # Colors matching gem.ico pixel art
        O = "\033[38;2;42;32;88m"       # outline (dark navy)
        H = "\033[38;2;210;200;240m"    # bright highlight
        L = "\033[38;2;178;165;220m"    # light body
        M = "\033[38;2;120;108;190m"    # medium body
        D = "\033[38;2;88;78;158m"      # dark body

        def row(*cols):
            """Render one pixel row. None = space, color = filled block █."""
            out = "  "
            for c in cols:
                out += " " if c is None else (c + "█" + R)
            return out

        _ = None  # blank pixel

        import datetime
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        char = [
            row(_,_,_,O,D,O,_,_,_,O,D,O,_,_),      # two ear bumps
            row(_,_,O,H,H,H,L,L,L,L,L,O,_,_),       # head top
            row(_,O,H,H,H,L,L,M,M,M,L,L,O,_),       # upper body
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

        current_cat = None
        shown = 0
        for idx, (cat, name, path) in enumerate(self._entries, 1):
            if filter_cat and filter_cat.lower() not in cat.lower():
                continue
            if filter_kw and filter_kw.lower() not in name.lower() and filter_kw.lower() not in path.lower():
                continue
            if cat != current_cat:
                print(f"\n  {CAT_CLR}{BOLD}[{cat}]{R}")
                current_cat = cat
            tag = _type_tag(path)
            num = f"{DIM}{idx:3d}.{R}"
            print(f"  {num} {tag} {BOLD}{name}{R}  {TEXT_SUB}{path}{R}")
            shown += 1

        if shown == 0:
            print(f"  {WARN}No matching entries.{R}")

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

    def do_connect(self, arg: str):
        """Connect to a terminal.  connect <#|name>"""
        if not arg.strip():
            # Show connection list
            if not self._conns:
                print(f"  {WARN}No connections registered.{R}")
                return
            print(f"\n  {CAT_CLR}{BOLD}[Connections]{R}")
            for i, c in enumerate(self._conns, 1):
                proto = c.get("protocol", "SSH")
                host  = c.get("host", "")
                name  = c.get("name", host)
                num   = f"{DIM}{i:3d}.{R}"
                tag   = f"{ACCENT}[{proto:<6}]{R}"
                print(f"  {num} {tag} {BOLD}{name}{R}  {TEXT_SUB}{host}{R}")
            return

        query = arg.strip()

        if query.isdigit():
            idx = int(query) - 1
            if 0 <= idx < len(self._conns):
                c = self._conns[idx]
                print(f"  {TEXT_SUB}[{c.get('name', c['host'])}]{R} connecting...")
                _launch_connection(c)
                print(f"  {SUCCESS}Launched.{R}")
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
            print(f"  {TEXT_SUB}[{c.get('name', c['host'])}]{R} connecting...")
            _launch_connection(c)
            print(f"  {SUCCESS}Launched.{R}")
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
                _launch_connection(c)
                print(f"  {SUCCESS}Launched.{R}")
            else:
                print(f"  {ERR}Invalid number.{R}")

    def do_reload(self, _):
        """Reload config.json."""
        self._reload()
        self._print_banner()
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

  {ACCENT}tasks{R}                    Show all tasks
  {ACCENT}tasks -e{R} <event>         Filter by event/category
  {ACCENT}tasks --todo{R}             Show incomplete tasks only
  {ACCENT}tasks --done{R}             Show completed tasks only
  {ACCENT}tasks --content{R}          Show memo/notes
  {ACCENT}tasks --recur{R}            Show recurrence setting
  {ACCENT}tasks --folders{R}          Show work folders

  {ACCENT}connect{R}                  List terminal connections
  {ACCENT}connect{R} <#|name>         Connect to a terminal

  {ACCENT}reload{R}                   Reload config.json
  {ACCENT}exit{R} / {ACCENT}quit{R}               Quit the shell

  {DIM}Type indicators:{R}
  {ACCENT}[dir ]{R}  folder    {FILE_CLR}[file]{R}  file    {ERR}[miss]{R}  not found
""")

    def do_exit(self, _):
        """Exit the shell."""
        print(f"\n  {TEXT_SUB}Bye!{R}\n")
        return True

    def do_quit(self, _):
        """Exit the shell."""
        return self.do_exit(_)

    def default(self, line: str):
        stripped = line.strip()
        if stripped.isdigit():
            self.do_open(stripped)
        else:
            print(f"  {ERR}Unknown command:{R} {line}  {DIM}(type 'help' for list){R}")

    def emptyline(self):
        pass

    def cmdloop(self, intro=None):
        """stdout.write でカラープロンプトを出力しつつタブ補完も維持するオーバーライド。"""
        if self.completekey:
            try:
                import readline as _rl
                self._old_completer = _rl.get_completer()
                _rl.set_completer(self.complete)
                _rl.parse_and_bind(self.completekey + ": complete")
            except ImportError:
                pass
        try:
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    sys.stdout.write(self.prompt)
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
            if self.completekey:
                try:
                    import readline as _rl
                    _rl.set_completer(self._old_completer)
                except ImportError:
                    pass

    def _print_wip_tasks(self):
        """StartWork で実行中のタスクを起動時に表示する。"""
        if not CONFIG_FILE.exists():
            return
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return
        aw = cfg.get("active_work")
        if not aw:
            return

        # active_work に対応するタスクを event+process で検索
        t = next(
            (x for x in self._tasks
             if x.get("event") == aw.get("event") and x.get("process") == aw.get("process")),
            None,
        )
        name  = aw.get("process", "(no title)")
        event = aw.get("event", "")
        start_str = aw.get("start", "")

        # 経過時間
        elapsed_part = ""
        if start_str:
            try:
                start_dt = datetime.datetime.fromisoformat(start_str)
                secs = int((datetime.datetime.now() - start_dt).total_seconds())
                h, m = divmod(secs // 60, 60)
                elapsed_part = f"  {DIM}elapsed {h}h {m:02d}m{R}"
            except ValueError:
                pass

        # 進捗バー（タスクが見つかった場合）
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

    def cmdloop_with_banner(self):
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
    _set_console_icon(str(_BASE_DIR / "gem.ico"))
    shell = GemShell()
    shell.cmdloop_with_banner()


if __name__ == "__main__":
    main()
