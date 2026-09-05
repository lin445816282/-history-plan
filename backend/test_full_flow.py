"""完整流程端到端测试：免费3次额度 + 每次添加条件验证推演结果变化"""
import json, time, httpx

BASE = "http://127.0.0.1:8023"
DEVICE = f"e2e-flow-{int(time.time())}"  # 全新 deviceId，免费3次从头开始
headers = {"Content-Type": "application/json", "X-Device-Id": DEVICE}

# 初始档案（医生）
base_profile = {
    "name": "林峰", "age": 35, "era": "医疗改革期，集采压缩利润，公立医院改制",
    "region": "杭州",
    "familyEconomicCapital": "父母普通职工", "familyCulturalCapital": "临床医学硕士",
    "familySymbolicCapital": "无医疗世家背景",
    "skills": "外科手术熟练(主刀8年)、有固定患者口碑",
    "personality": "严谨、责任心强、有点保守",
    "mindset": "纠结：继续熬资历评副高，还是跳出体制开诊所",
    "health": "良好",
    "financialResources": "存款60万，房贷月供8000",
    "networkResources": "导师人脉、几个想合伙的同事",
    "timeResources": "手术排期满", "toolResources": "手术技术、公立平台",
    "constraints": "公立晋升论资排辈、科研论文压力",
    "externalPressure": "集采降价、DRG控费",
    "unchangeableLimits": "非博士学历",
    "shortTermGoal": "两年内评上副主任医师", "mediumTermGoal": "实现执业自由度",
    "longTermGoal": "拥有自己的诊所或高端医疗品牌",
    "keyDecisions": "是否接受私立医院高薪挖角",
    "externalChanges": "多点执业政策放开",
}

results = []

def deduce(tag, profile):
    t0 = time.time()
    r = httpx.post(f"{BASE}/api/deduce", json={"profile": profile}, headers=headers, timeout=300)
    dt = time.time() - t0
    if r.status_code != 200:
        print(f"\n【{tag}】状态 {r.status_code} | 耗时 {round(dt,1)}s")
        print(f"  响应: {r.text[:120]}")
        results.append({"tag": tag, "status": r.status_code, "paths": None})
        return None
    d = r.json()
    paths = {p.get('name'): p.get('score') for p in d.get('paths', [])}
    best = d.get('summary', {}).get('bestPath', '')
    print(f"\n【{tag}】状态200 | 耗时 {round(dt,1)}s | reportId {d.get('reportId')}")
    print(f"  最佳路径: {best}")
    print(f"  路径评分: {json.dumps(paths, ensure_ascii=False)}")
    results.append({"tag": tag, "status": 200, "paths": paths})
    return d

# 查询初始额度
credits = httpx.get(f"{BASE}/api/credits", headers=headers).json()
print(f"🔑 初始额度: 免费 {credits['freeRemaining']}/{credits['freeTotal']}")

# 第1次：初始档案
d1 = deduce("第1次·初始档案", base_profile)

# 第2次：添加条件1（副高落选 + 私立offer + 腰椎确诊）
p2 = {**base_profile,
      "mindset": "副高落选后认真考虑私立医院机会",
      "health": "腰椎确诊椎间盘突出，需注意",
      "financialResources": "存款72万",
      "keyDecisions": "私立医院开出年薪翻倍offer，是否接受",
      "shortTermGoal": "半年内明确去留"}
d2 = deduce("第2次·加条件1(副高落选+私立offer+腰椎)", p2)

# 第3次：添加条件2（合伙人退出 + 政策收紧 + 腰椎恶化）
p3 = {**p2,
      "health": "腰椎恶化，医生建议手术",
      "networkResources": "合伙人临时退出，人脉收缩",
      "externalPressure": "集采扩大、社会办医政策收紧",
      "keyDecisions": "合伙人退出后是否独自开诊所"}
d3 = deduce("第3次·加条件2(合伙人退出+政策收紧+腰椎恶化)", p3)

# 第4次：验证免费额度耗尽 → 402
d4 = deduce("第4次·验证免费额度耗尽", p3)

# 额度最终状态
credits2 = httpx.get(f"{BASE}/api/credits", headers=headers).json()
print(f"\n🔑 最终额度: 免费剩余 {credits2['freeRemaining']} / 总计 {credits2['totalRemaining']}")

# 路径评分变化对比
print("\n" + "=" * 60)
print("📊 路径评分变化对比（同名路径跨次对比）")
all_names = []
for r in results:
    if r['paths']:
        all_names.extend(r['paths'].keys())
names = list(dict.fromkeys(all_names))  # 去重保序
print(f"{'路径':<12}", end='')
for r in results:
    print(f"{r['tag'].split('·')[0]:>14}", end='')
print()
for name in names:
    print(f"{name:<12}", end='')
    for r in results:
        s = r['paths'].get(name) if r['paths'] else ('402' if r['status'] == 402 else str(r['status']))
        print(f"{str(s):>14}", end='')
    print()

print("\n✅ 流程跑完")
