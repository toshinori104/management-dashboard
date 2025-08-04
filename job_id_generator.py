import json
import argparse
import re
from pathlib import Path
from datetime import datetime

COUNTER_FILE = Path("job_counters.json")

def load_counters():
    if COUNTER_FILE.exists():
        return json.loads(COUNTER_FILE.read_text(encoding="utf-8"))
    return {"orders": {}, "constructions": {}, "items": {}}

def save_counters(counters):
    COUNTER_FILE.write_text(json.dumps(counters, ensure_ascii=False, indent=2), encoding="utf-8")

def parse_era(era_input: str) -> str:
    era_input = era_input.strip()
    m = re.match(r'^(令和|R)(\d+)$', era_input, re.IGNORECASE)
    if m:
        year = int(m.group(2))
        return f"R{year}"
    m = re.match(r'^(平成|H)(\d+)$', era_input, re.IGNORECASE)
    if m:
        year = int(m.group(2))
        return f"H{year}"
    m = re.match(r'^(\d{4})$', era_input)
    if m:
        year = int(m.group(1))
        return str(year)[-1]
    digits = re.findall(r'\d+', era_input)
    if digits:
        year = int(digits[0])
        return str(year)[-1]
    now = datetime.now()
    reiwa_year = now.year - 2018  # 令和元年は2019
    return f"R{reiwa_year}"

def generate_job_id(year_suffix: str, client_code: str,
                    new_order=False, new_construction=False, new_item=False,
                    base_order=None, base_construction=None):
    counters = load_counters()

    order_key = f"{year_suffix}{client_code}"
    if new_order or order_key not in counters["orders"]:
        counters["orders"][order_key] = counters["orders"].get(order_key, 0) + 1
    order_number = base_order if base_order is not None else counters["orders"][order_key]

    construction_key = f"{year_suffix}{client_code}-{order_number}"
    if new_construction or construction_key not in counters["constructions"]:
        counters["constructions"][construction_key] = counters["constructions"].get(construction_key, 0) + 1
    construction_seq = base_construction if base_construction is not None else counters["constructions"][construction_key]

    item_key = f"{year_suffix}{client_code}-{order_number}-{construction_seq}"
    if new_item or item_key not in counters["items"]:
        counters["items"][item_key] = counters["items"].get(item_key, 0) + 1
    item_seq = counters["items"][item_key]

    save_counters(counters)
    return f"{year_suffix}{client_code}{order_number}-{construction_seq}-{item_seq}"

def run_tests():
    print("=== サンプル生成テスト ===")
    id1 = generate_job_id("R7", "D1", new_order=True, new_construction=True, new_item=True)
    print("1:", id1, "(期待例: R7D11-1-1)")
    id2 = generate_job_id("R7", "D1", new_item=True)
    print("2:", id2, "(期待例: R7D11-1-2)")
    id3 = generate_job_id("R7", "D1", new_construction=True, new_item=True)
    print("3:", id3, "(期待例: R7D11-2-1)")
    id4 = generate_job_id("R7", "D1", new_order=True, new_construction=True, new_item=True)
    print("4:", id4, "(期待例: R7D12-1-1)")

def main():
    parser = argparse.ArgumentParser(description="工番ID発番ユーティリティ（元号対応）")
    parser.add_argument("--era", help="元号または西暦。例: R7, 令和7, 2025")
    parser.add_argument("--client", help="取引先コード（例: D1）")
    parser.add_argument("--new-order", action="store_true", help="新しい受注を作る")
    parser.add_argument("--new-construction", action="store_true", help="新しい工事を作る")
    parser.add_argument("--new-item", action="store_true", help="新しい品目を作る")
    parser.add_argument("--test", action="store_true", help="サンプル生成を実行")
    args = parser.parse_args()

    if args.test:
        run_tests()
        return

    if not args.era:
        raise ValueError("必須: --era を指定してください（例: --era R7）")
    if not args.client:
        raise ValueError("必須: --client を指定してください（例: --client D1）")

    year_suffix = parse_era(args.era)
    job_id = generate_job_id(
        year_suffix=year_suffix,
        client_code=args.client,
        new_order=args.new_order,
        new_construction=args.new_construction,
        new_item=args.new_item
    )
    print(job_id)

if __name__ == "__main__":
    main()
