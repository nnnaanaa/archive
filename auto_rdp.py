import os
import time
import threading
import tempfile
import ctypes
import pyautogui
import win32gui
import win32con

# --- サーバ設定（増減はここだけ編集） ---
SERVERS = [
    {"ip": "10.0.0.26", "username": "nanahira", "password": "nanahira", "batch_path": r"C:\Users\nanahira\Desktop\connect_nas.bat"},
    {"ip": "10.0.0.27", "username": "nanahira", "password": "nanahira", "batch_path": r"C:\Users\nanahira\Desktop\connect_nas.bat"},
    {"ip": "10.0.0.28", "username": "nanahira", "password": "nanahira", "batch_path": r"C:\Users\nanahira\Desktop\connect_nas.bat"},
]

CONNECT_WAIT_SEC = 15

# ウィンドウ操作のタイミング調整（回線速度が遅い場合は大きくする）
ACTIVATE_WAIT   = 0.4   # ウィンドウフォーカス後の待機（秒）
RUN_DIALOG_WAIT = 1.0   # Win+R 後、リモートの実行ダイアログが開くまでの待機（秒）
TYPE_INTERVAL   = 0.02  # 文字入力間隔（秒）遅い回線なら 0.05 に増やす
# ----------------------------------------

window_lock   = threading.Lock()
start_barrier = threading.Barrier(len(SERVERS), timeout=60)
stop_watcher  = threading.Event()

# 押したいボタンのテキスト（日本語・英語 両対応）
ACCEPT_BUTTON_TEXTS = ("接続", "はい", "Connect", "Yes", "OK")

# ダイアログタイトルに含まれるキーワード（広めに設定）
DIALOG_KEYWORDS = (
    "リモート", "Remote", "Desktop", "デスクトップ",
    "接続", "Connection", "セキュリティ", "Security",
    "証明書", "Certificate", "認証", "Authentication",
    "セッション", "Session", "ログオン", "Logon", "ログイン", "Login",
)


def create_rdp_file(ip, username):
    """keyboardhook:i:1 を含む .rdp ファイルを生成する"""
    content = "\n".join([
        f"full address:s:{ip}",
        f"username:s:{username}",
        "keyboardhook:i:1",           # Win+R 等をリモートへ転送
        "authentication level:i:0",
        "prompt for credentials:i:0",
        "redirectclipboard:i:1",      # クリップボードリダイレクトを明示的に有効化
        "administrative session:i:1", # 管理セッションへ直接接続（セッション選択画面をスキップ）
    ])
    path = os.path.join(tempfile.gettempdir(), f"rdp_{ip.replace('.', '_')}.rdp")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def dialog_watcher():
    """
    #32770 クラス（標準ダイアログ）でRDP関連キーワードを含むウィンドウを
    1秒ごとに監視し、承認ボタンを直接クリックして閉じる。
    タイトルに依存しないため発行元警告・証明書警告など何段階出ても対応できる。
    """
    while not stop_watcher.is_set():
        try:
            dialogs = []

            def enum_callback(hwnd, _):
                if not win32gui.IsWindowVisible(hwnd):
                    return
                # 標準ダイアログクラスのみ対象
                if win32gui.GetClassName(hwnd) != "#32770":
                    return
                title = win32gui.GetWindowText(hwnd)
                if any(kw in title for kw in DIALOG_KEYWORDS):
                    dialogs.append((hwnd, title))

            win32gui.EnumWindows(enum_callback, None)

            for hwnd, title in dialogs:
                # 承認ボタンを直接クリック（"はい(Y)" 等の部分一致で検索）
                clicked = [False]

                def button_callback(child_hwnd, _):
                    if clicked[0]:
                        return
                    if win32gui.GetClassName(child_hwnd) != "Button":
                        return
                    text = win32gui.GetWindowText(child_hwnd)
                    if any(text.startswith(a) or a in text for a in ACCEPT_BUTTON_TEXTS):
                        win32gui.PostMessage(child_hwnd, win32con.BM_CLICK, 0, 0)
                        clicked[0] = True

                win32gui.EnumChildWindows(hwnd, button_callback, None)

                if clicked[0]:
                    print(f"  [ウォッチャー] ボタンクリックで閉じました: '{title}'")
                elif win32gui.IsWindowVisible(hwnd):
                    # ボタンが見つからない場合は Alt+Y で「はい(Y)」を押す
                    # （Enter はデフォルトが「いいえ」の場合に接続が拒否されるため使わない）
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
                    time.sleep(0.2)
                    pyautogui.hotkey("alt", "y")
                    print(f"  [ウォッチャー] Alt+Y で閉じました: '{title}'")

                time.sleep(0.3)

        except Exception:
            pass

        time.sleep(1)


