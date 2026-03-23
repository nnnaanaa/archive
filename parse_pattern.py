def parse_pattern_file(filepath):
    """
    パターンファイルを読み込み、各ブロックを辞書のリストとして返す。
    空行・ダッシュのみの行をブロックの区切りとして扱う。
    client は複数行ある場合はリストにまとめる。
    行頭・行末のダッシュ(-)やスペースは除去して解析する。
    """
    import re

    entries = []   # 全ブロックを格納するリスト
    current = {}   # 現在処理中のブロック

    with open(filepath, encoding="utf-8") as f:
        for line in f:
            # 行頭・行末の英数字以外の文字（記号・スペース等）を除去
            line = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', line)

            # 空行・ダッシュのみの行はブロックの区切り
            if not line:
                if current:
                    entries.append(current)  # 完成したブロックを追加
                    current = {}             # 次のブロック用にリセット
                continue

            # 行を「キー 値」に分割（最初のスペースで区切る）
            key, _, value = line.partition(" ")
            key = key.strip().lower()   # キーの余分なスペースと大文字を除去
            value = value.strip()       # 値の余分なスペースを除去

            if key in ("share", "path", "enable", "user"):
                # 単一値のキーはそのまま格納
                current[key] = value
            elif key == "client":
                # client は複数行ある場合があるのでリストに追加
                current.setdefault("client", []).append(value)

    # ファイル末尾に空行がない場合でも最後のブロックを追加
    if current:
        entries.append(current)

    return entries


def is_backup_path(path):
    """パスが /backup で始まる場合は True、それ以外は空文字を返す。"""
    return True if path.startswith("/backup") else ""


def to_2d_array(entries):
    """
    辞書のリストを二次元配列に変換する。
    client が複数ある場合は1クライアントにつき1行に展開する。
    """
    header = ["share", "path", "client", "enable", "user", "BKUP"]
    rows = [header]  # 1行目はヘッダー

    for entry in entries:
        path = entry.get("path", "")
        # パスが /backup で始まるか判定
        bkup = is_backup_path(path)

        # client ごとに1行生成（clientがない場合は空文字で1行）
        for client in entry.get("client", [""]):
            row = [
                entry.get("share", ""),
                path,
                client,
                entry.get("enable", ""),
                entry.get("user", ""),
                bkup,
            ]
            rows.append(row)

    return rows


if __name__ == "__main__":
    import sys
    import csv

    # コマンドライン引数でファイルパスを指定、省略時はデフォルトファイルを使用
    filepath = sys.argv[1] if len(sys.argv) > 1 else "patrern1.txt"
    output_csv = sys.argv[2] if len(sys.argv) > 2 else "output.csv"

    entries = parse_pattern_file(filepath)  # ファイルを読み込む
    array = to_2d_array(entries)            # 二次元配列に変換

    # CSVファイルに出力
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(array)

    print(f"{output_csv} に出力しました。")
