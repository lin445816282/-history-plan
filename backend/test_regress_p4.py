"""P4 回归：验证评分差异化约束后 E2/E3 是否不再偏向折中"""
import json, time, httpx

BASE = "http://127.0.0.1:8023"

def full(overrides):
    base = {
        "name": "测试", "age": 30, "era": "平稳期", "region": "杭州",
        "familyEconomicCapital": "普通家庭", "familyCulturalCapital": "本科",
        "familySymbolicCapital": "无", "skills": "通用技能",
        "personality": "中性", "mindset": "未定",
        "health": "良好", "financialResources": "存款50万",
        "networkResources": "一般", "timeResources": "充裕", "toolResources": "一般",
        "constraints": "无", "externalPressure": "无",
        "unchangeableLimits": "无", "shortTermGoal": "待定",
        "mediumTermGoal": "待定", "longTermGoal": "待定",
        "keyDecisions": "待定", "externalChanges": "无",
    }
    base.update(overrides)
    return base

scenarios = [
    {"id": "E2-24岁敢闯", "expect": "进取突破/冒险开拓", "profile": full({
        "name": "阿杰", "age": 24, "era": "行业风口期",
        "mindset": "年轻就是本钱，失败了大不了重来，最怕错过窗口",
        "personality": "敢闯敢拼、精力旺盛",
        "financialResources": "无存款但无负债，父母可兜底",
        "unchangeableLimits": "无家庭负担",
        "shortTermGoal": "三年内做出名堂", "longTermGoal": "财务自由",
        "keyDecisions": "裸辞全职创业还是边上班边试",
    })},
    {"id": "E3-富二代有产业", "expect": "冒险开拓", "profile": full({
        "name": "家豪", "age": 30, "era": "家族产业转型期",
        "mindset": "不缺钱，缺的是证明自己的机会，想干票大的",
        "personality": "自信、敢下重注",
        "financialResources": "家族产业现金流，可动用资金千万级",
        "networkResources": "家族人脉深厚", "familyEconomicCapital": "家族企业",
        "shortTermGoal": "开辟新赛道", "longTermGoal": "超越父辈成就",
        "keyDecisions": "是否大举投入新业务",
    })},
]

for sc in scenarios:
    device = f"regp4-{int(time.time()*1000)}"
    h = {"Content-Type": "application/json", "X-Device-Id": device}
    r = httpx.post(f"{BASE}/api/deduce", json={"profile": sc["profile"]}, headers=h, timeout=300)
    d = r.json()
    paths = {p.get("name"): p.get("score") for p in d.get("paths", [])}
    best = max(paths, key=lambda k: paths[k])
    ranked = " > ".join(f"{k}({v})" for k, v in sorted(paths.items(), key=lambda x: -x[1]))
    mark = "✅" if best in sc["expect"].split("/") else "❌仍偏向"
    print(f"[{sc['id']}] 期望={sc['expect']} 实际={best} {mark}")
    print(f"    {ranked}")
    time.sleep(1)
