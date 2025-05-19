import json, re, yaml
import pandas as pd
import requests
import urllib.parse
from tqdm import tqdm

# 讀設定
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# 載入你提供的 raw_jobs
with open(config["path"]["raw_jobs"], "r", encoding="utf-8") as f:
    jobs = json.load(f)

# 萃取公司名稱
companies = list(set(job["company"] for job in jobs if "company" in job))

def parse_emp_count(text):
    # 範例：'12000人' → 12000
    if not text:
        return None
    match = re.search(r"(\d+(,\d+)*)(?=人)", text.replace(",", ""))
    if match:
        return str(int(match.group(1)))
    return None

def parse_capital(text):
    # 範例：'資本額10億元' → 1000000000
    if not text:
        return None
    text = text.replace(",", "")
    match = re.search(r"(\d+(\.\d+)?)([萬億])", text)
    if match:
        number = float(match.group(1))
        unit = match.group(3)
        multiplier = {"萬": 1e4, "億": 1e8}.get(unit, 1)
        return str(int(number * multiplier))
    return None

def get_company_info(company_name):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.104.com.tw/company/search/"
    }
    keyword = urllib.parse.quote(company_name)
    search_url = f"https://www.104.com.tw/company/ajax/list?keyword={keyword}&searchType=company&page=1"

    try:
        search_res = requests.get(search_url, headers=headers, timeout=5)
        if search_res.status_code != 200:
            return "", "", "", "", "", "", f"HTTP {search_res.status_code}"

        data = search_res.json()
        if not data.get("data"):
            return "", "", "", "", "", "", "找不到"

        company = data["data"][0]
        name = company.get("name", "")
        cust_no = company.get("encodedCustNo", "")
        emp_count = company.get("employeeCountDesc", "")
        industry = company.get("industryDesc", "")
        if not cust_no:
            return name, "", emp_count, "", industry, "", ""

        # 第二階段：抓詳細資料（含資本額與產業描述）
        detail_url = f"https://www.104.com.tw/company/ajax/content/{cust_no}"
        detail_res = requests.get(detail_url, headers=headers, timeout=5)
        capital, industry_detail, official_url = "", "", f"https://www.104.com.tw/company/{cust_no}"
        if detail_res.status_code == 200:
            detail_data = detail_res.json().get("data", {})
            capital = detail_data.get("capital", "")
            if detail_data.get("custLink"):
                official_url = detail_data.get("custLink")
            description = detail_data.get("indcat", "")
        return name, official_url, emp_count, capital, industry, description, ""

    except Exception as e:
        return "", "", "", "", "", "", str(e)


# 執行查詢並儲存
results = []
for cname in tqdm(companies):
    name, url, emp, capital, industry, description, note = get_company_info(cname)
    emp = parse_emp_count(emp)
    capital = parse_capital(capital)
    results.append({
        "官方名稱": name,
        "公司網址": url,
        "員工人數": emp,
        "資本額": capital,
        "產業類別": industry,
        "產業描述": description,
        "備註": note
    })

df = pd.DataFrame(results)
df.to_csv(config["path"]["company_info"], index=False, encoding="utf-8-sig")
print("✅ 已儲存到 company_info_104.csv")
