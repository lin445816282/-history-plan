"""挑「自媒体创作者」职业推演"""
import json, time, httpx

BASE = "http://127.0.0.1:8023"
profile = {
    "name": "苏晓", "age": 27, "era": "短视频红利期，内容创业风口，AI 重塑内容生产，平台流量补贴退坡",
    "region": "成都",
    "familyEconomicCapital": "普通工薪家庭，无额外资助",
    "familyCulturalCapital": "普通二本文科",
    "familySymbolicCapital": "无资源背景",
    "skills": "文案写作、视频剪辑、账号运营，已有3万粉丝",
    "personality": "表达欲强、行动力强、但容易流量焦虑",
    "mindset": "纠结：辞职全职做内容，还是保住工作兼职过渡",
    "health": "良好，但长期熬夜剪辑",
    "financialResources": "存款15万，可支撑1年半无收入",
    "networkResources": "几个同赛道创作者朋友、一个MCN伸过橄榄枝",
    "timeResources": "下班后4小时，周末全天",
    "toolResources": "剪辑设备、AI辅助工具、拍摄器材",
    "constraints": "收入不稳定、流量焦虑、内容同质化竞争",
    "externalPressure": "平台算法多变、补贴退坡、行业洗牌",
    "unchangeableLimits": "非科班、无团队",
    "shortTermGoal": "一年内涨粉到10万",
    "mediumTermGoal": "建立稳定个人IP与多元变现",
    "longTermGoal": "内容创业，拥有自己的内容品牌或工作室",
    "keyDecisions": "是否接受MCN签约，还是坚持独立运营",
    "externalChanges": "AI 内容生成冲击、平台商业化规则变化",
}

t0 = time.time()
r = httpx.post(f"{BASE}/api/deduce", json={"profile": profile}, timeout=300)
dt = time.time() - t0
print(f"状态 {r.status_code} | 耗时 {round(dt,1)}s | reportId {r.json().get('reportId')}\n")

d = r.json()
meta = d.get("meta", {})
print(f"行业识别: {meta.get('detectedIndustry')} | 一致系数: {meta.get('consistencyCoefficient')} | 完整度: {meta.get('completenessScore')}%")
fs = meta.get("funnelStats", {})
print(f"漏斗: 641→{fs.get('finalTotal')} | 世道:{fs.get('worldTagDetected')} | 原型:{fs.get('prototypesDetected')}")

s = d.get("summary", {})
print("\n" + "=" * 50)
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
    print(f"    优势: {str(p.get('advantages',''))[:55]}")
    print(f"    历史翻车: {str(p.get('historicalRisk',''))[:48]}")

print("\n" + "=" * 50)
print("⚠️ 风险分析")
ra = d.get("riskAnalysis", {})
for w in ra.get("warnings", [])[:4]:
    print(f"  预警: {str(w)[:70]}")
if ra.get("sensitivity"): print(f"  敏感变量: {str(ra.get('sensitivity'))[:80]}")

json.dump(d, open("/tmp/creator_report.json", "w"), ensure_ascii=False, indent=2)
print("\n完整报告已存 /tmp/creator_report.json")
