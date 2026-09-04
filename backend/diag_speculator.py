"""诊断：投机者推演到底输出了什么敏感词触发拦截"""
import json, asyncio, sys
sys.path.insert(0, '.')
import main
from funnel import funnel_cases

profile = {
    "name": "陈豪", "age": 30, "era": "市场下行，股市剧烈动荡，经济衰退，流动性收紧",
    "region": "上海",
    "familyEconomicCapital": "中产家庭，父母不支持投机",
    "familyCulturalCapital": "本科金融",
    "familySymbolicCapital": "无特殊背景",
    "skills": "技术分析、短线交易、量化回测、盯盘",
    "personality": "激进、赌性强、敢于冒险、自信",
    "mindset": "追求高风险高回报，相信短线博弈能快速翻倍",
    "health": "熬夜盯盘，精神紧张",
    "financialResources": "本金100万，其中30万是借贷",
    "networkResources": "几个炒股群、券商客户经理",
    "timeResources": "全职盯盘，时间充裕",
    "toolResources": "量化工具、Level2行情、杠杆账户",
    "constraints": "亏损风险极大、杠杆爆仓压力、借贷利息",
    "externalPressure": "市场单边下跌、监管趋严、流动性危机",
    "unchangeableLimits": "本金有限、无稳定现金流",
    "shortTermGoal": "三个月内本金翻倍",
    "mediumTermGoal": "靠交易实现财务自由",
    "longTermGoal": "成为顶级交易员或私募操盘手",
    "keyDecisions": "是否继续加杠杆重仓博反弹",
    "externalChanges": "政策救市信号不明、外围市场崩盘",
}

async def run():
    prompt = main.load_prompt("system_prompt_v1.7.txt")
    industry = main.detect_industry(profile)
    filtered, _ = funnel_cases(profile, industry, main.load_knowledge().get("cases", []))
    user_content = json.dumps({"人物档案": profile, "行业标签": industry, "历史知识库上下文": filtered}, ensure_ascii=False)
    raw = await main.call_llm([
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_content},
    ], temperature=0.7)
    print("=== 原始输出触发的敏感词 ===")
    for w in main.SENSITIVE_WORDS:
        if w in raw:
            # 打印命中词上下文
            idx = raw.find(w)
            print(f"  命中「{w}」: ...{raw[max(0,idx-15):idx+len(w)+15]}...")
    print("\n=== 定数词 ===")
    for w in main.FATAL_WORDS:
        if w in raw:
            print(f"  命中「{w}」")
    print("\n=== 原始输出前 800 字 ===")
    print(raw[:800])

asyncio.run(run())
