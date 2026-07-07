"""测试 LLM 并发调用是否生效"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.ai.ark_client import ark_client
from app.ai.prompts import build_rerank_messages
import json

resume_json = json.dumps({"name":"测试","education":"硕士","skills":[{"name":"Java","level":"熟练"}]}, ensure_ascii=False)
job_json = json.dumps({"title":"Java工程师","requirements":[{"name":"Java","type":"必须"}]}, ensure_ascii=False)

def call_once(i):
    t0 = time.time()
    messages = build_rerank_messages(resume_json=resume_json, job_json=job_json)
    r = ark_client.chat_json(messages, temperature=0.1)
    return i, time.time()-t0, r.get("score")

# 串行 3 次
print("=== 串行调用 3 次 ===")
t0 = time.time()
for i in range(3):
    _, dt, score = call_once(i)
    print(f"  #{i}: {dt:.2f}s score={score}")
print(f"串行总耗时: {time.time()-t0:.2f}s")

# 并发 10 次
print("\n=== 并发调用 10 次 (max_workers=8) ===")
t0 = time.time()
with ThreadPoolExecutor(max_workers=8) as ex:
    futures = [ex.submit(call_once, i) for i in range(10)]
    for f in as_completed(futures):
        i, dt, score = f.result()
        print(f"  #{i}: {dt:.2f}s score={score}")
print(f"并发总耗时: {time.time()-t0:.2f}s")
