"""
三级漏斗算法 — 知识库案例过滤
目标：把 641 条案例从 23 万字符压缩到 ~2 万字符（约 55 条），同时保证相关性、不误杀。

三级漏斗（软过滤，宁多勿漏）：
  L1 世道过滤  档案 era 文本 → 识别「乱世/变革世/太平世」→ 古代案例按 worldTag 匹配
  L2 原型匹配  档案文本 → 识别原型（创业者/改革者/投机家…）→ 案例按 prototype 排序靠前
  L3 相关性top-N  2-gram 文本相似度评分 → 古代案例取 top-N

modern 案例按 industry 匹配全保留（高价值近现代对标，量小不裁剪）。
"""

# ---------- L1：世道识别关键词 ----------
# 按「宏观环境走向」三分类：下行恶化=乱世 / 上行转型=变革世 / 平稳成熟=太平世
WORLD_TAG_KEYWORDS = {
    "乱世": [
        "衰退", "下行", "危机", "动荡", "混乱", "失业", "崩盘", "崩", "战争", "疫情",
        "寒冬", "裁员", "收缩", "萧条", "低谷", "萎缩", "恶化", "泡沫破裂", "洗牌出清",
    ],
    "变革世": [
        "变革", "转型", "升级", "新兴", "风口", "红利", "增长", "改革", "创新", "突破",
        "换轨", "蓝海", "重构", "智能化", "数字化", "新赛道", "扩张", "爆发", "洗牌", "增量",
    ],
    "太平世": [
        "稳定", "平稳", "安逸", "体制内", "铁饭碗", "成熟", "规范", "固守", "存量", "稳态",
        "按部就班", "饱和", "守成", "稳定增长", "深耕",
    ],
}

# ---------- L2：原型识别关键词（覆盖 top 原型） ----------
PROTOTYPE_KEYWORDS = {
    "创业者": ["创业", "老板", "开店", "做生意", "起步", "从零", "白手起家", "创办", "公司", "合伙人"],
    "改革者": ["改革", "变革", "改变现状", "转型", "革新", "破局", "重构"],
    "投机家": ["投机", "博弈", "高风险", "快钱", "机会主义", "短线", "套利"],
    "冒险投机者": ["冒险", "梭哈", "all in", "重仓", "豪赌", "押注"],
    "长期价值投资者": ["价值投资", "长期持有", "复利", "定投", "长线", "价值股"],
    "文人": ["写作", "文人", "内容", "文案", "文学", "创作", "自媒体", "作家", "写手"],
    "匠人": ["手艺", "工匠", "精工", "打磨", "深耕", "技师", "专精", "极客"],
    "将才": ["带兵", "领导", "管理", "带队", "统率", "团队", "打仗", "指挥官", "主帅"],
    "谋士": ["谋略", "策划", "参谋", "策略", "出主意", "军师", "顾问", "规划"],
    "守成者": ["守成", "守业", "接班", "维持", "守住", "稳定经营", "继承"],
    "清流": ["清流", "原则", "正直", "不妥协", "理想主义", "洁身自好", "底线"],
    "权臣": ["权力", "权谋", "掌权", "仕途", "晋升", "官场", "上位", "政治"],
    "寒门崛起": ["寒门", "逆袭", "底层", "翻身", "跨越阶层", "穷", "草根", "农村"],
    "世家子弟": ["世家", "富二代", "背景", "资源雄厚", "起点高", "家族"],
    "科研攻坚者": ["科研", "研发", "攻克", "技术攻关", "实验室", "研究", "学术攻关"],
    "创新颠覆者": ["颠覆", "创新", "破坏式", "革新", "重新定义", "新模式"],
    "失意者": ["失意", "失败", "受挫", "低谷", "不得志", "落榜", "落魄"],
    "循吏": ["务实", "执行", "落地", "基层", "实干", "结果导向"],
    "隐士": ["隐居", "避世", "淡泊", "佛系", "躺平", "归隐", "田园"],
    "学者": ["学术", "学者", "教授", "研究", "读书", "学问", "考据"],
}