def connect_rdp(server):
    ip = server["ip"]
    os.system(f'cmdkey /add:{ip} /user:{server["username"]} /pass:{server["password"]}')
    rdp_path = create_rdp_file(ip, server["username"])
    os.system(f'start mstsc "{rdp_path}"')
    print(f"  [接続開始] {ip}")


def find_rdp_window(ip, retries=5, interval=2):
    for attempt in range(retries):
        found = []

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and ip in win32gui.GetWindowText(hwnd):
                found.append(hwnd)

        win32gui.EnumWindows(callback, None)
        if found:
            return found[0]

        if attempt < retries - 1:
            print(f"  [{ip}] ウィンドウ待機中... ({attempt + 1}/{retries})")
            time.sleep(interval)

    return None


def activate_window(hwnd):
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    ctypes.windll.user32.BringWindowToTop(hwnd)
    ctypes.windll.user32.SetForegroundWindow(hwnd)


def run_batch(server):
    ip = server["ip"]
    batch_path = server["batch_path"]

    try:
        start_barrier.wait()
    except threading.BrokenBarrierError:
        print(f"  [{ip}] バリアタイムアウト：スキップ")
        return

    with window_lock:
        hwnd = find_rdp_window(ip)
        if not hwnd:
            print(f"  [{ip}] 警告: ウィンドウが見つかりません（スキップ）")
            return

        activate_window(hwnd)
        time.sleep(ACTIVATE_WAIT)

        # RDP ウィンドウ中央をクリックしてリモートデスクトップにフォーカスを確実に当てる
        tl = win32gui.ClientToScreen(hwnd, (0, 0))
        cr = win32gui.GetClientRect(hwnd)
        pyautogui.click(tl[0] + cr[2] // 2, tl[1] + cr[3] // 2)
        time.sleep(0.3)

        # Win+R → リモートの「ファイル名を指定して実行」
        pyautogui.hotkey("win", "r")
        time.sleep(RUN_DIALOG_WAIT)

        # パスを1文字ずつ入力（クリップボードリダイレクト不要・確実に届く）
        pyautogui.write(batch_path, interval=TYPE_INTERVAL)
        time.sleep(0.2)
        pyautogui.press("enter")

    print(f"  [実行完了] {ip}")


# ── Phase 1: 全サーバへ同時にRDP接続 ──────────────────────────
print("=== Phase 1: 全サーバへRDP接続（同時） ===")
os.system(r'reg add "HKCU\Software\Microsoft\Terminal Server Client" /v "AuthenticationLevelOverride" /t REG_DWORD /d 0 /f')

# ダイアログウォッチャーを接続前に起動
watcher = threading.Thread(target=dialog_watcher, daemon=True)
watcher.start()
print("  [ウォッチャー起動] 確認ダイアログを自動処理します")

threads = [threading.Thread(target=connect_rdp, args=(s,), daemon=True) for s in SERVERS]
for t in threads:
    t.start()
for t in threads:
    t.join()

# ── Phase 2: 接続完了を待機（ウォッチャーが裏でダイアログを処理し続ける） ──
print(f"\n=== Phase 2: 接続完了待機中（{CONNECT_WAIT_SEC}秒） ===")
time.sleep(CONNECT_WAIT_SEC)

# ウォッチャーを停止
stop_watcher.set()

# ── Phase 3: 全スレッド一斉にバッチ実行 ───────────────────────
print(f"\n=== Phase 3: バッチ実行開始（全{len(SERVERS)}台） ===")
batch_threads = [threading.Thread(target=run_batch, args=(s,), daemon=True) for s in SERVERS]
for t in batch_threads:
    t.start()
for t in batch_threads:
    t.join()

print("\n=== 全処理完了 ===")
