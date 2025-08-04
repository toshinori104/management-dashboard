# excel_to_job.py
import pandas as pd
import json
from job_id_generator import parse_era, generate_job_id

def load_excel(path):
    # 工程管理表の例: '工番','客先','品名','工場','元号','出荷フラグ' などが列にある想定
    return pd.read_excel(path)

def row_to_job(row):
    # 元号からプレフィックス付き工番接頭辞を作る（必要ならオプションを拡張）
    full_suffix, numeric_only = parse_era(str(row.get("元号", "")))
    year_suffix = full_suffix  # 今はプレフィックス付き固定、後でオプション化可

    job_id = generate_job_id(
        year_suffix=year_suffix,
        client_code=str(row.get("客先", "") or "D1"),  # デフォルトを適宜調整
        new_order=True,
        new_construction=True,
        new_item=True,
    )

    job = {
        "job_id": job_id,
        "client": row.get("客先"),
        "item_name": row.get("品名"),
        "factory": row.get("工場"),
        "status": "in_progress" if not row.get("出荷フラグ", False) else "shipped",
        "is_shipped": bool(row.get("出荷フラグ", False)),
        "original_row": row.to_dict(),  # 追跡用
    }
    return job

def main():
    df = load_excel("工程管理表.xlsx")  # 実ファイル名に合わせる
    jobs = []
    for _, row in df.iterrows():
        job = row_to_job(row)
        jobs.append(job)
    # JSON に出力（例: jobs.json）
    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"生成した job を jobs.json に保存しました（件数: {len(jobs)}）")

if __name__ == "__main__":
    main()
