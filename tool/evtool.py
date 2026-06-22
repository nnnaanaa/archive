"""evtool: Tera Term マクロ試験のエビデンス取得・まとめツール（単一ファイル / Windows専用）.

使い方:
    py evtool.py

詳細は README.md を参照。
"""
from __future__ import annotations

import base64
import csv
import ctypes
import html
import io
import json
import os
import queue
import re
import shutil
import sys
import threading
import tkinter as tk
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

import win32con
import win32gui
import win32ui
from PIL import Image, ImageDraw, ImageGrab

__version__ = "0.1.0"

# ============================================================================
# ウィンドウ検出・スクリーンショット取得
# ============================================================================

# PrintWindow の flags。GPU描画などのレンダリング方式を問わず、また他ウィンドウに
# 重なっていてもウィンドウの内容を取得できるようにする。
PW_RENDERFULLCONTENT = 0x00000002

# 「画面全体」を対象として選んだことを表す特別な値（実際のhwndは正の整数なので衝突しない）。
FULL_SCREEN_HWND = -1


def list_capture_candidate_windows() -> list[tuple[int, str]]:
    """キャプチャ対象として選択可能なトップレベルウィンドウを (hwnd, タイトル) で列挙する.

    タイトル文字列ではなく hwnd で対象を固定して以降キャプチャするため、Tera Term の
    ウィンドウタイトルが接続先表示等で変化しても選択したウィンドウを継続して取得できる。
    """
    results: list[tuple[int, str]] = []

    def _callback(hwnd: int, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return
        if win32gui.GetWindow(hwnd, win32con.GW_OWNER) != 0:
            return  # 子/ポップアップウィンドウは除外
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if ex_style & win32con.WS_EX_TOOLWINDOW:
            return
        results.append((hwnd, title))

    win32gui.EnumWindows(_callback, None)
    return results


def capture_window(hwnd: int, save_path: Path) -> None:
    """指定ウィンドウを画面の重なりに関係なくキャプチャしてPNGとして保存する."""
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width, height = right - left, bottom - top
    if width <= 0 or height <= 0:
        raise RuntimeError("ウィンドウサイズが取得できません（最小化されていませんか？）")

    window_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(window_dc)
    save_dc = mfc_dc.CreateCompatibleDC()

    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
    save_dc.SelectObject(bitmap)

    result = ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), PW_RENDERFULLCONTENT)

    bmp_info = bitmap.GetInfo()
    bmp_bits = bitmap.GetBitmapBits(True)
    image = Image.frombuffer(
        "RGB",
        (bmp_info["bmWidth"], bmp_info["bmHeight"]),
        bmp_bits,
        "raw",
        "BGRX",
        0,
        1,
    )

    win32gui.DeleteObject(bitmap.GetHandle())
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, window_dc)

    if not result:
        raise RuntimeError("PrintWindow によるキャプチャに失敗しました")

    save_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(save_path)


def capture_full_screen(save_path: Path) -> None:
    """画面全体（接続されている全モニター）をキャプチャしてPNGとして保存する."""
    image = ImageGrab.grab(all_screens=True)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(save_path)


# ============================================================================
# エビデンス取得セッション（フォルダ構成・スクリーンショット・ログ・メタ情報）
# ============================================================================


def _timestamp(fmt: str = "%Y%m%d_%H%M%S") -> str:
    return datetime.now().strftime(fmt)


@dataclass
class ShotRecord:
    file: str
    time: str
    tag: str
    note: str = ""
    included: bool = True  # report.html に掲載するかどうか（終了時に取捨選択可能）


@dataclass
class SessionMeta:
    test_id: str
    title: str
    window_title: str
    start_time: str = ""
    end_time: str = ""
    duration_sec: float = 0.0
    result: str = ""
    note: str = ""
    log_file: str = ""
    shots: list = field(default_factory=list)


