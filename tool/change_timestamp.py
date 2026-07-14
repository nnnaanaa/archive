from datetime import datetime
import os
from pathlib import Path


def change_all_timestamps(target_dir, target_datetime):
    """指定したディレクトリとその配下の全ファイル・全フォルダのタイムスタンプを変更する"""
    target_path = Path(target_dir)

    if not target_path.exists():
        print(f"エラー: 指定されたパスが存在しません: {target_dir}")
        return

    # 日時オブジェクトをエポック秒に変換
    new_timestamp = target_datetime.timestamp()

    print(f"処理を開始します: {target_path}")
    print(f"設定日時: {target_datetime}\n" + "-" * 40)

    success_count = 0
    error_count = 0

    # 1. まず、指定されたルートフォルダ（bkup自体）のタイムスタンプを変更
    try:
        os.utime(target_path, (new_timestamp, new_timestamp))
        print(f"[成功] (ルートフォルダ) {target_path.name}")
        success_count += 1
    except Exception as e:
        print(f"[失敗] (ルートフォルダ) {target_path.name} - 理由: {e}")
        error_count += 1

    # 2. 配下のすべてのファイルとフォルダを再帰的に取得して変更
    # rglob("*") で取得できるものすべて（is_file() の制限を解除）を対象にします
    for item in target_path.rglob("*"):
        try:
            # ファイルまたはフォルダのアクセス日時・更新日時を変更
            os.utime(item, (new_timestamp, new_timestamp))
            print(f"[成功] {item.relative_to(target_path)}")
            success_count += 1
        except Exception as e:
            print(f"[失敗] {item.relative_to(target_path)} - 理由: {e}")
            error_count += 1

    print("-" * 40)
    print(f"処理完了。成功: {success_count}件, 失敗: {error_count}件")


if __name__ == "__main__":
    # 対象のディレクトリパス
    TARGET_DIRECTORY = r"P:\python\tool\bkup"

    # 変更したい日時 (年, 月, 日, 時, 分, 秒)
    NEW_DATETIME = datetime(2026, 7, 14, 8, 0, 0)

    change_all_timestamps(TARGET_DIRECTORY, NEW_DATETIME)