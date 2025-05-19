import requests
import json
import yaml
import os, re
from datetime import datetime
import time

# 讀設定
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

search_cfg = config["search"]
output_dir = os.path.dirname(config["path"]["raw_jobs"])
os.makedirs(output_dir, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.104.com.tw/jobs/search/"
}

def convert_analysis_type_to_range(a_type):
    return {
        1: "0～5人",
        2: "6～10人",
        3: "11～30人",
        4: "31人以上"
    }.get(a_type, "未知")

def fetch_detail(job_id):
    url = f"https://www.104.com.tw/job/ajax/content/{job_id}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200 and resp.headers.get("Content-Type", "").startswith("application/json"):
            data = resp.json()
            jd = data.get("data", {}).get("jobDetail", {})
            desc = jd.get("jobDescription", "").strip()
            raw_cats = jd.get("jobCategory", [])
            cats = [c.get("description") for c in raw_cats if "description" in c]
            analysis_type = data.get("data", {}).get("header", {}).get("analysisType", 0)
            applied_range = convert_analysis_type_to_range(analysis_type)
            cond=data.get("data", {}).get("condition", {})
            raw_skill = cond.get("skill", [])
            skill = [s.get("description") for s in raw_skill if "description" in s]
            other = cond.get("other", [])
            return desc, cats, analysis_type, applied_range, skill, other
    except Exception as e:
        print(f"❌ {job_id} 抓取失敗: {e}")
    return "", [], 0, "未知"



# 抓單頁職缺
def search_104_page(keyword, areas, jobcats, page=1):
    url = "https://www.104.com.tw/jobs/search/list"
    params = {
        "ro": "0",
        "kwop": "12",
        "keyword": keyword,
        "area": ",".join(areas),
        "jobcat": ",".join(jobcats),
        "order": "11",
        "page": str(page),
        "mode": "s"
    }
    resp = requests.get(url, params=params, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"❌ Page {page} 失敗: {resp.status_code}")
        return None

# 搜尋所有頁
def search_all(keyword, areas, jobcats, max_pages=20):
    all_jobs = {}
    for page in range(1, max_pages + 1):
        result = search_104_page(keyword, areas, jobcats, page)
        if not result or "data" not in result or not result["data"]["list"]:
            break
        for job in result["data"]["list"]:
            link = job.get("link", {}).get("job", "")
            match = re.search(r"/job/([a-zA-Z0-9]+)", link)
            if not match:
                continue  # 如果連 job_id 都抓不到就略過
            job_id = match.group(1)
            if job_id not in all_jobs:
                desc, cats, analysis_type, applied_range, skill, other = fetch_detail(job_id)
                if not desc:
                    print(f"⚠️ 無描述，略過 job_id: {job_id}")
                    continue

                all_jobs[job_id] = {
                    "job_id": job_id,
                    "job_name": job.get("jobName"),
                    "company": job.get("custName"),
                    "description": desc,
                    "appear_date": job.get("appearDate"),
                    "link": "https:" + job.get("link", {}).get("job", ""),
                    "categories": cats,
                    "analysis_type": analysis_type,
                    "applied_range": applied_range,
                    "skill": skill,
                    "other": other,
                }
        time.sleep(1)
    return list(all_jobs.values())

# 執行搜尋
jobs = search_all(
    keyword=search_cfg["keyword"],
    areas=search_cfg["areas"],
    jobcats=search_cfg["job_categories"],
    max_pages=search_cfg.get("max_pages", 1),
)

# 儲存成 JSON
save_path = f"{output_dir}/raw_jobs.json"
with open(save_path, "w", encoding="utf-8") as f:
    json.dump(jobs, f, ensure_ascii=False, indent=2)

print(f"✅ 共儲存 {len(jobs)} 筆職缺 → {save_path}")
