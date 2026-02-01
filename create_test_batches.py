import os
import glob

def create_test_variants_with_specific_log():
    source_dir = "bat"
    rtn0_dir = "rtn0"
    rtn1_dir = "rtn1"
    
    # ログファイルのフルパスを指定
    log_dir = r"D:\temp"
    log_path = os.path.join(log_dir, "execution_log.txt")

    # rtnフォルダの準備
    for folder in [rtn0_dir, rtn1_dir]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    bat_files = glob.glob(os.path.join(source_dir, "*.bat"))

    if not bat_files:
        print(f"'{source_dir}' 内にバッチファイルが見つかりません。")
        return

    for file_path in bat_files:
        file_name = os.path.basename(file_path)
        targets = [(rtn0_dir, 0, "SUCCESS"), (rtn1_dir, 1, "FAIL")]

        for folder, code, label in targets:
            output_path = os.path.join(folder, file_name)
            
            with open(output_path, "w", encoding="shift-jis") as f:
                f.write("@echo off\n")
                
                # ログ用ディレクトリが存在しない場合に作成するコマンドを追加
                f.write(f'if not exist "{log_dir}" mkdir "{log_dir}"\n')
                
                # ログ出力（エスケープ済みの | を使用）
                f.write(f'echo [%date% %time%] Name: %~nx0 ^| Args: %* ^| Return: {code} >> "{log_path}"\n')
                
                f.write(f'echo [{label}] Executed: %~nx0\n')
                f.write('echo Arguments received: %*\n')
                f.write(f"exit /b {code}\n")

        print(f"生成完了: {file_name} (ログ出力先: {log_path})")

if __name__ == "__main__":
    create_test_variants_with_specific_log()