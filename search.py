import csv
import ipaddress
import sys
import io
import os

# Windows環境でのUTF-8出力対応
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# CSVのカラム列番号設定（0始まり）
# 0:CIDR, 1:LAN名称, 2:IPアドレス, 3:使用用途
COL_IP = 2
COL_LAN = 1

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


def normalize_ip(ip_str: str) -> ipaddress.IPv4Address:
    """パディングの有無に関わらずIPアドレスをパースする"""
    octets = [str(int(o)) for o in ip_str.strip().split(".")]
    return ipaddress.IPv4Address(".".join(octets))


def normalize_cidr(cidr_str: str) -> ipaddress.IPv4Network:
    """パディングの有無に関わらずCIDRをパースする"""
    address, prefix = cidr_str.strip().split("/")
    octets = [str(int(o)) for o in address.split(".")]
    return ipaddress.IPv4Network(".".join(octets) + "/" + prefix, strict=False)


def build_index() -> list:
    """全CSVを読み込みインデックスを構築する"""
    index = []
    for filename in sorted(os.listdir(DATA_DIR)):
        if not filename.endswith(".csv"):
            continue
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            next(reader)  # ヘッダースキップ
            for row in reader:
                try:
                    network = normalize_cidr(row[0])
                    row_ip = normalize_ip(row[COL_IP])
                except ValueError:
                    continue
                index.append((network, row_ip, row[COL_LAN]))
    return index


def forward_search(target: ipaddress.IPv4Address, index: list) -> str | None:
    """IPアドレス → LAN名称"""
    for network, row_ip, lan_name in index:
        if row_ip == target and target in network:
            return lan_name
    return None


def reverse_search(target_lan: str, index: list) -> list:
    """LAN名称 → IPアドレス一覧"""
    return [str(row_ip) for _, row_ip, lan_name in index if lan_name == target_lan]


def run_forward(index: list, input_file: str):
    """IPアドレスからLAN名称を検索し result.csv へ出力"""
    output_file = os.path.join(BASE_DIR, "result.csv")

    if not os.path.exists(input_file):
        print(f"エラー: '{input_file}' が見つかりません。")
        sys.exit(1)

    rows = []
    with open(input_file, encoding="utf-8") as f:
        for line in f:
            ip_str = line.strip()
            if not ip_str:
                continue
            try:
                target = normalize_ip(ip_str)
            except ValueError:
                rows.append([ip_str, "（無効なIPアドレス）"])
                continue

            lan_name = forward_search(target, index)
            rows.append([ip_str, lan_name if lan_name else "（未登録）"])

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["IPアドレス", "LAN名称"])
        writer.writerows(rows)

    print(f"結果を '{output_file}' に出力しました。（{len(rows)} 件）")


def run_reverse(index: list, input_file: str):
    """LAN名称からIPアドレス一覧を検索し result.csv へ出力
    LAN名称1件につき複数のIPがある場合は1行1IPで出力する"""
    output_file = os.path.join(BASE_DIR, "result.csv")

    if not os.path.exists(input_file):
        print(f"エラー: '{input_file}' が見つかりません。")
        sys.exit(1)

    rows = []
    with open(input_file, encoding="utf-8") as f:
        for line in f:
            lan_name = line.strip()
            if not lan_name:
                continue

            ips = reverse_search(lan_name, index)
            if ips:
                for ip in ips:
                    rows.append([lan_name, ip])
            else:
                rows.append([lan_name, "（未登録）"])

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["LAN名称", "IPアドレス"])
        writer.writerows(rows)

    print(f"結果を '{output_file}' に出力しました。（{len(rows)} 件）")


def main():
    reverse_mode = "--reverse" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--reverse"]

    index = build_index()

    if reverse_mode:
        input_file = args[0] if args else os.path.join(BASE_DIR, "reverse.txt")
        run_reverse(index, input_file)
    else:
        input_file = args[0] if args else os.path.join(BASE_DIR, "search.txt")
        run_forward(index, input_file)


if __name__ == "__main__":
    main()
