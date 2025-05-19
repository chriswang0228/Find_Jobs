
# Find_Jobs

---

## 專案功能架構

```
emp_count.py       擷取公司規模資訊（員工數 / 資本額 / 產業）
job_alert.py       爬取符合條件的 104 職缺（多頁收集）
job_filter.py      根據偏好與條件過濾職缺（包含 visited.txt 排除）
vectorDB.py        將篩選後職缺轉為向量庫 FAISS Index
query_vectorDB.py  查詢向量庫並推薦最匹配的職缺
visited.py         記錄使用者已投遞 / 查閱的職缺（避免重複）
```

---

## 使用流程

1. **蒐集職缺**（from 104）
   ```bash
   python job_alert.py
   ```

2. **擷取公司資訊**
   ```bash
   python emp_count.py
   ```

3. **過濾職缺**
   ```bash
   python job_filter.py
   ```

4. **建立向量資料庫**
   ```bash
   python vectorDB.py
   ```

5. **查詢推薦職缺**
   ```bash
   python query_vectorDB.py
   ```

6. **更新已讀紀錄**
   ```bash
   python visited.py
   ```

---

## 設定檔 `config.yaml`

使用者可以透過 `config.yaml` 設定搜尋條件與過濾參數：

```yaml
search:
  keyword: "AI, 深度學習, 電腦視覺"
  areas: ["6001001000", "6001002000"]
  job_categories: ["2007001004", "2007001012"]

filter:
  exclude_keywords: ["韌體", "前端", "實習"]
  min_employees: 1000
  min_capital: 100000000
  min_analysis_type: 2

path:
  raw_jobs: "data/raw_jobs_YYYYMMDD.json"
  filtered_jobs: "data/filtered_jobs.json"
  company_info: "data/company_info_104.csv"
```

---

## VectorDB 說明

- 使用 [`sentence-transformers`](https://github.com/UKPLab/sentence-transformers) 的 `all-MiniLM-L6-v2` 將職缺資訊嵌入為語意向量
- 向量儲存於 [`FAISS`](https://github.com/facebookresearch/faiss) 向量庫中（支援高效率最近鄰查詢）
- 查詢語句支援自然語言或條列式格式，如：

  ```text
  【職缺】AI工程師, 資料科學家
  【公司】具規模的科技公司，資訊公司，員工超過 1000 人
  【描述】開發 NLP、影像辨識、生成式 AI 應用，不要與遊戲，網頁，硬體等相關
  ```

---

## 資料結構

```
data/
  raw_jobs.json     ← 從 104 抓取的完整職缺資料
  filtered_jobs.json         ← 經條件過濾後的有效職缺
  company_info_104.csv       ← 各公司基本資訊（人數 / 資本額）
  visited.txt                ← 使用者已投遞 / 瀏覽的職缺連結
  job_vector.index             ← FAISS 向量資料庫
  job_id_map.json              ← FAISS 索引對應的 job_id
  search_result.json           ← 查詢推薦的職缺列表
```

---

## 📦 安裝相依套件

建議使用 Python 3.9 + pip：

```bash
pip install -r requirements.txt
```

```bash
conda create -n rag_env python=3.9 -y
conda activate rag_env
pip install -r requirements.txt
```

