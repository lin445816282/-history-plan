"""挑「医生」职业做一次完整推演，展示报告全貌"""
import json, time, httpx

BASE = "http://127.0.0.1:8023"
profile = {
    "name": "林峰", "age": 35, "era": "医疗改革期，集采压缩利润，公立医院改制，医生多点执业放开",
    "region": "杭州",
    "familyEconomicCapital": "父母普通职工，无大额资助，靠工资攒了首付",
    "familyCulturalCapital": "临床医学硕士，导师是省内外科专家",
    "familySymbolicCapital": "无医疗世家背景，靠自己技术立足",
    "skills": "外科手术熟练（主刀8年）、有固定患者口碑、带教经验",
    "personality": "严谨、责任心强、有点保守",
    "mindset": "纠结：继续熬资历评副高，还是跳出体制开诊所搏一把",
    "health": "亚健康，长期手术站立腰椎劳损",
    "financialResources": "存款60万，房贷月供8000",
    "networkResources": "导师人脉、几个想合伙的同事、药企同学",
    "timeResources": "手术排期满，业余时间少",
    "toolResources": "手术技术、公立平台、执业资质",
    "constraints": "公立晋升论资排辈、科研论文压力、医患关系风险",
    "externalPressure": "集采降价、DRG控费、公立医院绩效改革",
    "unchangeableLimits": "非博士学历、非顶尖三甲出身",
    "shortTermGoal": "两年内评上副主任医师",
    "mediumTermGoal": "五年内实现执业自由度",
    "longTermGoal": "拥有自己的诊所或高端医疗品牌",
    "keyDecisions": "是否接受私立医院高薪挖角，还是留公立熬副高",
    "externalChanges": "多点执业政策放开、社会办医资本涌入",
}

t0 = time.time()
r = httpx.post(f"{BASE}/api/deduce", json={"profile": profile}, timeout=300)
dt = time.time() - t0
print(f"状态 {r.status_code} | 耗时 {round(dt,1)}s | reportId {r.json().get('reportId')}\n")

d = r.json()
meta = d.get("meta", {})
print(f"行业识别: {meta.get('detectedIndustry')} | 一致系数: {meta.get('consistencyCoefficient')} | 完整度: {meta.get('completenessScore')}%")
print(f"漏斗: {json.dumps(meta.get('funnelStats',{}), ensure_ascii=False)}\n")

s = d.get("summary", {})
print("=" * 50)
print("📋 一分钟速览")
for k in ("bestPath", "maxRisk", "topAction", "credibilityReason", "mindReminder"):
    if s.get(k): print(f"  {s[k]}")

print("\n" + "=" * 50)
print("🏛️ 历史对标")
hb = d.get("macroAnalysis", {}).get("historicalBenchmark", {})
for f in hb.get("ancientFigures", [])[:3]:
    print(f"  【古代】{f.get('name')}：{f.get('transformationPrinciple','')}")
for f in hb.get("modernFigures", [])[:3]:
    print(f"  【现代】{f.get('name')}（{f.get('industry','')}）：{f.get('principle','')}")
if hb.get("commonPrinciples"): print(f"  共性事理：{hb['commonPrinciples']}")

print("\n" + "=" * 50)
print("🛤️ 发展路径")
for p in d.get("paths", []):
    ci = p.get("scoreCI", {})
    print(f"  {p.get('name')}  评分 {p.get('score')} [CI {ci.get('lower')}~{ci.get('upper')}]  转换成本:{p.get('switchCost')}")
    print(f"    优势: {str(p.get('advantages',''))[:60]}")
    print(f"    历史翻车: {str(p.get('historicalRisk',''))[:50]}")

print("\n" + "=" * 50)
print("⚠️ 风险分析")
ra = d.get("riskAnalysis", {})
for w in ra.get("warnings", [])[:4]:
    print(f"  预警: {str(w)[:70]}")
if ra.get("sensitivity"): print(f"  敏感变量: {str(ra.get('sensitivity'))[:80]}")

# 打印完整 JSON 到文件备查
json.dump(d, open("/tmp/doctor_report.json", "w"), ensure_ascii=False, indent=2)
print("\n完整报告已存 /tmp/doctor_report.json")
