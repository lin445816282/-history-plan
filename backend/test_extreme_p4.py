"""P4/P5 深挖：极端画像是否仍系统性偏向「折中改良」，评分是否有区分度"""
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
    {
        "id": "E1-58岁求稳退休边缘",
        "expect": "守正待时",
        "profile": full({
            "name": "老周", "age": 58, "era": "临近退休",
            "mindset": "只求安稳退休，不想再折腾，最怕晚节不保",
            "personality": "极度保守、厌恶风险",
            "financialResources": "存款150万，退休金可覆盖生活",
            "shortTermGoal": "平稳干到退休", "longTermGoal": "安稳养老",
            "keyDecisions": "要不要提前内退",
        }),
    },
    {
        "id": "E2-24岁无负担敢闯",
        "expect": "进取突破/冒险开拓",
        "profile": full({
            "name": "阿杰", "age": 24, "era": "行业风口期",
            "mindset": "年轻就是本钱，失败了大不了重来，最怕错过窗口",
            "personality": "敢闯敢拼、精力旺盛",
            "financialResources": "无存款但无负债，父母可兜底",
            "timeResources": "大把时间", "unchangeableLimits": "无家庭负担",
            "shortTermGoal": "三年内做出名堂", "longTermGoal": "财务自由",
            "keyDecisions": "裸辞全职创业还是边上班边试",
        }),
    },
    {
        "id": "E3-高资源富二代有产业",
        "expect": "冒险开拓",
        "profile": full({
            "name": "家豪", "age": 30, "era": "家族产业转型期",
            "mindset": "不缺钱，缺的是证明自己的机会，想干票大的",
            "personality": "自信、敢下重注",
            "financialResources": "家族产业现金流，可动用资金千万级",
            "networkResources": "家族人脉深厚", "familyEconomicCapital": "家族企业",
            "shortTermGoal": "开辟新赛道", "longTermGoal": "超越父辈成就",
            "keyDecisions": "是否大举投入新业务",
        }),
    },
    {
        "id": "E4-40岁负债被裁困境",
        "expect": "守正待时/折中",
        "profile": full({
            "name": "大刘", "age": 40, "era": "行业寒冬",
            "mindset": "背着房贷车贷，刚被裁，只想先稳住别崩盘",
            "personality": "焦虑、求稳",
            "financialResources": "存款5万，负债80万，两个孩子",
            "externalPressure": "求职难、房贷压顶",
            "shortTermGoal": "尽快找到稳定收入", "longTermGoal": "还清债务",
            "keyDecisions": "先送外卖过渡还是继续找对口工作",
        }),
    },
]

print("画像 -> 期望最佳 vs 实际最佳（验证 P4 是否系统性偏向折中）")
print("=" * 70)
for sc in scenarios:
    device = f"extreme-{int(time.time()*1000)}"
    h = {"Content-Type": "application/json", "X-Device-Id": device}
    r = httpx.post(f"{BASE}/api/deduce", json={"profile": sc["profile"]}, headers=h, timeout=300)
    if r.status_code != 200:
        print(f"[{sc['id']}] {r.status_code}: {r.text[:120]}")
        continue
    d = r.json()
    paths = {p.get("name"): p.get("score") for p in d.get("paths", [])}
    best = max(paths, key=lambda k: paths[k])
    ranked = sorted(paths.items(), key=lambda x: -x[1])
    rank_str = " > ".join(f"{k}({v})" for k, v in ranked)
    mark = "✅" if best in sc["expect"].split("/") else "❌偏向"
    print(f"\n[{sc['id']}] 期望={sc['expect']} 实际最佳={best} {mark}")
    print(f"  排序: {rank_str}")
    time.sleep(1)

print("\n" + "=" * 70)
print("结论：若 4 个极端画像最佳路径仍高度雷同，则 P4 确认为系统性偏置")
