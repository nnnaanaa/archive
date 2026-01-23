import re
import os

def extract_batch_variables(input_file, output_file):
    # 変数名を抽出するための正規表現
    # set "VAR=VALUE" または set VAR=VALUE の形式にマッチ
    set_pattern = re.compile(r'^\s*set\s+"?([a-zA-Z0-9_]+)=', re.IGNORECASE)
    
    found_vars = set() # 重複を防ぐために集合（set）を使用

    try:
        # 一般的なWindowsのバッチファイルに合わせてShift-JISで読み込み
        with open(input_file, 'r', encoding='shift_jis') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        # 失敗した場合はUTF-8で試行
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

    for line in lines:
        match = set_pattern.match(line.strip())
        if match:
            var_name = match.group(1)
            found_vars.add(var_name)

    # アルファベット順に並べ替えて保存
    sorted_vars = sorted(list(found_vars))

    with open(output_file, 'w', encoding='utf-8') as f:
        for var in sorted_vars:
            f.write(var + '\n')

    print(f"元のファイル: {input_file}")
    print(f"出力ファイル: {output_file}")
    print(f"抽出された変数名: {', '.join(sorted_vars)}")
    print(f"--- 抽出完了 ---")

def main():
    # バッチファイルが格納されているディレクトリを指定
    target_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bat")

    # ディレクトリが存在しない場合は終了
    if not os.path.exists(target_dir):
        # os.makedirs(target_dir)
        return False
    
    # ディレクトリ内のすべての.batファイルを処理
    for file_name in os.listdir(target_dir):
        if file_name.lower().endswith('.bat'):
            input_path = os.path.join(target_dir, file_name)
            output_path = os.path.join(target_dir, f'config_{file_name}.txt')
            extract_batch_variables(input_path, output_path)
            # break

if __name__ == "__main__":
    main()