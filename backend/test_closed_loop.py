"""完整闭环测试：parse 极速录入 → deduce 推演 → deviation 偏差自检 → continue 校准推演
模拟真实用户从「用自然语言描述自己」到「记录现实进展后做校准推演」的完整路径
"""
import json, time, httpx

BASE = "http://127.0.0.1:8023"
device = f"closedloop-{int(time.time())}"
H = {"Content-Type": "application/json", "X-Device-Id": device}

STD_PATHS = {"进取突破", "折中改良", "守正待时", "冒险开拓"}
CORE_FIELDS = ["name","age","era","region","familyEconomicCapital","familyCulturalCapital",
    "familySymbolicCapital","skills","personality","mindset","health","financialResources",
    "networkResources","timeResources","toolResources","constraints","externalPressure",
    "unchangeableLimits","shortTermGoal","mediumTermGoal","longTermGoal","keyDecisions","externalChanges"]

def t0(): return time.time()

print("=" * 70)
print("【STEP 1/4】parse 极速录入 — 真实用户自然语言描述")
print("=" * 70)
user_text = ("我是老周，38岁，在广州做外贸跟单，做了12年，最近公司效益不好，"
             "听说可能要裁员。我英语还过得去，手上有积蓄30万，房贷还剩200万要还。"
             "想转行做跨境电商，但又怕没经验做不起来，白搭进去。我性格比较稳，不敢冒险。"
             "家里两个小孩要养，老婆工资一般。")
print(f"用户输入: {user_text}\n")

t = t0()
r = httpx.post(f"{BASE}/api/parse", json={"text": user_text}, headers=H, timeout=120)
print(f"  parse 状态 {r.status_code} | {round(time.time()-t,1)}s")
if r.status_code != 200:
    print(f"  ❌ {r.text[:300]}")
    exit(1)
parse = r.json()
prof = parse.get("profile", {})
pm = parse.get("parseMeta", {})
extracted = pm.get("extractedFields", [])
missing = pm.get("missingFields", [])
ambig = pm.get("ambiguousFields", [])
print(f"  提取字段 ({len(extracted)}): {extracted}")
print(f"  未提及字段 ({len(missing)}): {missing}")
print(f"  存疑字段: {ambig}")

# ---- parse 质量检查 ----
issues = []
nonempty = [k for k,v in prof.items() if str(v).strip() and str(v).strip() != ""]
for k in extracted:
    if k not in prof or not str(prof.get(k,"")).strip():
        issues.append(f"声称提取 {k} 但值为空")
for k in nonempty:
    if k not in extracted:
        issues.append(f"字段 {k} 有值但不在 extractedFields 列表")
# 脑补检查：未提及字段不应有值（era/health/学历等）
for k in missing:
    if str(prof.get(k,"")).strip():
        issues.append(f"未提及字段 {k} 被脑补填值: {prof.get(k)!r}")
# 存疑标记
for k in ambig:
    if "待确认" not in str(prof.get(k,"")):
        issues.append(f"存疑字段 {k} 未带【待确认】标记")
print(f"\n  parse 关键字段值:")
for k in ["name","age","region","skills","personality","financialResources","constraints","shortTermGoal","keyDecisions"]:
    print(f"    {k}: {prof.get(k,'')!r}")

if issues:
    print(f"\n  ⚠️ parse 问题 {len(issues)} 条:")
    for i in issues: print(f"     - {i}")
else:
    print(f"\n  ✅ parse 质量无问题")

print("\n" + "=" * 70)
print("【STEP 2/4】deduce 推演（用 parse 出的档案）")
print("=" * 70)
t = t0()
r = httpx.post(f"{BASE}/api/deduce", json={"profile": prof}, headers=H, timeout=300)
print(f"  deduce 状态 {r.status_code} | {round(time.time()-t,1)}s")
if r.status_code != 200:
    print(f"  ❌ {r.text[:300]}"); exit(1)
report = r.json()
paths = {p.get("name"): p.get("score") for p in report.get("paths", [])}
print(f"  路径: {json.dumps(paths, ensure_ascii=False)}")
print(f"  最佳: {report.get('summary',{}).get('bestPath','')[:60]}")
if set(paths.keys()) != STD_PATHS:
    print(f"  ⚠️ 路径名异常: {list(paths.keys())}")
