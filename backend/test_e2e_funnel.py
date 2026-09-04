"""单次端到端验证 — 程序员档案，确认漏斗统计回传 + 耗时 + reportId"""
import json, time, httpx

BASE = "http://127.0.0.1:8023"
profile = {
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
    "externalChanges": "AI 辅助编程冲击",
}

t0 = time.time()
r = httpx.post(f"{BASE}/api/deduce", json={"profile": profile, "industry": "科技互联网"}, timeout=300)
dt = time.time() - t0
print(f"状态: {r.status_code} | 耗时: {round(dt,1)}s")
d = r.json()
print(f"reportId: {d.get('reportId')}")
print(f"路径数: {len(d.get('paths', []))}")
meta = d.get("meta", {})
print(f"一致系数: {meta.get('consistencyCoefficient')} | 完整度: {meta.get('completenessScore')}%")
print(f"\n=== 漏斗统计 funnelStats ===")
print(json.dumps(meta.get("funnelStats", {}), ensure_ascii=False, indent=2))