def detect_world_tag(profile: dict) -> str:
    """从档案 era + constraints + externalPressure 文本识别世道，未命中返回空串"""
    text = " ".join(str(profile.get(k, "") or "") for k in ("era", "constraints", "externalPressure"))
    scores = {tag: sum(1 for kw in kws if kw in text) for tag, kws in WORLD_TAG_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else ""


def detect_prototypes(profile: dict) -> list[str]:
    """从档案 skills + personality + mindset + goals 识别原型，返回命中列表（按命中数降序）"""
    text = " ".join(str(profile.get(k, "") or "") for k in (
        "skills", "personality", "mindset", "shortTermGoal", "mediumTermGoal", "longTermGoal",
        "keyDecisions", "financialResources",
    ))
    hits = {proto: sum(1 for kw in kws if kw in text) for proto, kws in PROTOTYPE_KEYWORDS.items()}
    return [p for p, n in sorted(hits.items(), key=lambda x: -x[1]) if n > 0]


def _bigrams(text: str) -> set:
    """中文 2-gram + 英文/数字词，用于相关性评分"""
    import re
    s = set()
    # 中文 2-gram
    cn = re.sub(r"[^\u4e00-\u9fa5]", "", text)
    s.update(cn[i:i + 2] for i in range(len(cn) - 1))
    # 英文/数字词
    s.update(re.findall(r"[a-zA-Z0-9]{2,}", text))
    return s


def _case_text(case: dict) -> str:
    """案例的可评分文本（古代多含 ancientContext/boundaryNote）"""
    return " ".join(str(case.get(k, "") or "") for k in (
        "name", "prototype", "context", "ancientContext", "boundaryNote", "principle", "lesson",
    ))


def score_relevance(profile_bigrams: set, case: dict) -> float:
    """2-gram Dice 系数相关性评分"""
    case_bg = _bigrams(_case_text(case))
    if not case_bg:
        return 0.0
    inter = len(profile_bigrams & case_bg)
    return 2.0 * inter / (len(profile_bigrams) + len(case_bg))


def funnel_cases(profile: dict, industry: str, cases: list, top_n: int = 40):
    """三级漏斗主入口。返回 (filtered_cases, stats)"""
    ancient = [c for c in cases if c.get("type") == "ancient"]
    modern = [c for c in cases if c.get("type") == "modern"]

    profile_text = " ".join(str(v) for v in profile.values() if isinstance(v, str))
    profile_bigrams = _bigrams(profile_text)

    # ---- L1 世道过滤（仅古代案例） ----
    world_tag = detect_world_tag(profile)
    if world_tag:
        l1_ancient = [c for c in ancient if c.get("worldTag") == world_tag]
    else:
        l1_ancient = list(ancient)  # 未识别出世道，不硬过滤

    # ---- L2 原型匹配（排序靠前，不丢弃） ----
    prototypes = detect_prototypes(profile)
    proto_set = set(prototypes)
    if proto_set:
        l1_ancient.sort(key=lambda c: 0 if c.get("prototype") in proto_set else 1)

    # ---- L3 相关性 top-N（古代精筛） ----
    scored = sorted(
        l1_ancient,
        key=lambda c: (c.get("prototype") in proto_set, score_relevance(profile_bigrams, c)),
        reverse=True,
    )
    ancient_kept = scored[:top_n]

    # ---- modern：行业匹配全保留 + 其余按相关性补充 ----
    if industry:
        modern_matched = [c for c in modern if c.get("industry") == industry]
        modern_rest = [c for c in modern if c.get("industry") != industry]
    else:
        modern_matched = []
        modern_rest = list(modern)
    # 现代案例量小（≤61），行业匹配全保留；未匹配的按相关性补 top-10 兜底
    modern_rest_sorted = sorted(modern_rest, key=lambda c: score_relevance(profile_bigrams, c), reverse=True)
    modern_kept = modern_matched + modern_rest_sorted[:10]

    filtered = modern_kept + ancient_kept

    stats = {
        "total": len(cases),
        "modernTotal": len(modern),
        "ancientTotal": len(ancient),
        "worldTagDetected": world_tag or None,
        "l1AncientAfterWorldTag": len(l1_ancient),
        "prototypesDetected": prototypes,
        "ancientKept": len(ancient_kept),
        "modernKept": len(modern_kept),
        "finalTotal": len(filtered),
        "topN": top_n,
    }
    return filtered, stats
