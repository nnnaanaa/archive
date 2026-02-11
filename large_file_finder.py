import os

def get_large_files(target_dir, top_n=10):
    file_list = []

    # フォルダ内を再帰的に探索
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # ファイルサイズを取得（バイト単位）
                file_size = os.path.getsize(file_path)
                file_list.append((file_path, file_size))
            except (OSError, PermissionError):
                # アクセス権限がないファイルなどはスキップ
                continue

    # サイズが大きい順にソート
    file_list.sort(key=lambda x: x[1], reverse=True)

    # 上位n個を返す
    return file_list[:top_n]

def format_size(size_bytes):
    """バイト単位のサイズを読みやすい単位に変換"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024

# --- 設定と実行 ---
if __name__ == "__main__":
    # 調査したいフォルダのパスを指定
    target_folder = input("調査するフォルダのパスを入力してください: ")
    
    print(f"\n{target_folder} 内の大きいファイルを検索中...\n")
    
    top_files = get_large_files(target_folder, top_n=10)

    print(f"--- サイズが大きいファイル TOP 10 ---")
    for i, (path, size) in enumerate(top_files, 1):
        print(f"{i}. {format_size(size)} - {path}")