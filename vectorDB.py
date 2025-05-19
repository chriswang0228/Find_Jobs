import json, yaml
import numpy as np
import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer
import tqdm

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
# 1. 載入職缺資料
with open(config["path"]["filtered_jobs"], "r", encoding="utf-8") as f:
    jobs = json.load(f)

# 2. 載入公司資料表
company_df = pd.read_csv(config["path"]["company_info"])
company_df = company_df.drop_duplicates(subset="官方名稱", keep="first")
company_map = company_df.set_index("官方名稱")[["員工人數", "資本額", "產業類別", "產業描述"]].to_dict("index")

# 3. 初始化模型
model = SentenceTransformer(config["vector"]["embedding_model"], device="cuda")

texts = []
ids = []

# 4. 建立文本語料
for job in tqdm.tqdm(jobs):
    skill = ", ".join(job.get("skill", [])) if isinstance(job.get("skill"), list) else job.get("skill", "")
    other = job.get("other", "")
    cname = job.get("company", "").strip()
    company_info = company_map.get(cname, {})
    
    emp = str(company_info.get("員工人數", ""))
    capital = str(company_info.get("資本額", ""))
    industry = company_info.get("產業類別", "")
    industry_desc = company_info.get("產業描述", "")

    text = f"""【職缺】{job.get('job_name', '')}
                【公司】{cname}
                【描述】{job.get('description', '')}
                【技能】{skill}
                【其他條件】{other}
                【職類】{', '.join(job.get('categories', []))}
                【公司人數】{emp}人
                【資本額】{capital}元
                【產業類別】{industry}
                【產業描述】{industry_desc}
                【應徵人數】{job.get("applied_range", "")}"""
    texts.append(text)
    ids.append(job["job_id"])

# 5. 產生向量
embeddings = model.encode(texts, show_progress_bar=True)

# 6. 建立向量索引
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(np.array(embeddings))

# 7. 儲存向量資料庫與 id map
faiss.write_index(index, config["path"]["faiss_index"])
with open(config["path"]["faiss_ids"], "w", encoding="utf-8") as f:
    json.dump(ids, f, ensure_ascii=False, indent=2)

print("✅ 向量資料庫與 job_id 對照表已建立")
