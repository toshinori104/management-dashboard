import argparse
import json
import re
from pathlib import Path
from datetime import datetime

COUNTER_FILE = Path("job_counters.json")


def load_counters():
    if COUNTER_FILE.exists():
        return json.loads(COUNTER_FILE.read_text(encoding="utf-8"))
    return {}


def save_counters(counters):
    COUNTER_FILE.write_text(json.dumps(counters, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_era(era_input: str) -> tuple[str, str]:
    """
    戻り値: (full_suffix, numeric_only)
    例:
      '令和7' -> ('R7', '7')
      'R7'    -> ('R7', '7')
      '平成31'-> ('H31', '31')
      '2025'  -> ('R7', '7')  # 西暦を令和換算（令和元年=2019）
    """
    era_input = (era_input or "").strip()
    m = re.match(r'^(令和|R)(\d+)$', era_input, re.IGNORECASE)
    if m:
        year = int(m.group(2))
        return f"R{year}", str(year)
    m = re.match(r'^(平成|H)(\d+)$', era_input, re.IGNORECASE)
    if m:
        year = int(m.group(2))
        return f"H{year}", str(year)
    # 西暦を受け取ったら令和換算（令和元年=2019）
    try:
        year = int(era_input)
        reiwa_year = year - 2018
        return f"R{reiwa_year}", str(reiwa_year)
    except Exception:
        now = datetime.now()
        reiwa_year = now.year - 2018
        return f"R{reiwa_year}", str(reiwa_year)


def generate_job_id(year_suffix: str, client_code: str,
                    new_order=False, new_construction=False, new_item=False) -> str:
    """
    工番の形式例: R7D11-1-1
    year_suffix: 'R7' など（プレフィックス付き or 数字のみの制御は呼び出し元で）
    client_code: 取引先コード（例 D1）
    new_order / new_construction / new_item: 各階層の新規フラグ
    """
    counters = load_counters()
    key = f"{year_suffix}-{client_code}"
    if key not in counters:
        counters[key] = {"order": 0, "construction": {}, "item": {}}

    # 受注
    if new_order:
        counters[key]["order"] += 1
        counters[key]["construction"] = {}
    order_num = counters[key]["order"]

    # 工事
    if new_construction:
        counters[key]["construction"][str(order_num)] = {"number": 0, "items": {}}
    construction_dict = counters[key]["construction"].get(str(order_num), {"number": 0, "items": {}})
    construction_num = construction_dict["number"]
    if new_construction:
        construction_num += 1
        construction_dict["number"] = construction_num
        construction_dict["items"] = {}
        counters[key]["construction"][str(order_num)] = construction_dict

    # 品目
    if new_item:
        items = construction_dict.get("items", {})
        items[str(construction_num)] = items.get(str(construction_num), 0) + 1
        construction_dict["items"] = items
        counters[key]["construction"][str(order_num)] = construction_dict

    # 決定した番号を使って生成
    item_num = construction_dict.get("items", {}).get(str(construction_num), 1)
    job_id = f"{year_suffix}{client_code}-{order_num}-{construction_num}-{item_num}"

    save_counters(counters)
    return job_id


def run_tests():
    print("=== サンプル生成テスト ===")
    # テスト用の例（引数なしで動くように仮の client を使う）
    full_suffix, numeric_only = parse_era("R7")
    id1 = generate_job_id(year_suffix=full_suffix, client_code="D1", new_order=True, new_construction=True, new_item=True)
    id2 = generate_job_id(year_suffix=full_suffix, client_code="D1", new_item=True)
    id3 = generate_job_id(year_suffix=full_suffix, client_code="D1", new_construction=True, new_item=True)
    full_suffix2, _ = parse_era("R8")
    id4 = generate_job_id(year_suffix=full_suffix2, client_code="D1", new_order=True, new_construction=True, new_item=True)
    print("1:", id1)
    print("2:", id2)
    print("3:", id3)
    print("4:", id4)


def main():
    parser = argparse.ArgumentParser(description="工番ID発番ユーティリティ（元号対応・プレフィックス制御）")
    parser.add_argument("--era", help="元号または西暦。例: R7, 令和7, 2025")
    parser.add_argument("--client", help="取引先コード（例: D1）")
    parser.add_argument("--new-order", action="store_true", help="新しい受注を作る")
    parser.add_argument("--new-construction", action="store_true", help="新しい工事を作る")
    parser.add_argument("--new-item", action="store_true", help="新しい品目を作る")
    parser.add_argument("--test", action="store_true", help="サンプル生成を実行")
    parser.add_argument("--no-prefix", action="store_true", help="元号のプレフィックス（R/H）を外して数字だけ使う")
    parser.add_argument("--zero-pad", action="store_true", help="数字だけのときにゼロ埋め（例: 7 -> 07）")
    args = parser.parse_args()

    if args.test:
        run_tests()
        return

    if not args.client:
        raise ValueError("必須: --client を指定してください（例: --client D1）")

    full_suffix, numeric_only = parse_era(args.era or "")
    if args.no_prefix:
        year_suffix = numeric_only
        if args.zero_pad and year_suffix.isdigit():
            year_suffix = year_suffix.zfill(2)
    else:
        year_suffix = full_suffix

    job_id = generate_job_id(
        year_suffix=year_suffix,
        client_code=args.client,
        new_order=args.new_order,
        new_construction=args.new_construction,
        new_item=args.new_item,
    )
    print(job_id)


if __name__ == "__main__":
    main()
