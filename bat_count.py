import glob
import os

def count_effective_bat_lines(target_dir="bat"):
    search_path = os.path.join(target_dir, "*.bat")
    bat_files = glob.glob(search_path)
    
    if not bat_files:
        print(f"'{target_dir}' フォルダに .bat ファイルが見つかりませんでした。")
        return

    print(f"{'ファイル名':<30} | {'有効行数':>10}")
    print("-" * 45)

    for file_path in bat_files:
        count = 0
        try:
            # Shift-JIS(cp932)とUTF-8の両方に対応できるよう設定
            with open(file_path, 'r', encoding='cp932', errors='ignore') as f:
                for line in f:
                    clean_line = line.strip()
                    # 空行を除外
                    if not clean_line:
                        continue
                    # コメント行(REM または ::)を除外
                    upper_line = clean_line.upper()
                    if upper_line.startswith("REM") or upper_line.startswith("::"):
                        continue
                    
                    count += 1
            
            print(f"{os.path.basename(file_path):<30} | {count:>10}")
        except Exception as e:
            print(f"{file_path} の処理中にエラー: {e}")

# 実行
count_effective_bat_lines()