else:
    print(f"  ✅ 路径名标准4个")

# 提取三条关键预测用于 deviation
best = report.get("summary",{}).get("bestPath","")
maxrisk = report.get("summary",{}).get("maxRisk","")
mind = report.get("summary",{}).get("mindReminder","")
predictions = [best, maxrisk, mind]
print(f"\n  提取的 3 条预测:")
for p in predictions: print(f"    · {p}")

print("\n" + "=" * 70)
print("【STEP 3/4】deviation 偏差自检（对比预测 vs 现实）")
print("=" * 70)
# 模拟 3 个月后现实：公司裁员了，补偿金到手，跨境试水小亏
actual = ("三个月后：公司真的裁员了，老周拿了N+1补偿金约15万。"
          "他尝试做跨境电商，第一批货卖得一般，亏了约2万。"
          "目前靠补偿金和积蓄过渡，还没找到稳定方向，心态有点慌。")
print(f"  现实情况: {actual}\n")
t = t0()
r = httpx.post(f"{BASE}/api/deviation", json={"predictions": predictions, "actualEvents": actual}, headers=H, timeout=120)
print(f"  deviation 状态 {r.status_code} | {round(time.time()-t,1)}s")
if r.status_code != 200:
    print(f"  ❌ {r.text[:300]}"); exit(1)
dev = r.json()
print(f"  准确项: {dev.get('accurate', [])}")
print(f"  偏差项: {dev.get('deviated', [])}")
print(f"  整体分析: {dev.get('analysis', '')}")

print("\n" + "=" * 70)
print("【STEP 4/4】continue 校准推演（档案+报告+偏差+现实）")
print("=" * 70)
t = t0()
r = httpx.post(f"{BASE}/api/continue", json={
    "profile": prof,
    "previousReport": report,
    "deviation": dev,
    "actualEvents": actual,
}, headers=H, timeout=300)
print(f"  continue 状态 {r.status_code} | {round(time.time()-t,1)}s")
if r.status_code != 200:
    print(f"  ❌ {r.text[:300]}"); exit(1)
creport = r.json()
cpaths = {p.get("name"): p.get("score") for p in creport.get("paths", [])}
print(f"  校准后路径: {json.dumps(cpaths, ensure_ascii=False)}")
print(f"  校准后最佳: {creport.get('summary',{}).get('bestPath','')[:60]}")

# ---- continue 质量检查 ----
cissues = []
if set(cpaths.keys()) != STD_PATHS:
    cissues.append(f"校准后路径名异常: {list(cpaths.keys())}")
else:
    print(f"\n  ✅ 校准后路径名仍标准4个（归一化生效）")
# 评分变化方向：现实是"裁员+跨境小亏"，进取/冒险应下调，守正/折中应相对上调
if paths and cpaths:
    print(f"\n  评分变化对比:")
    for nm in STD_PATHS:
        old = paths.get(nm, "?")
        new = cpaths.get(nm, "?")
        delta = ""
        if isinstance(old,(int,float)) and isinstance(new,(int,float)):
            delta = f"({'↑' if new>old else '↓' if new<old else '='}{abs(round(new-old,1))})"
        print(f"    {nm}: {old} → {new} {delta}")
    # 冒险开拓应下调（现实证明跨境试水亏了）
    if isinstance(paths.get("冒险开拓"),(int,float)) and isinstance(cpaths.get("冒险开拓"),(int,float)):
        if cpaths["冒险开拓"] <= paths["冒险开拓"]:
            print(f"  ✅ 冒险开拓下调（现实验证跨境风险）")
        else:
            cissues.append(f"冒险开拓不降反升（现实已证明跨境亏钱）")

print(f"\n{'='*70}\n闭环测试完成")
print(f"parse 问题: {len(issues)} 条 | continue 问题: {len(cissues)} 条")
if issues or cissues:
    print("⚠️ 有问题需处理")
else:
    print("✅ 全链路无问题")
