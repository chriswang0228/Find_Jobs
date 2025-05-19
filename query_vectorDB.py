import json, yaml
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# === 可自訂查詢文字與 Top K 數量 ===
query_text = f"""【職缺】AI工程師, 資料科學家
【公司】具規模的科技公司，資訊公司，員工超過 1000 人
【描述】開發 NLP、影像辨識、生成式 AI 應用，不要與遊戲，網頁，硬體等相關
【技能】Python, PyTorch, NLP, Computer Vision
【職類】軟體工程師, 資料科學家
【資本額】十億以上
【應徵人數】應徵者超過 30 人"""

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

top_k = config["vector"]["top_k"]
# === 載入向量資料庫與模型 ===
index = faiss.read_index(config["path"]["faiss_index"])

with open(config["path"]["faiss_ids"], "r", encoding="utf-8") as f:
    job_ids = json.load(f)

with open(config["path"]["filtered_jobs"], "r", encoding="utf-8") as f:
    job_data = {job["job_id"]: job for job in json.load(f)}

model = SentenceTransformer(config["vector"]["embedding_model"], device="cuda")

# === 查詢向量資料庫 ===
query_vec = model.encode([query_text])
D, I = index.search(np.array(query_vec), top_k)
results = []

for rank, idx in enumerate(I[0]):
    job_id = job_ids[idx]
    job = job_data.get(job_id)
    if not job:
        continue
    result = {
        "rank": rank + 1,
        "job_name": job["job_name"],
        "company": job["company"],
        "link": job["link"],
        "description": job["description"][:100] + "...",
    }
    results.append(result)

# === 印出結果 ===
print(f"🔍 查詢：「{query_text}」\nTop {top_k} 結果：\n")
for res in results:
    print(f"{res['rank']}. 📌 {res['job_name']} @ {res['company']}")
    print(f"    🔗 {res['link']}")
    print(f"    📄 {res['description']}\n")

# === 儲存 JSON 結果 ===
with open(config["path"]["search_result"], "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("✅ 已將結果儲存至 search_result.json")
