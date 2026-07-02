"""evtool: ウィンドウのエビデンス取得・まとめツール（単一ファイル / Windows専用）.

Tera Term マクロ試験を主用途として作られているが、対象ウィンドウは hwnd で
固定して追跡するため、任意のアプリケーションのスクリーンショット・ログ取得にも
使える。

使い方:
    py evtool.py

詳細は README.md を参照。
"""
from __future__ import annotations

import base64
import csv
import ctypes
import difflib
import hashlib
import html
import io
import json
import math
import os
import queue
import re
import shutil
import sys
import tempfile
import threading
import tkinter as tk
from ctypes import wintypes
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, font as tkfont, messagebox, ttk
from typing import Callable, Optional
from urllib.parse import quote

import win32api
import win32clipboard
import win32con
import win32gui
import win32ui
from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageGrab, ImageTk

__version__ = "0.1.0"

# ============================================================================
# ウィンドウ検出・スクリーンショット取得
# ============================================================================

# PrintWindow の flags。GPU描画などのレンダリング方式を問わず、また他ウィンドウに
# 重なっていてもウィンドウの内容を取得できるようにする。
PW_RENDERFULLCONTENT = 0x00000002

# 「画面全体」を対象として選んだことを表す特別な値（実際のhwndは正の整数なので衝突しない）。
FULL_SCREEN_HWND = -1

# 個別モニターを対象として選んだことを表す値の基準点。モニター0 = -2, モニター1 = -3,
# ... というように負方向に連番を振る（実際のhwndは正の整数なので衝突しない）。
MONITOR_HWND_BASE = -2

# ドラッグで指定した画面上の矩形範囲を対象として選んだことを表す特別な値。
# モニター用の連番（-2, -3, ...）と衝突しないよう、十分離れた値にする。
REGION_HWND = -100000


def list_monitors() -> list[tuple[int, int, int, int]]:
    """接続されている各モニターの矩形 (left, top, right, bottom) を仮想スクリーン座標で列挙する."""
    return [info[2] for info in win32api.EnumDisplayMonitors()]


def is_monitor_hwnd(hwnd: int) -> bool:
    return MONITOR_HWND_BASE >= hwnd > REGION_HWND


def monitor_hwnd(index: int) -> int:
    return MONITOR_HWND_BASE - index


def monitor_index_from_hwnd(hwnd: int) -> int:
    return MONITOR_HWND_BASE - hwnd


