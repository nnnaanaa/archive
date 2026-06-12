import os
import shutil

# 読み込むテキストファイルのパス
TEXT_FILE_PATH = "folder_list.txt"


def process_folders(file_path):
    if not os.path.exists(file_path):
        print(f"エラー: 設定ファイル '{file_path}' が見つかりません。")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 空行を除外して正確な数をカウント
    folder_list = [line.strip() for line in lines if line.strip()]
    total_folders = len(folder_list)
    print(f"合計 {total_folders} 個のフォルダを処理します。\n")

    for index, folder_path in enumerate(folder_list, 1):
        print(f"--- [{index}/{total_folders}] 処理開始 ---")
        print(f"対象フォルダ: {folder_path}")

        # 1. 存在する場合に削除
        if os.path.exists(folder_path):
            try:
                shutil.rmtree(folder_path)
                print(f"状態: 既存のフォルダを削除しました。")
            except Exception as e:
                print(f"エラー: フォルダの削除に失敗しました。: {e}")
                print("このフォルダの処理をスキップします。\n")
                continue
        else:
            print(f"状態: フォルダは存在しませんでした（削除スキップ）。")

        # ★ 応答待ち①（削除後・再作成前）
        input(
            ">> ［Enter］キーを押すと、フォルダを【再作成】します..."
        )

        # 2. 再作成
        try:
            os.makedirs(folder_path, exist_ok=True)
            print(f"状態: フォルダを再作成しました。")
        except Exception as e:
            print(f"エラー: フォルダの再作成に失敗しました。: {e}")

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