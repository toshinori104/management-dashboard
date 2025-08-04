# excel_to_job_mapped.py
import pandas as pd
import json
import argparse
from job_id_generator import parse_era, generate_job_id

def safe_value(v):
    if pd.isna(v):
        return None
    return v

def is_shipped_marker(val):
    return str(val).strip() == "〇"

def row_to_job(row):
    # 元号がシートにないので現行の令和年を使う（parse_era に空文字渡すと今の年になる）
    full_suffix, numeric_only = parse_era("")
    year_suffix = full_suffix

    client_code = safe_value(row.get("Unnamed: 1")) or "D1"
    # 品名を加工／本社あたりと仮定（調整可）
    item_name = safe_value(row.get("Unnamed: 3"))
    # 製作工場（本社など）
    factory = safe_value(row.get("Unnamed: 9"))

    shipped = is_shipped_marker(row.get("Unnamed: 21"))
    status = "shipped" if shipped else "in_progress"

    job_id = generate_job_id(
        year_suffix=year_suffix,
        client_code=str(client_code),
        new_order=True,
        new_construction=True,
        new_item=True,
    )

    job = {
        "job_id": job_id,
        "client": client_code,
        "item_name": item_name,
        "factory": factory,
        "status": status,
        "is_shipped": shipped,
        "original_row": {k: (v.isoformat() if hasattr(v, "isoformat") else (v if not pd.isna(v) else None)) for k, v in row.to_dict().items()},
    }
    return job

def main():
    parser = argparse.ArgumentParser(description="Excel（工程管理表）から job を生成（固定マッピング版）")
    parser.add_argument("excel", help="Excel ファイル名")
    parser.add_argument("--output", default="jobs.json", help="出力ファイル")
    args = parser.parse_args()

    df = pd.read_excel(args.excel)  # 必要なら header=1 等を調整
    print("読み込んだ列:", list(df.columns))
    jobs = []
    for _, row in df.iterrows():
        jobs.append(row_to_job(row))

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

    print(f"生成した job を {args.output} に保存しました（件数: {len(jobs)}）")

if __name__ == "__main__":
    main()
