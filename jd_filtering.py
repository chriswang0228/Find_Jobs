import json
import yaml
import os
import pandas as pd
import re

# === 讀取設定 ===
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# === 找出最新 raw_jobs 檔案 ===
data_dir = "data"
raw_files = [f for f in os.listdir(data_dir) if f.startswith("raw_jobs") and f.endswith(".json")]
latest_file = sorted(raw_files)[-1]
with open(os.path.join(data_dir, latest_file), "r", encoding="utf-8") as f:
    jobs = json.load(f)

# === 載入 visited.txt 職缺連結，擷取 job_id ===
with open(config["path"]["visited"], "r", encoding="utf-8") as f:
    visited_links = f.readlines()

visited_ids = set()
for url in visited_links:
    match = re.search(r"/job/([a-zA-Z0-9]+)", url)
    if match:
        visited_ids.add(match.group(1))

# === 讀入公司人數表並清洗 ===
company_df = pd.read_csv(config["path"]["company_info"])
company_df = company_df.drop_duplicates(subset="官方名稱", keep="first")
company_df["員工人數_clean"] = pd.to_numeric(company_df["員工人數"], errors="coerce")
company_df["資本額_clean"] = pd.to_numeric(company_df["資本額"], errors="coerce")
company_map = company_df.set_index("官方名稱")[["員工人數_clean", "資本額_clean"]].to_dict("index")

# === 過濾職缺條件 ===
def is_valid_job(job):
    job_id = job.get("job_id")
    cname = job.get("company", "").strip()

    # 排除已投過
    if job_id in visited_ids:
        return False

    # 排除類別名稱
    for cat in job.get("categories", []):
        if any(kw in cat for kw in config["filter"]["exclude_keywords"]):
            return False

    # 排除冷門
    if job.get("analysis_type", 0) <= config["filter"]["min_analysis_type"]:
        return False

    # 排除實習與研替
    title = job.get("job_name", "")
    if any(kw in title for kw in ["役", "實習", "資深"]):
        return False

    # 公司門檻過濾
    info = company_map.get(cname)
    if not info:
        return False

    emp = info.get("員工人數_clean")
    cap = info.get("資本額_clean")
    if pd.isna(emp) or emp < config["filter"]["min_employees"]:
        return False
    if pd.isna(cap) or cap < config["filter"]["min_capital"]:
        return False

    return True

# === 篩選職缺 ===
filtered = [job for job in jobs if is_valid_job(job)]

# === 儲存結果 ===
output_path = config["path"]["filtered_jobs"]
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(filtered, f, ensure_ascii=False, indent=2)

print(f"✅ 共保留 {len(filtered)} 筆職缺（篩除已投遞、實習、研替、冷門、小公司）")
