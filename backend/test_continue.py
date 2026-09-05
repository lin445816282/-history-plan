"""测试 /api/continue 持仓式增量再推演 — 医生档案模拟「持仓一段时间后」"""
import json, time, httpx

BASE = "http://127.0.0.1:8023"

# 上次推演报告（用之前存的医生报告）
prev = json.load(open("/tmp/doctor_report.json"))
# 精简注入：只取关键部分，模拟前端传完整报告
prev_report = prev

profile = {
    "name": "林峰", "age": 36, "era": "医疗改革深化，集采扩大，DRG控费全面落地，社会办医政策回暖",
    "region": "杭州",
    "familyEconomicCapital": "父母普通职工",
    "familyCulturalCapital": "临床医学硕士，导师是省内外科专家",
    "familySymbolicCapital": "无医疗世家背景",
    "skills": "外科手术熟练（主刀9年）、有固定患者口碑、带教经验",
    "personality": "严谨、责任心强、开始松动保守心态",
    "mindset": "副高落选后开始认真考虑私立医院机会",
    "health": "腰椎劳损加重，已确诊椎间盘突出",
    "financialResources": "存款72万，房贷月供8000",
    "networkResources": "导师人脉、两个想合伙的同事、一家私立医院已发offer",
    "timeResources": "手术排期满，业余时间少",
    "toolResources": "手术技术、公立平台、执业资质",
    "constraints": "公立晋升受阻、科研论文压力、腰椎健康告急",
    "externalPressure": "DRG控费、集采降价、公立绩效改革",
    "unchangeableLimits": "非博士学历",
    "shortTermGoal": "半年内明确去留",
    "mediumTermGoal": "实现执业自由度与健康平衡",
    "longTermGoal": "拥有自己的诊所或高端医疗品牌",
    "keyDecisions": "是否接受私立医院高薪挖角",
    "externalChanges": "多点执业放开、私立医院扩张",
}

# 偏差复盘结果（模拟：上次预测部分准、部分偏）
deviation = {
    "accurate": ["最佳路径折中改良风险较低", "腰椎问题是重要风险点"],
    "deviated": [
        {"item": "两年内评上副主任医师", "reason": "外部变局冲击"},
        {"item": "折中改良路径被低估", "reason": "模型推理局限"},
    ],
    "analysis": "体制内晋升比预期更慢，私立市场窗口比预期更早打开，健康约束被低估。",
}

# 现实进展
actual = "副高落选；私立医院开出年薪翻倍offer；腰椎确诊椎间盘突出；两个同事愿意合伙。"

t0 = time.time()
r = httpx.post(f"{BASE}/api/continue", json={
    "profile": profile, "previousReport": prev_report,
    "deviation": deviation, "actualEvents": actual,
}, timeout=300)
dt = time.time() - t0
print(f"状态 {r.status_code} | 耗时 {round(dt,1)}s")

if r.status_code != 200:
    print(f"⚠️ {r.text[:300]}")
else:
    d = r.json()
    meta = d.get("meta", {})
    print(f"reportId {d.get('reportId')} | 校准自: {meta.get('continueFrom')}")
    print(f"行业: {meta.get('detectedIndustry')} | 一致系数: {meta.get('consistencyCoefficient')} | 完整度: {meta.get('completenessScore')}%")

    s = d.get("summary", {})
    print("\n📋 一分钟速览")
    for k in ("bestPath", "maxRisk", "topAction", "mindReminder"):
        if s.get(k): print(f"  {s[k]}")

    print("\n🛤️ 路径（对比上次）")
    prev_paths = {p.get("name"): p.get("score") for p in prev.get("paths", [])}
    for p in d.get("paths", []):
        n = p.get("name")
        old = prev_paths.get(n, "—")
        ci = p.get("scoreCI", {})
        arrow = "↑" if old != "—" and p.get("score", 0) > old else ("↓" if old != "—" and p.get("score", 0) < old else "→")
        print(f"  {n}  上次{old} → 本次{p.get('score')} {arrow} [CI {ci.get('lower')}~{ci.get('upper')}]")

    print("\n⚠️ 风险预警")
    for w in d.get("riskAnalysis", {}).get("warnings", [])[:4]:
        print(f"  {str(w)[:70]}")

    json.dump(d, open("/tmp/doctor_continue_report.json", "w"), ensure_ascii=False, indent=2)
    print("\n完整报告已存 /tmp/doctor_continue_report.json")
