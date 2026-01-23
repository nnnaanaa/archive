import re

def create_debug_batch(input_file, output_file):
    with open(input_file, 'r', encoding='shift_jis') as f:
        lines = f.readlines()

    debug_lines = []
    # SET文を抽出する正規表現（set "VAR=VALUE" や set VAR=VALUE に対応）
    set_pattern = re.compile(r'^\s*set\s+"?([a-zA-Z0-9_]+)=', re.IGNORECASE)

    for line in lines:
        debug_lines.append(line)
        
        # 行のトリミングをしてから判定
        stripped = line.strip()
        match = set_pattern.match(stripped)
        
        if match:
            var_name = match.group(1)
            # ループ内などの遅延展開を考慮して !var! 形式で出力するechoを追加
            # 視認性を高めるために [DEBUG] プレフィックスを付与
            indent = line[:line.find(stripped)] # 元のインデントを維持
            debug_echo = f'{indent}echo [DEBUG] {var_name} is set to: !{var_name}!\n'
            debug_lines.append(debug_echo)

    with open(output_file, 'w', encoding='shift_jis') as f:
        f.writelines(debug_lines)

    print(f"変換完了: {output_file} を作成しました。")

if __name__ == "__main__":
    # 先ほど作成したバッチファイル名を指定
    create_debug_batch('organizer.bat', 'debug_organizer.bat')