class EvidenceSession:
    """1件の試験項目に対するエビデンス取得を担当するセッション.

    キャプチャ対象は開始時に選択した hwnd に固定する。Tera Term のウィンドウ
    タイトルは接続先表示等で実行中に変化することがあるため、タイトル文字列の
    再検索ではなく hwnd 固定で追跡する。
    """

    def __init__(
        self,
        base_dir: Path,
        test_id: str,
        title: str,
        hwnd: int,
        window_label: str,
        auto_capture: bool = False,
        interval: float = 10.0,
        log_callback: Optional[Callable[[str], None]] = None,
    ):
        self.hwnd = hwnd
        self.auto_capture = auto_capture
        self.interval = interval
        self._log_callback = log_callback or print

        folder_name = f"{test_id}_{_timestamp()}"
        self.dir = Path(base_dir) / folder_name
        self.shots_dir = self.dir / "screenshots"
        self.shots_dir.mkdir(parents=True, exist_ok=True)

        self.meta = SessionMeta(test_id=test_id, title=title, window_title=window_label)
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._shot_seq = 0

    # ---- ライフサイクル ----------------------------------------------
    def start(self) -> None:
        self.meta.start_time = datetime.now().isoformat(timespec="seconds")
        if self.auto_capture:
            self._thread = threading.Thread(target=self._auto_capture_loop, daemon=True)
            self._thread.start()

    def finish(
        self,
        result: str = "",
        note: str = "",
        log_file: Optional[str] = None,
        included_files: Optional[set] = None,
    ) -> Path:
        """セッションを終了し meta.json を確定する.

        included_files を指定すると、report.html に掲載するスクリーンショットを
        絞り込める（screenshots/ フォルダ内のファイル自体は削除しない）。
        None の場合は全件を掲載する（既定動作）。
        """
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self.interval + 5)

        self.meta.end_time = datetime.now().isoformat(timespec="seconds")
        start_dt = datetime.fromisoformat(self.meta.start_time)
        end_dt = datetime.fromisoformat(self.meta.end_time)
        self.meta.duration_sec = round((end_dt - start_dt).total_seconds(), 1)
        self.meta.result = result
        self.meta.note = note

        if included_files is not None:
            for shot in self.meta.shots:
                shot["included"] = shot["file"] in included_files

        if log_file:
            self._collect_log(Path(log_file))

        meta_path = self.dir / "meta.json"
        meta_path.write_text(
            json.dumps(asdict(self.meta), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.dir

    # ---- キャプチャ ----------------------------------------------------
    def capture_now(self, tag: str = "manual", note: str = "") -> Optional[str]:
        is_full_screen = self.hwnd == FULL_SCREEN_HWND
        if not is_full_screen and not win32gui.IsWindow(self.hwnd):
            self._log_callback("警告: 対象ウィンドウが見つかりません（閉じられた可能性があります）")
            return None

        with self._lock:
            self._shot_seq += 1
            filename = f"shot_{_timestamp()}_{self._shot_seq:03d}_{tag}.png"
            path = self.shots_dir / filename
            try:
                if is_full_screen:
                    capture_full_screen(path)
                else:
                    capture_window(self.hwnd, path)
            except Exception as exc:  # noqa: BLE001 - 取得は続けたいので例外は握り潰して警告のみ
                self._log_callback(f"警告: キャプチャに失敗しました: {exc}")
                return None

            self.meta.shots.append(
                asdict(
                    ShotRecord(
                        file=f"screenshots/{filename}",
                        time=datetime.now().isoformat(timespec="seconds"),
                        tag=tag,
                        note=note,
                    )
                )
            )
            suffix = f" - {note}" if note else ""
            self._log_callback(f"キャプチャしました: {filename} ({tag}){suffix}")
            return filename

    def _auto_capture_loop(self) -> None:
        while not self._stop_event.wait(self.interval):
            self.capture_now(tag="auto")

    # ---- ログ -----------------------------------------------------------
    def _collect_log(self, log_path: Path) -> None:
        dest = self.dir / "textlog.log"
        try:
            shutil.copyfile(log_path, dest)
            self.meta.log_file = dest.name
        except OSError as exc:
            self._log_callback(f"警告: ログファイルのコピーに失敗しました: {exc}")


# ============================================================================
# 簡易HTMLレポート生成
# ============================================================================

_REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>試験エビデンス: {test_id} - {title}</title>
<style>
  :root {{
    --bg: #F7F8FC;
    --card: #FFFFFF;
    --accent: #C9D6FF;
    --accent-dark: #7C8FE0;
    --pastel-pink: #F4B6C2;
    --pastel-mint: #B7E4C7;
    --text: #3A3A4A;
    --border: #E3E6F0;
  }}
  body {{
    font-family: "Yu Gothic UI", "Segoe UI", "Meiryo", sans-serif;
    margin: 0;
    padding: 2em;
    color: var(--text);
    background: var(--bg);
  }}
  h1 {{ font-weight: 600; color: var(--accent-dark); }}
  h2 {{ font-weight: 600; color: var(--accent-dark); border-bottom: 2px solid var(--accent); padding-bottom: 4px; }}
  table {{
    border-collapse: collapse;
    margin-bottom: 1.5em;
    background: var(--card);
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }}
  th, td {{ border: 1px solid var(--border); padding: 6px 14px; text-align: left; }}
  th {{ background: #EEF1FB; font-weight: 600; }}
  .shot {{
    margin-bottom: 1.5em;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }}
  .shot img {{ max-width: 900px; border: 1px solid var(--border); border-radius: 6px; display: block; margin-top: 6px; }}
  .tag-auto {{ color: #6B7A99; background: #E7ECF7; border-radius: 6px; padding: 2px 8px; font-size: 0.85em; }}
  .tag-manual {{ color: #B23A5A; background: var(--pastel-pink); border-radius: 6px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; }}
  .shot-note {{ margin-top: 6px; padding: 6px 10px; background: var(--pastel-mint); border-radius: 6px; display: inline-block; }}
  pre {{ background: #EEF1FB; padding: 1em; border-radius: 8px; overflow-x: auto; max-height: 400px; }}
</style>
</head>
<body>
<h1>試験エビデンス: {test_id} - {title}</h1>
<table>
  <tr><th>試験ID</th><td>{test_id}</td></tr>
  <tr><th>試験項目</th><td>{title}</td></tr>
  <tr><th>対象ウィンドウ</th><td>{window_title}</td></tr>
  <tr><th>開始時刻</th><td>{start_time}</td></tr>
  <tr><th>終了時刻</th><td>{end_time}</td></tr>
  <tr><th>所要時間(秒)</th><td>{duration_sec}</td></tr>
  <tr><th>結果</th><td>{result}</td></tr>
  <tr><th>備考</th><td>{note}</td></tr>
</table>

<h2>スクリーンショット ({shot_count})</h2>
{shots_html}

<h2>テキストログ</h2>
{log_html}

</body>
</html>
"""

_SHOT_TEMPLATE = """<div class="shot">
  <div><span class="tag-{tag}">[{tag}]</span> {time}</div>
  {note_html}
  <img src="{src}" alt="{file}">
</div>
"""


def generate_report(session_dir: Path) -> Path:
    """report.html を screenshots/ や textlog.log への参照なしで単体完結するように生成する."""
    meta = json.loads((session_dir / "meta.json").read_text(encoding="utf-8"))

    all_shots = meta["shots"]
    included_shots = [s for s in all_shots if s.get("included", True)]

    shot_blocks = []
    for s in included_shots:
        img_path = session_dir / s["file"]
        if img_path.exists():
            b64 = base64.b64encode(img_path.read_bytes()).decode("ascii")
            src = f"data:image/png;base64,{b64}"
        else:
            src = ""
        note = s.get("note") or ""
        note_html = f'<div class="shot-note">備考: {html.escape(note)}</div>' if note else ""
        shot_blocks.append(
            _SHOT_TEMPLATE.format(
                tag=html.escape(s["tag"]),
                time=html.escape(s["time"]),
                src=src,
                file=html.escape(s["file"]),
                note_html=note_html,
            )
        )
    shots_html = "".join(shot_blocks) or "<p>(スクリーンショットはありません)</p>"

    if len(included_shots) != len(all_shots):
        shot_count_label = f"{len(included_shots)}件 / 取得{len(all_shots)}件中"
    else:
        shot_count_label = f"{len(included_shots)}件"

    log_html = "<p>(ログファイルはありません)</p>"
    log_name = meta.get("log_file")
    if log_name:
        log_path = session_dir / log_name
        if log_path.exists():
            log_text = log_path.read_text(encoding="utf-8", errors="replace")
            log_html = f"<pre>{html.escape(log_text)}</pre>"

    report_html = _REPORT_TEMPLATE.format(
        test_id=html.escape(meta["test_id"]),
        title=html.escape(meta["title"]),
        window_title=html.escape(meta["window_title"]),
        start_time=html.escape(meta["start_time"]),
        end_time=html.escape(meta["end_time"]),
        duration_sec=meta["duration_sec"],
        result=html.escape(meta.get("result") or ""),
        note=html.escape(meta.get("note") or ""),
        shot_count=shot_count_label,
        shots_html=shots_html,
        log_html=log_html,
    )

    report_path = session_dir / "report.html"
    report_path.write_text(report_html, encoding="utf-8")
    return report_path


# ============================================================================
# 机上確認（ソースコード確認）・動作確認コード挿入 ユーティリティ
# ============================================================================

ENCODINGS = ["utf-8", "utf-8-sig", "shift_jis", "cp932", "euc_jp"]

# 代表的な言語向けの動作確認用出力コードのプリセット。
# {name} は対象変数名に置換される（単純な文字列置換のため、対象言語側の
# 文字列展開記法と衝突しないよう、テンプレートは連結（+, &, <<）スタイルで統一している）。
OUTPUT_TEMPLATES: dict[str, str] = {
    "Python: print()": 'print("[evtool] {name} =", {name})',
    "C / C++: printf": 'printf("[evtool] {name} = %d\\n", {name});',
    "C++: std::cout": 'std::cout << "[evtool] {name} = " << {name} << std::endl;',
    "Java: System.out.println": 'System.out.println("[evtool] {name} = " + {name});',
    "C#: Console.WriteLine": 'Console.WriteLine("[evtool] {name} = " + {name});',
    "JavaScript: console.log": 'console.log("[evtool] {name} =", {name});',
    "PowerShell: Write-Host": 'Write-Host "[evtool] {name} = ${name}"',
    "VBScript: WScript.Echo": 'WScript.Echo "[evtool] {name} = " & {name}',
    "Tera Termマクロ: messagebox": (
        "sprintf2 evtool_msg '[evtool] {name} = %s' {name}\n"
        "messagebox evtool_msg '{name}'"
    ),
    "カスタム": '{name}',
}


def build_variable_pattern(var_name: str, expected_value: str = "", as_regex: bool = False) -> str:
    """変数定義（代入）行を検出する正規表現を生成する.

    expected_value を指定すると、その値が代入されている行のみにマッチする。
    """
    var_re = re.escape(var_name)
    if expected_value:
        value_part = expected_value if as_regex else re.escape(expected_value)
        return rf"\b{var_re}\b\s*[+\-*/%&|^]?=\s*{value_part}"
    return rf"\b{var_re}\b\s*[+\-*/%&|^]?=(?!=)"


def build_branch_pattern(condition: str, as_regex: bool = False) -> str:
    """if文の行を検出する正規表現を生成する（'if' と条件文字列を同一行に含むことを要求）."""
    cond_part = condition if as_regex else re.escape(condition)
    return rf"(?=.*\bif\b)(?=.*{cond_part})"


def find_pattern_lines(lines: list[str], pattern: str) -> list[tuple[int, str]]:
    """各行に対して正規表現を適用し、マッチした (行番号, 行内容) を全て返す（1始まり）."""
    compiled = re.compile(pattern)
    return [(i, line) for i, line in enumerate(lines, start=1) if compiled.search(line)]


@dataclass
class CheckItem:
    """机上確認の確認項目1件分."""

    kind: str  # "variable" / "branch" / "custom"
    label: str
    pattern: str
    result: str = "-"  # "-" / "OK" / "NG"
    matched_line: str = ""


@dataclass
class Occurrence:
    """動作確認コード挿入のための、変数定義行の候補1件分."""

    var_name: str
    line_no: int
    line_text: str
    indent: str


def increment_test_id(test_id: str) -> str:
    """試験IDの末尾が数字の場合、桁数を保ったまま+1した文字列を返す（次の試験項目の入力を省力化する）."""
    match = re.search(r"(\d+)$", test_id)
    if not match:
        return test_id
    number = match.group(1)
    incremented = str(int(number) + 1).zfill(len(number))
    return test_id[: match.start()] + incremented


def split_names(text: str) -> list[str]:
    """改行・カンマ区切りのテキストから、空でない名前の一覧を抜き出す."""
    names: list[str] = []
    for chunk in re.split(r"[,\n]", text):
        name = chunk.strip()
        if name:
            names.append(name)
    return names


def read_csv_table(path: str) -> tuple[list[str], list[list[str]]]:
    """CSVを読み込み、(ヘッダー行, データ行のリスト) を返す.

    Excel等で保存されたCSVを想定し、utf-8-sig / cp932 の順で読み込みを試す。
    """
    last_exc: Optional[Exception] = None
    rows: list[list[str]] = []
    for encoding in ("utf-8-sig", "cp932"):
        try:
            with open(path, newline="", encoding=encoding) as f:
                rows = list(csv.reader(f))
            break
        except UnicodeDecodeError as exc:
            last_exc = exc
            continue
    else:
        raise last_exc  # type: ignore[misc]

    if not rows:
        return [], []
    return rows[0], rows[1:]


BULK_CHECK_FORMAT_HELP = (
    "1行1項目で入力（#で始まる行は無視）:\n"
    "  変数名             → 変数定義の存在を確認\n"
    "  変数名 = 期待値     → 変数定義＋期待値を確認\n"
    "  if 条件式          → 分岐(if)の存在を確認\n"
    "  re: 正規表現        → カスタム正規表現で確認"
)


def parse_bulk_check_line(line: str) -> Optional["CheckItem"]:
    """机上確認のまとめ入力1行を CheckItem に変換する（空行・コメント行は None）."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    if re.match(r"(?i)^if\s+", stripped):
        condition = re.sub(r"(?i)^if\s+", "", stripped).strip()
        pattern = build_branch_pattern(condition)
        return CheckItem(kind="branch", label=f"if: {condition}", pattern=pattern)

    if re.match(r"(?i)^re:", stripped):
        pattern = re.sub(r"(?i)^re:", "", stripped).strip()
        return CheckItem(kind="custom", label=pattern, pattern=pattern)

    name, sep, expected = stripped.partition("=")
    name = name.strip()
    expected = expected.strip() if sep else ""
    pattern = build_variable_pattern(name, expected)
    label = f"変数: {name}" + (f" = {expected}" if expected else "")
    return CheckItem(kind="variable", label=label, pattern=pattern)


def find_assignment_occurrences(lines: list[str], var_names: list[str]) -> list[Occurrence]:
    """指定した変数名それぞれについて、定義（代入）箇所の候補を全て検出する."""
    results: list[Occurrence] = []
    for var in var_names:
        pattern = re.compile(build_variable_pattern(var))
        for i, raw_line in enumerate(lines, start=1):
            if pattern.search(raw_line):
                indent_match = re.match(r"[ \t]*", raw_line)
                indent = indent_match.group(0) if indent_match else ""
                results.append(Occurrence(var_name=var, line_no=i, line_text=raw_line, indent=indent))
    results.sort(key=lambda o: o.line_no)
    return results


def apply_instrumentation(lines: list[str], selected: list[Occurrence], template: str) -> list[str]:
    """選択された定義行の直後に、テンプレートを変数名置換した出力コードを挿入する.

    挿入行のインデントは、対象の定義行と同じインデントに合わせる。
    """
    inserts_by_line: dict[int, list[str]] = {}
    for occ in selected:
        rendered = template.replace("{name}", occ.var_name)
        for tmpl_line in rendered.splitlines() or [rendered]:
            inserts_by_line.setdefault(occ.line_no, []).append(occ.indent + tmpl_line)

    output: list[str] = []
    for i, line in enumerate(lines, start=1):
        output.append(line)
        output.extend(inserts_by_line.get(i, []))
    return output


_CHECK_REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>机上確認結果: {file_name}</title>
<style>
  body {{ font-family: "Yu Gothic UI", "Segoe UI", "Meiryo", sans-serif; margin: 0; padding: 2em;
          background: #F7F8FC; color: #3A3A4A; }}
  h1 {{ color: #7C8FE0; }}
  table {{ border-collapse: collapse; width: 100%; background: #FFFFFF; border-radius: 10px;
           overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }}
  th, td {{ border: 1px solid #E3E6F0; padding: 6px 12px; text-align: left; }}
  th {{ background: #EEF1FB; }}
  .ok {{ background: #B7E4C7; color: #2F7A4F; border-radius: 6px; padding: 2px 8px; font-weight: 600; }}
  .ng {{ background: #F4B6C2; color: #B23A5A; border-radius: 6px; padding: 2px 8px; font-weight: 600; }}
  .warn {{ background: #FCE8B5; color: #9A6B00; border-radius: 6px; padding: 2px 8px; font-weight: 600; }}
  code {{ background: #EEF1FB; padding: 2px 6px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>机上確認結果</h1>
<p>対象ファイル: <code>{file_path}</code></p>
<p>確認日時: {checked_at} / 結果: {ok_count} / {total_count} 件 OK</p>
<table>
<tr><th>種別</th><th>名称</th><th>結果</th><th>該当行</th></tr>
{rows_html}
</table>
</body>
</html>
"""

_CHECK_ROW_TEMPLATE = (
    '<tr><td>{kind}</td><td>{label}</td>'
    '<td><span class="{result_class}">{result}</span></td><td>{matched}</td></tr>\n'
)


# ============================================================================
# GUI (tkinter) - パステル配色のモダンテーマ
# ============================================================================

PALETTE = {
    "bg": "#F7F8FC",
    "panel": "#FFFFFF",
    "accent": "#C9D6FF",
    "accent_dark": "#7C8FE0",
    "pink": "#F4B6C2",
    "pink_dark": "#B23A5A",
    "mint": "#B7E4C7",
    "mint_dark": "#2F7A4F",
    "text": "#3A3A4A",
    "muted": "#8A8FA3",
    "border": "#DCE1F0",
}
FONT_FAMILY = "Yu Gothic UI"
FONT_SIZE = 8


def _build_app_icon() -> list[tk.PhotoImage]:
    """タスクバー等に表示するアプリアイコンを実行時に生成する（外部アセット不要）.

    256x256 で描いてから複数サイズに縮小することで、タスクバー/タイトルバーの
    小さいサイズでもアンチエイリアスが効いて綺麗に見えるようにする。
    """
    size = 256
    margin = 10
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        (margin, margin, size - margin, size - margin), radius=60, fill=(94, 110, 219, 255)
    )

    highlight = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hdraw = ImageDraw.Draw(highlight)
    hdraw.rounded_rectangle(
        (margin, margin, size - margin, int(size * 0.55)), radius=60, fill=(255, 255, 255, 35)
    )
    img = Image.alpha_composite(img, highlight)
    draw = ImageDraw.Draw(img)

    check_width = 26
    points = [(72, 138), (110, 178), (190, 80)]
    draw.line(points, fill=(255, 255, 255, 255), width=check_width, joint="curve")
    cap_radius = check_width // 2
    for x, y in (points[0], points[-1]):
        draw.ellipse(
            (x - cap_radius, y - cap_radius, x + cap_radius, y + cap_radius), fill=(255, 255, 255, 255)
        )

    icons = []
    for target_size in (64, 32, 16):
        resized = img.resize((target_size, target_size), Image.LANCZOS)
        buf = io.BytesIO()
        resized.save(buf, format="PNG")
        icons.append(tk.PhotoImage(data=buf.getvalue()))
    return icons


def _apply_theme(root: tk.Tk) -> None:
    """パステルカラー・モダンフォント・コンパクトな余白の ttk テーマを適用する."""
    default_font = (FONT_FAMILY, FONT_SIZE)
    root.option_add("*Font", default_font)
    root.configure(bg=PALETTE["bg"])

    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=PALETTE["bg"], foreground=PALETTE["text"], font=default_font)
    style.configure("TFrame", background=PALETTE["bg"])
    style.configure("TLabel", background=PALETTE["bg"], foreground=PALETTE["text"])
    style.configure("Header.TLabel", font=(FONT_FAMILY, 10, "bold"), foreground=PALETTE["accent_dark"])
    style.configure("Status.TLabel", foreground=PALETTE["muted"])

    style.configure(
        "TEntry",
        fieldbackground=PALETTE["panel"],
        bordercolor=PALETTE["border"],
        lightcolor=PALETTE["panel"],
        darkcolor=PALETTE["panel"],
        padding=2,
    )
    style.configure(
        "TCombobox",
        fieldbackground=PALETTE["panel"],
        bordercolor=PALETTE["border"],
        padding=2,
    )
    style.configure("TCheckbutton", background=PALETTE["bg"], foreground=PALETTE["text"])
    style.configure("TLabelframe", background=PALETTE["bg"], bordercolor=PALETTE["border"])
    style.configure("TLabelframe.Label", background=PALETTE["bg"], foreground=PALETTE["accent_dark"])

    style.configure(
        "TButton",
        background=PALETTE["accent"],
        foreground=PALETTE["text"],
        borderwidth=0,
        focusthickness=0,
        padding=(6, 2),
        font=default_font,
    )
    style.map("TButton", background=[("active", PALETTE["accent_dark"]), ("disabled", "#E5E7F0")])

    style.configure(
        "Primary.TButton",
        background=PALETTE["accent_dark"],
        foreground="#FFFFFF",
        padding=(8, 3),
        font=(FONT_FAMILY, FONT_SIZE, "bold"),
    )
    style.map("Primary.TButton", background=[("active", "#6577CC"), ("disabled", "#C7CCE8")])

    style.configure("Capture.TButton", background=PALETTE["mint"], foreground=PALETTE["mint_dark"])
    style.map("Capture.TButton", background=[("active", "#9FD8B6"), ("disabled", "#E5E7F0")])

    style.configure("Finish.TButton", background=PALETTE["pink"], foreground=PALETTE["pink_dark"])
    style.map("Finish.TButton", background=[("active", "#EC9CAC"), ("disabled", "#E5E7F0")])

    style.configure("TScrollbar", background=PALETTE["accent"], troughcolor=PALETTE["bg"])

    style.configure(
        "TNotebook",
        background=PALETTE["bg"],
        bordercolor=PALETTE["border"],
        tabmargins=(2, 3, 2, 0),
    )
    style.configure(
        "TNotebook.Tab",
        background=PALETTE["accent"],
        foreground=PALETTE["text"],
        padding=(8, 2),
        font=default_font,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", PALETTE["panel"])],
        foreground=[("selected", PALETTE["accent_dark"])],
    )

    style.configure(
        "Treeview",
        background=PALETTE["panel"],
        fieldbackground=PALETTE["panel"],
        foreground=PALETTE["text"],
        bordercolor=PALETTE["border"],
        rowheight=18,
        font=default_font,
    )
    style.configure(
        "Treeview.Heading",
        background=PALETTE["accent"],
        foreground=PALETTE["text"],
        font=(FONT_FAMILY, FONT_SIZE, "bold"),
    )
    style.map("Treeview", background=[("selected", PALETTE["accent"])], foreground=[("selected", PALETTE["text"])])


class Tooltip:
    """ウィジェットにマウスを乗せたときに簡単な説明を表示するツールチップ."""

    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text
        self._tip: Optional[tk.Toplevel] = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _event: object = None) -> None:
        if self._tip is not None:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self._tip,
            text=self.text,
            justify="left",
            background="#FFF8DC",
            foreground=PALETTE["text"],
            relief="solid",
            borderwidth=1,
            font=(FONT_FAMILY, FONT_SIZE),
            padx=6,
            pady=3,
        )
        label.pack()

    def _hide(self, _event: object = None) -> None:
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None


class WindowPickerDialog(tk.Toplevel):
    """現在開いているウィンドウから、キャプチャ対象を選択させるダイアログ.

    選択結果は hwnd で確定するため、以降タイトルが変化しても対象を継続して
    追跡できる（Tera Term の接続先表示などでタイトルが変わるケースに対応）。
    """

    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        self.title("対象ウィンドウの選択")
        self.geometry("440x340")
        self.configure(bg=PALETTE["bg"])
        self.transient(parent)

        self.selected: Optional[tuple[int, str]] = None
        self._windows: list[tuple[int, str]] = []

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(
            frm,
            text=(
                "キャプチャ対象を選んでください（一覧先頭の「画面全体」を選ぶと\n"
                "デスクトップ全体をキャプチャします）。ウィンドウを選んだ場合は、\n"
                "以後タイトルが変化しても同じウィンドウを継続して追跡します。"
            ),
            justify="left",
        ).pack(fill="x", pady=(0, 8))

        list_frame = ttk.Frame(frm)
        list_frame.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(
            list_frame,
            activestyle="dotbox",
            bg=PALETTE["panel"],
            fg=PALETTE["text"],
            selectbackground=PALETTE["accent"],
            selectforeground=PALETTE["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
        )
        scrollbar = ttk.Scrollbar(list_frame, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.listbox.bind("<Double-Button-1>", lambda _e: self._on_ok())

        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(10, 0))
        ttk.Button(btns, text="更新", command=self._refresh).pack(side="left")
        ttk.Button(btns, text="キャンセル", command=self._on_cancel).pack(side="right")
        ttk.Button(btns, text="選択", style="Primary.TButton", command=self._on_ok).pack(
            side="right", padx=(0, 6)
        )

        self.bind("<Escape>", lambda _e: self._on_cancel())
        self._refresh()
        self.grab_set()

    def _refresh(self) -> None:
        self.listbox.delete(0, "end")
        self._windows = [(FULL_SCREEN_HWND, "画面全体（すべてのモニター）")] + list_capture_candidate_windows()
        for _hwnd, title in self._windows:
            self.listbox.insert("end", title)

    def _on_ok(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("選択エラー", "ウィンドウを選択してください", parent=self)
            return
        self.selected = self._windows[selection[0]]
        self.destroy()

    def _on_cancel(self) -> None:
        self.selected = None
        self.destroy()


class ShotSelectionDialog(tk.Toplevel):
    """終了時に、report.html に掲載するスクリーンショットを取捨選択させるダイアログ.

    既定では全件選択（=掲載）した状態で開く。チェックを外しても screenshots\\ 内の
    元ファイルは削除されない（report.html への掲載対象から外れるだけ）。
    """

    def __init__(self, parent: tk.Misc, shots: list[dict]):
        super().__init__(parent)
        self.title("掲載するスクリーンショットの選択")
        self.geometry("520x420")
        self.configure(bg=PALETTE["bg"])
        self.transient(parent)

        self.shots = shots
        self.cancelled = True
        self.included_files: set = set()

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(
            frm,
            text=(
                "report.html に掲載するスクリーンショットを選んでください（複数選択可）。\n"
                "選択を外したものも screenshots フォルダには残ります。"
            ),
            justify="left",
        ).pack(fill="x", pady=(0, 6))

        list_frame = ttk.Frame(frm)
        list_frame.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(
            list_frame,
            selectmode="extended",
            activestyle="dotbox",
            bg=PALETTE["panel"],
            fg=PALETTE["text"],
            selectbackground=PALETTE["accent"],
            selectforeground=PALETTE["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
        )
        scrollbar = ttk.Scrollbar(list_frame, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for shot in self.shots:
            note_part = f" - {shot['note']}" if shot.get("note") else ""
            self.listbox.insert("end", f"[{shot['tag']}] {shot['time']}  {shot['file']}{note_part}")
        self.listbox.selection_set(0, "end")

        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(8, 0))
        ttk.Button(btns, text="すべて選択", command=lambda: self.listbox.selection_set(0, "end")).pack(
            side="left"
        )
        ttk.Button(btns, text="すべて解除", command=lambda: self.listbox.selection_clear(0, "end")).pack(
            side="left", padx=6
        )
        ttk.Button(btns, text="autoを除外", command=self._deselect_auto).pack(side="left")

        btns2 = ttk.Frame(frm)
        btns2.pack(fill="x", pady=(8, 0))
        ttk.Button(btns2, text="キャンセル", command=self._on_cancel).pack(side="right", padx=(6, 0))
        ttk.Button(btns2, text="次へ", style="Primary.TButton", command=self._on_ok).pack(side="right")

        self.bind("<Escape>", lambda _e: self._on_cancel())
        self.grab_set()

    def _deselect_auto(self) -> None:
        for i, shot in enumerate(self.shots):
            if shot["tag"] == "auto":
                self.listbox.selection_clear(i)

    def _on_ok(self) -> None:
        selected = self.listbox.curselection()
        self.included_files = {self.shots[i]["file"] for i in selected}
        self.cancelled = False
        self.destroy()

    def _on_cancel(self) -> None:
        self.cancelled = True
        self.destroy()


class FinishDialog(tk.Toplevel):
    """終了時に結果(OK/NG等)と備考を入力させるモーダルダイアログ."""

    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        self.title("試験結果の入力")
        self.resizable(False, False)
        self.configure(bg=PALETTE["bg"])
        self.transient(parent)

        self.result_value: Optional[str] = None
        self.note_value: str = ""

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="結果").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.var_result = tk.StringVar(value="OK")
        ttk.Combobox(
            frm, textvariable=self.var_result, values=["OK", "NG", "未実施"], width=20
        ).grid(row=0, column=1, sticky="w", pady=(0, 6))

        ttk.Label(frm, text="備考").grid(row=1, column=0, sticky="nw")
        self.note_text = tk.Text(
            frm,
            width=42,
            height=6,
            bg=PALETTE["panel"],
            fg=PALETTE["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
            font=(FONT_FAMILY, FONT_SIZE),
        )
        self.note_text.grid(row=1, column=1, sticky="we")

        btns = ttk.Frame(frm)
        btns.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky="e")
        ttk.Button(btns, text="キャンセル", command=self._on_cancel).pack(side="right", padx=(6, 0))
        ttk.Button(btns, text="OK", style="Primary.TButton", command=self._on_ok).pack(side="right")

        self.bind("<Return>", lambda _event: self._on_ok())
        self.bind("<Escape>", lambda _event: self._on_cancel())
        self.grab_set()
        self.note_text.focus_set()

    def _on_ok(self) -> None:
        self.result_value = self.var_result.get().strip()
        self.note_value = self.note_text.get("1.0", "end").strip()
        self.destroy()

    def _on_cancel(self) -> None:
        self.result_value = None
        self.destroy()


class SourceCheckFrame(ttk.Frame):
    """ソースコードの机上確認（変数定義・分岐(if)の存在確認）を行うタブ.

    確認はファイル全体に対する正規表現の行検索のみで行う簡易的なテキストベースの
    チェックであり、実際の構文解析は行わない（コメント内の文字列等も検出され得る）。
    """

    def __init__(self, parent: tk.Misc, log_callback: Callable[[str], None]):
        super().__init__(parent, padding=10)
        self._log = log_callback
        self.items: dict[str, CheckItem] = {}
        self._next_id = 0
        self._build()

    def _build(self) -> None:
        ttk.Label(
            self,
            text="操作の流れ:  ①対象ファイルを選択 → ②確認したい項目をまとめて追加 → ③確認を実行 → ④結果をHTMLで保存",
            style="Status.TLabel",
        ).pack(fill="x", pady=(0, 6))

        file_row = ttk.Frame(self)
        file_row.pack(fill="x", pady=(0, 6))
        ttk.Label(file_row, text="対象ファイル").pack(side="left")
        self.var_file = tk.StringVar()
        ttk.Entry(file_row, textvariable=self.var_file, state="readonly").pack(
            side="left", fill="x", expand=True, padx=6
        )
        ttk.Button(file_row, text="参照...", command=self._browse_file).pack(side="left")
        ttk.Label(file_row, text="エンコーディング").pack(side="left", padx=(10, 4))
        self.var_encoding = tk.StringVar(value="utf-8")
        ttk.Combobox(
            file_row, textvariable=self.var_encoding, values=ENCODINGS, width=10, state="readonly"
        ).pack(side="left")

        add_frame = ttk.LabelFrame(self, text="② 確認項目のまとめ追加（1行1項目、複数貼り付け可）")
        add_frame.pack(fill="x", pady=(0, 6))

        ttk.Label(add_frame, text=BULK_CHECK_FORMAT_HELP, foreground=PALETTE["muted"], justify="left").pack(
            anchor="w", padx=6, pady=(4, 2)
        )

        bulk_row = ttk.Frame(add_frame)
        bulk_row.pack(fill="x", padx=6, pady=(0, 6))
        self.bulk_text = tk.Text(
            bulk_row,
            height=4,
            bg=PALETTE["panel"],
            fg=PALETTE["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
            font=(FONT_FAMILY, FONT_SIZE),
        )
        self.bulk_text.pack(side="left", fill="x", expand=True)
        button_col = ttk.Frame(bulk_row)
        button_col.pack(side="left", padx=(6, 0), anchor="n")
        ttk.Button(button_col, text="② 項目を追加", style="Primary.TButton", command=self._add_bulk_items).pack(
            fill="x"
        )
        btn_csv = ttk.Button(button_col, text="CSVから読み込み", command=self._load_csv)
        btn_csv.pack(fill="x", pady=(4, 0))
        Tooltip(
            btn_csv,
            "確認項目を書いたCSVファイルを読み込みます。\n"
            "列名（1行目）に 種別/内容(または変数名・条件式・正規表現)/期待値/名称 を\n"
            "含めると自動で認識します。列名が無い場合は1列目を内容、2列目を期待値として\n"
            "扱います（種別は省略時「変数定義」）。",
        )

        columns = ("kind", "detail", "result", "matched")
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, pady=(0, 6))
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="extended", height=7
        )
        self.tree.heading("kind", text="種別")
        self.tree.heading("detail", text="名称")
        self.tree.heading("result", text="結果")
        self.tree.heading("matched", text="該当行")
        self.tree.column("kind", width=90, anchor="w")
        self.tree.column("detail", width=180, anchor="w")
        self.tree.column("result", width=50, anchor="center")
        self.tree.column("matched", width=280, anchor="w")
        tree_scroll = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        select_frame = ttk.Frame(self)
        select_frame.pack(fill="x")
        ttk.Button(select_frame, text="すべて選択", command=lambda: self.tree.selection_set(self.tree.get_children())).pack(
            side="left"
        )
        ttk.Button(
            select_frame,
            text="選択解除",
            command=lambda: self.tree.selection_remove(self.tree.get_children()),
        ).pack(side="left", padx=6)
        ttk.Button(select_frame, text="選択項目を削除", command=self._delete_selected).pack(side="left")

        action_frame = ttk.Frame(self)
        action_frame.pack(fill="x", pady=(4, 0))
        ttk.Button(
            action_frame, text="③ 確認を実行", style="Capture.TButton", command=self._run_checks
        ).pack(side="left")
        ttk.Label(action_frame, text="出力先フォルダ").pack(side="left", padx=(12, 4))
        self.var_output = tk.StringVar(value="evidence")
        ttk.Entry(action_frame, textvariable=self.var_output, width=18).pack(side="left")
        ttk.Button(action_frame, text="参照...", command=self._browse_output).pack(side="left", padx=4)
        ttk.Button(
            action_frame, text="④ 結果をHTMLで保存", style="Finish.TButton", command=self._export_html
        ).pack(side="left", padx=(12, 0))

    def _browse_file(self) -> None:
        path = filedialog.askopenfilename(title="確認対象ファイルを選択")
        if path:
            self.var_file.set(path)

    def _browse_output(self) -> None:
        path = filedialog.askdirectory(title="出力先フォルダを選択")
        if path:
            self.var_output.set(path)

    def _add_bulk_items(self) -> None:
        raw_text = self.bulk_text.get("1.0", "end")
        added = 0
        errors: list[str] = []
        for line_no, line in enumerate(raw_text.splitlines(), start=1):
            try:
                item = parse_bulk_check_line(line)
            except re.error as exc:
                errors.append(f"{line_no}行目: {exc}")
                continue
            if item is None:
                continue
            try:
                re.compile(item.pattern)
            except re.error as exc:
                errors.append(f"{line_no}行目: 正規表現エラー: {exc}")
                continue

            item_id = str(self._next_id)
            self._next_id += 1
            self.items[item_id] = item
            self.tree.insert(
                "", "end", iid=item_id, values=(self._kind_label(item.kind), item.label, item.result, "")
            )
            added += 1

        self.bulk_text.delete("1.0", "end")
        self._log(f"机上確認項目を{added}件追加しました" + (f"（エラー{len(errors)}件）" if errors else ""))
        if errors:
            messagebox.showwarning("一部の行を追加できませんでした", "\n".join(errors))

    def _load_csv(self) -> None:
        path = filedialog.askopenfilename(
            title="確認項目CSVを選択", filetypes=[("CSV", "*.csv"), ("すべてのファイル", "*.*")]
        )
        if not path:
            return
        try:
            header, data_rows = read_csv_table(path)
        except (OSError, UnicodeDecodeError) as exc:
            messagebox.showerror("読み込みエラー", f"CSVを読み込めません: {exc}")
            return
        if not data_rows:
            messagebox.showinfo("読み込み結果", "CSVにデータ行がありませんでした")
            return

        header_lower = [h.strip().lower() for h in header]

        def find_col(*names: str) -> Optional[int]:
            for name in names:
                if name.lower() in header_lower:
                    return header_lower.index(name.lower())
            return None

        idx_kind = find_col("種別", "kind", "type")
        idx_content = find_col("内容", "変数名", "変数", "条件式", "正規表現", "name", "content", "regex")
        idx_expected = find_col("期待値", "expected")
        idx_label = find_col("名称", "label")
        if idx_content is None:
            # 列名が認識できない場合は1列目=内容, 2列目=期待値とみなす（種別は変数定義扱い）
            idx_content = 0
            if idx_expected is None and len(header) > 1:
                idx_expected = 1

        def cell(row: list[str], idx: Optional[int]) -> str:
            return row[idx].strip() if idx is not None and idx < len(row) else ""

        added = 0
        errors: list[str] = []
        for line_no, row in enumerate(data_rows, start=2):
            content = cell(row, idx_content)
            if not content:
                continue
            kind_raw = cell(row, idx_kind).lower()
            expected = cell(row, idx_expected)
            label = cell(row, idx_label)

            if kind_raw in ("分岐", "if", "branch", "分岐(if)"):
                pattern = build_branch_pattern(content)
                kind_key = "branch"
                default_label = f"if: {content}"
            elif kind_raw in ("カスタム", "regex", "custom", "正規表現", "カスタム正規表現"):
                pattern = content
                kind_key = "custom"
                default_label = content
            else:
                pattern = build_variable_pattern(content, expected)
                kind_key = "variable"
                default_label = f"変数: {content}" + (f" = {expected}" if expected else "")

            try:
                re.compile(pattern)
            except re.error as exc:
                errors.append(f"{line_no}行目: 正規表現エラー: {exc}")
                continue

            item = CheckItem(kind=kind_key, label=label or default_label, pattern=pattern)
            item_id = str(self._next_id)
            self._next_id += 1
            self.items[item_id] = item
            self.tree.insert(
                "", "end", iid=item_id, values=(self._kind_label(item.kind), item.label, item.result, "")
            )
            added += 1

        self._log(f"CSVから机上確認項目を{added}件読み込みました" + (f"（エラー{len(errors)}件）" if errors else ""))
        if errors:
            messagebox.showwarning("一部の行を読み込めませんでした", "\n".join(errors))

    def _delete_selected(self) -> None:
        for item_id in self.tree.selection():
            self.tree.delete(item_id)
            self.items.pop(item_id, None)

    def _run_checks(self) -> None:
        path_str = self.var_file.get().strip()
        if not path_str:
            messagebox.showerror("入力エラー", "対象ファイルを選択してください")
            return
        if not self.items:
            messagebox.showinfo("確認項目なし", "確認項目を追加してください")
            return

        try:
            text = Path(path_str).read_text(encoding=self.var_encoding.get())
        except (OSError, UnicodeDecodeError) as exc:
            messagebox.showerror("読み込みエラー", f"ファイルを読み込めません: {exc}")
            return

        lines = text.splitlines()
        ok_count = 0
        for item_id, item in self.items.items():
            matches = find_pattern_lines(lines, item.pattern)
            if matches:
                item.result = "OK"
                line_no, line_text = matches[0]
                item.matched_line = f"L{line_no}: {line_text.strip()}"
                if len(matches) > 1:
                    item.matched_line += f" (他{len(matches) - 1}件)"
                ok_count += 1
            else:
                item.result = "NG"
                item.matched_line = "(該当なし)"
            self.tree.item(
                item_id, values=(self._kind_label(item.kind), item.label, item.result, item.matched_line)
            )

        self._log(f"机上確認: {len(self.items)}件中 {ok_count}件OK ({Path(path_str).name})")

    @staticmethod
    def _kind_label(kind_key: str) -> str:
        return {"variable": "変数定義", "branch": "分岐(if)", "custom": "カスタム正規表現"}.get(
            kind_key, kind_key
        )

    def _export_html(self) -> None:
        if not self.items:
            messagebox.showinfo("確認項目なし", "確認項目がありません")
            return
        out_dir = Path(self.var_output.get().strip() or "evidence")
        out_dir.mkdir(parents=True, exist_ok=True)
        report_path = out_dir / f"sourcecheck_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        rows_html = "".join(
            _CHECK_ROW_TEMPLATE.format(
                kind=html.escape(self._kind_label(item.kind)),
                label=html.escape(item.label),
                result_class="ok" if item.result == "OK" else ("ng" if item.result == "NG" else "warn"),
                result=html.escape(item.result),
                matched=html.escape(item.matched_line),
            )
            for item in self.items.values()
        )
        ok_count = sum(1 for item in self.items.values() if item.result == "OK")
        report_html = _CHECK_REPORT_TEMPLATE.format(
            file_name=html.escape(Path(self.var_file.get()).name),
            file_path=html.escape(self.var_file.get()),
            checked_at=datetime.now().isoformat(timespec="seconds"),
            ok_count=ok_count,
            total_count=len(self.items),
            rows_html=rows_html,
        )
        report_path.write_text(report_html, encoding="utf-8")
        self._log(f"机上確認結果を保存しました: {report_path}")
        if messagebox.askyesno("完了", "保存した確認結果を開きますか？"):
            os.startfile(report_path)  # noqa: S606 - ユーザー自身が生成したローカルファイルを開く


class InstrumentFrame(ttk.Frame):
    """変数定義の直後に動作確認用の出力コードを挿入するタブ.

    変数の代入行をテキストベースの正規表現で検出するため、実際の構文解析は
    行わない。検出した候補から挿入箇所を選び、新しいファイルとして書き出す
    （元ファイルは変更しない）。
    """

    def __init__(self, parent: tk.Misc, log_callback: Callable[[str], None]):
        super().__init__(parent, padding=10)
        self._log = log_callback
        self.occurrences: dict[str, Occurrence] = {}
        self._lines: list[str] = []
        self._next_id = 0
        self._build()

    def _build(self) -> None:
        ttk.Label(
            self,
            text=(
                "操作の流れ:  ①対象ファイルを選択 → ②変数名を入力して候補を検索 → "
                "③挿入箇所を選択 → ④テンプレートを選んで挿入"
            ),
            style="Status.TLabel",
        ).pack(fill="x", pady=(0, 6))

        file_row = ttk.Frame(self)
        file_row.pack(fill="x", pady=(0, 6))
        ttk.Label(file_row, text="① 対象ファイル").pack(side="left")
        self.var_file = tk.StringVar()
        ttk.Entry(file_row, textvariable=self.var_file, state="readonly").pack(
            side="left", fill="x", expand=True, padx=6
        )
        ttk.Button(file_row, text="参照...", command=self._browse_file).pack(side="left")
        ttk.Label(file_row, text="エンコーディング").pack(side="left", padx=(10, 4))
        self.var_encoding = tk.StringVar(value="utf-8")
        ttk.Combobox(
            file_row, textvariable=self.var_encoding, values=ENCODINGS, width=10, state="readonly"
        ).pack(side="left")

        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", pady=(0, 6))
        ttk.Label(search_frame, text="② 変数名\n(改行/カンマ区切りで複数可)", justify="left").pack(
            side="left", anchor="n"
        )
        self.names_text = tk.Text(
            search_frame,
            height=3,
            width=30,
            bg=PALETTE["panel"],
            fg=PALETTE["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
            font=(FONT_FAMILY, FONT_SIZE),
        )
        self.names_text.pack(side="left", padx=6, fill="x", expand=True)
        Tooltip(self.names_text, "確認したい変数の名前を入力します。\n例: threshold, bonus\nまたは1行に1つずつ改行で入力してもOKです。")
        btn_col = ttk.Frame(search_frame)
        btn_col.pack(side="left", anchor="n")
        ttk.Button(btn_col, text="候補を検索", style="Capture.TButton", command=self._search).pack(fill="x")
        btn_csv = ttk.Button(btn_col, text="CSVから読込", command=self._load_csv)
        btn_csv.pack(fill="x", pady=(4, 0))
        Tooltip(btn_csv, "変数名を書いたCSV（1列でも複数列でも可）を読み込み、変数名欄に追加します。")

        columns = ("var", "line", "content")
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, pady=(0, 6))
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="extended", height=6
        )
        self.tree.heading("var", text="変数")
        self.tree.heading("line", text="行番号")
        self.tree.heading("content", text="内容")
        self.tree.column("var", width=90, anchor="w")
        self.tree.column("line", width=60, anchor="center")
        self.tree.column("content", width=400, anchor="w")
        tree_scroll = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        select_frame = ttk.Frame(self)
        select_frame.pack(fill="x", pady=(0, 6))
        ttk.Label(select_frame, text="③ 挿入したい行を選択:").pack(side="left")
        ttk.Button(
            select_frame,
            text="すべて選択",
            command=lambda: self.tree.selection_set(self.tree.get_children()),
        ).pack(side="left", padx=(6, 0))
        ttk.Button(
            select_frame,
            text="選択解除",
            command=lambda: self.tree.selection_remove(self.tree.get_children()),
        ).pack(side="left", padx=6)

        ttk.Label(
            self,
            text=(
                "④ 出力テンプレート（言語ごとのひな形を選べます。{name} の部分は挿入時に"
                "実際の変数名へ自動的に置き換わるプレースホルダーです）"
            ),
            wraplength=620,
            justify="left",
        ).pack(anchor="w")
        template_row = ttk.Frame(self)
        template_row.pack(fill="x", pady=(2, 2))
        ttk.Label(template_row, text="言語/書式:").pack(side="left")
        self.var_preset = tk.StringVar(value=next(iter(OUTPUT_TEMPLATES)))
        preset_combo = ttk.Combobox(
            template_row,
            textvariable=self.var_preset,
            values=list(OUTPUT_TEMPLATES.keys()),
            state="readonly",
            width=26,
        )
        preset_combo.pack(side="left", padx=(4, 0))
        preset_combo.bind("<<ComboboxSelected>>", lambda _e: self._apply_preset())

        self.template_text = tk.Text(
            self,
            height=3,
            bg=PALETTE["panel"],
            fg=PALETTE["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
            font=(FONT_FAMILY, FONT_SIZE),
        )
        self.template_text.pack(fill="x", pady=(4, 2))
        self.template_text.bind("<KeyRelease>", lambda _e: self._update_preview())

        self.preview_var = tk.StringVar()
        ttk.Label(
            self,
            textvariable=self.preview_var,
            foreground=PALETTE["mint_dark"],
            wraplength=620,
            justify="left",
        ).pack(fill="x", pady=(0, 6), anchor="w")

        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._update_preview())
        self._apply_preset()

        action_frame = ttk.Frame(self)
        action_frame.pack(fill="x")
        ttk.Label(action_frame, text="保存先サフィックス").pack(side="left")
        self.var_suffix = tk.StringVar(value="_instrumented")
        suffix_entry = ttk.Entry(action_frame, textvariable=self.var_suffix, width=16)
        suffix_entry.pack(side="left", padx=6)
        Tooltip(
            suffix_entry,
            "生成されるファイル名に付く接尾辞です。元のファイル名が sample.py なら\n"
            "sample_instrumented.py として、元ファイルとは別の新しいファイルが作られます。",
        )
        ttk.Button(
            action_frame,
            text="選択箇所に挿入してファイル生成",
            style="Primary.TButton",
            command=self._apply_instrumentation,
        ).pack(side="left", padx=(6, 0))

    def _browse_file(self) -> None:
        path = filedialog.askopenfilename(title="対象ファイルを選択")
        if path:
            self.var_file.set(path)

    def _apply_preset(self) -> None:
        template = OUTPUT_TEMPLATES.get(self.var_preset.get(), "{name}")
        self.template_text.delete("1.0", "end")
        self.template_text.insert("1.0", template)
        self._update_preview()

    def _update_preview(self) -> None:
        """テンプレートの {name} を実際の変数名に置き換えた例を表示する（言語を問わず動作）."""
        template = self.template_text.get("1.0", "end").rstrip("\n")
        selection = self.tree.selection()
        if selection:
            example_name = self.occurrences[selection[0]].var_name
        else:
            example_name = "変数名"
        rendered = template.replace("{name}", example_name) or "(テンプレート未入力)"
        self.preview_var.set(f"実際に挿入される行の例（選択中の変数: {example_name}）:\n{rendered}")

    def _load_csv(self) -> None:
        path = filedialog.askopenfilename(
            title="変数名CSVを選択", filetypes=[("CSV", "*.csv"), ("すべてのファイル", "*.*")]
        )
        if not path:
            return
        try:
            header, data_rows = read_csv_table(path)
        except (OSError, UnicodeDecodeError) as exc:
            messagebox.showerror("読み込みエラー", f"CSVを読み込めません: {exc}")
            return

        names = [cell.strip() for row in ([header] + data_rows) for cell in row if cell and cell.strip()]
        if not names:
            messagebox.showinfo("読み込み結果", "CSVから変数名が見つかりませんでした")
            return

        current = self.names_text.get("1.0", "end").strip()
        combined = (current + "\n" if current else "") + "\n".join(names)
        self.names_text.delete("1.0", "end")
        self.names_text.insert("1.0", combined)
        self._log(f"CSVから変数名を{len(names)}件読み込みました")

    def _search(self) -> None:
        path_str = self.var_file.get().strip()
        var_names = split_names(self.names_text.get("1.0", "end"))
        if not path_str or not var_names:
            messagebox.showerror("入力エラー", "対象ファイルと変数名を指定してください")
            return
        try:
            text = Path(path_str).read_text(encoding=self.var_encoding.get())
        except (OSError, UnicodeDecodeError) as exc:
            messagebox.showerror("読み込みエラー", f"ファイルを読み込めません: {exc}")
            return

        self._lines = text.splitlines()
        self.tree.delete(*self.tree.get_children())
        self.occurrences.clear()
        self._next_id = 0

        occurrences = find_assignment_occurrences(self._lines, var_names)
        for occ in occurrences:
            item_id = str(self._next_id)
            self._next_id += 1
            self.occurrences[item_id] = occ
            self.tree.insert("", "end", iid=item_id, values=(occ.var_name, occ.line_no, occ.line_text.strip()))

        self._log(
            f"動作確認コード挿入: {len(occurrences)}件の定義候補が見つかりました ({Path(path_str).name})"
        )
        if not occurrences:
            messagebox.showinfo("候補なし", "指定した変数の定義行が見つかりませんでした")

    def _apply_instrumentation(self) -> None:
        selected_ids = self.tree.selection()
        if not selected_ids:
            messagebox.showerror("入力エラー", "挿入する箇所を一覧から選択してください")
            return
        if not self._lines:
            messagebox.showerror("入力エラー", "先に候補を検索してください")
            return

        template = self.template_text.get("1.0", "end").rstrip("\n")
        if not template.strip():
            messagebox.showerror("入力エラー", "出力テンプレートを入力してください")
            return

        selected = [self.occurrences[item_id] for item_id in selected_ids]
        output_lines = apply_instrumentation(self._lines, selected, template)

        source_path = Path(self.var_file.get())
        suffix = self.var_suffix.get().strip() or "_instrumented"
        output_path = source_path.with_name(f"{source_path.stem}{suffix}{source_path.suffix}")
        try:
            output_path.write_text("\n".join(output_lines) + "\n", encoding=self.var_encoding.get())
        except OSError as exc:
            messagebox.showerror("書き込みエラー", f"ファイルを書き込めません: {exc}")
            return

        self._log(f"動作確認コードを{len(selected)}箇所に挿入しました: {output_path}")
        if messagebox.askyesno("完了", f"{output_path.name} を生成しました。開きますか？"):
            os.startfile(output_path)  # noqa: S606 - ユーザー自身が生成したローカルファイルを開く


class EvToolApp:
    """evtool のメインウィンドウ."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("evtool")
        self.root.geometry("560x460")
        self.root.minsize(480, 380)
        _apply_theme(self.root)

        self._icon_images = _build_app_icon()
        self.root.iconphoto(True, *self._icon_images)

        self.session: Optional[EvidenceSession] = None
        self.target_hwnd: Optional[int] = None
        self.target_window_label: str = ""
        self._log_queue: "queue.Queue[str]" = queue.Queue()
        self._entries: list[tk.Widget] = []
        self._test_id_history: list[str] = []
        self._title_history: list[str] = []

        self._build_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(150, self._poll_log_queue)

    # ---- widgets ---------------------------------------------------------
    def _build_widgets(self) -> None:
        ttk.Label(self.root, text="evtool", style="Header.TLabel", padding=(10, 8, 10, 4)).pack(
            anchor="w"
        )

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        capture_tab = ttk.Frame(notebook)
        notebook.add(capture_tab, text="エビデンス取得")
        self._build_capture_tab(capture_tab)

        check_tab = SourceCheckFrame(notebook, log_callback=self._log)
        notebook.add(check_tab, text="机上確認")

        instrument_tab = InstrumentFrame(notebook, log_callback=self._log)
        notebook.add(instrument_tab, text="動作確認コード挿入")

    def _build_capture_tab(self, parent: tk.Widget) -> None:
        ttk.Label(
            parent,
            text="操作の流れ:  ①対象ウィンドウを選択 → ②開始 → ③今すぐキャプチャ（必要なら自動も） → ④終了してまとめる",
            style="Status.TLabel",
            padding=(10, 6, 10, 0),
        ).pack(fill="x")

        form = ttk.Frame(parent, padding=10)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        self.var_test_id = tk.StringVar()
        self.var_title = tk.StringVar()
        self.var_window_display = tk.StringVar(value="(未選択)")
        self.var_auto_capture = tk.BooleanVar(value=False)
        self.var_interval = tk.StringVar(value="10")
        self.var_output = tk.StringVar(value="evidence")
        self.var_log_file = tk.StringVar()
        self.var_shot_note = tk.StringVar()

        def add_row(row: int, label: str, var: tk.StringVar, browse=None, width=40):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=4)
            entry = ttk.Entry(form, textvariable=var, width=width)
            entry.grid(row=row, column=1, sticky="we", padx=(6, 6), pady=4)
            self._entries.append(entry)
            if browse is not None:
                ttk.Button(form, text="参照...", command=browse).grid(row=row, column=2, pady=4)
            return entry

        ttk.Label(form, text="試験ID *").grid(row=0, column=0, sticky="w", pady=4)
        self.combo_test_id = ttk.Combobox(form, textvariable=self.var_test_id, width=38)
        self.combo_test_id.grid(row=0, column=1, sticky="we", padx=(6, 6), pady=4)
        self._entries.append(self.combo_test_id)
        Tooltip(
            self.combo_test_id,
            "試験IDを入力します。前回末尾が数字（例: TC001）であれば、\n"
            "「終了してまとめる」後に自動的に次の番号（TC002）を入力しておきます。\n"
            "過去に使ったIDは▼から選べます。",
        )

        ttk.Label(form, text="試験項目名 *").grid(row=1, column=0, sticky="w", pady=4)
        self.combo_title = ttk.Combobox(form, textvariable=self.var_title, width=38)
        self.combo_title.grid(row=1, column=1, sticky="we", padx=(6, 6), pady=4)
        self._entries.append(self.combo_title)
        Tooltip(self.combo_title, "試験項目名を入力します。過去に使った項目名は▼から選べます。")

        ttk.Label(form, text="対象ウィンドウ *").grid(row=2, column=0, sticky="w", pady=4)
        window_entry = ttk.Entry(form, textvariable=self.var_window_display, state="readonly")
        window_entry.grid(row=2, column=1, sticky="we", padx=(6, 6), pady=4)
        self.btn_pick_window = ttk.Button(form, text="選択...", command=self._on_pick_window)
        self.btn_pick_window.grid(row=2, column=2, pady=4)
        Tooltip(
            self.btn_pick_window,
            "現在開いているウィンドウの一覧から、キャプチャしたい画面を選びます。\n"
            "選択後はウィンドウのタイトルが変わっても、同じウィンドウを追跡し続けます。\n"
            "一覧先頭の「画面全体」を選ぶと、デスクトップ全体をキャプチャできます。",
        )

        auto_frame = ttk.Frame(form)
        auto_frame.grid(row=3, column=0, columnspan=3, sticky="we", pady=4)
        self.chk_auto = ttk.Checkbutton(
            auto_frame,
            text="自動キャプチャを有効にする",
            variable=self.var_auto_capture,
            command=self._on_toggle_auto,
        )
        self.chk_auto.pack(side="left")
        Tooltip(
            self.chk_auto,
            "チェックしない場合（既定）は「今すぐキャプチャ」ボタンを押したときだけ記録します。\n"
            "チェックすると、それに加えて指定した間隔(秒)で自動的にもキャプチャします。",
        )
        ttk.Label(auto_frame, text="間隔(秒)").pack(side="left", padx=(12, 4))
        self.entry_interval = ttk.Entry(auto_frame, textvariable=self.var_interval, width=8, state="disabled")
        self.entry_interval.pack(side="left")
        self._entries.append(self.entry_interval)

        add_row(4, "出力先フォルダ", self.var_output, browse=self._browse_output)
        log_entry = add_row(5, "Tera Termのログファイル(任意)", self.var_log_file, browse=self._browse_log_file)
        Tooltip(
            log_entry,
            "Tera Term側で「ファイル > ログ」やマクロの logopen で保存している、\n"
            "コマンドの入出力を記録したテキストファイルです（評価したい操作と直接の\n"
            "関係はありません。任意項目で、指定しなくても画面キャプチャだけで進められます）。\n"
            "指定すると、「終了してまとめる」時にその内容がコピーされ、\n"
            "evidenceフォルダ内に textlog.log として保存・レポートに添付されます。",
        )

        btn_frame = ttk.Frame(parent, padding=(10, 0, 10, 8))
        btn_frame.pack(fill="x")
        self.btn_start = ttk.Button(btn_frame, text="開始", style="Primary.TButton", command=self._on_start)
        self.btn_start.pack(side="left")
        self.btn_capture = ttk.Button(
            btn_frame,
            text="今すぐキャプチャ",
            style="Capture.TButton",
            command=self._on_capture,
            state="disabled",
        )
        self.btn_capture.pack(side="left", padx=6)
        ttk.Label(btn_frame, text="備考:").pack(side="left", padx=(6, 4))
        self.entry_shot_note = ttk.Entry(btn_frame, textvariable=self.var_shot_note, width=24, state="disabled")
        self.entry_shot_note.pack(side="left")
        self.btn_finish = ttk.Button(
            btn_frame,
            text="終了してまとめる",
            style="Finish.TButton",
            command=self._on_finish,
            state="disabled",
        )
        self.btn_finish.pack(side="left", padx=(12, 0))

        self.status_var = tk.StringVar(value="待機中")
        ttk.Label(parent, textvariable=self.status_var, style="Status.TLabel", padding=(10, 0, 10, 4)).pack(
            fill="x"
        )

        log_frame = ttk.Frame(parent, padding=(10, 0, 10, 10))
        log_frame.pack(fill="both", expand=True)
        self.log_text = tk.Text(
            log_frame,
            state="disabled",
            wrap="word",
            bg=PALETTE["panel"],
            fg=PALETTE["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
            font=(FONT_FAMILY, FONT_SIZE),
        )
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _browse_output(self) -> None:
        path = filedialog.askdirectory(title="エビデンス出力先フォルダを選択")
        if path:
            self.var_output.set(path)

    def _browse_log_file(self) -> None:
        path = filedialog.askopenfilename(title="Tera Term ログファイルを選択")
        if path:
            self.var_log_file.set(path)

    def _on_pick_window(self) -> None:
        dialog = WindowPickerDialog(self.root)
        self.root.wait_window(dialog)
        if dialog.selected is not None:
            self.target_hwnd, self.target_window_label = dialog.selected
            self.var_window_display.set(self.target_window_label)

    def _on_toggle_auto(self) -> None:
        self.entry_interval.configure(state="normal" if self.var_auto_capture.get() else "disabled")

    # ---- logging -----------------------------------------------------------
    def _log(self, message: str) -> None:
        self._log_queue.put(message)

    def _poll_log_queue(self) -> None:
        while True:
            try:
                message = self._log_queue.get_nowait()
            except queue.Empty:
                break
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.configure(state="normal")
            self.log_text.insert("end", f"[{timestamp}] {message}\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        self.root.after(150, self._poll_log_queue)

    # ---- actions -----------------------------------------------------------
    @staticmethod
    def _remember(history: list[str], combo: ttk.Combobox, value: str) -> None:
        if value in history:
            history.remove(value)
        history.insert(0, value)
        combo.configure(values=history)

    def _set_form_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for entry in self._entries:
            if entry is self.entry_interval and enabled and not self.var_auto_capture.get():
                continue  # 自動キャプチャ未使用時は間隔欄を無効のままにする
            entry.configure(state=state)
        self.btn_pick_window.configure(state=state)
        self.chk_auto.configure(state=state)

    def _on_start(self) -> None:
        test_id = self.var_test_id.get().strip()
        title = self.var_title.get().strip()
        if not test_id or not title:
            messagebox.showerror("入力エラー", "試験IDと試験項目名は必須です")
            return
        is_valid_target = self.target_hwnd is not None and (
            self.target_hwnd == FULL_SCREEN_HWND or win32gui.IsWindow(self.target_hwnd)
        )
        if not is_valid_target:
            messagebox.showerror("入力エラー", "対象ウィンドウを選択してください")
            return

        self._remember(self._test_id_history, self.combo_test_id, test_id)
        self._remember(self._title_history, self.combo_title, title)

        auto_capture = self.var_auto_capture.get()
        interval = 10.0
        if auto_capture:
            try:
                interval = float(self.var_interval.get())
                if interval <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("入力エラー", "自動キャプチャ間隔は正の数値で入力してください")
                return

        self.session = EvidenceSession(
            base_dir=Path(self.var_output.get().strip() or "evidence"),
            test_id=test_id,
            title=title,
            hwnd=self.target_hwnd,
            window_label=self.target_window_label,
            auto_capture=auto_capture,
            interval=interval,
            log_callback=self._log,
        )
        self.session.start()
        self._log(f"エビデンス取得を開始しました: {self.session.dir}")
        if auto_capture:
            self._log(f'対象ウィンドウ: "{self.target_window_label}" / 自動キャプチャ間隔: {interval}秒')
        else:
            self._log(f'対象ウィンドウ: "{self.target_window_label}" / 自動キャプチャ: 無効（手動のみ）')
        self.status_var.set(f"取得中: {self.session.dir}")

        self._set_form_enabled(False)
        self.btn_start.configure(state="disabled")
        self.btn_capture.configure(state="normal")
        self.entry_shot_note.configure(state="normal")
        self.btn_finish.configure(state="normal")

    def _on_capture(self) -> None:
        if self.session is not None:
            note = self.var_shot_note.get().strip()
            self.session.capture_now(tag="manual", note=note)
            self.var_shot_note.set("")

    def _on_finish(self) -> None:
        if self.session is None:
            return

        included_files = None
        if self.session.meta.shots:
            selection_dialog = ShotSelectionDialog(self.root, self.session.meta.shots)
            self.root.wait_window(selection_dialog)
            if selection_dialog.cancelled:
                return
            included_files = selection_dialog.included_files

        dialog = FinishDialog(self.root)
        self.root.wait_window(dialog)
        if dialog.result_value is None:
            return

        log_file = self.var_log_file.get().strip() or None
        session_dir = self.session.finish(
            result=dialog.result_value,
            note=dialog.note_value,
            log_file=log_file,
            included_files=included_files,
        )
        report_path = generate_report(session_dir)
        self._log(f"エビデンスをまとめました: {session_dir}")
        self._log(f"レポート: {report_path}")
        self.status_var.set(f"完了: {session_dir}")

        self.session = None
        self._set_form_enabled(True)
        self.btn_start.configure(state="normal")
        self.btn_capture.configure(state="disabled")
        self.entry_shot_note.configure(state="disabled")
        self.btn_finish.configure(state="disabled")

        finished_test_id = self.var_test_id.get().strip()
        next_test_id = increment_test_id(finished_test_id)
        self.var_test_id.set(next_test_id)
        if next_test_id != finished_test_id:
            self._log(f"次の試験ID候補を入力しておきました: {next_test_id}")

        if messagebox.askyesno("完了", "レポートを開きますか？"):
            os.startfile(report_path)  # noqa: S606 - ユーザー自身が生成したローカルファイルを開く

    def _on_close(self) -> None:
        if self.session is not None:
            if not messagebox.askyesno(
                "確認", "エビデンス取得中です。保存せずに終了しますか？"
            ):
                return
        self.root.destroy()


def main() -> int:
    root = tk.Tk()
    EvToolApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
