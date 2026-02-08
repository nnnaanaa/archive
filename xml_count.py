import glob
import os

def count_xml_lines_only(target_dir="xml"):
    # フォルダ内の .xml ファイルを検索
    search_path = os.path.join(target_dir, "*.xml")
    xml_files = glob.glob(search_path)
    
    if not xml_files:
        print(f"'{target_dir}' フォルダ内に XML ファイルが見つかりませんでした。")
        return

    print(f"--- XML行数集計 (空行は除外) ---")
    print(f"{'ファイル名':<30} | {'行数':>10}")
    print("-" * 45)

    total_all_files = 0

    for file_path in xml_files:
        count = 0
        try:
            # エンコーディングは一般的な utf-8 を指定
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    # strip() で空白や改行文字を除去し、中身があればカウント
                    if line.strip():
                        count += 1
            
            file_name = os.path.basename(file_path)
            print(f"{file_name:<30} | {count:>10}")
            total_all_files += count
            
        except Exception as e:
            print(f"{file_path} の読み込み中にエラーが発生しました: {e}")

    print("-" * 45)
    print(f"{'合計':<30} | {total_all_files:>10}")

if __name__ == "__main__":
    # xmlフォルダが存在しない場合は作成（初回実行用）
    if not os.path.exists("xml"):
        os.makedirs("xml")
        print("'xml' フォルダを作成しました。ここにファイルを配置してください。")
    else:
        count_xml_lines_only()