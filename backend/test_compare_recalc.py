"""测试 compare（二选一对比）+ recalc（参数微调重算）两个端点"""
import json, time, httpx

BASE = "http://127.0.0.1:8023"
device = f"cr-{int(time.time())}"
H = {"Content-Type": "application/json", "X-Device-Id": device}

print("=" * 70)
print("【compare】二选一对比 — 应届生考研 vs 就业")
print("=" * 70)
profile = {
    "name": "林小雨", "age": 22, "era": "就业严峻，考公热", "region": "武汉",
    "familyEconomicCapital": "普通工薪，能支持考研一年", "familyCulturalCapital": "父母高中学历",
    "skills": "新闻传播专业，写作尚可", "personality": "温和，缺社会经验",
    "mindset": "迷茫", "financialResources": "无积蓄，家庭支持一年",
    "shortTermGoal": "确定方向", "mediumTermGoal": "上岸或入行", "longTermGoal": "经济独立",
    "keyDecisions": "全职备考还是先就业",
}
t = time.time()
r = httpx.post(f"{BASE}/api/compare", json={
    "profile": profile,
    "optionA": "考研深造（新闻传播硕士）",
    "optionB": "直接就业（进新媒体行业）",
}, headers=H, timeout=120)
print(f"  compare 状态 {r.status_code} | {round(time.time()-t,1)}s")
if r.status_code != 200:
    print(f"  ❌ {r.text[:300]}"); exit(1)
cmp = r.json()
opts = cmp.get("options", [])
issues = []
if len(opts) != 2:
    issues.append(f"选项数 {len(opts)} != 2")
for o in opts:
    print(f"  [{o.get('name')}] {o.get('score')}分")
    print(f"    优势: {o.get('pros', [])}")
    print(f"    劣势: {o.get('cons', [])}")
    print(f"    风险: {o.get('risk', '')}")
    if not o.get("pros") or not o.get("cons"):
        issues.append(f"{o.get('name')} 缺 pros/cons")
    sc = o.get("score")
    if not isinstance(sc,(int,float)) or not 0<=sc<=10:
        issues.append(f"{o.get('name')} 评分越界 {sc}")
print(f"  推荐: {cmp.get('recommendation', '')}")
print(f"  核心差异: {cmp.get('keyDifference', '')}")
print(f"  {'✅ compare 无问题' if not issues else '⚠️ '+str(issues)}")

print("\n" + "=" * 70)
print("【recalc】参数微调 — 程序员存款翻倍（90万→180万）")
print("=" * 70)
# 先 deduce 拿 paths
t = time.time()
r = httpx.post(f"{BASE}/api/deduce", json={"profile": {
    "name": "陈宇", "age": 35, "era": "互联网寒冬", "region": "深圳",
    "familyEconomicCapital": "父母退休职工", "familyCulturalCapital": "普通本科",
    "skills": "前端8年带团队", "personality": "技术执着", "mindset": "被裁焦虑",
    "health": "颈椎病", "financialResources": "存款90万，房贷月供1.2万",
    "networkResources": "前同事内推", "timeResources": "失业期充裕", "toolResources": "技术能力",
    "constraints": "35岁门槛", "externalPressure": "行业下行", "unchangeableLimits": "非名校",
    "shortTermGoal": "半年找方向", "mediumTermGoal": "稳定现金流", "longTermGoal": "财务自由",
    "keyDecisions": "是否接受降薪offer", "externalChanges": "AI工具爆发",
}}, headers=H, timeout=300)
if r.status_code != 200:
    print(f"  deduce 失败 {r.text[:200]}"); exit(1)
report = r.json()
paths_in = [{"name": p.get("name"), "score": p.get("score")} for p in report.get("paths", [])]
print(f"  原始路径: {json.dumps(paths_in, ensure_ascii=False)}")

# recalc：存款翻倍（+100%）
t = time.time()
r = httpx.post(f"{BASE}/api/recalc", json={
    "profile": report.get("profile") if isinstance(report.get("profile"), dict) else {
        "financialResources": "存款90万", "networkResources": "前同事内推",
        "timeResources": "失业期充裕", "toolResources": "技术能力"},
    "paths": paths_in,
    "adjustments": [{"field": "financialResources", "label": "资金储备", "delta": 0.5}],
}, headers=H, timeout=120)
print(f"  recalc 状态 {r.status_code} | {round(time.time()-t,1)}s")
if r.status_code != 200:
    print(f"  ❌ {r.text[:300]}"); exit(1)
rc = r.json()
rpaths = rc.get("paths", [])
print(f"  风险更新: {rc.get('riskUpdates', [])}")
print(f"  总结: {rc.get('summary', '')}")
print(f"\n  重算结果:")
rissues = []
in_map = {p["name"]: p["score"] for p in paths_in}
for p in rpaths:
    nm = p.get("name")
    orig, new, delta = p.get("originalScore"), p.get("newScore"), p.get("delta")
    reason = p.get("reason", "")
    print(f"    {nm}: {orig} → {new} (delta {delta}) {reason}")
    # originalScore 应等于输入
    if nm in in_map and abs(orig - in_map[nm]) > 0.05:
        rissues.append(f"{nm} originalScore {orig} 与输入 {in_map[nm]} 不符")
    # delta = new - orig
    if abs((new - orig) - delta) > 0.05:
        rissues.append(f"{nm} delta {delta} != new-orig {round(new-orig,1)}")
# 方向检查：资金+100%，需要资金启动的"进取突破/冒险开拓"应上调或持平（不应下调）
for p in rpaths:
    nm = p.get("name")
    if nm in ("进取突破", "冒险开拓") and p.get("delta", 0) < 0:
        rissues.append(f"{nm} 资金翻倍反而下调 delta={p.get('delta')}（方向反了）")
print(f"\n  {'✅ recalc 无问题' if not rissues else '⚠️ '+str(rissues)}")

print(f"\n{'='*70}\ncompare 问题 {len(issues)} 条 | recalc 问题 {len(rissues)} 条")
