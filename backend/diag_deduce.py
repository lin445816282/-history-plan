"""诊断前两个推演 0.1s 异常 — 检查是否 SimHash 缓存误命中"""
import json, time, httpx

BASE = "http://127.0.0.1:8023"

p1 = {
    "name": "张伟", "age": 32, "era": "现代", "region": "深圳",
    "familyEconomicCapital": "父母工薪，无额外资助",
    "familyCulturalCapital": "普通本科",
    "familySymbolicCapital": "无背景",
    "skills": "Java/Go 后端、系统设计、带过5人小组",
    "personality": "踏实肯干、抗压",
    "mindset": "想从纯技术转管理，但担心技术荒废",
    "health": "良好",
    "financialResources": "存款40万",
    "networkResources": "前同事人脉一般",
    "timeResources": "可投入业余时间学习管理",
    "toolResources": "电脑、在线课程",
    "constraints": "35岁危机焦虑",
    "externalPressure": "大厂裁员潮",
    "unchangeableLimits": "非名校出身",
    "shortTermGoal": "一年内晋升技术经理",
    "mediumTermGoal": "三年内站稳中层",
    "longTermGoal": "技术+管理复合型负责人",
    "keyDecisions": "是否接受晋升 offer 放弃编码",
    "externalChanges": "AI 辅助编程冲击"
}

def deduce(profile, industry, tag):
    t0 = time.time()
    r = httpx.post(f"{BASE}/api/deduce", json={"profile": profile, "industry": industry}, timeout=300)
    dt = time.time() - t0
    d = r.json()
    meta = d.get("meta", {})
    print(f"[{tag}] 状态={r.status_code} 耗时={dt:.2f}s")
    print(f"  completeness={meta.get('completenessScore')}")
    print(f"  reusedFromSimilar={meta.get('reusedFromSimilar', False)}")
    print(f"  consistency={meta.get('consistencyCoefficient')}")
    print(f"  detectedIndustry={meta.get('detectedIndustry')}")
    print(f"  reportId={d.get('reportId', 'N/A')}")
    print(f"  bestPath={json.dumps(d.get('summary',{}), ensure_ascii=False)[:100]}")
    return d

print("=== 第一次推演（程序员）===")
d1 = deduce(p1, "科技互联网", "第1次")

print("\n=== 等3秒后第二次推演（同一档案，应命中缓存）===")
time.sleep(3)
d2 = deduce(p1, "科技互联网", "第2次")

# 检查两次是否同一 reportId
print(f"\n两次 reportId 相同: {d1.get('reportId') == d2.get('reportId')}")
print(f"第2次 meta.reusedFromSimilar = {d2.get('meta',{}).get('reusedFromSimilar')}")
