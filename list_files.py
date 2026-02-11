import pathlib

def export_file_list(target_path, extension, output_filename):
    """
    指定されたフォルダから特定の拡張子を持つファイルを探し、
    そのパスをテキストファイルに書き出す関数
    """
    
    # 1. 検索対象のフォルダを「パスオブジェクト」として読み込む
    base_dir = pathlib.Path(target_path)
    
    # 2. 検索条件（パターン）を作成
    # 拡張子の前にドット（.）があってもなくても動作するように調整
    clean_ext = extension.lstrip('.')
    search_pattern = f"**/*.{clean_ext}"
    
    print(f"「{base_dir.resolve()}」の中で .{clean_ext} ファイルを探しています...")

    # 3. 指定したフォルダ内を再帰的に検索
    # glob() を使うことでサブフォルダの中身まで一括で取得
    file_paths = list(base_dir.glob(search_pattern))
    
    # 4. 見つかったファイルの結果をテキストファイルに保存
    with open(output_filename, mode="w", encoding="utf-8") as f:
        # ファイルが一つも見つからなかった場合の処理
        if not file_paths:
            print("対象のファイルは見つかりませんでした。")
            return

        # 見つかったファイルの数だけループして一行ずつ書き込む
        for path in file_paths:
            # path.resolve() で「絶対パス（フルパス）」を取得して書き出し
            f.write(str(path.resolve()) + "\n")
            
    print(f"【完了】 {len(file_paths)} 件のファイルを '{output_filename}' にリスト化しました。")

# --- ここからがプログラムの設定（自由に変更してください） ---

# 検索を開始する場所（ ./ は「このプログラムがあるフォルダ」という意味）
SEARCH_DIRECTORY = r"D:"

# 探したいファイルの拡張子（例: jpg, pdf, csv など）
TARGET_EXTENSION = "mp4"

# 保存するリストのファイル名
OUTPUT_FILE = "file_list.txt"

# プログラムの実行
if __name__ == "__main__":
    export_file_list(SEARCH_DIRECTORY, TARGET_EXTENSION, OUTPUT_FILE)