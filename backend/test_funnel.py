"""三级漏斗单元测试 — 不调 LLM，纯验证过滤逻辑与 token 缩减"""
import json
from funnel import funnel_cases, detect_world_tag, detect_prototypes

kb = json.load(open("knowledge/cases.json"))
cases = kb["cases"]

# 全量注入字符数（基线）
full_chars = sum(len(json.dumps(c, ensure_ascii=False)) for c in cases)
print(f"基线：全量 {len(cases)} 条 = {full_chars} 字符 ≈ {full_chars//2} token\n")

profiles = {
    "程序员（科技/变革世/创业者）": {
        "era": "互联网行业转型期，AI 风口，技术红利",
        "skills": "编程、架构、产品",
        "personality": "务实、爱钻研",
        "mindset": "想创业做独立开发者",
        "shortTermGoal": "做自己的 App 产品",
        "longTermGoal": "创业成功，白手起家",
        "constraints": "内卷严重，裁员潮",
        "financialResources": "有一定积蓄",
    },
    "淘宝卖家（商业金融/太平世/守成）": {
        "era": "电商行业成熟，存量博弈，稳定经营",
        "skills": "运营、选品、客服",
        "personality": "稳重、守成",
        "mindset": "稳定经营，守住店铺",
        "shortTermGoal": "维持店铺流水",
        "longTermGoal": "稳定经营，接班",
        "constraints": "行业饱和，竞争激烈",
    },
    "股票投资者（商业金融/乱世/投机）": {
        "era": "市场下行，股市动荡，经济衰退",
        "skills": "分析、交易、量化",
        "personality": "理性、敢冒险",
        "mindset": "高风险博弈，投机套利",
        "shortTermGoal": "短线套利",
        "longTermGoal": "长期价值投资",
        "constraints": "市场崩盘风险",
    },
    "失意者（乱世/失意/低谷）": {
        "era": "失业，行业寒冬，经济下行",
        "skills": "",
        "personality": "消沉",
        "mindset": "受挫，不得志",
        "constraints": "失业，落魄",
    },
}

for name, profile in profiles.items():
    filtered, stats = funnel_cases(profile, "", cases)
    chars = sum(len(json.dumps(c, ensure_ascii=False)) for c in filtered)
    print(f"【{name}】")
    print(f"  世道识别: {stats['worldTagDetected']} | 原型识别: {stats['prototypesDetected'][:6]}")
    print(f"  L1世道后古代: {stats['ancientTotal']} → {stats['l1AncientAfterWorldTag']}")
    print(f"  L3古代保留: {stats['ancientKept']} | modern保留: {stats['modernKept']}")
    print(f"  最终: {stats['finalTotal']} 条 = {chars} 字符 ≈ {chars//2} token")
    print(f"  缩减: {full_chars}/{chars} = {full_chars/chars:.1f}x  | 省 {100-round(chars/full_chars*100)}%")
    print()
