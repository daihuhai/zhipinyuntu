"""测试匹配接口耗时 (首次 + 二次) - 使用 urllib"""
import time
import json
import urllib.request
import urllib.error

BASE = "http://localhost:8001/api/v1"

def post_json(url, body):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_json(url, headers, timeout=300):
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

# 登录 seeker2
d = post_json(f"{BASE}/auth/login", {"account": "seeker2", "password": "123456"})
token = d["data"]["access_token"]
print(f"登录成功, token 长度: {len(token)}")
headers = {"Authorization": f"Bearer {token}"}

resume_id = 1

def show_match_result(label, status, j, elapsed):
    items = (j.get("data") or {}).get("items") or []
    print(f"{label}: HTTP {status}, 耗时: {elapsed:.2f}s, code={j.get('code')}, 返回 {len(items)} 条推荐")
    if items:
        first = items[0]
        print(f"  Top1: score={first.get('total_score')} title={first.get('job',{}).get('title')} reason={(first.get('match_reason') or '')[:50]}")

# 首次匹配
print(f"\n=== 首次匹配 resume_id={resume_id} (含批量 embedding 生成) ===")
t0 = time.time()
try:
    status, j = get_json(f"{BASE}/match/resume/{resume_id}/jobs?top_k=10", headers, timeout=300)
    show_match_result("首次匹配", status, j, time.time()-t0)
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}, 耗时: {time.time()-t0:.2f}s, body={e.read().decode('utf-8')[:300]}")

# 二次匹配
print(f"\n=== 二次匹配 resume_id={resume_id} (embedding 已缓存) ===")
t0 = time.time()
try:
    status, j = get_json(f"{BASE}/match/resume/{resume_id}/jobs?top_k=10", headers, timeout=300)
    show_match_result("二次匹配", status, j, time.time()-t0)
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}, 耗时: {time.time()-t0:.2f}s, body={e.read().decode('utf-8')[:300]}")

# 职位广场 page1
print(f"\n=== 职位广场加载 (page=1 size=12) ===")
t0 = time.time()
try:
    status, j = get_json(f"{BASE}/jobs/plaza?page=1&size=12", headers, timeout=30)
    t1 = time.time()
    print(f"HTTP {status}, 耗时: {t1-t0:.3f}s, total={j['data']['total']}, 返回 {len(j['data']['items'])} 条")
except urllib.error.HTTPError as e:
    t1 = time.time()
    print(f"HTTP {e.code}, 耗时: {t1-t0:.3f}s, body={e.read().decode('utf-8')[:300]}")

# 职位广场 page2
print(f"\n=== 职位广场加载 (page=2 size=12) ===")
t0 = time.time()
try:
    status, j = get_json(f"{BASE}/jobs/plaza?page=2&size=12", headers, timeout=30)
    t1 = time.time()
    print(f"HTTP {status}, 耗时: {t1-t0:.3f}s")
except urllib.error.HTTPError as e:
    t1 = time.time()
    print(f"HTTP {e.code}, 耗时: {t1-t0:.3f}s, body={e.read().decode('utf-8')[:300]}")
