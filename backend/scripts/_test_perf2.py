"""连续性能测试 - 排除冷启动"""
import time
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8001/api/v1"

def post_json(url, body):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_json(url, headers, timeout=300):
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

d = post_json(f"{BASE}/auth/login", {"account": "seeker2", "password": "123456"})
token = d["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 职位广场连续 5 次 (排除冷启动)
print("=== 职位广场连续 5 次 ===")
for i in range(5):
    t0 = time.time()
    status, j = get_json(f"{BASE}/jobs/plaza?page=1&size=12", headers, timeout=30)
    print(f"  #{i+1}: {time.time()-t0:.3f}s")

# 匹配 (RERANK_TOP_N=4, 带缓存)
print("\n=== 匹配 resume_id=1 (Top4 批量精排+缓存) ===")
for i in range(3):
    t0 = time.time()
    try:
        status, j = get_json(f"{BASE}/match/resume/1/jobs?top_k=10", headers, timeout=120)
        items = (j.get("data") or {}).get("items") or []
        print(f"  #{i+1}: {time.time()-t0:.2f}s, 返回 {len(items)} 条")
        if items:
            print(f"    Top1: {items[0].get('total_score')} {items[0].get('job',{}).get('title')}")
    except urllib.error.HTTPError as e:
        print(f"  #{i+1}: HTTP {e.code} {time.time()-t0:.2f}s")
