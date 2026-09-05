"""端到端验证 deviceId 隔离 — 两个 deviceId 用相同档案推演，验证不互相命中缓存"""
import json, time, httpx

BASE = "http://127.0.0.1:8023"
profile = {
    "name": "隔离测试员", "age": 30, "era": "互联网转型期，AI风口",
    "skills": "编程、架构", "personality": "务实", "mindset": "想创业",
    "health": "良好", "financialResources": "存款50万", "networkResources": "人脉一般",
    "timeResources": "时间充裕", "toolResources": "电脑", "constraints": "内卷裁员",
    "externalPressure": "竞争激烈", "unchangeableLimits": "非名校",
    "shortTermGoal": "一年内晋升", "mediumTermGoal": "站稳中层", "longTermGoal": "复合型负责人",
    "keyDecisions": "是否转管理", "externalChanges": "AI冲击",
    "familyEconomicCapital": "工薪", "familyCulturalCapital": "本科", "familySymbolicCapital": "无",
}

headers_a = {"Content-Type": "application/json", "X-Device-Id": "e2e-user-A"}
headers_b = {"Content-Type": "application/json", "X-Device-Id": "e2e-user-B"}

# 用户A推演（存缓存）
t0 = time.time()
r_a = httpx.post(f"{BASE}/api/deduce", json={"profile": profile}, headers=headers_a, timeout=300)
print(f"用户A: {r_a.status_code} | 耗时 {round(time.time()-t0,1)}s | reportId {r_a.json().get('reportId')}")
print(f"  reusedFromSimilar: {r_a.json().get('meta',{}).get('reusedFromSimilar', False)}")

# 用户B推演相同档案（隔离生效则不应复用A的缓存，重新推演）
t0 = time.time()
r_b = httpx.post(f"{BASE}/api/deduce", json={"profile": profile}, headers=headers_b, timeout=300)
print(f"用户B: {r_b.status_code} | 耗时 {round(time.time()-t0,1)}s | reportId {r_b.json().get('reportId')}")
reused_b = r_b.json().get('meta', {}).get('reusedFromSimilar', False)
print(f"  reusedFromSimilar: {reused_b}")

# 用户A再次推演相同档案（应命中自己的缓存，很快）
t0 = time.time()
r_a2 = httpx.post(f"{BASE}/api/deduce", json={"profile": profile}, headers=headers_a, timeout=300)
print(f"用户A二次: {r_a2.status_code} | 耗时 {round(time.time()-t0,1)}s | reportId {r_a2.json().get('reportId')}")
print(f"  reusedFromSimilar: {r_a2.json().get('meta',{}).get('reusedFromSimilar', False)}")

print("\n判定：")
print(f"  {'✅' if not reused_b else '❌'} 用户B未复用A缓存（隔离生效）")
print(f"  {'✅' if r_a2.json().get('meta',{}).get('reusedFromSimilar') else '⚠️'} 用户A二次命中自己缓存")
