# -*- coding: utf-8 -*-
"""
IPアドレスとサブネットマスクから設定可能なIPアドレス範囲を返すプログラム
動作条件: Python 3.9+
"""
import argparse
import csv
import ipaddress
import sys
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

CSV_FIELDS = [
    "入力IPアドレス",
    "入力サブネットマスク",
    "ネットワークアドレス",
    "ブロードキャストアドレス",
    "サブネットマスク",
    "プレフィックス長",
    "設定可能な先頭IP",
    "設定可能な末尾IP",
    "設定可能なホスト数",
    "総アドレス数",
    "エラー",
]

CSV_FIELDS_SIMPLE = [
    "入力IPアドレス",
    "入力サブネットマスク",
    "設定可能な先頭IP",
    "設定可能な末尾IP",
    "エラー",
]


def get_usable_ip_range(ip_address: str, subnet_mask: str) -> dict:
    """
    IPアドレスとサブネットマスクから設定可能なIPアドレス範囲を返す。

    Args:
        ip_address: IPアドレス (例: "192.168.0.0")
        subnet_mask: サブネットマスク (例: "255.255.252.0")

    Returns:
        ネットワーク情報を含む辞書
    """
    network = ipaddress.IPv4Network(f"{ip_address}/{subnet_mask}", strict=False)
    hosts = list(network.hosts())

    return {
        "network_address": str(network.network_address),
        "broadcast_address": str(network.broadcast_address),
        "subnet_mask": str(network.netmask),
        "prefix_length": network.prefixlen,
        "first_usable": str(hosts[0]) if hosts else None,
        "last_usable": str(hosts[-1]) if hosts else None,
        "usable_host_count": len(hosts),
        "total_address_count": network.num_addresses,
    }


def normalize_mask(mask: str) -> str:
    """255.x.x.x 形式・/N 形式・N 形式をすべて受け付けてサブネットマスク形式に変換する。"""
    mask = mask.lstrip("/")
    if mask.isdigit():
        return str(ipaddress.IPv4Network(f"0.0.0.0/{mask}").netmask)
    return mask


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="IPアドレスとサブネットマスクから設定可能なIPアドレス範囲を表示する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "使用例:\n"
            "  # 1件指定\n"
            "  python subnet_range.py 192.168.0.0 255.255.252.0\n"
            "\n"
            "  # テキストファイルから複数件読み込み、CSV出力\n"
            "  python subnet_range.py -f input.txt -o result.csv\n"
            "\n"
            "入力ファイル形式 (1行につき「IPアドレス サブネットマスク」をスペース区切り):\n"
            "  192.168.0.0 255.255.252.0\n"
            "  10.0.0.0    255.0.0.0\n"
            "  172.16.0.0  22\n"
            "  # この行はコメントとして無視されます\n"
        ),
    )

    parser.add_argument("ip", metavar="IPアドレス", nargs="?", help="対象のIPアドレス (単体指定時)")
    parser.add_argument(
        "mask",
        metavar="サブネットマスク",
        nargs="?",
        help="サブネットマスクまたはプレフィックス長 (単体指定時)",
    )
    parser.add_argument(
        "-f", "--file",
        metavar="入力ファイル",
        help="IPアドレスとサブネットマスクを記載したテキストファイル",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="出力ファイル",
        default="result.csv",
        help="結果を出力するCSVファイルのパス (デフォルト: result.csv)",
    )
    parser.add_argument(
        "-s", "--simple",
        action="store_true",
        help="設定可能な先頭IP・末尾IPのみ出力する",
    )
    return parser.parse_args()


def load_entries_from_file(file_path: str) -> list[tuple[str, str]]:
    """テキストファイルから (IPアドレス, サブネットマスク) のリストを読み込む。"""
    entries = []
    path = Path(file_path)

    if not path.exists():
        print(f"エラー: ファイルが見つかりません: {file_path}", file=sys.stderr)
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")] if "," in line else line.split()
            if len(parts) != 2:
                print(
                    f"警告: {lineno}行目をスキップしました (形式不正): {line!r}",
                    file=sys.stderr,
                )
                continue
            entries.append((parts[0], parts[1]))

    return entries


def process_entry(ip: str, raw_mask: str) -> dict:
    """1件分の入力を処理し、CSV出力用の辞書を返す。"""
    row = {"入力IPアドレス": ip, "入力サブネットマスク": raw_mask, "エラー": ""}
    try:
        mask = normalize_mask(raw_mask)
        result = get_usable_ip_range(ip, mask)
        row.update({
            "ネットワークアドレス": result["network_address"],
            "ブロードキャストアドレス": result["broadcast_address"],
            "サブネットマスク": result["subnet_mask"],
            "プレフィックス長": f"/{result['prefix_length']}",
            "設定可能な先頭IP": result["first_usable"],
            "設定可能な末尾IP": result["last_usable"],
            "設定可能なホスト数": result["usable_host_count"],
            "総アドレス数": result["total_address_count"],
        })
    except ValueError as e:
        row["エラー"] = str(e)
    return row


def write_csv(rows: list[dict], output_path: str, simple: bool = False) -> None:
    """結果をCSVファイルに書き出す。"""
    fields = CSV_FIELDS_SIMPLE if simple else CSV_FIELDS
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def print_result(result: dict, simple: bool = False) -> None:
    """1件分の結果を標準出力に表示する。"""
    if simple:
        print(f"設定可能な先頭IP: {result['設定可能な先頭IP']}")
        print(f"設定可能な末尾IP: {result['設定可能な末尾IP']}")
        return
    print(f"入力IPアドレス  : {result['入力IPアドレス']}")
    print(f"サブネットマスク: {result['サブネットマスク']} ({result['プレフィックス長']})")
    print("-" * 40)
    print(f"ネットワークアドレス    : {result['ネットワークアドレス']}")
    print(f"ブロードキャストアドレス: {result['ブロードキャストアドレス']}")
    print(f"設定可能な先頭IP        : {result['設定可能な先頭IP']}")
    print(f"設定可能な末尾IP        : {result['設定可能な末尾IP']}")
    print(f"設定可能なホスト数      : {result['設定可能なホスト数']} 台")
    print(f"総アドレス数            : {result['総アドレス数']} 個")


def main():
    args = parse_args()

    # ファイル指定モード
    if args.file:
        entries = load_entries_from_file(args.file)
        if not entries:
            print("エラー: 有効な入力が1件もありませんでした。", file=sys.stderr)
            sys.exit(1)

        rows = [process_entry(ip, mask) for ip, mask in entries]
        write_csv(rows, args.output, simple=args.simple)

        ok = sum(1 for r in rows if not r["エラー"])
        ng = len(rows) - ok
        print(f"{len(rows)} 件処理しました (成功: {ok} 件 / エラー: {ng} 件)")
        print(f"結果を出力しました: {args.output}")
        return

    # 単体指定モード
    if not args.ip or not args.mask:
        print("エラー: IPアドレスとサブネットマスクを指定するか、-f でファイルを指定してください。", file=sys.stderr)
        print("  python subnet_range.py --help", file=sys.stderr)
        sys.exit(1)

    row = process_entry(args.ip, args.mask)
    if row["エラー"]:
        print(f"エラー: {row['エラー']}", file=sys.stderr)
        sys.exit(1)

    print_result(row, simple=args.simple)


if __name__ == "__main__":
    main()
