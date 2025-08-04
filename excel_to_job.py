# excel_to_job.py
import pandas as pd
import json
import argparse
from job_id_generator import parse_era, generate_job_id

def load_excel(path):
    # 工程管理表の想定カラム: '元号', '客先', '品名', '工場', '出荷フラグ'
    return pd.read_excel(path)

def row_to_job(row):
    full_suffix, numeric_only = parse_era(str(row.get("元号", "")))
    year_suffix = full_suffix  # 後で --no-prefix 等を入れるならここを拡張

    job_id = generate_job_id(
        year_suffix=year_suffix,
        client_code=str(row.get("客先", "") or "D1"),
        new_order=True,
        new_construction=True,
        new_item=True,
    )

    job = {
        "job_id": job_id,
        "client": row.get("客先"),
        "item_name": row.get("品名"),
        "factory": row.get("工場"),
        "status": "shipped" if row.get("出荷フラグ", False) else "in_progress",
        "is_shipped": bool(row.get("出荷フラグ", False)),
        "original_row": row.to_dict(),
    }
    return job

def main():
    parser = argparse.ArgumentParser(description="Excel から job を生成する（工程管理表）")
    parser.add_argument("excel", help="工程管理表の Excel ファイル名（例: 管理01_工程管理表.xlsx）")
    parser.add_argument("--output", default="jobs.json", help="出力する job JSON ファイル名")
    args = parser.parse_args()

    try:
        df = load_excel(args.excel)
    except FileNotFoundError:
        print(f"ファイルが見つかりません: {args.excel}")
        return

    jobs = []
    for _, row in df.iterrows():
        job = row_to_job(row)
        jobs.append(job)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

    print(f"生成した job を {args.output} に保存しました（件数: {len(jobs)}）")

if __name__ == "__main__":
    main()
