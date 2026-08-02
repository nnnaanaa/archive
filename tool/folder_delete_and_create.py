import os
import shutil
from datetime import datetime

# 読み込むテキストファイルのパス
TEXT_FILE_PATH = "folder_list.txt"

# 削除したフォルダを退避させておくバックアップ先
BACKUP_ROOT = "backup"


def load_folder_list(file_path):
    if not os.path.exists(file_path):
        print(f"エラー: 設定ファイル '{file_path}' が見つかりません。")
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 空行を除外して正確な数をカウント
    return [line.strip() for line in lines if line.strip()]


def evacuate_to_backup(folder_path):
    """存在する場合、folder_path を BACKUP_ROOT 配下へ退避（削除）する。退避先パス（無ければ None）を返す。"""
    if not os.path.exists(folder_path):
        print(f"状態: フォルダは存在しませんでした（退避スキップ）。")
        return None

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    folder_name = os.path.basename(os.path.normpath(folder_path))
    backup_path = os.path.join(BACKUP_ROOT, f"{folder_name}_{timestamp}")
    os.makedirs(BACKUP_ROOT, exist_ok=True)
    shutil.move(folder_path, backup_path)
    print(f"状態: フォルダを削除し、バックアップへ退避しました。（{backup_path}）")
    return backup_path


def restore_from_backup(folder_path, backup_path):
    """backup_path の中身を folder_path へサブフォルダ・ファイルごと戻す。backup_path が無ければ空フォルダを作成する。"""
    if backup_path is None:
        os.makedirs(folder_path, exist_ok=True)
        print(f"状態: 退避したバックアップが無かったため、空フォルダを作成しました。")
        return

    # 親フォルダごと削除されているケースに備えて、親ディレクトリを先に用意する
    parent_dir = os.path.dirname(os.path.normpath(folder_path))
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    shutil.move(backup_path, folder_path)
    print(f"状態: フォルダをサブフォルダ・ファイルを含めて元に戻しました。")


def process_folders(file_path):
    folder_list = load_folder_list(file_path)
    if folder_list is None:
        return

    total_folders = len(folder_list)
    print(f"合計 {total_folders} 個のフォルダを処理します。\n")

    for index, folder_path in enumerate(folder_list, 1):
        print(f"--- [{index}/{total_folders}] 処理開始 ---")
        print(f"対象フォルダ: {folder_path}")

        # 1. 存在する場合にバックアップへ退避（削除）
        try:
            backup_path = evacuate_to_backup(folder_path)
        except Exception as e:
            print(f"エラー: フォルダの削除・退避に失敗しました。: {e}")
            print("このフォルダの処理をスキップします。\n")
            continue

        # ★ 応答待ち①（退避後・復元前）
        input(
            ">> ［Enter］キーを押すと、フォルダを【元に戻します】（サブフォルダ含む）..."
        )

        # 2. 元に戻す（退避したバックアップをサブフォルダ・ファイルごと戻す）
        try:
            restore_from_backup(folder_path, backup_path)
        except Exception as e:
            print(f"エラー: フォルダを元に戻す処理に失敗しました。: {e}")

        print(f"--- [{index}/{total_folders}] 処理完了 ---")

        # ★ 応答待ち②（次のフォルダへ進む前）
        # ※ 最後のフォルダの場合は、次に進むフォルダがないためスキップします
        if index < total_folders:
            input(
                ">> ［Enter］キーを押すと、【次のフォルダの処理】へ進みます...\n"
            )
        else:
            print()  # 最後の行は見栄えのために改行

    print("すべてのフォルダの処理が終了しました。")


if __name__ == "__main__":
    process_folders(TEXT_FILE_PATH)
