import paramiko
import time
import datetime
import os
import logging

def setup_logging(log_file):
    """
    ログ設定を初期化します。コンソールとファイルの両方に出力します。
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO) # INFO以上のログを出力

    # 既存のハンドラをクリア (スクリプトの複数回実行時に重複を避けるため)
    if logger.handlers:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    # コンソールハンドラ
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # ファイルハンドラ
    fh = logging.FileHandler(log_path, encoding='utf-8', mode='a') # 追記モード
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger

def run_commands_via_shell_with_logging(hostname, username, password, command_file, logger):
    """
    SSH経由でリモートホストに接続し、シェルを開いてファイルからコマンドを読み込んで実行します。
    結果はloggingモジュール経由で出力されます。
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # 本番環境での使用は非推奨

    try:
        logger.info(f"[{hostname}]へのSSH接続を試みています...")
        client.connect(hostname, username=username, password=password, timeout=10)
        logger.info(f"[{hostname}]に接続しました。シェルセッションを開始します。")

        chan = client.invoke_shell()
        time.sleep(1)
        chan.recv(4096).decode('utf-8')

        with open(command_file, 'r', encoding='utf-8') as f:
            commands = f.readlines()

        for i, command in enumerate(commands):
            command = command.strip()
            if not command:
                continue

            logger.info(f"\n--- コマンド送信中 ({i+1}/{len(commands)}): '{command}' ---")
            
            chan.send(command + '\n')
            time.sleep(1)

            output = ""
            while True:
                if chan.recv_ready():
                    output += chan.recv(4096).decode('utf-8')
                else:
                    time.sleep(0.1)
                    if not chan.recv_ready() and not output.strip().endswith(('$', '#', '>')):
                        continue
                    break

            if output:
                logger.info(f"出力:\n{output.strip()}")
            else:
                logger.info("出力なし。")

    except FileNotFoundError:
        logger.error(f"エラー: コマンドファイル '{command_file}' が見つかりません。", exc_info=True)
    except paramiko.AuthenticationException:
        logger.error("エラー: 認証に失敗しました。ユーザー名とパスワードを確認してください。", exc_info=True)
    except paramiko.SSHException as ssh_err:
        logger.error(f"エラー: SSH接続に問題が発生しました: {ssh_err}", exc_info=True)
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}", exc_info=True)
    finally:
        if client:
            client.close()
            logger.info(f"[{hostname}]へのSSH接続を閉じました。")

if __name__ == "__main__":
    ip_address = "nanahira"
    user_id = "nanahira"
    user_password = "nanahira"
    command_file_name = "command.txt"
    
    # ログファイルの命名規則を改善
    log_file_name = datetime.datetime.now().strftime("ssh_execution_%Y%m%d_%H%M%S.log")

    # ロギング設定
    my_logger = setup_logging(log_file_name)

    run_commands_via_shell_with_logging(ip_address, user_id, user_password, command_file_name, my_logger)