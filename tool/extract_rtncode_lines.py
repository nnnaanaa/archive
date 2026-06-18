import os

BASE_DIR = r"P:\python\test\data"


def main():
    for root, _, files in os.walk(BASE_DIR):
        for name in sorted(files):
            path = os.path.join(root, name)
            rel = os.path.relpath(path, BASE_DIR)
            with open(path, "r", encoding="utf-8") as f:
                matched_lines = [line.rstrip("\n") for line in f if "RtnCode" in line]
            for line in matched_lines:
                print(f"{rel}: {line}")


if __name__ == "__main__":
    main()
