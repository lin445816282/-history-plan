"""回归验证：P2 一致性等级 + P3 信息不全评分保守"""
import json, time, httpx

BASE = "http://127.0.0.1:8023"

def deduce(tag, profile):
    device = f"regress-{int(time.time()*1000)}"
    h = {"Content-Type": "application/json", "X-Device-Id": device}
    t0 = time.time()
    r = httpx.post(f"{BASE}/api/deduce", json={"profile": profile}, headers=h, timeout=300)
    dt = round(time.time()-t0, 1)
    print(f"\n{'='*60}\n[{tag}] {r.status_code} | {dt}s")
    if r.status_code != 200:
        print(f"  {r.text[:200]}")
        return
    d = r.json()
    m = d.get("meta", {})
    print(f"  完整度 {m.get('completenessScore')} | 可信度 {m.get('credibilityRating')} | 一致性 {m.get('consistencyCoefficient')!r}")
    if m.get("credibilityWarning"):
        print(f"  警告: {m['credibilityWarning']}")
    print(f"  摘要可信度: {d.get('summary', {}).get('credibilityReason', '')[:80]}")
    for p in d.get("paths", []):
        ci = p.get("scoreCI", {})
        print(f"    {p.get('name')}: {p.get('score')}  CI[{ci.get('lower')}-{ci.get('upper')}]")

# P2 + P3：极简档案（完整度低，验证评分保守 + CI 加宽 + 一致性默认"中"不触发）
deduce("P3-极简档案", {
    "name": "张伟", "age": 30, "era": "", "region": "",
    "skills": "", "mindset": "想换个活法，但没想清楚",
})

# P2：完整档案（完整度100%，触发一致性，验证返回"高/中/低"字符串）
deduce("P2-完整档案", {
    "name": "陈宇", "age": 35, "era": "互联网寒冬", "region": "深圳",
    "familyEconomicCapital": "父母退休职工", "familyCulturalCapital": "普通本科",
    "familySymbolicCapital": "无", "skills": "前端8年带团队",
    "personality": "技术执着", "mindset": "被裁后焦虑",
    "health": "颈椎病", "financialResources": "存款90万房贷1.2万",
    "networkResources": "前同事内推", "timeResources": "失业期充裕", "toolResources": "技术能力",
    "constraints": "35岁门槛", "externalPressure": "行业下行",
    "unchangeableLimits": "非名校", "shortTermGoal": "半年找方向",
    "mediumTermGoal": "稳定现金流", "longTermGoal": "财务自由",
    "keyDecisions": "是否接受降薪offer", "externalChanges": "AI工具爆发",
})
