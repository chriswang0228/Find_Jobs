import json, yaml

# === 讀取設定 ===
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# 讀入 JSON 職缺清單
with open(config["path"]["search_result"], "r", encoding="utf-8") as f:
    jobs = json.load(f)

# 萃取所有連結
links = [job["link"] for job in jobs if "link" in job]

# 寫入 visited.txt（覆蓋）
with open(config["path"]["visited"], "a", encoding="utf-8") as f:
    for link in links:
        f.write(link.strip() + "\n")

print(f"✅ 已寫入 {len(links)} 筆職缺連結到 visited.txt")
