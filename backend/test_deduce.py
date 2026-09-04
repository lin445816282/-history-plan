"""全行业推演压力测试 — 构造各行业人物档案，批量调 /api/deduce，记录耗时/结果/问题"""
import json, time, httpx

BASE = "http://127.0.0.1:8023"

# 各行业人物档案（按 CORE_FIELDS 构造）
PROFILES = [
    {
        "industry": "科技互联网", "label": "程序员转管理",
        "profile": {
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
    },
    {
        "industry": "商业金融", "label": "淘宝卖家扩张",
        "profile": {
            "name": "李芳", "age": 28, "era": "现代", "region": "杭州",
            "familyEconomicCapital": "普通家庭",
            "familyCulturalCapital": "大专",
            "familySymbolicCapital": "无",
            "skills": "选品、运营、直播",
            "personality": "敢闯敢拼",
            "mindset": "想把单店做成品牌",
            "health": "睡眠不足",
            "financialResources": "流动资金20万",
            "networkResources": "有稳定供应商",
            "timeResources": "全时投入",
            "toolResources": "店铺、直播设备",
            "constraints": "平台规则多变",
            "externalPressure": "同行价格战",
            "unchangeableLimits": "资金有限",
            "shortTermGoal": "月销翻倍",
            "mediumTermGoal": "开第二家店",
            "longTermGoal": "自有品牌",
            "keyDecisions": "是否压货扩品",
            "externalChanges": "直播电商红利退坡"
        }
    },
    {
        "industry": "教育学术", "label": "教培老师转型",
        "profile": {
            "name": "王强", "age": 35, "era": "现代", "region": "北京",
            "familyEconomicCapital": "工薪",
            "familyCulturalCapital": "师范本科",
            "familySymbolicCapital": "无",
            "skills": "教学、课程设计",
            "personality": "严谨负责",
            "mindset": "教培受政策冲击，想转型",
            "health": "良好",
            "financialResources": "存款30万",
            "networkResources": "家长资源多",
            "timeResources": "待业可全时",
            "toolResources": "电脑、录课设备",
            "constraints": "行业萎缩",
            "externalPressure": "双减政策",
            "unchangeableLimits": "年龄偏大",
            "shortTermGoal": "找到转型方向",
            "mediumTermGoal": "知识付费或私教",
            "longTermGoal": "稳定收入来源",
            "keyDecisions": "转型知识付费还是考编",
            "externalChanges": "AI 教育产品崛起"
        }
    },
]

def deduce(profile, industry):
    t0 = time.time()
    try:
        r = httpx.post(f"{BASE}/api/deduce", json={"profile": profile, "industry": industry}, timeout=300)
        dt = time.time() - t0
        return {"status": r.status_code, "time": round(dt, 1), "body": r.text}
    except Exception as e:
        dt = time.time() - t0
        return {"status": "EXC", "time": round(dt, 1), "body": str(e)}

for p in PROFILES:
    print(f"\n{'='*60}")
    print(f"[{p['industry']}] {p['label']}")
    res = deduce(p["profile"], p["industry"])
    print(f"  状态: {res['status']} | 耗时: {res['time']}s")
    if res["status"] == 200:
        try:
            d = json.loads(res["body"])
            print(f"  路径数: {len(d.get('paths', []))}")
            print(f"  摘要: {str(d.get('summary', ''))[:80]}")
            meta = d.get("meta", {})
            print(f"  知识库版本: {meta.get('knowledgeVersion')} | 一致系数: {meta.get('consistencyCoefficient')}")
        except Exception as e:
            print(f"  解析失败: {e}")
            print(f"  原始前200字: {res['body'][:200]}")
    else:
        print(f"  错误: {res['body'][:300]}")
