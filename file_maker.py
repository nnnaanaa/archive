import os
import sys

def create_files_custom(target_folders, file_names, default_content="", config=None):
    """
    指定された複数のフォルダにファイルを作成する。
    フォルダごとにファイルの中身を細かく出し分け可能。
    """
    if config is None:
        config = {}

    # 1. すべてのフォルダが存在するか事前チェック
    for folder in target_folders:
        if not os.path.isdir(folder):
            print(f"【エラー】フォルダが見つかりません: {folder}", file=sys.stderr)
            return

    # 2. ファイル作成処理
    for folder in target_folders:
        print(f"--- {folder} の処理を開始 ---")
        
        # このフォルダ専用の設定を取得
        folder_config = config.get(folder, {})
        # 全フォルダ共通の設定を取得
        common_config = config.get("all", {})

        for name in file_names:
            file_path = os.path.join(folder, name)
            
            # 優先順位: 1.フォルダ個別設定 > 2.共通設定 > 3.デフォルト(0byte等)
            content = folder_config.get(name, common_config.get(name, default_content))
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # ログ表示
            if name in folder_config:
                status = f"★{folder}専用"
            elif name in common_config:
                status = "●共通設定"
            else:
                status = "○デフォルト"
            print(f"  [{status}] {name}")

# --- 設定エリア ---

# 1. 対象フォルダを1箇所で指定
target_dirs = ["./folder_A", "./folder_B"]

# 2. 作成するファイル名のリスト
files_to_create = [
    "ABCD01.txt", "ABCD02.txt", "EFGH01.txt", "EFGH02.txt",
    "IJKL01.txt", "IJKL02.txt", "OPQR01.txt", "OPQR02.txt",
    "STUV01.txt", "STUV02.txt", "VWXY01.txt", "VWXY02.txt"
]

# 3. 内容の設定
special_data = {
    # 全フォルダで共通の設定
    "all": {
    },
    
    # 【ここがポイント】フォルダA専用の設定
    "./folder_A": {
        "ABCD01.txt": "test1",
        "EFGH01.txt": "test1"
    },
    
    # 【ここがポイント】フォルダB専用の設定
    "./folder_B": {
        "ABCD01.txt": "test2",
        "STUV01.txt": "test2"
    }
}

# デフォルト（上記に指定がない場合は0byte）
default_text = ""

# 実行
if __name__ == "__main__":
    create_files_custom(target_dirs, files_to_create, default_text, special_data)