def list_capture_candidate_windows() -> list[tuple[int, str]]:
    """キャプチャ対象として選択可能なトップレベルウィンドウを (hwnd, タイトル) で列挙する.

    タイトル文字列ではなく hwnd で対象を固定して以降キャプチャするため、対象アプリの
    ウィンドウタイトルが実行中に変化しても選択したウィンドウを継続して取得できる
    （例: Tera Term は接続先表示でタイトルが変わる）。
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


def capture_monitor(rect: tuple[int, int, int, int], save_path: Path) -> None:
    """指定した矩形範囲（モニター1台分・ドラッグ指定範囲など）をキャプチャしてPNGとして保存する."""
    image = ImageGrab.grab(bbox=rect, all_screens=True)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(save_path)


def stamp_timestamp(path: Path, when: datetime) -> None:
    """保存済みのスクリーンショット右下に撮影時刻を焼き込む（エビデンスの証跡性向上）."""
    text = when.strftime("%Y-%m-%d %H:%M:%S")
    with Image.open(path) as img:
        base = img.convert("RGBA")

    font_size = max(14, base.width // 80)
    font = None
    for font_name in ("segoeui.ttf", "meiryo.ttc", "arial.ttf"):
        try:
            font = ImageFont.truetype(font_name, font_size)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    pad, margin = 6, 10
    box_w, box_h = (right - left) + pad * 2, (bottom - top) + pad * 2
    x0 = base.width - box_w - margin
    y0 = base.height - box_h - margin
    draw.rectangle((x0, y0, x0 + box_w, y0 + box_h), fill=(0, 0, 0, 140))
    draw.text((x0 + pad - left, y0 + pad - top), text, fill=(255, 255, 255, 255), font=font)
    Image.alpha_composite(base, overlay).convert("RGB").save(path)


def copy_image_to_clipboard(path: Path) -> None:
    """画像ファイルをWindowsのクリップボードへ（Excel等に直接貼り付けられるDIB形式で）コピーする."""
    with Image.open(path) as img:
        image = img.convert("RGB")
    buf = io.BytesIO()
    image.save(buf, "BMP")
    data = buf.getvalue()[14:]  # BMPファイルヘッダ(14バイト)を除いた部分がDIB

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_DIB, data)
    finally:
        win32clipboard.CloseClipboard()


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

    キャプチャ対象は開始時に選択した hwnd に固定する。対象アプリのウィンドウ
    タイトルは実行中に変化することがあるため（例: Tera Term の接続先表示）、
    タイトル文字列の再検索ではなく hwnd 固定で追跡する。
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
        region: Optional[tuple[int, int, int, int]] = None,
        stamp_time: bool = False,
    ):
        self.hwnd = hwnd
        self.region = region  # hwnd == REGION_HWND のときのキャプチャ範囲（仮想スクリーン座標）
        self.stamp_time = stamp_time
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
        self._pause_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._shot_seq = 0
        self.failed_count = 0
        self._last_capture_hash: Optional[str] = None

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

        self._save_meta_snapshot()
        return self.dir

    def cancel(self) -> None:
        """セッションを取りやめる（finish()と異なりレポート化せず、取得済みのデータも削除する）.

        「開始」を誤って押した場合などに使う想定のため、確認は呼び出し側
        （GUI）の責務とし、ここでは無条件に削除する。
        """
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self.interval + 5)
        shutil.rmtree(self.dir, ignore_errors=True)

    def _save_meta_snapshot(self) -> None:
        """現時点の meta.json を保存する.

        capture_now の成功ごとに呼ぶことで、長時間の試験中にアプリが異常終了
        しても、それまでに撮れていたスクリーンショットとその対応関係（タグ・
        備考等）を失わないようにする（finish() 時にも確定版として上書きされる）。
        """
        meta_path = self.dir / "meta.json"
        try:
            meta_path.write_text(
                json.dumps(asdict(self.meta), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            self._log_callback(f"警告: meta.json の保存に失敗しました: {exc}")

    # ---- キャプチャ ----------------------------------------------------
    def toggle_pause(self) -> bool:
        """自動キャプチャの一時停止状態を反転し、新しい状態（True=一時停止中）を返す.

        一時停止中も手動キャプチャ（capture_now）は通常どおり使える。
        """
        if self._pause_event.is_set():
            self._pause_event.clear()
        else:
            self._pause_event.set()
        return self._pause_event.is_set()

    def capture_now(self, tag: str = "manual", note: str = "") -> Optional[str]:
        is_full_screen = self.hwnd == FULL_SCREEN_HWND
        is_monitor = is_monitor_hwnd(self.hwnd)
        is_region = self.hwnd == REGION_HWND
        if not is_full_screen and not is_monitor and not is_region and not win32gui.IsWindow(self.hwnd):
            self.failed_count += 1
            self._log_callback("警告: 対象ウィンドウが見つかりません（閉じられた可能性があります）")
            return None

        with self._lock:
            self._shot_seq += 1
            filename = f"shot_{_timestamp()}_{self._shot_seq:03d}_{tag}.png"
            path = self.shots_dir / filename
            try:
                if is_full_screen:
                    capture_full_screen(path)
                elif is_region:
                    if self.region is None:
                        raise RuntimeError("キャプチャ範囲が設定されていません")
                    capture_monitor(self.region, path)
                elif is_monitor:
                    monitors = list_monitors()
                    index = monitor_index_from_hwnd(self.hwnd)
                    if index >= len(monitors):
                        raise RuntimeError("モニター構成が変化したため取得できません")
                    capture_monitor(monitors[index], path)
                else:
                    capture_window(self.hwnd, path)
            except Exception as exc:  # noqa: BLE001 - 取得は続けたいので例外は握り潰して警告のみ
                self.failed_count += 1
                self._log_callback(f"警告: キャプチャに失敗しました: {exc}")
                return None

            self.failed_count = 0
            # 重複判定は時刻焼き込みの「前」の画像で行う（焼き込むと毎回時刻分だけ
            # 変化してしまい、autoの同一画面スキップが効かなくなるため）。
            current_hash = hashlib.md5(path.read_bytes()).hexdigest()
            if tag == "auto" and current_hash == self._last_capture_hash:
                path.unlink(missing_ok=True)
                self._shot_seq -= 1
                return None
            self._last_capture_hash = current_hash
            if self.stamp_time:
                try:
                    stamp_timestamp(path, datetime.now())
                except Exception as exc:  # noqa: BLE001 - 焼き込み失敗でも画像自体は残す
                    self._log_callback(f"警告: 撮影時刻の焼き込みに失敗しました: {exc}")
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
            self._save_meta_snapshot()
            suffix = f" - {note}" if note else ""
            self._log_callback(f"キャプチャしました: {filename} ({tag}){suffix}")
            return filename

    def _auto_capture_loop(self) -> None:
        consecutive_failures = 0
        max_consecutive_failures = 3
        while not self._stop_event.wait(self.interval):
            if self._pause_event.is_set():
                continue
            prev_failed_count = self.failed_count
            self.capture_now(tag="auto")
            if self.failed_count > prev_failed_count:
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    self._log_callback(
                        f"警告: 対象が{max_consecutive_failures}回連続で取得できないため、"
                        "自動キャプチャを停止しました。"
                    )
                    break
            else:
                consecutive_failures = 0

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

_REPORT_STYLE_PASTEL = """<style>
  :root {
    --bg: #F7F8FC;
    --card: #FFFFFF;
    --accent: #C9D6FF;
    --accent-dark: #7C8FE0;
    --pastel-pink: #F4B6C2;
    --pastel-mint: #B7E4C7;
    --text: #3A3A4A;
    --border: #E3E6F0;
  }
  body {
    font-family: "Yu Gothic UI", "Segoe UI", "Meiryo", sans-serif;
    margin: 0;
    padding: 2em;
    color: var(--text);
    background: var(--bg);
  }
  h1 { font-weight: 600; color: var(--accent-dark); }
  h2 { font-weight: 600; color: var(--accent-dark); border-bottom: 2px solid var(--accent); padding-bottom: 4px; }
  table {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 1.5em;
    background: var(--card);
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }
  th, td { border: 1px solid var(--border); padding: 6px 14px; text-align: left; }
  th { background: #EEF1FB; font-weight: 600; width: 180px; }
  .shot-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5em; }
  .shot {
    margin-bottom: 0;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }
  .shot img { max-width: 100%; border: 1px solid var(--border); border-radius: 6px; display: block; margin-top: 6px; }
  .tag-auto { color: #6B7A99; background: #E7ECF7; border-radius: 6px; padding: 2px 8px; font-size: 0.85em; }
  .tag-manual { color: #B23A5A; background: var(--pastel-pink); border-radius: 6px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; }
  .shot-note { margin-top: 6px; padding: 6px 10px; background: var(--pastel-mint); border-radius: 6px; display: inline-block; }
  pre { background: #EEF1FB; padding: 1em; border-radius: 8px; overflow-x: auto; max-height: 400px; }
</style>"""

_REPORT_STYLE_MONO = """<style>
  :root { --bg: #FFFFFF; --card: #FFFFFF; --accent: #999999; --accent-dark: #333333; --text: #000000; --border: #999999; }
  body { font-family: "Yu Gothic UI", "Segoe UI", "Meiryo", sans-serif; margin: 0; padding: 2em; color: var(--text); background: var(--bg); }
  h1 { font-weight: 700; color: var(--text); border-bottom: 2px solid var(--text); padding-bottom: 4px; }
  h2 { font-weight: 700; color: var(--text); border-bottom: 1px solid var(--border); padding-bottom: 4px; }
  table { border-collapse: collapse; margin-bottom: 1.5em; }
  th, td { border: 1px solid var(--border); padding: 6px 14px; text-align: left; }
  th { background: #EEEEEE; font-weight: 700; }
  .shot-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5em; }
  .shot { margin-bottom: 0; border: 1px solid var(--border); padding: 12px; page-break-inside: avoid; }
  .shot img { max-width: 100%; border: 1px solid var(--border); display: block; margin-top: 6px; }
  .tag-auto, .tag-manual { color: var(--text); background: #EEEEEE; border: 1px solid var(--border); padding: 2px 8px; font-size: 0.85em; }
  .tag-manual { font-weight: 700; }
  .shot-note { margin-top: 6px; padding: 6px 10px; border: 1px dashed var(--border); display: inline-block; }
  pre { background: #F5F5F5; border: 1px solid var(--border); padding: 1em; overflow-x: auto; max-height: 400px; }
</style>"""

_REPORT_STYLE_DARK = """<style>
  :root {
    --bg: #1E1E2A; --card: #2A2A3A; --accent: #5B6BA8; --accent-dark: #8FA0E8;
    --pastel-pink: #E08CA0; --pastel-mint: #6FBF8F; --text: #E4E6F0; --border: #3D3D52;
  }
  body { font-family: "Yu Gothic UI", "Segoe UI", "Meiryo", sans-serif; margin: 0; padding: 2em; color: var(--text); background: var(--bg); }
  h1 { font-weight: 600; color: var(--accent-dark); }
  h2 { font-weight: 600; color: var(--accent-dark); border-bottom: 2px solid var(--accent); padding-bottom: 4px; }
  table { border-collapse: collapse; margin-bottom: 1.5em; background: var(--card); border-radius: 10px; overflow: hidden; }
  th, td { border: 1px solid var(--border); padding: 6px 14px; text-align: left; }
  th { background: #33334A; font-weight: 600; }
  .shot-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5em; }
  .shot { margin-bottom: 0; background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 12px; }
  .shot img { max-width: 100%; border: 1px solid var(--border); border-radius: 6px; display: block; margin-top: 6px; }
  .tag-auto { color: #B7C0E0; background: #33334A; border-radius: 6px; padding: 2px 8px; font-size: 0.85em; }
  .tag-manual { color: #2A1018; background: var(--pastel-pink); border-radius: 6px; padding: 2px 8px; font-size: 0.85em; font-weight: 600; }
  .shot-note { margin-top: 6px; padding: 6px 10px; background: var(--pastel-mint); color: #102A18; border-radius: 6px; display: inline-block; }
  pre { background: #15151E; border: 1px solid var(--border); padding: 1em; border-radius: 8px; overflow-x: auto; max-height: 400px; }
</style>"""

REPORT_STYLES: dict[str, str] = {
    "パステル（既定）": _REPORT_STYLE_PASTEL,
    "シンプル（白黒・印刷向け）": _REPORT_STYLE_MONO,
    "ダーク": _REPORT_STYLE_DARK,
}

_REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>試験エビデンス: {test_id} - {title}</title>
{style_css}
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
<div class="shot-grid">
{shots_html}
</div>

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

_SHOT_TEMPLATE_MINIMAL = """<div class="shot">
  <img src="{src}" alt="{file}">
  {note_html}
</div>
"""

_REPORT_TEMPLATE_MINIMAL = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>試験エビデンス: {test_id} - {title}</title>
{style_css}
</head>
<body>
<h1>{test_id} - {title}</h1>
<div class="shot-grid">
{shots_html}
</div>
</body>
</html>
"""

REPORT_CONTENT_FULL = "詳細（既定）"
REPORT_CONTENT_MINIMAL = "画像と備考のみ"
REPORT_CONTENTS: list[str] = [REPORT_CONTENT_FULL, REPORT_CONTENT_MINIMAL]


def generate_report(
    session_dir: Path,
    style: str = "パステル（既定）",
    content: str = REPORT_CONTENT_FULL,
) -> Path:
    """report.html を screenshots/ や textlog.log への参照なしで単体完結するように生成する.

    style は REPORT_STYLES のキー。未知の値が渡された場合は既定（パステル）にフォールバックする。
    content が REPORT_CONTENT_MINIMAL の場合、試験情報の表やログを省き、画像と備考だけの
    簡易なレポートにする。
    """
    meta = json.loads((session_dir / "meta.json").read_text(encoding="utf-8"))

    all_shots = meta["shots"]
    included_shots = [s for s in all_shots if s.get("included", True)]
    minimal = content == REPORT_CONTENT_MINIMAL

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
        if minimal:
            shot_blocks.append(
                _SHOT_TEMPLATE_MINIMAL.format(src=src, file=html.escape(s["file"]), note_html=note_html)
            )
        else:
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

    style_css = REPORT_STYLES.get(style, _REPORT_STYLE_PASTEL)

    if minimal:
        report_html = _REPORT_TEMPLATE_MINIMAL.format(
            test_id=html.escape(meta["test_id"]),
            title=html.escape(meta["title"]),
            shots_html=shots_html,
            style_css=style_css,
        )
    else:
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
            style_css=style_css,
        )

    report_path = session_dir / "report.html"
    report_path.write_text(report_html, encoding="utf-8")
    return report_path


# ============================================================================
# セッション横断のまとめレポート（index.html / summary.csv）
# ============================================================================

_INDEX_ROW_TEMPLATE = (
    '<tr><td>{test_id}</td><td>{title}</td>'
    '<td><span class="{result_class}">{result}</span></td>'
    '<td>{start}</td><td>{duration}</td><td>{shots}</td><td>{note}</td><td>{link}</td></tr>\n'
)

_INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>試験エビデンス一覧</title>
{style_css}
</head>
<body>
<h1>試験エビデンス一覧</h1>
<p>対象フォルダ: <code>{base_dir}</code></p>
<p>生成日時: {generated_at} / 全{count}件（OK {ok_count} / NG {ng_count} / その他 {other_count}）</p>
<table>
<tr><th>試験ID</th><th>試験項目</th><th>結果</th><th>開始時刻</th><th>所要(秒)</th><th>ショット数</th><th>備考</th><th>レポート</th></tr>
{rows_html}
</table>
</body>
</html>
"""


def generate_summary_index(base_dir: Path) -> tuple[Optional[Path], Optional[Path], int]:
    """出力先フォルダ内の全セッション（meta.jsonを持つサブフォルダ）を一覧化する.

    base_dir 直下に index.html（各セッションの report.html へのリンク付き）と
    summary.csv（Excelでの集計用、utf-8-sig）を生成する。セッションが1件も
    見つからない場合は何も書き出さず (None, None, 0) を返す。
    """
    entries: list[tuple[Path, dict]] = []
    for meta_path in sorted(base_dir.glob("*/meta.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue  # 壊れた/書きかけのmeta.jsonはスキップして残りを一覧化する
        entries.append((meta_path.parent, meta))
    if not entries:
        return None, None, 0
    entries.sort(key=lambda e: e[1].get("start_time") or "")

    rows_html = []
    csv_rows = []
    ok_count = ng_count = 0
    for folder, meta in entries:
        result = meta.get("result") or ""
        if result == "OK":
            ok_count += 1
            result_class = "ok"
        elif result == "NG":
            ng_count += 1
            result_class = "ng"
        else:
            result_class = "warn"
        shots = len(meta.get("shots", []))
        report_file = folder / "report.html"
        link = (
            f'<a href="{quote(folder.name)}/report.html">開く</a>' if report_file.exists() else ""
        )
        rows_html.append(
            _INDEX_ROW_TEMPLATE.format(
                test_id=html.escape(meta.get("test_id") or ""),
                title=html.escape(meta.get("title") or ""),
                result_class=result_class,
                result=html.escape(result or "-"),
                start=html.escape(meta.get("start_time") or ""),
                duration=meta.get("duration_sec", ""),
                shots=shots,
                note=html.escape(meta.get("note") or ""),
                link=link,
            )
        )
        csv_rows.append(
            [
                meta.get("test_id") or "",
                meta.get("title") or "",
                result,
                meta.get("start_time") or "",
                meta.get("end_time") or "",
                meta.get("duration_sec", ""),
                shots,
                meta.get("note") or "",
                folder.name,
            ]
        )

    index_html = _INDEX_TEMPLATE.format(
        style_css=_CHECK_REPORT_STYLE_PASTEL,
        base_dir=html.escape(str(base_dir.resolve())),
        generated_at=datetime.now().isoformat(timespec="seconds"),
        count=len(entries),
        ok_count=ok_count,
        ng_count=ng_count,
        other_count=len(entries) - ok_count - ng_count,
        rows_html="".join(rows_html),
    )
    index_path = base_dir / "index.html"
    index_path.write_text(index_html, encoding="utf-8")

    csv_path = base_dir / "summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["試験ID", "試験項目", "結果", "開始時刻", "終了時刻", "所要時間(秒)", "ショット数", "備考", "フォルダ"])
        writer.writerows(csv_rows)
    return index_path, csv_path, len(entries)


# ============================================================================
# 机上確認（ソースコード確認）・動作確認コード挿入 ユーティリティ
# ============================================================================

ENCODINGS = ["utf-8", "utf-8-sig", "shift_jis", "cp932", "euc_jp"]


def detect_encoding(path: "str | Path") -> str:
    """ファイルの先頭バイトとデコード試行から、最も妥当そうなエンコーディングを推測する.

    BOM付きUTF-8は専用に検出する。それ以外は utf-8 → cp932 → shift_jis → euc_jp の順に
    デコードを試し、最初に成功したものを採用する（全て失敗した場合は utf-8 を返す。
    cp932 は shift_jis の上位互換にあたるため、日本語Windows環境での誤判定を避けるべく
    shift_jis より先に試す）。
    """
    data = Path(path).read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    for encoding in ("utf-8", "cp932", "shift_jis", "euc_jp"):
        try:
            data.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return "utf-8"

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

    変数名は \\b（単語境界）ではなく前後の非単語文字判定で囲むため、$var や obj.prop
    のように英数字・アンダースコア以外の特殊文字を含む/それで始まる変数名でも正しく
    検出できる（\\b は境界の片側に単語文字が必要なため、$ のような非単語文字の前に
    単語文字が無いと機能しない）。変数名の直後には GROUP_LIST[0] や arr[i] のような
    配列添字を任意で許容する。期待値側は ' " のクォートで囲まれていても無くても
    マッチするよう、入力側のクォートは比較前に取り除き、ソースコード側のクォートは
    あっても無くても良いものとして扱う。
    """
    var_re = re.escape(var_name)
    name_part = rf"(?<!\w){var_re}(?!\w)(?:\[[^\]\n]*\])?"
    if expected_value:
        value = expected_value
        if not as_regex and len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        value_part = value if as_regex else re.escape(value)
        return rf"{name_part}\s*[+\-*/%&|^]?=\s*['\"]?{value_part}['\"]?"
    return rf"{name_part}\s*[+\-*/%&|^]?=(?!=)"


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
    """机上確認の確認項目1件分.

    label・pattern は content/expected から動的に算出する。取込み後に Treeview 上で
    内容や期待値を編集すれば、表示ラベルも検索に使う正規表現も自動的に追従する。
    custom_label が設定されている場合（CSVの「名称」列で明示指定された場合）はそちらを
    表示優先する。
    """

    kind: str  # "variable" / "branch" / "custom"
    content: str  # variable: 変数名 / branch: 条件式 / custom: 正規表現
    expected: str = ""  # variable のときの期待値（branch/custom では未使用）
    custom_label: str = ""
    result: str = "-"  # "-" / "OK" / "NG"
    matched_line: str = ""

    @property
    def label(self) -> str:
        if self.custom_label:
            return self.custom_label
        if self.kind == "branch":
            return f"if: {self.content}"
        if self.kind == "custom":
            return self.content
        return f"変数: {self.content}" + (f" = {self.expected}" if self.expected else "")

    @property
    def pattern(self) -> str:
        if self.kind == "branch":
            return build_branch_pattern(self.content)
        if self.kind == "custom":
            return self.content
        return build_variable_pattern(self.content, self.expected)


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


def extract_variable_names_from_text(lines: list[str]) -> list[str]:
    """机上確認の「まとめ追加」と同じ書式（変数名 / 変数名 = 期待値）の行から変数名だけを抜き出す.

    変数名だけのリストでも、期待値付きの行が混在していても変数名部分のみを取り出せるように
    する。if/re: の行（変数定義ではないため）やコメント(#)・空行は対象外とする。
    """
    names: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if re.match(r"(?i)^(if\s+|re:)", stripped):
            continue
        name = stripped.split("=", 1)[0].strip()
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
    "  re: 正規表現        → カスタム正規表現で確認\n"
    "\n"
    "CSVから読み込み:\n"
    "  .txt → 上記と同じ1行1項目形式のテキストファイルとして読み込みます。\n"
    "  .csv → 列名（1行目）に 種別/内容(または変数名・条件式・正規表現)/期待値/名称 を含める\n"
    "    と自動で認識します。列名が無い場合は1列目を内容、2列目を期待値として扱います\n"
    "    （種別は省略時「変数定義」）。"
)


def parse_bulk_check_line(line: str) -> Optional["CheckItem"]:
    """机上確認のまとめ入力1行を CheckItem に変換する（空行・コメント行は None）."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    if re.match(r"(?i)^if\s+", stripped):
        condition = re.sub(r"(?i)^if\s+", "", stripped).strip()
        return CheckItem(kind="branch", content=condition)

    if re.match(r"(?i)^re:", stripped):
        pattern = re.sub(r"(?i)^re:", "", stripped).strip()
        return CheckItem(kind="custom", content=pattern)

    name, sep, expected = stripped.partition("=")
    name = name.strip()
    expected = expected.strip() if sep else ""
    return CheckItem(kind="variable", content=name, expected=expected)


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


# 挿入した動作確認コードを識別するためのマーカー。OUTPUT_TEMPLATES の各テンプレートに
# 含まれる "[evtool]" と、Tera Termマクロ用テンプレートの変数 "evtool_msg" を目印にする。
INSTRUMENT_MARKERS = ("[evtool]", "evtool_msg")


def strip_instrumentation(lines: list[str]) -> tuple[list[str], int]:
    """挿入済みの動作確認コード行を取り除き、(残った行, 除去した行数) を返す.

    マーカー（INSTRUMENT_MARKERS）を含む行を除去対象とする。「カスタム」テンプレートで
    マーカーを含まないコードを挿入した場合は検出できない。
    """
    kept = [line for line in lines if not any(marker in line for marker in INSTRUMENT_MARKERS)]
    return kept, len(lines) - len(kept)


_CHECK_REPORT_STYLE_PASTEL = """<style>
  body { font-family: "Yu Gothic UI", "Segoe UI", "Meiryo", sans-serif; margin: 0; padding: 2em;
          background: #F7F8FC; color: #3A3A4A; }
  h1 { color: #7C8FE0; }
  table { border-collapse: collapse; width: 100%; background: #FFFFFF; border-radius: 10px;
           overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
  th, td { border: 1px solid #E3E6F0; padding: 6px 12px; text-align: left; }
  th { background: #EEF1FB; }
  .ok { background: #B7E4C7; color: #2F7A4F; border-radius: 6px; padding: 2px 8px; font-weight: 600; }
  .ng { background: #F4B6C2; color: #B23A5A; border-radius: 6px; padding: 2px 8px; font-weight: 600; }
  .warn { background: #FCE8B5; color: #9A6B00; border-radius: 6px; padding: 2px 8px; font-weight: 600; }
  code { background: #EEF1FB; padding: 2px 6px; border-radius: 4px; }
</style>"""

_CHECK_REPORT_STYLE_MONO = """<style>
  body { font-family: "Yu Gothic UI", "Segoe UI", "Meiryo", sans-serif; margin: 0; padding: 2em;
          background: #FFFFFF; color: #000000; }
  h1 { color: #000000; border-bottom: 2px solid #000000; padding-bottom: 4px; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #999999; padding: 6px 12px; text-align: left; }
  th { background: #EEEEEE; font-weight: 700; }
  .ok, .ng, .warn { background: #EEEEEE; color: #000000; border: 1px solid #999999; padding: 2px 8px; font-weight: 700; }
  code { background: #F5F5F5; border: 1px solid #999999; padding: 2px 6px; }
</style>"""

_CHECK_REPORT_STYLE_DARK = """<style>
  body { font-family: "Yu Gothic UI", "Segoe UI", "Meiryo", sans-serif; margin: 0; padding: 2em;
          background: #1E1E2A; color: #E4E6F0; }
  h1 { color: #8FA0E8; }
  table { border-collapse: collapse; width: 100%; background: #2A2A3A; border-radius: 10px; overflow: hidden; }
  th, td { border: 1px solid #3D3D52; padding: 6px 12px; text-align: left; }
  th { background: #33334A; }
  .ok { background: #6FBF8F; color: #102A18; border-radius: 6px; padding: 2px 8px; font-weight: 600; }
  .ng { background: #E08CA0; color: #2A1018; border-radius: 6px; padding: 2px 8px; font-weight: 600; }
  .warn { background: #E8C97A; color: #2A2008; border-radius: 6px; padding: 2px 8px; font-weight: 600; }
  code { background: #15151E; border: 1px solid #3D3D52; padding: 2px 6px; border-radius: 4px; }
</style>"""

CHECK_REPORT_STYLES: dict[str, str] = {
    "パステル（既定）": _CHECK_REPORT_STYLE_PASTEL,
    "シンプル（白黒・印刷向け）": _CHECK_REPORT_STYLE_MONO,
    "ダーク": _CHECK_REPORT_STYLE_DARK,
}

_CHECK_REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>机上確認結果: {file_name}</title>
{style_css}
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
    "bg": "#EAF3FA",
    "panel": "#FFFFFF",
    "accent": "#AED1EA",
    "accent_dark": "#5B9BC4",
    "pink": "#F4B6C2",
    "pink_dark": "#B23A5A",
    "mint": "#B7E4C7",
    "mint_dark": "#2F7A4F",
    "text": "#3A3A4A",
    "muted": "#8A8FA3",
    "border": "#CFE3F0",
}
FONT_FAMILY = "Yu Gothic UI"
FONT_SIZE = 8

# アプリアイコン・ウィンドウのタイトルバーで共通して使う配色（パステルなサックス
# ブルー系。紫みを抑え、GUI本体のアクセント色と同じ濃いサックスブルーの線）。
APP_ICON_TOP_COLOR = (158, 196, 224)
APP_ICON_BOTTOM_COLOR = (200, 226, 240)
APP_ICON_LINE_COLOR = (62, 110, 148)
APP_ICON_TITLEBAR_TEXT_COLOR = (58, 58, 74)

# 入力欄(Entry/Combobox)の幅をタブ間で揃えるための共通定数。
ENTRY_WIDTH_TEXT = 14  # 試験ID・試験項目名・変数名・フォルダ名など、文字列を入れる欄
ENTRY_WIDTH_SHORT = 4  # 間隔(秒)など、数値だけを入れる欄
COMBO_WIDTH_ENCODING = 6  # エンコーディング選択


def _enable_high_dpi_support() -> None:
    """プロセスを Per-Monitor DPI aware にする（tk.Tk() より前に呼ぶこと）.

    これを呼ばないと、拡大率100%超のディスプレイでは OS がウィンドウ全体を
    ビットマップとして引き伸ばして表示するため、文字やアイコンがぼやける。
    """
    try:
        DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)
        ok = ctypes.windll.user32.SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
        if not ok:
            raise OSError("SetProcessDpiAwarenessContext failed")
    except (AttributeError, OSError):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        except (AttributeError, OSError):
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except (AttributeError, OSError):
                pass


def _set_app_user_model_id() -> None:
    """タスクバーにこのプロセス専用のアイコンを表示させる（tk.Tk() より前に呼ぶこと）.

    これを設定しないと、`py`/`python` 経由起動時にタスクバーが python.exe
    本体と同一視し、ランタイムで設定したアイコンではなく python.exe の
    既定アイコンを表示してしまうことがある。
    """
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("evtool.EvidenceTool")
    except (AttributeError, OSError):
        pass


def _build_app_icon() -> tuple[list[tk.PhotoImage], Optional[Path]]:
    """タスクバー等に表示するアプリアイコンを実行時に生成する（外部アセット不要）.

    戻り値は (タイトルバー用 PhotoImage のリスト, タスクバー用 .ico ファイルのパス)。
    256x256 で描いてから複数サイズに縮小することで、タスクバー/タイトルバーの
    小さいサイズでもアンチエイリアスが効いて綺麗に見えるようにする。GUI本体と同じ
    パステルなサックスブルーのグラデーション地に、本体のアクセント色と同じ濃い
    サックスブルーの細い輪郭線だけで描いた虫眼鏡を置く、落ち着いた印象のモチーフ
    にする。
    """
    size = 256
    margin = 14
    radius = 56
    line_color = (*APP_ICON_LINE_COLOR, 255)

    # 背景グラデーション（GUI本体と同じパステルなサックスブルー、縦方向）
    top_color = APP_ICON_TOP_COLOR
    bottom_color = APP_ICON_BOTTOM_COLOR
    gradient = Image.new("RGBA", (size, size))
    pixels = gradient.load()
    for y in range(size):
        t = y / size
        r = round(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = round(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = round(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        for x in range(size):
            pixels[x, y] = (r, g, b, 255)

    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((margin, margin, size - margin, size - margin), radius=radius, fill=255)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    img.paste(gradient, (0, 0), mask)

    # 上半分に控えめなハイライトを重ねて立体感を出す
    highlight = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hdraw = ImageDraw.Draw(highlight)
    hdraw.rounded_rectangle(
        (margin, margin, size - margin, int(size * 0.5)), radius=radius, fill=(255, 255, 255, 22)
    )
    img = Image.alpha_composite(img, highlight)
    draw = ImageDraw.Draw(img)

    # 縁に沿った細いアイボリーホワイトの内枠（上品さを出すフレーム）
    draw.rounded_rectangle(
        (margin + 10, margin + 10, size - margin - 10, size - margin - 10),
        radius=radius - 10,
        outline=(line_color[0], line_color[1], line_color[2], 130),
        width=2,
    )

    # 虫眼鏡: 確認・検証を行うツールであることを表すモチーフ。塗りはせず、
    # アイボリーホワイトの輪郭線だけで描く。
    cx, cy, r = 118, 118, 46
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=line_color, width=8)
    handle_angle = math.radians(45)
    hx1 = cx + r * math.cos(handle_angle)
    hy1 = cy + r * math.sin(handle_angle)
    hx2 = hx1 + 46 * math.cos(handle_angle)
    hy2 = hy1 + 46 * math.sin(handle_angle)
    draw.line((hx1, hy1, hx2, hy2), fill=line_color, width=10)

    photo_sizes = (64, 48, 32, 24, 16)
    icons = []
    for target_size in photo_sizes:
        resized = img.resize((target_size, target_size), Image.LANCZOS)
        buf = io.BytesIO()
        resized.save(buf, format="PNG")
        icons.append(tk.PhotoImage(data=buf.getvalue()))

    # Windows のタスクバーボタンは iconphoto だけでは反映されず、python.exe の既定
    # アイコンが優先されることがあるため、.ico も明示的に書き出して iconbitmap で
    # 設定する（_set_app_icon 参照）。高DPI環境では LoadImage が要求するサイズが
    # 32/16 とは限らないため、ぼやけずに済むよう Windows標準のサイズを広く埋め込む。
    ico_sizes = (16, 20, 24, 32, 40, 48, 64, 96, 128, 256)
    ico_path: Optional[Path] = None
    try:
        ico_path = Path(tempfile.gettempdir()) / "evtool_app_icon.ico"
        img.save(ico_path, format="ICO", sizes=[(s, s) for s in ico_sizes])
    except OSError:
        ico_path = None

    return icons, ico_path


def _set_app_icon(root: tk.Tk) -> list[tk.PhotoImage]:
    """ウィンドウ・タスクバーの双方にアプリアイコンを反映させる.

    iconphoto/iconbitmap だけでは Windows のタスクバーボタンに反映されず、
    python.exe の既定アイコン（py コマンド経由起動時など）のままになることが
    あるため、Win32 API で対象ウィンドウへ直接 WM_SETICON を送って上書きする。
    戻り値の PhotoImage リストは GC で消えないよう呼び出し側で参照を保持すること。
    """
    icon_images, ico_path = _build_app_icon()
    root.iconphoto(True, *icon_images)
    if ico_path is not None:
        try:
            root.iconbitmap(default=str(ico_path))
        except tk.TclError:
            pass
        try:
            # winfo_id() が返すのは Tk が内部で持つ子ウィンドウ(フレーム)の hwnd であり、
            # タスクバー/タイトルバーが参照する実際のトップレベルウィンドウではない。
            # そのままだと WM_SETICON 等が無関係なウィンドウに送られ、アイコンが
            # 一切反映されない。GetParent で実際のトップレベルの hwnd まで遡る必要がある
            # が、tk.Tk() 直後はこのラッパー用トップレベルウィンドウがまだ生成されて
            # おらず GetParent は 0 を返す。update_idletasks() で生成を強制してから
            # 取得する。
            root.update_idletasks()
            hwnd = win32gui.GetParent(root.winfo_id()) or root.winfo_id()
            # 32/16固定だと高DPI環境では実際に必要なサイズと食い違い、Windows側の
            # 拡大表示でぼやけるため、実際のシステムメトリクスから要求サイズを取る。
            big_size = win32api.GetSystemMetrics(win32con.SM_CXICON) or 32
            small_size = win32api.GetSystemMetrics(win32con.SM_CXSMICON) or 16
            hicon_big = win32gui.LoadImage(
                0, str(ico_path), win32con.IMAGE_ICON, big_size, big_size, win32con.LR_LOADFROMFILE
            )
            hicon_small = win32gui.LoadImage(
                0, str(ico_path), win32con.IMAGE_ICON, small_size, small_size, win32con.LR_LOADFROMFILE
            )
            win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hicon_big)
            win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, hicon_small)
            # WM_SETICON だけではタスクバーボタンに反映されないことがあるため、
            # ウィンドウクラス自体のアイコンも書き換える（py 経由起動時の対策）。
            ctypes.windll.user32.SetClassLongPtrW.restype = ctypes.c_void_p
            ctypes.windll.user32.SetClassLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
            ctypes.windll.user32.SetClassLongPtrW(hwnd, win32con.GCL_HICON, hicon_big)
            ctypes.windll.user32.SetClassLongPtrW(hwnd, win32con.GCL_HICONSM, hicon_small)
        except Exception:  # noqa: BLE001 - アイコン設定に失敗しても起動自体は継続したい
            pass
        try:
            _set_titlebar_color(hwnd, APP_ICON_TOP_COLOR, APP_ICON_TITLEBAR_TEXT_COLOR)
        except Exception:  # noqa: BLE001 - Windows 10等でDWM属性が使えなくても継続したい
            pass
    return icon_images


def _set_titlebar_color(hwnd: int, caption_rgb: tuple[int, int, int], text_rgb: tuple[int, int, int]) -> None:
    """ウィンドウのタイトルバー自体もアイコンと同系統の配色にする（Windows 11のみ有効）.

    DwmSetWindowAttribute の DWMWA_CAPTION_COLOR/DWMWA_TEXT_COLOR は
    Windows 11 (build 22000) 以降でのみサポートされる。古い Windows では
    呼び出しが失敗するだけで、ウィンドウの表示自体には影響しない。
    """
    DWMWA_CAPTION_COLOR = 35
    DWMWA_TEXT_COLOR = 36
    dwm_set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
    dwm_set_window_attribute.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint]
    dwm_set_window_attribute.restype = ctypes.c_long

    def to_colorref(rgb: tuple[int, int, int]) -> ctypes.c_int:
        return ctypes.c_int(rgb[0] | (rgb[1] << 8) | (rgb[2] << 16))

    caption_ref = to_colorref(caption_rgb)
    dwm_set_window_attribute(hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(caption_ref), ctypes.sizeof(caption_ref))
    text_ref = to_colorref(text_rgb)
    dwm_set_window_attribute(hwnd, DWMWA_TEXT_COLOR, ctypes.byref(text_ref), ctypes.sizeof(text_ref))


class GlobalHotkeyListener:
    """OS全体で効くホットキー（Ctrl+F5）を待ち受け、押されたらコールバックを呼ぶ.

    tkのキーバインドは自ウィンドウにフォーカスがあるときしか効かないため、
    対象アプリを操作したままキャプチャできるよう RegisterHotKey を使う。
    RegisterHotKey は登録したスレッドのメッセージループでしか WM_HOTKEY を
    受け取れないため、専用のバックグラウンドスレッドでループを回す。
    コールバックはそのスレッドから呼ばれるので、呼び出し側でGUIスレッドへの
    受け渡し（イベント/キュー）を行うこと。
    """

    _WM_HOTKEY = 0x0312
    _WM_QUIT = 0x0012
    _MOD_CONTROL = 0x0002
    _MOD_NOREPEAT = 0x4000
    _VK_F5 = 0x74
    _HOTKEY_ID = 1

    def __init__(self, on_hotkey: Callable[[], None]):
        self._on_hotkey = on_hotkey
        self._thread: Optional[threading.Thread] = None
        self._thread_id: Optional[int] = None
        self._ready = threading.Event()
        self._registered = False

    def start(self) -> bool:
        """待ち受けを開始する。登録に失敗した場合（他アプリが使用中等）は False を返す."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=2)
        return self._registered

    def stop(self) -> None:
        if self._thread is None or not self._thread.is_alive() or self._thread_id is None:
            return
        ctypes.windll.user32.PostThreadMessageW(self._thread_id, self._WM_QUIT, 0, 0)
        self._thread.join(timeout=1)

    def _run(self) -> None:
        self._thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        self._registered = bool(
            ctypes.windll.user32.RegisterHotKey(
                None, self._HOTKEY_ID, self._MOD_CONTROL | self._MOD_NOREPEAT, self._VK_F5
            )
        )
        self._ready.set()
        if not self._registered:
            return
        try:
            msg = wintypes.MSG()
            while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == self._WM_HOTKEY:
                    try:
                        self._on_hotkey()
                    except Exception:  # noqa: BLE001 - 通知失敗で待ち受け自体は止めない
                        pass
        finally:
            ctypes.windll.user32.UnregisterHotKey(None, self._HOTKEY_ID)


_THEME_IMAGE_REFS: list[ImageTk.PhotoImage] = []

_BUTTON_IMG_SIZE = (48, 18)
_BUTTON_RADIUS = 7
_BUTTON_IMG_BORDER = 8

_FIELD_IMG_SIZE = (60, 22)
_FIELD_RADIUS = 6
_FIELD_IMG_BORDER = 7


def _rounded_photo(
    size: tuple[int, int],
    radius: int,
    fill: str,
    outline: Optional[str] = None,
    outline_width: int = 0,
) -> ImageTk.PhotoImage:
    """角丸長方形を描いたPhotoImageを生成する（ttkのimage要素の素材用）.

    生成したPhotoImageはGC対策で _THEME_IMAGE_REFS に保持し続ける（ttkの
    image要素はPythonから参照が切れると表示が消えてしまうため）。
    """
    width, height = size
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    inset = outline_width / 2
    draw.rounded_rectangle(
        (inset, inset, width - 1 - inset, height - 1 - inset),
        radius=radius,
        fill=(*ImageColor.getrgb(fill), 255),
        outline=(*ImageColor.getrgb(outline), 255) if outline else None,
        width=outline_width,
    )
    photo = ImageTk.PhotoImage(img)
    _THEME_IMAGE_REFS.append(photo)
    return photo


def _apply_rounded_button_style(
    style: ttk.Style,
    style_name: str,
    *,
    fill: str,
    fg: str,
    fill_active: str,
    fill_disabled: str,
    fg_disabled: str,
    img_size: tuple[int, int] = _BUTTON_IMG_SIZE,
    radius: int = _BUTTON_RADIUS,
    img_border: int = _BUTTON_IMG_BORDER,
    padding: tuple[int, int] = (10, 1),
) -> None:
    """ボタンスタイルの背景を角丸画像に置き換える.

    clamテーマ標準の Button.border はフラットな矩形しか描けないため、PILで
    生成した角丸画像をttkのimage要素として差し込む。スタイル名ごとに専用の
    要素名を使うことで、TButton/Primary/Capture/Finishそれぞれの色を保てる
    （ttkは ".TButton" 接尾辞からレイアウトを継承するため、要素名を共有すると
    色が混ざってしまう）。img_size/radius/img_border/paddingは「▼」だけの
    アイコンボタンのように、通常のボタンより一回り小さくしたい場合に上書きする。
    """
    element = f"{style_name.replace('.', '_')}.button"
    normal = _rounded_photo(img_size, radius, fill)
    active = _rounded_photo(img_size, radius, fill_active)
    disabled = _rounded_photo(img_size, radius, fill_disabled)

    style.element_create(
        element, "image", normal,
        ("disabled", disabled),
        ("pressed", active),
        ("active", active),
        border=img_border, sticky="nsew",
    )
    style.layout(style_name, [
        (element, {"sticky": "nsew", "children": [
            ("Button.focus", {"sticky": "nsew", "children": [
                ("Button.padding", {"sticky": "nsew", "children": [
                    ("Button.label", {"sticky": "nsew"}),
                ]}),
            ]}),
        ]}),
    ])
    style.configure(style_name, foreground=fg, padding=padding, borderwidth=0, focusthickness=0)
    style.map(style_name, foreground=[("disabled", fg_disabled)])


def _apply_rounded_field_style(style: ttk.Style, kind: str) -> None:
    """Entry/Comboboxの入力欄背景を角丸画像に置き換える（フォーカス時は枠をアクセント色に）."""
    normal = _rounded_photo(_FIELD_IMG_SIZE, _FIELD_RADIUS, PALETTE["panel"], outline=PALETTE["border"], outline_width=1)
    focus = _rounded_photo(
        _FIELD_IMG_SIZE, _FIELD_RADIUS, PALETTE["panel"], outline=PALETTE["accent_dark"], outline_width=2
    )
    disabled = _rounded_photo(_FIELD_IMG_SIZE, _FIELD_RADIUS, "#EEF1FB", outline=PALETTE["border"], outline_width=1)

    if kind == "entry":
        style.element_create(
            "Rounded.entry.field", "image", normal,
            ("disabled", disabled), ("focus", focus),
            border=_FIELD_IMG_BORDER, sticky="nsew",
        )
        style.layout("TEntry", [
            ("Rounded.entry.field", {"sticky": "nsew", "children": [
                ("Entry.padding", {"sticky": "nsew", "children": [
                    ("Entry.textarea", {"sticky": "nsew"}),
                ]}),
            ]}),
        ])
        style.configure("TEntry", padding=(5, 2))
    else:
        style.element_create(
            "Rounded.combobox.field", "image", normal,
            ("disabled", disabled), ("focus", focus),
            border=_FIELD_IMG_BORDER, sticky="nsew",
        )
        # ▼(downarrow)は角丸フィールドの外ではなく内側に置く。外に置くと▼だけが
        # 角丸枠から切り離された細長い矩形として浮いて見え、レイアウトが崩れて見える。
        style.layout("TCombobox", [
            ("Rounded.combobox.field", {"sticky": "nsew", "children": [
                ("Combobox.downarrow", {"side": "right", "sticky": "ns"}),
                ("Combobox.padding", {"expand": "1", "sticky": "nsew", "children": [
                    ("Combobox.textarea", {"sticky": "nsew"}),
                ]}),
            ]}),
        ])
        style.configure("TCombobox", padding=(5, 2))


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
    style.configure("Warning.TLabel", foreground=PALETTE["pink_dark"], font=(FONT_FAMILY, FONT_SIZE, "bold"))

    style.configure(
        "TEntry",
        fieldbackground=PALETTE["panel"],
        bordercolor=PALETTE["border"],
        lightcolor=PALETTE["panel"],
        darkcolor=PALETTE["panel"],
        padding=5,
    )
    # ▼(downarrow)は角丸フィールド画像の内側に描くため（_apply_rounded_field_style参照）、
    # ▼自身の背景・枠は入力欄と同じ白にして境目が見えないようにする。
    style.configure(
        "TCombobox",
        fieldbackground=PALETTE["panel"],
        background=PALETTE["panel"],
        bordercolor=PALETTE["panel"],
        lightcolor=PALETTE["panel"],
        darkcolor=PALETTE["panel"],
        arrowcolor=PALETTE["accent_dark"],
        padding=5,
    )
    style.map(
        "TCombobox",
        background=[("active", PALETTE["panel"]), ("pressed", PALETTE["panel"])],
        arrowcolor=[("disabled", PALETTE["muted"])],
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
        padding=(14, 7),
        font=default_font,
    )
    style.map("TButton", background=[("active", PALETTE["accent_dark"]), ("disabled", "#E5E7F0")])

    style.configure(
        "Primary.TButton",
        background=PALETTE["accent_dark"],
        foreground="#FFFFFF",
        padding=(14, 7),
        font=(FONT_FAMILY, FONT_SIZE, "bold"),
    )
    style.map("Primary.TButton", background=[("active", "#3E7CA6"), ("disabled", "#C7D8E2")])

    style.configure("Capture.TButton", background=PALETTE["mint"], foreground=PALETTE["mint_dark"])
    style.map("Capture.TButton", background=[("active", "#9FD8B6"), ("disabled", "#E5E7F0")])

    style.configure("Finish.TButton", background=PALETTE["pink"], foreground=PALETTE["pink_dark"])
    style.map("Finish.TButton", background=[("active", "#EC9CAC"), ("disabled", "#E5E7F0")])

    style.configure("TScrollbar", background=PALETTE["accent"], troughcolor=PALETTE["bg"])

    # ボタン・入力欄を角丸のモダンな見た目にする（PIL生成画像をttkのimage要素として使用）。
    _apply_rounded_button_style(
        style, "TButton",
        fill=PALETTE["accent"], fg=PALETTE["text"],
        fill_active=PALETTE["accent_dark"], fill_disabled="#E5E7F0", fg_disabled=PALETTE["muted"],
    )
    _apply_rounded_button_style(
        style, "Primary.TButton",
        fill=PALETTE["accent_dark"], fg="#FFFFFF",
        fill_active="#3E7CA6", fill_disabled="#C7D8E2", fg_disabled="#FFFFFF",
    )
    _apply_rounded_button_style(
        style, "Capture.TButton",
        fill=PALETTE["mint"], fg=PALETTE["mint_dark"],
        fill_active="#9FD8B6", fill_disabled="#E5E7F0", fg_disabled=PALETTE["muted"],
    )
    _apply_rounded_button_style(
        style, "Finish.TButton",
        fill=PALETTE["pink"], fg=PALETTE["pink_dark"],
        fill_active="#EC9CAC", fill_disabled="#E5E7F0", fg_disabled=PALETTE["muted"],
    )
    _apply_rounded_field_style(style, "entry")
    _apply_rounded_field_style(style, "combobox")

    # 「▼」だけの開閉トグルなど、通常のボタンより一回り小さくしたいアイコン専用ボタン。
    _apply_rounded_button_style(
        style, "Icon.TButton",
        fill=PALETTE["accent"], fg=PALETTE["text"],
        fill_active=PALETTE["accent_dark"], fill_disabled="#E5E7F0", fg_disabled=PALETTE["muted"],
        img_size=(22, 18), radius=7, img_border=8, padding=(6, 1),
    )

    style.configure(
        "ShotRow.TFrame", background=PALETTE["panel"], relief="flat", borderwidth=1
    )

    style.configure(
        "Treeview",
        background=PALETTE["panel"],
        fieldbackground=PALETTE["panel"],
        foreground=PALETTE["text"],
        bordercolor=PALETTE["border"],
        rowheight=20,
        font=default_font,
    )
    style.configure(
        "Treeview.Heading",
        background="#8BBCD8",
        foreground=PALETTE["text"],
        font=(FONT_FAMILY, FONT_SIZE, "bold"),
    )
    style.map("Treeview", background=[("selected", PALETTE["accent"])], foreground=[("selected", PALETTE["text"])])



class CapturePreviewPopup(tk.Toplevel):
    """キャプチャ直後に、実際に撮れた画像をその場で確認できるポップアップ.

    レポート（HTML化）を生成するまでキャプチャ内容を確認する手段がなかった課題に
    対応するため、キャプチャ直後・対象ウィンドウ選択直後に一時的に表示する。
    クリックまたは一定時間で自動的に閉じる。
    """

    def __init__(self, parent: tk.Misc, image_path: Path, caption: str = "", auto_close_ms: int = 5000):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        self._photo: Optional[ImageTk.PhotoImage] = None
        outer = tk.Frame(self, bg=PALETTE["accent_dark"], padx=2, pady=2)
        outer.pack()
        inner = tk.Frame(outer, bg=PALETTE["panel"])
        inner.pack()

        try:
            with Image.open(image_path) as img:
                max_width = 360
                ratio = min(1.0, max_width / img.width)
                size = (max(1, round(img.width * ratio)), max(1, round(img.height * ratio)))
                thumb = img.convert("RGB").resize(size, Image.LANCZOS)
            self._photo = ImageTk.PhotoImage(thumb)
            tk.Label(inner, image=self._photo, bg=PALETTE["panel"]).pack()
        except Exception as exc:  # noqa: BLE001 - プレビューに失敗しても処理は継続したい
            tk.Label(
                inner, text=f"(プレビューを表示できません: {exc})", bg=PALETTE["panel"], fg=PALETTE["muted"]
            ).pack(padx=20, pady=20)

        if caption:
            tk.Label(
                inner, text=caption, bg=PALETTE["panel"], fg=PALETTE["muted"], font=(FONT_FAMILY, FONT_SIZE)
            ).pack(anchor="w", padx=4, pady=(0, 2))

        tk.Label(
            inner, text="クリックで閉じます", bg=PALETTE["panel"], fg=PALETTE["muted"],
            font=(FONT_FAMILY, FONT_SIZE - 1),
        ).pack(anchor="e", padx=4, pady=(0, 2))

        self.update_idletasks()
        self._place_near(parent)

        self.bind("<Button-1>", lambda _e: self._safe_destroy())
        self.after(auto_close_ms, self._safe_destroy)

    def _place_near(self, parent: tk.Misc) -> None:
        # 親ウィンドウの内側(右下)に重ねるとキャプチャモードのような小さい
        # ウィンドウではボタンを覆ってしまうため、親ウィンドウの外側・直下に
        # 表示する（右端は揃える）。
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = parent.winfo_rootx() + parent.winfo_width() - width
        y = parent.winfo_rooty() + parent.winfo_height() + 8
        x = max(0, min(x, screen_w - width))
        y = max(0, min(y, screen_h - height))
        self.geometry(f"+{x}+{y}")

    def _safe_destroy(self) -> None:
        if self.winfo_exists():
            self.destroy()


class RegionSelectOverlay(tk.Toplevel):
    """画面全体を覆う半透明オーバーレイ上でドラッグし、キャプチャ範囲を指定させる.

    確定した範囲は仮想スクリーン座標の (left, top, right, bottom) として
    self.result に入る（キャンセル時は None）。
    """

    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        self.result: Optional[tuple[int, int, int, int]] = None
        self._start: Optional[tuple[int, int]] = None
        self._rect_id: Optional[int] = None
        self._size_text_id: Optional[int] = None

        self._vx = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
        self._vy = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
        vw = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        vh = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)

        self.overrideredirect(True)
        self.geometry(f"{vw}x{vh}+{self._vx}+{self._vy}")
        self.attributes("-alpha", 0.3)
        self.attributes("-topmost", True)

        self.canvas = tk.Canvas(self, bg="black", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_text(
            vw // 2, 60,
            text="ドラッグでキャプチャ範囲を指定してください（Escで取消）",
            fill="white", font=(FONT_FAMILY, 14, "bold"),
        )

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Escape>", lambda _e: self.destroy())

        self.update_idletasks()
        self.focus_force()
        self.grab_set()

    def _on_press(self, event: tk.Event) -> None:
        self._start = (event.x, event.y)
        self._rect_id = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="white", width=2
        )
        self._size_text_id = self.canvas.create_text(
            event.x, event.y - 12, text="", fill="white", font=(FONT_FAMILY, 10, "bold")
        )

    def _on_drag(self, event: tk.Event) -> None:
        if self._start is None or self._rect_id is None:
            return
        x0, y0 = self._start
        self.canvas.coords(self._rect_id, x0, y0, event.x, event.y)
        if self._size_text_id is not None:
            self.canvas.coords(self._size_text_id, (x0 + event.x) / 2, min(y0, event.y) - 12)
            self.canvas.itemconfigure(
                self._size_text_id, text=f"{abs(event.x - x0)} x {abs(event.y - y0)}"
            )

    def _on_release(self, event: tk.Event) -> None:
        if self._start is None:
            self.destroy()
            return
        x0, y0 = self._start
        left, right = sorted((x0, event.x))
        top, bottom = sorted((y0, event.y))
        # 誤クリック（ほぼドラッグなし）は範囲として扱わない
        if right - left >= 5 and bottom - top >= 5:
            self.result = (self._vx + left, self._vy + top, self._vx + right, self._vy + bottom)
        self.destroy()


class DiffPreviewDialog(tk.Toplevel):
    """ファイル書き出し前に、変更内容をunified diff形式で確認させるダイアログ."""

    def __init__(self, parent: tk.Misc, diff_lines: list[str], confirm_text: str = "この内容で生成"):
        super().__init__(parent)
        self.title("変更内容の確認")
        self.geometry("640x480")
        self.minsize(480, 320)
        self.configure(bg=PALETTE["bg"])
        self.transient(parent)
        self.confirmed = False

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        text_frame = ttk.Frame(frm)
        text_frame.pack(fill="both", expand=True)
        text = tk.Text(
            text_frame,
            wrap="none",
            bg=PALETTE["panel"],
            fg=PALETTE["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
            font=("Consolas", FONT_SIZE + 1),
        )
        text.tag_configure("add", foreground=PALETTE["mint_dark"], background="#EAF7EF")
        text.tag_configure("del", foreground=PALETTE["pink_dark"], background="#FBEDF0")
        text.tag_configure("hdr", foreground=PALETTE["accent_dark"])
        y_scroll = ttk.Scrollbar(text_frame, command=text.yview)
        text.configure(yscrollcommand=y_scroll.set)
        text.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

        for line in diff_lines:
            if line.startswith("+") and not line.startswith("+++"):
                tag = "add"
            elif line.startswith("-") and not line.startswith("---"):
                tag = "del"
            elif line.startswith("@@") or line.startswith("+++") or line.startswith("---"):
                tag = "hdr"
            else:
                tag = ""
            text.insert("end", line + "\n", tag)
        text.configure(state="disabled")

        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(10, 0))
        ttk.Button(btns, text="キャンセル", width=10, command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(btns, text=confirm_text, style="Primary.TButton", command=self._on_ok).pack(side="right")

        self.bind("<Escape>", lambda _e: self.destroy())
        self.grab_set()

    def _on_ok(self) -> None:
        self.confirmed = True
        self.destroy()


class WindowPickerDialog(tk.Toplevel):
    """現在開いているウィンドウから、キャプチャ対象を選択させるダイアログ.

    選択結果は hwnd で確定するため、以降タイトルが変化しても対象を継続して
    追跡できる（例: Tera Term は接続先表示でタイトルが変わる）。
    """

    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        self.title("対象ウィンドウの選択")
        self.geometry("440x340")
        self.configure(bg=PALETTE["bg"])
        self.transient(parent)

        self.selected: Optional[tuple[int, str]] = None
        self.selected_region: Optional[tuple[int, int, int, int]] = None  # 「範囲指定...」で確定した矩形
        self._windows: list[tuple[int, str]] = []

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(
            frm,
            text=(
                "キャプチャ対象を選んでください（「画面全体」は全モニターをまとめて、\n"
                "「モニターN」は1台分だけをキャプチャします。複数モニター使用時に表示\n"
                "されます）。ウィンドウを選んだ場合は、以後タイトルが変化しても同じ\n"
                "ウィンドウを継続して追跡します。"
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
        ttk.Button(btns, text="更新", width=6, command=self._refresh).pack(side="left")
        ttk.Button(btns, text="範囲指定...", command=self._on_pick_region).pack(side="left", padx=(6, 0))
        ttk.Button(btns, text="キャンセル", width=10, command=self._on_cancel).pack(side="right")
        ttk.Button(btns, text="選択", width=10, style="Primary.TButton", command=self._on_ok).pack(
            side="right", padx=(0, 6)
        )

        self.bind("<Return>", lambda _e: self._on_ok())
        self.bind("<Escape>", lambda _e: self._on_cancel())
        self._refresh()
        self.grab_set()

    def _refresh(self) -> None:
        self.listbox.delete(0, "end")
        monitors = list_monitors()
        monitor_entries = [
            (monitor_hwnd(i), f"モニター{i + 1}（{rect[2] - rect[0]}x{rect[3] - rect[1]}）")
            for i, rect in enumerate(monitors)
        ]
        if len(monitors) <= 1:
            monitor_entries = []  # モニター1台なら「画面全体」と同じなので個別選択肢は出さない
        self._windows = (
            [(FULL_SCREEN_HWND, "画面全体（すべてのモニター）")]
            + monitor_entries
            + list_capture_candidate_windows()
        )
        for _hwnd, title in self._windows:
            self.listbox.insert("end", title)
        if self._windows:
            self.listbox.select_set(0)
            self.listbox.see(0)

    def _on_pick_region(self) -> None:
        """画面上をドラッグしてキャプチャ範囲を指定させる（このダイアログは一旦隠す）."""
        self.withdraw()
        overlay = RegionSelectOverlay(self)
        self.wait_window(overlay)
        if overlay.result is None:
            self.deiconify()
            self.grab_set()  # withdraw中に外れたモーダル状態を回復する
            return
        left, top, right, bottom = overlay.result
        self.selected_region = overlay.result
        self.selected = (REGION_HWND, f"選択範囲（{right - left}x{bottom - top} @ {left},{top}）")
        self.destroy()

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
    """終了時に、report.html に掲載するスクリーンショットをサムネイルで確認しながら
    取捨選択させるダイアログ.

    キャプチャ内容を確認する手段がレポート生成（HTML化）後しかなかった課題に対応する
    ため、ここでサムネイルを表示し、ちゃんと撮れているものだけを選んでまとめられる
    ようにする。既定では全件選択（=掲載）した状態で開く。チェックを外しても
    screenshots\\ 内の元ファイルは削除されない（report.html への掲載対象から外れる
    だけ）。
    """

    THUMB_WIDTH = 220

    def __init__(self, parent: tk.Misc, shots: list[dict], session_dir: Path):
        super().__init__(parent)
        self.title("掲載するスクリーンショットの選択")
        self.geometry("760x620")
        self.minsize(520, 380)
        self.configure(bg=PALETTE["bg"])
        self.transient(parent)

        self.shots = shots
        self.session_dir = session_dir
        self.cancelled = True
        self.included_files: set = set()
        self._check_vars: list[tk.BooleanVar] = []
        self._thumb_images: list[ImageTk.PhotoImage] = []  # GC対策で参照を保持

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(
            frm,
            text=(
                "サムネイルを確認し、report.html に掲載するスクリーンショットを選んで\n"
                "ください（既定は全選択）。選択を外したものも screenshots フォルダには残ります。"
            ),
            justify="left",
        ).pack(fill="x", pady=(0, 6))

        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(0, 6))
        ttk.Button(btns, text="すべて選択", width=10, command=self._select_all).pack(side="left")
        ttk.Button(btns, text="すべて解除", width=10, command=self._deselect_all).pack(side="left", padx=6)
        ttk.Button(btns, text="autoを除外", width=10, command=self._deselect_auto).pack(side="left")

        list_frame = ttk.Frame(frm)
        list_frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(list_frame, bg=PALETTE["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        inner = ttk.Frame(canvas)
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind(
            "<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(inner_id, width=e.width))

        def _on_wheel(event: tk.Event) -> None:
            canvas.yview_scroll(int(-event.delta / 120), "units")

        canvas.bind_all("<MouseWheel>", _on_wheel)
        self.bind("<Destroy>", lambda e: self.unbind_all("<MouseWheel>") if e.widget is self else None)

        for shot in self.shots:
            self._build_row(inner, shot)

        btns2 = ttk.Frame(frm)
        btns2.pack(fill="x", pady=(8, 0))
        ttk.Button(btns2, text="キャンセル", width=10, command=self._on_cancel).pack(side="right", padx=(6, 0))
        ttk.Button(btns2, text="次へ", width=10, style="Primary.TButton", command=self._on_ok).pack(side="right")

        self.bind("<Escape>", lambda _e: self._on_cancel())
        self.grab_set()

    def _load_thumbnail(self, shot: dict) -> Optional[ImageTk.PhotoImage]:
        img_path = self.session_dir / shot["file"]
        if not img_path.exists():
            return None
        try:
            with Image.open(img_path) as img:
                ratio = self.THUMB_WIDTH / img.width
                size = (self.THUMB_WIDTH, max(1, round(img.height * ratio)))
                thumb = img.convert("RGB").resize(size, Image.LANCZOS)
        except Exception:  # noqa: BLE001 - サムネイル生成に失敗しても選択自体は続けたい
            return None
        photo = ImageTk.PhotoImage(thumb)
        self._thumb_images.append(photo)  # 参照保持しないとGCで画像が消える
        return photo

    def _build_row(self, parent: tk.Misc, shot: dict) -> None:
        row = ttk.Frame(parent, padding=6)
        row.pack(fill="x", pady=(0, 4))
        row.configure(style="ShotRow.TFrame")

        var = tk.BooleanVar(value=True)
        self._check_vars.append(var)
        ttk.Checkbutton(row, variable=var).pack(side="left", anchor="n", padx=(0, 8))

        photo = self._load_thumbnail(shot)
        thumb_frame = tk.Frame(
            row, width=self.THUMB_WIDTH, height=130, bg=PALETTE["panel"],
            highlightthickness=1, highlightbackground=PALETTE["border"],
        )
        thumb_frame.pack(side="left", padx=(0, 10))
        thumb_frame.pack_propagate(False)
        if photo is not None:
            tk.Label(thumb_frame, image=photo, bg=PALETTE["panel"]).place(relx=0.5, rely=0.5, anchor="center")
        else:
            tk.Label(
                thumb_frame, text="(画像なし)", bg=PALETTE["panel"], fg=PALETTE["muted"]
            ).place(relx=0.5, rely=0.5, anchor="center")

        note_part = f"\n備考: {shot['note']}" if shot.get("note") else ""
        info = ttk.Frame(row, style="ShotRow.TFrame")
        info.pack(side="left", fill="x", expand=True, anchor="n")
        ttk.Label(
            info,
            text=f"[{shot['tag']}] {shot['time']}",
            style="Status.TLabel" if shot["tag"] == "auto" else "Header.TLabel",
            background=PALETTE["panel"],
        ).pack(anchor="w")
        ttk.Label(info, text=shot["file"], foreground=PALETTE["muted"], background=PALETTE["panel"]).pack(
            anchor="w"
        )
        if note_part:
            ttk.Label(
                info, text=note_part.strip(), foreground=PALETTE["mint_dark"], background=PALETTE["panel"]
            ).pack(anchor="w")

    def _select_all(self) -> None:
        for var in self._check_vars:
            var.set(True)

    def _deselect_all(self) -> None:
        for var in self._check_vars:
            var.set(False)

    def _deselect_auto(self) -> None:
        for shot, var in zip(self.shots, self._check_vars):
            if shot["tag"] == "auto":
                var.set(False)

    def _on_ok(self) -> None:
        self.included_files = {
            shot["file"] for shot, var in zip(self.shots, self._check_vars) if var.get()
        }
        self.cancelled = False
        self.destroy()

    def _on_cancel(self) -> None:
        self.cancelled = True
        self.destroy()


class FinishDialog(tk.Toplevel):
    """終了時に結果(OK/NG等)と備考を入力させるモーダルダイアログ."""

    def __init__(self, parent: tk.Misc, initial_log_file: str = "", initial_zip: bool = False):
        super().__init__(parent)
        self.title("試験結果の入力")
        self.resizable(False, False)
        self.configure(bg=PALETTE["bg"])
        self.transient(parent)

        self.result_value: Optional[str] = None
        self.note_value: str = ""
        self.log_file_value: str = ""
        self.report_style_value: str = next(iter(REPORT_STYLES))
        self.report_content_value: str = REPORT_CONTENT_FULL
        self.zip_value: bool = initial_zip

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="結果").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.var_result = tk.StringVar(value="OK")
        ttk.Combobox(
            frm, textvariable=self.var_result, values=["OK", "NG", "未実施"], width=20
        ).grid(row=0, column=1, columnspan=2, sticky="w", pady=(0, 6))

        ttk.Label(frm, text="備考").grid(row=1, column=0, sticky="nw")
        self.note_text = tk.Text(
            frm,
            width=24,
            height=4,
            bg=PALETTE["panel"],
            fg=PALETTE["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
            font=(FONT_FAMILY, FONT_SIZE),
        )
        self.note_text.grid(row=1, column=1, columnspan=2, sticky="we")

        # 試験開始前はまだログファイルが存在しないことが多いため、ここ（終了時）で
        # 指定できるようにする。試験中に都度ブラウズする手間を避けるための配慮。
        ttk.Label(frm, text="実行ログファイル\n(任意)", justify="left").grid(row=2, column=0, sticky="nw", pady=(8, 0))
        self.var_log_file = tk.StringVar(value=initial_log_file)
        ttk.Entry(frm, textvariable=self.var_log_file, width=ENTRY_WIDTH_TEXT).grid(
            row=2, column=1, sticky="we", padx=(0, 6), pady=(8, 0)
        )
        ttk.Button(frm, text="参照...", width=6, command=self._browse_log_file).grid(row=2, column=2, pady=(8, 0))

        ttk.Label(frm, text="レポートのデザイン").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.var_report_style = tk.StringVar(value=next(iter(REPORT_STYLES)))
        ttk.Combobox(
            frm, textvariable=self.var_report_style, values=list(REPORT_STYLES.keys()),
            state="readonly", width=20,
        ).grid(row=3, column=1, columnspan=2, sticky="w", pady=(8, 0))

        ttk.Label(frm, text="レポート内容").grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.var_report_content = tk.StringVar(value=REPORT_CONTENT_FULL)
        ttk.Combobox(
            frm, textvariable=self.var_report_content, values=REPORT_CONTENTS,
            state="readonly", width=20,
        ).grid(row=4, column=1, columnspan=2, sticky="w", pady=(8, 0))

        self.var_zip = tk.BooleanVar(value=initial_zip)
        ttk.Checkbutton(
            frm, text="セッションフォルダをzip化する（提出用）", variable=self.var_zip
        ).grid(row=5, column=0, columnspan=3, sticky="w", pady=(8, 0))

        btns = ttk.Frame(frm)
        btns.grid(row=6, column=0, columnspan=3, pady=(10, 0), sticky="e")
        ttk.Button(btns, text="キャンセル", width=10, command=self._on_cancel).pack(side="right", padx=(6, 0))
        ttk.Button(btns, text="OK", width=10, style="Primary.TButton", command=self._on_ok).pack(side="right")

        self.bind("<Control-Return>", lambda _event: self._on_ok())
        self.bind("<Escape>", lambda _event: self._on_cancel())
        self.grab_set()
        self.note_text.focus_set()

    def _browse_log_file(self) -> None:
        path = filedialog.askopenfilename(title="実行ログファイルを選択", parent=self)
        if path:
            self.var_log_file.set(path)

    def _on_ok(self) -> None:
        self.result_value = self.var_result.get().strip()
        self.note_value = self.note_text.get("1.0", "end").strip()
        self.log_file_value = self.var_log_file.get().strip()
        self.report_style_value = self.var_report_style.get()
        self.report_content_value = self.var_report_content.get()
        self.zip_value = self.var_zip.get()
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
        super().__init__(parent, padding=6)
        self._log = log_callback
        self.items: dict[str, CheckItem] = {}
        self._next_id = 0
        self._build()

    def _build(self) -> None:
        file_row = ttk.Frame(self)
        file_row.pack(fill="x", pady=(0, 4))
        ttk.Label(file_row, text="① 対象ファイル").pack(side="left")
        self.var_file = tk.StringVar()
        ttk.Entry(file_row, textvariable=self.var_file, width=ENTRY_WIDTH_TEXT, state="readonly").pack(
            side="left", fill="x", expand=True, padx=6
        )
        ttk.Button(file_row, text="参照...", width=6, command=self._browse_file).pack(side="left")
        ttk.Label(file_row, text="エンコーディング").pack(side="left", padx=(8, 4))
        self.var_encoding = tk.StringVar(value="utf-8")
        ttk.Combobox(
            file_row, textvariable=self.var_encoding, values=ENCODINGS, width=COMBO_WIDTH_ENCODING, state="readonly"
        ).pack(side="left")

        add_frame = ttk.LabelFrame(self, text="② 確認項目のまとめ追加（1行1項目、複数貼り付け可）")
        add_frame.pack(fill="x", pady=(0, 4))

        bulk_row = ttk.Frame(add_frame)
        bulk_row.pack(fill="x", padx=6, pady=(4, 6))
        # ボタン列を先に右側へ確保してから残りをTextに渡す。逆順だとTextが
        # reqwidth分のスペースを占有し、ボタンが見切れるため。縦積みにして
        # 2つのボタンの幅を揃え、行全体の必要幅も抑える。
        button_col = ttk.Frame(bulk_row)
        button_col.pack(side="right", padx=(6, 0), anchor="n")
        ttk.Button(
            button_col, text="② 項目を追加", style="Primary.TButton", command=self._add_bulk_items
        ).pack(fill="x")
        btn_csv = ttk.Button(button_col, text="CSVから読み込み", command=self._load_csv)
        btn_csv.pack(fill="x", pady=(4, 0))
        self.bulk_text = tk.Text(
            bulk_row,
            width=20,
            height=3,
            bg=PALETTE["panel"],
            fg=PALETTE["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
            font=(FONT_FAMILY, FONT_SIZE),
        )
        self.bulk_text.pack(side="left", fill="both", expand=True)

        columns = ("kind", "content", "expected", "result", "matched")
        tree_frame = ttk.Frame(self)
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="extended", height=5
        )
        self.tree.heading("kind", text="種別")
        self.tree.heading("content", text="内容")
        self.tree.heading("expected", text="期待値")
        self.tree.heading("result", text="結果")
        self.tree.heading("matched", text="該当行")
        self.tree.column("kind", width=60, anchor="w")
        self.tree.column("content", width=90, anchor="w")
        self.tree.column("expected", width=70, anchor="w")
        self.tree.column("result", width=36, anchor="center")
        self.tree.column("matched", width=120, anchor="w")
        tree_scroll = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self._on_tree_double_click)

        select_frame = ttk.Frame(self)
        ttk.Button(
            select_frame, text="すべて選択", width=10,
            command=lambda: self.tree.selection_set(self.tree.get_children()),
        ).pack(side="left")
        ttk.Button(
            select_frame,
            text="選択解除", width=10,
            command=lambda: self.tree.selection_remove(self.tree.get_children()),
        ).pack(side="left", padx=4)
        ttk.Button(select_frame, text="選択項目を削除", command=self._delete_selected).pack(side="left")
        ttk.Button(select_frame, text="項目をCSVへ保存", command=self._export_items_csv).pack(side="right")
        # 「NGのみ」ではなく「OKを隠す」にすることで、未確認(-)の項目が
        # フィルタ中に追加されても見えなくならないようにする。
        self.var_hide_ok = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            select_frame, text="OKの項目を隠す", variable=self.var_hide_ok,
            command=self._apply_result_filter,
        ).pack(side="right", padx=(0, 8))

        # 出力設定と実行ボタンを1行に詰め込むと窮屈で必要幅も大きくなるため、
        # 「設定行」（出力先・デザイン）と「実行行」（③・④ボタン）の2段に分ける。
        option_row = ttk.Frame(self)
        ttk.Label(option_row, text="出力先フォルダ").pack(side="left")
        self.var_output = tk.StringVar(value="evidence")
        ttk.Entry(option_row, textvariable=self.var_output, width=ENTRY_WIDTH_TEXT).pack(
            side="left", fill="x", expand=True, padx=(6, 4)
        )
        ttk.Button(option_row, text="参照...", width=6, command=self._browse_output).pack(side="left")
        ttk.Label(option_row, text="デザイン").pack(side="left", padx=(10, 4))
        self.var_report_style = tk.StringVar(value=next(iter(CHECK_REPORT_STYLES)))
        ttk.Combobox(
            option_row, textvariable=self.var_report_style, values=list(CHECK_REPORT_STYLES.keys()),
            state="readonly", width=14,
        ).pack(side="left")

        action_frame = ttk.Frame(self)
        ttk.Button(
            action_frame, text="③ 確認を実行", style="Capture.TButton", command=self._run_checks
        ).pack(side="left")
        ttk.Button(
            action_frame, text="④ 結果をHTMLで保存", style="Finish.TButton", command=self._export_html
        ).pack(side="right")

        # 可変要素(Treeview)より先にボタン行を下端へ固定し、ウィンドウを縮小しても
        # 操作ボタンが画面外に出ないようにする（Treeview側だけが縮小される）。
        action_frame.pack(side="bottom", fill="x", pady=(4, 0))
        option_row.pack(side="bottom", fill="x", pady=(4, 0))
        select_frame.pack(side="bottom", fill="x", pady=(2, 4))
        tree_frame.pack(fill="both", expand=True, pady=(0, 4))

    def _browse_file(self) -> None:
        path = filedialog.askopenfilename(title="確認対象ファイルを選択")
        if not path:
            return
        if path != self.var_file.get():
            # 前のファイルに対するOK/NGが新しいファイルの結果に見えてしまわないよう、
            # 対象を切り替えたら結果列をリセットする。
            for item_id, item in self.items.items():
                item.result = "-"
                item.matched_line = ""
                self.tree.item(item_id, values=self._row_values(item))
            self._apply_result_filter()  # 結果リセットで全項目が「OK以外」になるため表示し直す
        self.var_file.set(path)
        self.var_encoding.set(detect_encoding(path))

    def _browse_output(self) -> None:
        path = filedialog.askdirectory(title="出力先フォルダを選択")
        if path:
            self.var_output.set(path)

    def _register_item(self, item: "CheckItem") -> None:
        item_id = str(self._next_id)
        self._next_id += 1
        self.items[item_id] = item
        self.tree.insert("", "end", iid=item_id, values=self._row_values(item))

    @staticmethod
    def _row_values(item: "CheckItem") -> tuple[str, str, str, str, str]:
        return (
            SourceCheckFrame._kind_label(item.kind),
            item.content,
            item.expected,
            item.result,
            item.matched_line,
        )

    def _on_tree_double_click(self, event: tk.Event) -> None:
        """一覧の「内容」「期待値」セルをダブルクリックでその場編集できるようにする."""
        if self.tree.identify("region", event.x, event.y) != "cell":
            return
        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        item = self.items.get(row_id)
        if item is None:
            return

        columns = self.tree["columns"]
        try:
            col_name = columns[int(col_id.replace("#", "")) - 1]
        except (ValueError, IndexError):
            return
        if col_name not in ("content", "expected"):
            return  # 種別・結果・該当行は確認実行で決まるため編集対象外

        bbox = self.tree.bbox(row_id, col_id)
        if not bbox:
            return
        x, y, width, height = bbox

        current_value = item.content if col_name == "content" else item.expected
        edit_var = tk.StringVar(value=current_value)
        entry = tk.Entry(
            self.tree,
            textvariable=edit_var,
            font=(FONT_FAMILY, FONT_SIZE),
            bg=PALETTE["panel"],
            fg=PALETTE["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=PALETTE["accent_dark"],
            insertbackground=PALETTE["text"],
        )
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus_set()
        entry.select_range(0, "end")

        def commit(_event: object = None) -> None:
            if not entry.winfo_exists():
                return
            new_value = edit_var.get().strip()
            entry.destroy()
            if col_name == "content" and not new_value:
                return  # 内容は空にできないため、編集を取り消す
            old_content, old_expected = item.content, item.expected
            if col_name == "content":
                item.content = new_value
            else:
                item.expected = new_value
            # まとめ追加・CSV読み込みと同様に、編集後も正規表現として成立することを
            # 検証する。不正なまま確定すると「③ 確認を実行」が例外で失敗するため。
            try:
                re.compile(item.pattern)
            except re.error as exc:
                item.content, item.expected = old_content, old_expected
                messagebox.showwarning("正規表現エラー", f"編集後の内容が正しい正規表現になりません:\n{exc}")
                return
            # 内容/期待値を変えたら、以前の確認結果は意味を持たないためリセットする。
            item.result = "-"
            item.matched_line = ""
            self.tree.item(row_id, values=self._row_values(item))

        def cancel(_event: object = None) -> None:
            if entry.winfo_exists():
                entry.destroy()

        entry.bind("<Return>", commit)
        entry.bind("<FocusOut>", commit)
        entry.bind("<Escape>", cancel)

    def _add_items_from_lines(self, lines: list[str]) -> tuple[int, list[str]]:
        """「まとめ追加」と同じ1行1項目形式の行リストを机上確認項目として登録する."""
        added = 0
        errors: list[str] = []
        for line_no, line in enumerate(lines, start=1):
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
            self._register_item(item)
            added += 1
        return added, errors

    def _add_bulk_items(self) -> None:
        raw_text = self.bulk_text.get("1.0", "end")
        added, errors = self._add_items_from_lines(raw_text.splitlines())
        self.bulk_text.delete("1.0", "end")
        self._log(f"机上確認項目を{added}件追加しました" + (f"（エラー{len(errors)}件）" if errors else ""))
        if errors:
            messagebox.showwarning("一部の行を追加できませんでした", "\n".join(errors))

    def _load_text_file(self, path: str) -> None:
        """.txt ファイルを「まとめ追加」と同じ1行1項目形式として読み込む（CSVの列分割は行わない）."""
        try:
            text = Path(path).read_text(encoding=detect_encoding(path))
        except OSError as exc:
            messagebox.showerror("読み込みエラー", f"ファイルを読み込めません: {exc}")
            return
        added, errors = self._add_items_from_lines(text.splitlines())
        self._log(
            f"テキストファイルから机上確認項目を{added}件読み込みました" + (f"（エラー{len(errors)}件）" if errors else "")
        )
        if errors:
            messagebox.showwarning("一部の行を読み込めませんでした", "\n".join(errors))

    def _load_csv(self) -> None:
        path = filedialog.askopenfilename(
            title="確認項目CSV/テキストを選択", filetypes=[("CSV/テキスト", "*.csv *.txt"), ("すべてのファイル", "*.*")]
        )
        if not path:
            return
        if Path(path).suffix.lower() == ".txt":
            self._load_text_file(path)
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
                kind_key = "branch"
            elif kind_raw in ("カスタム", "regex", "custom", "正規表現", "カスタム正規表現"):
                kind_key = "custom"
            else:
                kind_key = "variable"

            item = CheckItem(kind=kind_key, content=content, expected=expected, custom_label=label)
            try:
                re.compile(item.pattern)
            except re.error as exc:
                errors.append(f"{line_no}行目: 正規表現エラー: {exc}")
                continue

            self._register_item(item)
            added += 1

        self._log(f"CSVから机上確認項目を{added}件読み込みました" + (f"（エラー{len(errors)}件）" if errors else ""))
        if errors:
            messagebox.showwarning("一部の行を読み込めませんでした", "\n".join(errors))

    def _delete_selected(self) -> None:
        for item_id in self.tree.selection():
            self.tree.delete(item_id)
            self.items.pop(item_id, None)

    def _apply_result_filter(self) -> None:
        """「OKの項目を隠す」の状態に合わせて、一覧の表示/非表示を切り替える.

        Treeviewのdetach/reattachで隠すだけなので、項目自体（self.items）は
        保持され、確認実行・HTML保存は非表示の項目も含めて動作する。
        """
        hide_ok = self.var_hide_ok.get()
        index = 0
        for item_id, item in self.items.items():
            if hide_ok and item.result == "OK":
                self.tree.detach(item_id)
            else:
                self.tree.reattach(item_id, "", index)
                index += 1

    def _export_items_csv(self) -> None:
        """確認項目の一覧を「CSVから読み込み」でそのまま再読込できる列構成で書き出す."""
        if not self.items:
            messagebox.showinfo("確認項目なし", "保存する確認項目がありません")
            return
        path = filedialog.asksaveasfilename(
            title="確認項目の保存先",
            defaultextension=".csv",
            initialfile="check_items.csv",
            filetypes=[("CSV", "*.csv"), ("すべてのファイル", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["種別", "内容", "期待値", "名称"])
                for item in self.items.values():
                    writer.writerow([self._kind_label(item.kind), item.content, item.expected, item.custom_label])
        except OSError as exc:
            messagebox.showerror("書き込みエラー", f"CSVを保存できません: {exc}")
            return
        self._log(f"確認項目{len(self.items)}件をCSVへ保存しました: {path}")

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
            try:
                matches = find_pattern_lines(lines, item.pattern)
            except re.error as exc:
                # 通常は追加・編集時に検証済みだが、万一不正な正規表現が紛れ込んでも
                # 確認全体が中断しないよう、その項目だけ未確認扱いにして続行する。
                item.result = "-"
                item.matched_line = f"(正規表現エラー: {exc})"
                self.tree.item(item_id, values=self._row_values(item))
                continue
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
            self.tree.item(item_id, values=self._row_values(item))

        self._apply_result_filter()
        self._log(f"机上確認: {len(self.items)}件中 {ok_count}件OK ({Path(path_str).name})")

    @staticmethod
    def _kind_label(kind_key: str) -> str:
        return {"variable": "変数定義", "branch": "分岐(if)", "custom": "カスタム正規表現"}.get(
            kind_key, kind_key
        )

    def _build_report_html(self) -> str:
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
        style_css = CHECK_REPORT_STYLES.get(self.var_report_style.get(), _CHECK_REPORT_STYLE_PASTEL)
        return _CHECK_REPORT_TEMPLATE.format(
            file_name=html.escape(Path(self.var_file.get()).name),
            file_path=html.escape(self.var_file.get()),
            checked_at=datetime.now().isoformat(timespec="seconds"),
            ok_count=ok_count,
            total_count=len(self.items),
            rows_html=rows_html,
            style_css=style_css,
        )

    def _report_output_path(self, suffix: str) -> Path:
        out_dir = Path(self.var_output.get().strip() or "evidence")
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir / f"sourcecheck_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"

    def _export_html(self) -> None:
        if not self.items:
            messagebox.showinfo("確認項目なし", "確認項目がありません")
            return
        try:
            report_path = self._report_output_path(".html")
            report_path.write_text(self._build_report_html(), encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("書き込みエラー", f"確認結果を保存できません: {exc}")
            return
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
        super().__init__(parent, padding=6)
        self._log = log_callback
        self.occurrences: dict[str, Occurrence] = {}
        self._lines: list[str] = []
        self._next_id = 0
        self._build()

    def _build(self) -> None:
        file_row = ttk.Frame(self)
        file_row.pack(fill="x", pady=(0, 4))
        ttk.Label(file_row, text="① 対象ファイル").pack(side="left")
        self.var_file = tk.StringVar()
        ttk.Entry(file_row, textvariable=self.var_file, width=ENTRY_WIDTH_TEXT, state="readonly").pack(
            side="left", fill="x", expand=True, padx=6
        )
        ttk.Button(file_row, text="参照...", width=6, command=self._browse_file).pack(side="left")
        ttk.Label(file_row, text="エンコーディング").pack(side="left", padx=(8, 4))
        self.var_encoding = tk.StringVar(value="utf-8")
        ttk.Combobox(
            file_row, textvariable=self.var_encoding, values=ENCODINGS, width=COMBO_WIDTH_ENCODING, state="readonly"
        ).pack(side="left")

        # 机上確認タブの「まとめ追加」とレイアウトを揃える（LabelFrame＋右側に縦積みボタン）。
        # 複数行のラベルを入力欄の左に置くと、他の行と入力欄の左端が揃わず崩れて見えるため。
        search_frame = ttk.LabelFrame(self, text="② 変数名（改行・カンマ区切りで複数指定可）")
        search_frame.pack(fill="x", pady=(0, 4))
        names_row = ttk.Frame(search_frame)
        names_row.pack(fill="x", padx=6, pady=(4, 6))
        btn_col = ttk.Frame(names_row)
        btn_col.pack(side="right", padx=(6, 0), anchor="n")
        ttk.Button(
            btn_col, text="候補を検索", style="Capture.TButton", command=self._search
        ).pack(fill="x")
        btn_csv = ttk.Button(btn_col, text="CSVから読込", command=self._load_csv)
        btn_csv.pack(fill="x", pady=(4, 0))
        self.names_text = tk.Text(
            names_row,
            height=3,
            width=ENTRY_WIDTH_TEXT,
            bg=PALETTE["panel"],
            fg=PALETTE["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
            font=(FONT_FAMILY, FONT_SIZE),
        )
        self.names_text.pack(side="left", fill="both", expand=True)

        columns = ("var", "line", "content")
        tree_frame = ttk.Frame(self)
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="extended", height=5
        )
        self.tree.heading("var", text="変数")
        self.tree.heading("line", text="行番号")
        self.tree.heading("content", text="内容")
        self.tree.column("var", width=60, anchor="w")
        self.tree.column("line", width=40, anchor="center")
        self.tree.column("content", width=160, anchor="w")
        tree_scroll = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        select_frame = ttk.Frame(self)
        ttk.Label(select_frame, text="③ 挿入したい行を選択:").pack(side="left")
        ttk.Button(
            select_frame,
            text="すべて選択", width=10,
            command=lambda: self.tree.selection_set(self.tree.get_children()),
        ).pack(side="left", padx=(4, 0))
        ttk.Button(
            select_frame,
            text="選択解除", width=10,
            command=lambda: self.tree.selection_remove(self.tree.get_children()),
        ).pack(side="left", padx=4)

        template_row = ttk.Frame(self)
        ttk.Label(template_row, text="言語/書式:").pack(side="left")
        self.var_preset = tk.StringVar(value=next(iter(OUTPUT_TEMPLATES)))
        preset_combo = ttk.Combobox(
            template_row,
            textvariable=self.var_preset,
            values=list(OUTPUT_TEMPLATES.keys()),
            state="readonly",
            width=16,
        )
        preset_combo.pack(side="left", padx=(4, 0))
        preset_combo.bind("<<ComboboxSelected>>", lambda _e: self._apply_preset())

        self.template_text = tk.Text(
            self,
            width=20,
            height=2,
            bg=PALETTE["panel"],
            fg=PALETTE["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
            font=(FONT_FAMILY, FONT_SIZE),
        )
        self.template_text.bind("<KeyRelease>", lambda _e: self._update_preview())

        self.preview_var = tk.StringVar()
        preview_label = ttk.Label(
            self,
            textvariable=self.preview_var,
            foreground=PALETTE["mint_dark"],
            wraplength=620,
            justify="left",
        )

        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._update_preview())
        self._apply_preset()

        action_frame = ttk.Frame(self)
        ttk.Label(action_frame, text="保存先サフィックス").pack(side="left")
        self.var_suffix = tk.StringVar(value="_instrumented")
        suffix_entry = ttk.Entry(action_frame, textvariable=self.var_suffix, width=ENTRY_WIDTH_TEXT)
        suffix_entry.pack(side="left", padx=(4, 0))
        ttk.Button(
            action_frame,
            text="選択箇所に挿入してファイル生成",
            style="Primary.TButton",
            command=self._apply_instrumentation,
        ).pack(side="right")
        # 挿入の逆操作。試験後の後始末として、マーカー([evtool])入りの挿入行を
        # 取り除いたファイルを生成する。
        ttk.Button(
            action_frame, text="挿入コードを撤去", command=self._strip_instrumentation
        ).pack(side="right", padx=(0, 6))

        # 可変要素(Treeview)より下に来る要素群は下端に固定し、ウィンドウを縮小しても
        # テンプレート選択・実行ボタンが画面外に出ないようにする（Treeview側だけが縮小される）。
        action_frame.pack(side="bottom", fill="x", pady=(4, 0))
        preview_label.pack(side="bottom", fill="x", pady=(0, 4), anchor="w")
        self.template_text.pack(side="bottom", fill="x", pady=(2, 1))
        template_row.pack(side="bottom", fill="x", pady=(2, 2))
        select_frame.pack(side="bottom", fill="x", pady=(2, 4))
        tree_frame.pack(fill="both", expand=True, pady=(0, 4))

    def _browse_file(self) -> None:
        path = filedialog.askopenfilename(title="対象ファイルを選択")
        if not path:
            return
        if path != self.var_file.get():
            # 候補一覧は検索時に読み込んだ内容(self._lines)と対になっている。前の
            # ファイルの候補を残したまま挿入を実行すると、古いファイルの内容が
            # 新しいファイル名で書き出されてしまうため、対象を切り替えたら破棄する。
            self.tree.delete(*self.tree.get_children())
            self.occurrences.clear()
            self._lines = []
            self._update_preview()
        self.var_file.set(path)
        self.var_encoding.set(detect_encoding(path))

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
            title="変数名CSV/テキストを選択", filetypes=[("CSV/テキスト", "*.csv *.txt"), ("すべてのファイル", "*.*")]
        )
        if not path:
            return

        if Path(path).suffix.lower() == ".txt":
            try:
                text = Path(path).read_text(encoding=detect_encoding(path))
            except OSError as exc:
                messagebox.showerror("読み込みエラー", f"ファイルを読み込めません: {exc}")
                return
            # .txt は机上確認の「まとめ追加」と同じ書式（変数名 / 変数名 = 期待値）を想定し、
            # = より前の変数名部分だけを取り出す（CSVの列分割は行わない）。
            names = extract_variable_names_from_text(text.splitlines())
        else:
            try:
                header, data_rows = read_csv_table(path)
            except (OSError, UnicodeDecodeError) as exc:
                messagebox.showerror("読み込みエラー", f"CSVを読み込めません: {exc}")
                return
            names = [row[0].strip() for row in ([header] + data_rows) if row and row[0].strip()]

        if not names:
            messagebox.showinfo("読み込み結果", "ファイルから変数名が見つかりませんでした")
            return

        current = self.names_text.get("1.0", "end").strip()
        combined = (current + "\n" if current else "") + "\n".join(names)
        self.names_text.delete("1.0", "end")
        self.names_text.insert("1.0", combined)
        self._log(f"ファイルから変数名を{len(names)}件読み込みました")

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
        if not self._confirm_diff(self._lines, output_lines):
            return

        source_path = Path(self.var_file.get())
        suffix = self.var_suffix.get().strip() or "_instrumented"
        output_path = source_path.with_name(f"{source_path.stem}{suffix}{source_path.suffix}")
        try:
            output_path.write_text("\n".join(output_lines) + "\n", encoding=self.var_encoding.get())
        except UnicodeEncodeError as exc:
            # 例: cp932 のファイルに cp932 で表せない文字を含むテンプレートを挿入した場合
            messagebox.showerror(
                "書き込みエラー",
                f"挿入したコードに、エンコーディング {self.var_encoding.get()} で保存できない文字が含まれています: {exc}",
            )
            return
        except OSError as exc:
            messagebox.showerror("書き込みエラー", f"ファイルを書き込めません: {exc}")
            return

        self._log(f"動作確認コードを{len(selected)}箇所に挿入しました: {output_path}")
        if messagebox.askyesno("完了", f"{output_path.name} を生成しました。開きますか？"):
            os.startfile(output_path)  # noqa: S606 - ユーザー自身が生成したローカルファイルを開く

    def _confirm_diff(self, old_lines: list[str], new_lines: list[str]) -> bool:
        """書き出し前に変更内容をdiffで確認させる。確定したらTrueを返す."""
        diff = list(
            difflib.unified_diff(old_lines, new_lines, fromfile="変更前", tofile="変更後", lineterm="")
        )
        dialog = DiffPreviewDialog(self, diff)
        self.wait_window(dialog)
        return dialog.confirmed

    def _strip_instrumentation(self) -> None:
        """挿入済みの動作確認コード行を取り除いたファイルを生成する（挿入の逆操作）."""
        path_str = self.var_file.get().strip()
        if not path_str:
            messagebox.showerror("入力エラー", "対象ファイルを選択してください")
            return
        try:
            text = Path(path_str).read_text(encoding=self.var_encoding.get())
        except (OSError, UnicodeDecodeError) as exc:
            messagebox.showerror("読み込みエラー", f"ファイルを読み込めません: {exc}")
            return

        lines = text.splitlines()
        stripped_lines, removed = strip_instrumentation(lines)
        if removed == 0:
            messagebox.showinfo(
                "撤去対象なし",
                "挿入コードの行（" + " / ".join(INSTRUMENT_MARKERS) + " を含む行）は見つかりませんでした",
            )
            return
        if not self._confirm_diff(lines, stripped_lines):
            return

        source_path = Path(path_str)
        output_path = source_path.with_name(f"{source_path.stem}_stripped{source_path.suffix}")
        try:
            output_path.write_text("\n".join(stripped_lines) + "\n", encoding=self.var_encoding.get())
        except (OSError, UnicodeEncodeError) as exc:
            messagebox.showerror("書き込みエラー", f"ファイルを書き込めません: {exc}")
            return

        self._log(f"挿入コードを{removed}行撤去しました: {output_path}")
        if messagebox.askyesno("完了", f"{output_path.name} を生成しました。開きますか？"):
            os.startfile(output_path)  # noqa: S606 - ユーザー自身が生成したローカルファイルを開く


class SegmentedControl(tk.Frame):
    """画面切替用の、ピル型インジケーターが角丸で移動するセグメントコントロール.

    ttk::notebook のタブはテーマやTkバージョンによってアクティブなペインの
    実体化・サイズ計算の振る舞いが揺れ、切替時にボタンの位置や高さがガタつく
    一因になっていた。見た目もタブらしくなりモダンな印象に欠けるため、ここでは
    Canvas + PIL で角丸の背景を自前描画する独立した置き換え用ウィジェットにする
    （サイズ計算はEvToolApp側でgrid+tkraiseのページ切替により別途固定する）。
    """

    HEIGHT = 32
    PAD_X = 10
    OUTER_PAD = 2

    def __init__(self, parent: tk.Misc, items: list[tuple[str, str]], command: Callable[[str], None]):
        super().__init__(parent, bg=PALETTE["bg"])
        self._items = items
        self._command = command
        self._selected = items[0][0]
        self._hovered: Optional[str] = None
        self._segment_bounds: dict[str, tuple[int, int]] = {}
        self._bg_photo: Optional[ImageTk.PhotoImage] = None

        self._font_regular = tkfont.Font(family=FONT_FAMILY, size=FONT_SIZE)
        self._font_bold = tkfont.Font(family=FONT_FAMILY, size=FONT_SIZE, weight="bold")

        # 選択時(太字)・非選択時で文字幅が変わってもスロット幅が変動しないよう、
        # 両方のフォントで測った幅の大きい方を採用する。
        self._widths = [
            max(self._font_regular.measure(label), self._font_bold.measure(label)) + self.PAD_X * 2
            for _key, label in items
        ]
        total_width = sum(self._widths) + self.OUTER_PAD * 2

        self.canvas = tk.Canvas(
            self, width=total_width, height=self.HEIGHT, highlightthickness=0, bg=PALETTE["bg"], cursor="hand2"
        )
        self.canvas.pack()

        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)

        self._redraw()

    def select(self, key: str) -> None:
        if key != self._selected:
            self._selected = key
            self._redraw()

    def _segment_at(self, x: int) -> Optional[str]:
        for key, (x0, x1) in self._segment_bounds.items():
            if x0 <= x < x1:
                return key
        return None

    def _on_click(self, event: tk.Event) -> None:
        key = self._segment_at(event.x)
        if key is not None and key != self._selected:
            self._selected = key
            self._redraw()
            self._command(key)

    def _on_motion(self, event: tk.Event) -> None:
        key = self._segment_at(event.x)
        if key != self._hovered:
            self._hovered = key
            self._redraw()

    def _on_leave(self, _event: tk.Event) -> None:
        if self._hovered is not None:
            self._hovered = None
            self._redraw()

    def _redraw(self) -> None:
        width = int(self.canvas["width"])
        height = int(self.canvas["height"])

        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle(
            (0, 0, width - 1, height - 1),
            radius=height // 2,
            fill=(*ImageColor.getrgb(PALETTE["panel"]), 255),
            outline=(*ImageColor.getrgb(PALETTE["border"]), 255),
            width=1,
        )

        self._segment_bounds = {}
        x = self.OUTER_PAD
        for (key, _label), seg_width in zip(self._items, self._widths):
            self._segment_bounds[key] = (x, x + seg_width)
            if key == self._selected:
                inset = 3
                draw.rounded_rectangle(
                    (x + inset, inset, x + seg_width - inset, height - inset),
                    radius=(height - inset * 2) // 2,
                    fill=(*ImageColor.getrgb(PALETTE["accent_dark"]), 255),
                )
            x += seg_width

        self._bg_photo = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self._bg_photo, anchor="nw")

        x = self.OUTER_PAD
        for (key, label), seg_width in zip(self._items, self._widths):
            is_selected = key == self._selected
            if is_selected:
                color, font = "#FFFFFF", self._font_bold
            elif key == self._hovered:
                color, font = PALETTE["accent_dark"], self._font_regular
            else:
                color, font = PALETTE["text"], self._font_regular
            self.canvas.create_text(x + seg_width / 2, height / 2, text=label, fill=color, font=font)
            x += seg_width


class EvToolApp:
    """evtool のメインウィンドウ."""

    _SETTINGS_PATH = Path(__file__).with_name("evtool_settings.json")

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("evtool")
        _apply_theme(self.root)

        self._icon_images = _set_app_icon(self.root)

        self.session: Optional[EvidenceSession] = None
        self.target_hwnd: Optional[int] = None
        self.target_region: Optional[tuple[int, int, int, int]] = None  # 範囲指定キャプチャ用
        self.target_window_label: str = ""
        self._log_queue: "queue.Queue[str]" = queue.Queue()
        self._entries: list[tk.Widget] = []
        self._test_id_history: list[str] = []
        self._title_history: list[str] = []
        self._normal_geometry: str = ""
        self._zip_after_finish: bool = False
        # Ctrl+F5 グローバルホットキー。押下はリスナースレッドからこのEventに通知され、
        # GUIスレッド側の _poll_log_queue が拾って実際のキャプチャを行う
        # （tkinterはGUIスレッド以外から操作できないため）。
        self._hotkey_listener: Optional[GlobalHotkeyListener] = None
        self._hotkey_capture_requested = threading.Event()

        self._build_widgets()
        self._load_settings()
        self.root.bind("<F5>", lambda _e: self._on_capture() if self.session else None)
        self.root.bind("<F10>", lambda _e: self._on_finish() if self.session else None)
        self._set_default_target_window()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(150, self._poll_log_queue)

        # ウィンドウサイズは固定値(560x460等)で固定しない。固定値だとモニターのDPIに
        # よって実際に必要な幅・高さと食い違い、下端や右端のボタンが画面外に隠れて
        # 押せなくなることがある（マルチモニタ環境ではモニター毎にDPIが異なるため、
        # 起動時に一度だけ計算した固定値はその後別のDPIで開いた場合に食い違う）。
        # 実際に組んだウィジェット一式が必要とする最小限のサイズ（＝最もコンパクトな
        # サイズ）を都度計算して使う。タブ切替で毎回サイズが変わると操作感が落ち着か
        # ないため、ウィンドウサイズはタブに関わらず一定にする。
        self.root.update_idletasks()
        self._default_minsize = (self.root.winfo_reqwidth(), self.root.winfo_reqheight())
        self.root.geometry(f"{self._default_minsize[0]}x{self._default_minsize[1]}")
        self.root.minsize(*self._default_minsize)

    # ---- widgets ---------------------------------------------------------
    def _build_widgets(self) -> None:
        self.nav = SegmentedControl(
            self.root,
            items=[
                ("capture", "エビデンス取得"),
                ("check", "机上確認"),
                ("instrument", "動作確認コード挿入"),
            ],
            command=self._on_nav_select,
        )
        self.nav.pack(anchor="w", padx=6, pady=(6, 4))

        # 各ページを同じセルにgridで重ね、tkraiseで切り替える。grid はそのセルに
        # 配置された全ウィジェット（非表示中のものも含む）の最大サイズをセルの
        # サイズとして採用するため、ページ切替時にコンテナのサイズが変動しない
        # （ttk::notebookのタブ切替で生じていたボタン位置のガタつきの根本対策）。
        self.page_container = ttk.Frame(self.root)
        self.page_container.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.page_container.columnconfigure(0, weight=1)
        self.page_container.rowconfigure(0, weight=1)

        self._pages: dict[str, tk.Widget] = {}

        capture_tab = ttk.Frame(self.page_container)
        self._build_capture_tab(capture_tab)
        self._pages["capture"] = capture_tab

        check_tab = SourceCheckFrame(self.page_container, log_callback=self._log)
        self._pages["check"] = check_tab

        instrument_tab = InstrumentFrame(self.page_container, log_callback=self._log)
        self._pages["instrument"] = instrument_tab

        for page in self._pages.values():
            page.grid(row=0, column=0, sticky="nsew")
        self._pages["capture"].tkraise()

        self.capture_mode_frame = self._build_capture_mode_frame(self.root)

    def _on_nav_select(self, key: str) -> None:
        self._pages[key].tkraise()

    def _build_capture_mode_frame(self, parent: tk.Widget) -> ttk.Frame:
        """キャプチャ中だけ表示するコンパクトなUI（今すぐキャプチャ・停止のみ）を作る.

        通常のフォーム・ログ欄を隠してウィンドウを小さくすることで、対象アプリの
        操作画面を占有しすぎず、手元に置いたまま手動キャプチャ・終了操作だけを
        行えるようにする。
        """
        frame = ttk.Frame(parent, padding=10)

        header_row = ttk.Frame(frame)
        header_row.pack(fill="x")
        self.capture_mode_info_var = tk.StringVar()
        ttk.Label(
            header_row,
            textvariable=self.capture_mode_info_var,
            style="Header.TLabel",
            wraplength=230,
            justify="left",
        ).pack(side="left", anchor="n")
        ttk.Label(
            header_row, text="● 取得中", style="Status.TLabel", foreground=PALETTE["accent_dark"]
        ).pack(side="right", anchor="n")

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill="x", pady=(8, 2))
        ttk.Button(
            btn_row, text="今すぐキャプチャ", style="Capture.TButton", command=self._on_capture
        ).pack(side="left")
        ttk.Button(
            btn_row, text="終了してまとめる", style="Finish.TButton", command=self._on_finish
        ).pack(side="left", padx=(8, 0))

        self.hotkey_hint_var = tk.StringVar()
        ttk.Label(frame, textvariable=self.hotkey_hint_var, style="Status.TLabel").pack(
            anchor="w", pady=(0, 6)
        )

        note_row = ttk.Frame(frame)
        note_row.pack(fill="x")
        ttk.Label(note_row, text="備考:").pack(side="left")
        ttk.Entry(note_row, textvariable=self.var_shot_note).pack(
            side="left", fill="x", expand=True, padx=(4, 0)
        )

        util_row = ttk.Frame(frame)
        util_row.pack(fill="x", pady=(6, 0))
        ttk.Button(util_row, text="最新をコピー", command=self._on_copy_last_shot).pack(side="left")
        # 自動キャプチャが有効なセッションのときだけ _enter_capture_mode() で表示する
        self.btn_pause = ttk.Button(util_row, text="自動キャプチャを一時停止", command=self._on_toggle_pause)

        ttk.Label(
            frame,
            textvariable=self.capture_warning_var,
            style="Warning.TLabel",
            wraplength=300,
            justify="left",
        ).pack(anchor="w", pady=(6, 0))

        # 「開始」の誤操作を取り消せるように、主要なボタンとは離して控えめに置く。
        cancel_row = ttk.Frame(frame)
        cancel_row.pack(fill="x", pady=(8, 0))
        ttk.Button(cancel_row, text="開始を取りやめる", command=self._on_cancel_session).pack(side="right")

        return frame

    def _enter_capture_mode(self) -> None:
        self._normal_geometry = self.root.geometry()
        self.nav.pack_forget()
        self.page_container.pack_forget()
        self.capture_mode_info_var.set(
            f"{self.var_test_id.get()} - {self.var_title.get()}\n対象: {self.target_window_label}"
        )
        if self.session is not None and self.session.auto_capture:
            self.btn_pause.configure(text="自動キャプチャを一時停止")
            self.btn_pause.pack(side="left", padx=(6, 0))
        else:
            self.btn_pause.pack_forget()
        self.capture_mode_frame.pack(fill="both", expand=True)
        # 固定値だとモニターのDPIによってボタンがあふれるため、明示的なサイズ
        # 指定を解除してから、コンパクトモードの内容に必要な最小サイズを計算
        # して使う（通常表示時と同じ考え方）。
        self.root.geometry("")
        self.root.update_idletasks()
        width, height = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(width, height)
        self.root.attributes("-topmost", True)

    def _exit_capture_mode(self) -> None:
        self.capture_mode_frame.pack_forget()
        self.root.attributes("-topmost", False)
        self.nav.pack(anchor="w", padx=6, pady=(6, 4))
        self.page_container.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.root.minsize(*self._default_minsize)
        if self._normal_geometry:
            self.root.geometry(self._normal_geometry)

    def _build_capture_tab(self, parent: tk.Widget) -> None:
        form = ttk.Frame(parent, padding=6)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        self.var_test_id = tk.StringVar()
        self.var_title = tk.StringVar()
        self.var_window_display = tk.StringVar(value="(未選択)")
        self.var_auto_capture = tk.BooleanVar(value=False)
        self.var_interval = tk.StringVar(value="10")
        self.var_output = tk.StringVar(value="evidence")
        self.var_shot_note = tk.StringVar()

        def add_row(row: int, label: str, var: tk.StringVar, browse=None, width=ENTRY_WIDTH_TEXT):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=3)
            entry = ttk.Entry(form, textvariable=var, width=width)
            entry.grid(row=row, column=1, sticky="we", padx=(6, 6), pady=3)
            self._entries.append(entry)
            if browse is not None:
                # 右列(列2)の幅は「選択...」「確認」の2ボタン行で決まるため、1ボタンだけの
                # 行は列いっぱいに伸ばして左右の端を揃える。
                ttk.Button(form, text="参照...", width=6, command=browse).grid(
                    row=row, column=2, sticky="we", pady=3
                )
            return entry

        ttk.Label(form, text="試験ID *").grid(row=0, column=0, sticky="w", pady=3)
        self.combo_test_id = ttk.Combobox(form, textvariable=self.var_test_id, width=ENTRY_WIDTH_TEXT)
        self.combo_test_id.grid(row=0, column=1, sticky="we", padx=(6, 6), pady=3)
        self._entries.append(self.combo_test_id)

        ttk.Label(form, text="試験項目名").grid(row=1, column=0, sticky="w", pady=3)
        self.combo_title = ttk.Combobox(form, textvariable=self.var_title, width=ENTRY_WIDTH_TEXT)
        self.combo_title.grid(row=1, column=1, sticky="we", padx=(6, 6), pady=3)
        self._entries.append(self.combo_title)

        ttk.Label(form, text="対象ウィンドウ *").grid(row=2, column=0, sticky="w", pady=3)
        window_entry = ttk.Entry(
            form, textvariable=self.var_window_display, width=ENTRY_WIDTH_TEXT, state="readonly"
        )
        window_entry.grid(row=2, column=1, sticky="we", padx=(6, 6), pady=3)
        window_btn_frame = ttk.Frame(form)
        window_btn_frame.grid(row=2, column=2, sticky="we", pady=3)
        self.btn_pick_window = ttk.Button(window_btn_frame, text="選択...", width=6, command=self._on_pick_window)
        self.btn_pick_window.pack(side="left", fill="x", expand=True)
        # 選択直後だけでなく、開始前にいつでも対象を再確認できるようにする。
        ttk.Button(window_btn_frame, text="確認", width=6, command=self._preview_target_window).pack(
            side="left", fill="x", expand=True, padx=(4, 0)
        )

        auto_frame = ttk.Frame(form)
        auto_frame.grid(row=3, column=0, columnspan=3, sticky="we", pady=3)
        self.chk_auto = ttk.Checkbutton(
            auto_frame,
            text="自動キャプチャを有効にする",
            variable=self.var_auto_capture,
            command=self._on_toggle_auto,
        )
        self.chk_auto.pack(side="left")
        ttk.Label(auto_frame, text="間隔(秒)").pack(side="left", padx=(12, 4))
        self.entry_interval = ttk.Entry(
            auto_frame, textvariable=self.var_interval, width=ENTRY_WIDTH_SHORT, state="disabled"
        )
        self.entry_interval.pack(side="left")
        self._entries.append(self.entry_interval)
        self.var_stamp_time = tk.BooleanVar(value=False)
        self.chk_stamp = ttk.Checkbutton(
            auto_frame, text="撮影時刻を画像に焼き込む", variable=self.var_stamp_time
        )
        self.chk_stamp.pack(side="left", padx=(16, 0))

        add_row(4, "出力先フォルダ", self.var_output, browse=self._browse_output)

        tools_row = ttk.Frame(form)
        tools_row.grid(row=5, column=0, columnspan=3, sticky="we", pady=(6, 0))
        ttk.Button(tools_row, text="まとめレポートを生成", command=self._on_generate_index).pack(side="left")
        ttk.Label(
            tools_row,
            text="出力先フォルダ内の全セッションを一覧化（index.html / summary.csv）",
            style="Status.TLabel",
        ).pack(side="left", padx=(8, 0))

        # ボタン行・ステータス行は下端に固定し、フォームとの間の余白はログ欄が
        # 伸縮して吸収する（机上確認・動作確認コード挿入タブのTreeviewと同じ役割。
        # タブ切替時にボタンの縦位置・高さの見え方がガタつかないよう、
        # 「可変要素が余白を吸収し、ボタン行は常に下端」という構成を全タブで揃える）。
        bottom_area = ttk.Frame(parent)
        bottom_area.pack(side="bottom", fill="x")

        btn_frame = ttk.Frame(bottom_area, padding=(6, 6, 6, 4))
        btn_frame.pack(fill="x")
        self.btn_start = ttk.Button(btn_frame, text="開始", width=6, style="Primary.TButton", command=self._on_start)
        self.btn_start.pack(side="left")
        self.btn_capture = ttk.Button(
            btn_frame,
            text="今すぐキャプチャ",
            style="Capture.TButton",
            command=self._on_capture,
            state="disabled",
        )
        self.btn_capture.pack(side="left", padx=6)
        self.btn_finish = ttk.Button(
            btn_frame,
            text="終了してまとめる",
            style="Finish.TButton",
            command=self._on_finish,
            state="disabled",
        )
        self.btn_finish.pack(side="right")
        ttk.Label(btn_frame, text="備考:").pack(side="left", padx=(6, 4))
        self.entry_shot_note = ttk.Entry(btn_frame, textvariable=self.var_shot_note, state="disabled")
        self.entry_shot_note.pack(side="left", fill="x", expand=True, padx=(0, 12))

        self.status_var = tk.StringVar(value="待機中")
        self.status_label = ttk.Label(
            bottom_area, textvariable=self.status_var, style="Status.TLabel", padding=(6, 2, 6, 2)
        )
        self.status_label.pack(fill="x")

        self.capture_warning_var = tk.StringVar(value="")
        self.capture_warning_label = ttk.Label(
            bottom_area, textvariable=self.capture_warning_var, style="Warning.TLabel", padding=(6, 2, 6, 2)
        )
        self.capture_warning_label.pack(fill="x")

        self.log_frame = ttk.Frame(parent, padding=(6, 2, 6, 2))
        self.log_text = tk.Text(
            self.log_frame,
            width=20,
            height=4,
            state="disabled",
            wrap="word",
            bg=PALETTE["panel"],
            fg=PALETTE["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
            font=(FONT_FAMILY, FONT_SIZE),
        )
        self.log_text.tag_configure("warn", foreground="#C05C00")
        scrollbar = ttk.Scrollbar(self.log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.log_frame.pack(fill="both", expand=True)

    def _browse_output(self) -> None:
        path = filedialog.askdirectory(title="エビデンス出力先フォルダを選択")
        if path:
            self.var_output.set(path)

    def _set_default_target_window(self) -> None:
        """起動時点では対象未選択のままにせず、メイン画面（プライマリモニター）を
        既定の対象にしておく。モニター1台のみの環境では「画面全体」と等価なので
        そちらを既定にする。「選択...」で後から変更できる。
        """
        monitors = list_monitors()
        if len(monitors) <= 1:
            self.target_hwnd = FULL_SCREEN_HWND
            self.target_window_label = "画面全体（すべてのモニター）"
        else:
            primary_index = 0
            for i, (left, top, _right, _bottom) in enumerate(monitors):
                if left == 0 and top == 0:
                    primary_index = i
                    break
            rect = monitors[primary_index]
            self.target_hwnd = monitor_hwnd(primary_index)
            self.target_window_label = f"モニター{primary_index + 1}（{rect[2] - rect[0]}x{rect[3] - rect[1]}）"
        self.var_window_display.set(self.target_window_label)

    def _on_pick_window(self) -> None:
        dialog = WindowPickerDialog(self.root)
        self.root.wait_window(dialog)
        if dialog.selected is not None:
            self.target_hwnd, self.target_window_label = dialog.selected
            self.target_region = dialog.selected_region  # 範囲指定以外ではNone
            self.var_window_display.set(self.target_window_label)
            self._preview_target_window()

    def _preview_target_window(self) -> None:
        """選択した対象を試し撮りし、正しく映っているかをその場で確認できるようにする."""
        tmp_path = Path(tempfile.gettempdir()) / f"evtool_preview_{os.getpid()}.png"
        try:
            if self.target_hwnd == FULL_SCREEN_HWND:
                capture_full_screen(tmp_path)
            elif self.target_hwnd == REGION_HWND:
                if self.target_region is None:
                    raise RuntimeError("キャプチャ範囲が設定されていません")
                capture_monitor(self.target_region, tmp_path)
            elif is_monitor_hwnd(self.target_hwnd):
                monitors = list_monitors()
                index = monitor_index_from_hwnd(self.target_hwnd)
                capture_monitor(monitors[index], tmp_path)
            else:
                capture_window(self.target_hwnd, tmp_path)
        except Exception as exc:  # noqa: BLE001 - プレビューに失敗しても選択自体は続行する
            self._log(f"警告: プレビューの取得に失敗しました: {exc}")
            return
        CapturePreviewPopup(self.root, tmp_path, caption=f"対象: {self.target_window_label}")

    def _on_generate_index(self) -> None:
        """出力先フォルダ内の全セッションを一覧化した index.html / summary.csv を生成する."""
        base_dir = Path(self.var_output.get().strip() or "evidence")
        if not base_dir.is_dir():
            messagebox.showinfo("フォルダなし", f"出力先フォルダが見つかりません: {base_dir}")
            return
        try:
            index_path, csv_path, count = generate_summary_index(base_dir)
        except OSError as exc:
            messagebox.showerror("書き込みエラー", f"まとめレポートを生成できません: {exc}")
            return
        if count == 0:
            messagebox.showinfo(
                "セッションなし", f"{base_dir} 内に meta.json を持つセッションフォルダがありません"
            )
            return
        self._log(f"まとめレポートを生成しました（{count}セッション）: {index_path} / {csv_path}")
        if messagebox.askyesno("完了", f"{count}件のセッションをまとめました。一覧を開きますか？"):
            os.startfile(index_path)  # noqa: S606 - ユーザー自身が生成したローカルファイルを開く

    def _on_copy_last_shot(self) -> None:
        """直近に撮れたスクリーンショットをクリップボードへコピーする（Excel等への貼り付け用）."""
        if self.session is None or not self.session.meta.shots:
            self._log("警告: コピーできるスクリーンショットがまだありません")
            return
        last = self.session.meta.shots[-1]
        path = self.session.dir / last["file"]
        try:
            copy_image_to_clipboard(path)
        except Exception as exc:  # noqa: BLE001 - クリップボードは他プロセスと競合し得る
            self._log(f"警告: クリップボードへのコピーに失敗しました: {exc}")
            return
        self._log(f"クリップボードにコピーしました: {Path(last['file']).name}")

    def _on_toggle_pause(self) -> None:
        if self.session is None:
            return
        paused = self.session.toggle_pause()
        self.btn_pause.configure(text="自動キャプチャを再開" if paused else "自動キャプチャを一時停止")
        self._log("自動キャプチャを一時停止しました（手動キャプチャは可能）" if paused else "自動キャプチャを再開しました")

    def _on_toggle_auto(self) -> None:
        self.entry_interval.configure(state="normal" if self.var_auto_capture.get() else "disabled")

    # ---- logging -----------------------------------------------------------
    def _log(self, message: str) -> None:
        self._log_queue.put(message)

    def _poll_log_queue(self) -> None:
        # Ctrl+F5（グローバルホットキー）の押下通知。リスナースレッドから直接
        # tkinterを操作できないため、ここ（GUIスレッドの定期処理）で拾う。
        if self._hotkey_capture_requested.is_set():
            self._hotkey_capture_requested.clear()
            if self.session is not None:
                self._on_capture()
        for _ in range(20):
            try:
                message = self._log_queue.get_nowait()
            except queue.Empty:
                break
            timestamp = datetime.now().strftime("%H:%M:%S")
            line = f"[{timestamp}] {message}\n"
            self.log_text.configure(state="normal")
            tag = "warn" if message.startswith("警告:") else ""
            self.log_text.insert("end", line, tag)
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        self.root.after(150, self._poll_log_queue)

    # ---- actions -----------------------------------------------------------
    @staticmethod
    def _remember(history: list[str], combo: ttk.Combobox, value: str, max_size: int = 20) -> None:
        if not value:
            return  # 任意項目（試験項目名）が未入力のとき、空文字列を履歴に残さない
        if value in history:
            history.remove(value)
        history.insert(0, value)
        del history[max_size:]
        combo.configure(values=history)

    def _set_form_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for entry in self._entries:
            if entry is self.entry_interval and enabled and not self.var_auto_capture.get():
                continue  # 自動キャプチャ未使用時は間隔欄を無効のままにする
            entry.configure(state=state)
        self.btn_pick_window.configure(state=state)
        self.chk_auto.configure(state=state)
        self.chk_stamp.configure(state=state)

    def _on_start(self) -> None:
        test_id = self.var_test_id.get().strip()
        title = self.var_title.get().strip()
        if not test_id:
            messagebox.showerror("入力エラー", "試験IDは必須です")
            return
        is_valid_target = self.target_hwnd is not None and (
            self.target_hwnd == FULL_SCREEN_HWND
            or (self.target_hwnd == REGION_HWND and self.target_region is not None)
            or is_monitor_hwnd(self.target_hwnd)
            or win32gui.IsWindow(self.target_hwnd)
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

        try:
            self.session = EvidenceSession(
                base_dir=Path(self.var_output.get().strip() or "evidence"),
                test_id=test_id,
                title=title,
                hwnd=self.target_hwnd,
                window_label=self.target_window_label,
                auto_capture=auto_capture,
                interval=interval,
                log_callback=self._log,
                region=self.target_region,
                stamp_time=self.var_stamp_time.get(),
            )
        except OSError as exc:
            # 出力先に使えないパス（禁止文字・権限なし等）を指定した場合。
            # 例外のままだと何も起きていないように見えるため、明示的に知らせる。
            self.session = None
            messagebox.showerror("開始エラー", f"エビデンス出力先フォルダを作成できません:\n{exc}")
            return
        self.session.start()
        self._log(f"エビデンス取得を開始しました: {self.session.dir}")
        if auto_capture:
            self._log(f'対象ウィンドウ: "{self.target_window_label}" / 自動キャプチャ間隔: {interval}秒')
        else:
            self._log(f'対象ウィンドウ: "{self.target_window_label}" / 自動キャプチャ: 無効（手動のみ）')
        self.status_var.set(f"取得中: {self.session.dir}")
        self.capture_warning_var.set("")

        self._start_hotkey_listener()

        self._set_form_enabled(False)
        self.btn_start.configure(state="disabled")
        self.btn_capture.configure(state="normal")
        self.entry_shot_note.configure(state="normal")
        self.btn_finish.configure(state="normal")
        self._enter_capture_mode()

    def _start_hotkey_listener(self) -> None:
        """セッション中だけ Ctrl+F5 のグローバルホットキーを有効にする."""
        self._hotkey_capture_requested.clear()
        self._hotkey_listener = GlobalHotkeyListener(self._hotkey_capture_requested.set)
        if self._hotkey_listener.start():
            self.hotkey_hint_var.set("F5 / Ctrl+F5（他アプリ操作中も有効）でキャプチャ")
        else:
            self.hotkey_hint_var.set("F5でキャプチャ（Ctrl+F5は他のアプリが使用中のため無効）")
            self._log("警告: グローバルホットキー(Ctrl+F5)を登録できませんでした（他のアプリが使用中の可能性）")
            self._hotkey_listener = None

    def _stop_hotkey_listener(self) -> None:
        if self._hotkey_listener is not None:
            self._hotkey_listener.stop()
            self._hotkey_listener = None

    def _on_capture(self) -> None:
        if self.session is None:
            return
        note = self.var_shot_note.get().strip()
        filename = self.session.capture_now(tag="manual", note=note)
        self.var_shot_note.set("")
        if filename:
            self.capture_warning_var.set("")
            img_path = self.session.shots_dir / filename
            CapturePreviewPopup(self.root, img_path, caption=filename)
        else:
            self.capture_warning_var.set("警告: 直前のキャプチャに失敗しました（詳細はログ欄を確認）")

    def _on_finish(self) -> None:
        if self.session is None:
            return

        included_files = None
        if self.session.meta.shots:
            selection_dialog = ShotSelectionDialog(self.root, self.session.meta.shots, self.session.dir)
            self.root.wait_window(selection_dialog)
            if selection_dialog.cancelled:
                return
            included_files = selection_dialog.included_files

        dialog = FinishDialog(self.root, initial_zip=self._zip_after_finish)
        self.root.wait_window(dialog)
        if dialog.result_value is None:
            return
        self._zip_after_finish = dialog.zip_value  # 次回の既定値として記憶（設定にも保存）

        log_file = dialog.log_file_value or None
        session_dir = self.session.finish(
            result=dialog.result_value,
            note=dialog.note_value,
            log_file=log_file,
            included_files=included_files,
        )
        report_path: Optional[Path] = None
        try:
            report_path = generate_report(
                session_dir, style=dialog.report_style_value, content=dialog.report_content_value
            )
            self._log(f"エビデンスをまとめました: {session_dir}")
            self._log(f"レポート: {report_path}")
            self.status_var.set(f"完了: {session_dir}")
        except Exception as exc:  # noqa: BLE001
            self._log(f"警告: レポートの生成に失敗しました: {exc}")
            messagebox.showwarning("レポート生成エラー", f"エビデンスは保存されましたが、レポートの生成に失敗しました:\n{exc}")
            self.status_var.set(f"完了（レポートエラー）: {session_dir}")
        finally:
            self._stop_hotkey_listener()
            self.capture_warning_var.set("")
            self.session = None
            self._set_form_enabled(True)
            self.btn_start.configure(state="normal")
            self.btn_capture.configure(state="disabled")
            self.entry_shot_note.configure(state="disabled")
            self.btn_finish.configure(state="disabled")
            self._exit_capture_mode()

            finished_test_id = self.var_test_id.get().strip()
            next_test_id = increment_test_id(finished_test_id)
            self.var_test_id.set(next_test_id)
            if next_test_id != finished_test_id:
                self._log(f"次の試験ID候補を入力しておきました: {next_test_id}")

        if dialog.zip_value:
            try:
                zip_path = shutil.make_archive(
                    str(session_dir), "zip", root_dir=session_dir.parent, base_dir=session_dir.name
                )
                self._log(f"セッションフォルダをzip化しました: {zip_path}")
            except OSError as exc:
                self._log(f"警告: zip化に失敗しました: {exc}")

        if report_path is not None and messagebox.askyesno("完了", "レポートを開きますか？"):
            os.startfile(report_path)  # noqa: S606 - ユーザー自身が生成したローカルファイルを開く

    def _on_cancel_session(self) -> None:
        """「開始」を誤って押した場合などに、エビデンス取得そのものを取りやめる.

        finish() と異なり結果入力やレポート生成を行わず、取得済みのスクリーン
        ショット等も削除して通常表示に戻す。
        """
        if self.session is None:
            return
        if not messagebox.askyesno(
            "取りやめ",
            f"このエビデンス取得を取りやめますか？\n取得済みのデータは削除されます。\n\n{self.session.dir}",
        ):
            return

        session_dir = self.session.dir
        self.session.cancel()
        self._stop_hotkey_listener()
        self._log(f"エビデンス取得を取りやめました: {session_dir}")
        self.status_var.set("待機中")
        self.capture_warning_var.set("")

        self.session = None
        self._set_form_enabled(True)
        self.btn_start.configure(state="normal")
        self.btn_capture.configure(state="disabled")
        self.entry_shot_note.configure(state="disabled")
        self.btn_finish.configure(state="disabled")
        self._exit_capture_mode()

    # ---- settings persistence --------------------------------------------
    def _load_settings(self) -> None:
        try:
            data = json.loads(self._SETTINGS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return
        if "output_dir" in data:
            self.var_output.set(data["output_dir"])
        if "test_id_history" in data:
            self._test_id_history = list(data["test_id_history"])
            self.combo_test_id["values"] = self._test_id_history
            if self._test_id_history:
                self.combo_test_id.set(self._test_id_history[0])
        if "title_history" in data:
            self._title_history = list(data["title_history"])
            self.combo_title["values"] = self._title_history
            if self._title_history:
                self.combo_title.set(self._title_history[0])
        if "auto_capture" in data:
            self.var_auto_capture.set(bool(data["auto_capture"]))
            self._on_toggle_auto()
        if "interval" in data:
            self.var_interval.set(str(data["interval"]))
        if "stamp_time" in data:
            self.var_stamp_time.set(bool(data["stamp_time"]))
        if "zip_after_finish" in data:
            self._zip_after_finish = bool(data["zip_after_finish"])

    def _save_settings(self) -> None:
        try:
            data = {
                "output_dir": self.var_output.get(),
                "test_id_history": self._test_id_history,
                "title_history": self._title_history,
                "auto_capture": self.var_auto_capture.get(),
                "interval": self.var_interval.get(),
                "stamp_time": self.var_stamp_time.get(),
                "zip_after_finish": self._zip_after_finish,
            }
            self._SETTINGS_PATH.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            pass

    def _on_close(self) -> None:
        if self.session is not None:
            if not messagebox.askyesno(
                "確認", "エビデンス取得中です。保存せずに終了しますか？"
            ):
                return
        self._stop_hotkey_listener()
        self._save_settings()
        self.root.destroy()


def main() -> int:
    _enable_high_dpi_support()
    _set_app_user_model_id()
    root = tk.Tk()
    EvToolApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
