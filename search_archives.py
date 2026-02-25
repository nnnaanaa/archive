import os
import shutil

def move_compressed_files(source_dir, destination_dir):
    # 対象とする拡張子
    extensions = ('.zip', '.lzh', '.rar', '.7z', '.tar', '.gz')
    
    # 移動先フォルダがなければ作成する
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
        print(f"作成しました: {destination_dir}")

    count = 0
    # os.walkでサブフォルダまでスキャン
    for root, dirs, files in os.walk(source_dir):
        # 移動先フォルダ自体を検索対象から除外（無限ループ防止）
        if os.path.abspath(root) == os.path.abspath(destination_dir):
            continue

        for file in files:
            if file.lower().endswith(extensions):
                source_path = os.path.join(root, file)
                dest_path = os.path.join(destination_dir, file)

                # 同名ファイルが移動先にある場合の処理（上書き防止）
                if os.path.exists(dest_path):
                    print(f"スキップ（同名あり）: {file}")
                    continue

                # ファイルの移動実行
                shutil.move(source_path, dest_path)
                print(f"移動済み: {file}")
                count += 1
    
    return count

# --- 実行部分 ---
src = input("検索したい元のフォルダパス: ")
dst = input("移動先のフォルダパス: ")

if os.path.exists(src):
    print(f"\n実行中...")
    moved_count = move_compressed_files(src, dst)
    print(f"\n完了！ 合計 {moved_count} 個のファイルを移動しました。")
else:
    print("元のフォルダパスが正しくありません。")