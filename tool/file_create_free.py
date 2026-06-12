import os

# ==========================================
# 設定（ここを自由に変更してください）
# ==========================================
N = 5           # 作成するファイル数（command1.txt ～ commandN.txt）
n = 3           # 各ファイルに書き込むhostnameの行数
HOSTNAME = "example-host"  # 書き込むホスト名

# フォルダリストが記載されたテキストファイルのパス
FOLDER_LIST_FILE = "folders.txt" 
# ==========================================

def create_command_files():
    # フォルダリストファイルの存在確認
    if not os.path.exists(FOLDER_LIST_FILE):
        print(f"エラー: {FOLDER_LIST_FILE} が見つかりません。")
        return

    # テキストファイルからフォルダパスを読み込み
    folders = []
    with open(FOLDER_LIST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 空行、または「#」で始まる行（コメント）はスキップ
            if not line or line.startswith("#"):
                continue
            folders.append(line)

    # 各フォルダに対して処理を実行
    for folder in folders:
        # フォルダが存在しない場合は自動作成
        if not os.path.exists(folder):
            try:
                os.makedirs(folder, exist_ok=True)
                print(f"フォルダを作成しました: {folder}")
            except Exception as e:
                print(f"[エラー] フォルダ {folder} の作成に失敗しました: {e}")
                continue

        print(f"処理中: {folder}")

        # command1.txt から commandN.txt までを作成
        for i in range(1, N + 1):
            file_name = f"command{i}.txt"
            file_path = os.path.join(folder, file_name)

            # ファイルにhostnameをn行書き込み
            try:
                with open(file_path, "w", encoding="utf-8") as file:
                    for _ in range(n):
                        file.write(HOSTNAME + "\n")
                print(f"  --> {file_name} を作成/上書きしました。")
            except Exception as e:
                print(f"  [エラー] {file_name} の作成に失敗しました: {e}")

if __name__ == "__main__":
    create_command_files()