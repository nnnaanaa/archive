import re
import os

"""
バッチファイルの変数監視機能を追加するためのスクリプト
"""


def create_debug_batch(input_file, config_file, output_file):
    # 設定ファイルから監視対象の変数リストを読み込む
    if not os.path.exists(config_file):
        print(f"エラー: {config_file} が見つかりません。")
        return

    with open(config_file, 'r', encoding='utf-8') as f:
        # 空行を除去し、大文字小文字を区別せず比較するためにすべて小文字で保持
        target_vars = [line.strip().lower() for line in f if line.strip()]

    if not target_vars:
        print("監視対象の変数が指定されていません。")
        return

    # 2. 元のバッチファイルを読み込む
    try:
        with open(input_file, 'r', encoding='shift_jis') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        # Shift-JISでエラーが出る場合はUTF-8を試す
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

    debug_lines = []
    # SET文の変数名を抽出する正規表現
    set_pattern = re.compile(r'^\s*set\s+"?([a-zA-Z0-9_]+)=', re.IGNORECASE)

    # 3. ファイルを1行ずつ解析
    for line in lines:
        debug_lines.append(line)
        
        stripped = line.strip()
        match = set_pattern.match(stripped)
        
        if match:
            var_name = match.group(1)
            # 変数名が設定ファイル内に存在するか確認
            if var_name.lower() in target_vars:
                indent = line[:line.find(stripped)]
                # デバッグ用のecho文を作成
                debug_echo = f'{indent}echo [WATCH] {var_name} : !{var_name}!\n'
                debug_lines.append(debug_echo)

    # 4. 新しいバッチファイルを出力
    with open(output_file, 'w', encoding='shift_jis') as f:
        f.writelines(debug_lines)

    print(f"成功: '{output_file}' を作成しました。")
    print(f"監視対象: {', '.join(target_vars)}")

if __name__ == "__main__":
    # 対象のバッチファイル名、設定ファイル名、出力先を指定
    create_debug_batch(r'.\bat\test.bat', r'.\bat\config_test.bat.txt', 'debug_custom.bat')