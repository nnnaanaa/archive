import itertools

def grep_with_context(file_path, target_word, n_lines):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 行イテレータを作成
            line_iterator = iter(f)
            
            for line in line_iterator:
                if target_word in line:
                    print(f"--- Match Found ---")
                    # ヒットした行を表示
                    print(f"Hit: {line.strip()}")
                    
                    # 次のN行を切り出して表示
                    # islice(イテレータ, 個数) で次の要素を指定数だけ取り出す
                    next_n_rows = list(itertools.islice(line_iterator, n_lines))
                    
                    for i, follow_line in enumerate(next_n_rows, 1):
                        print(f" +{i}: {follow_line.strip()}")
                    
                    print("-" * 20)
                    
    except FileNotFoundError:
        print(f"Error: ファイル '{file_path}' が見つかりませんでした。")

# 設定
file_name = 'test.txt'
search_word = 'English'
n = 3  # ヒットした行の後に何行表示するか

grep_with_context(file_name, search_word, n)