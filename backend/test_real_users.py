"""真实用户场景训练测试：多样化画像推演，记录结构/评分/边界问题"""
import json, time, httpx

BASE = "http://127.0.0.1:8023"
STD_PATHS = {"进取突破", "折中改良", "守正待时", "冒险开拓"}
TOP_MODULES = ["meta", "summary", "macroAnalysis", "paths", "mindCultivation", "actionPlan", "riskAnalysis", "disclaimer"]

# ---------- 6 个真实用户场景 ----------
scenarios = [
    {
        "id": "S1-程序员35被裁",
        "profile": {
            "name": "陈宇", "age": 35, "era": "互联网寒冬，大厂裁员潮，AI替代焦虑",
            "region": "深圳",
            "familyEconomicCapital": "父母县城退休职工，无房产可继承",
            "familyCulturalCapital": "普通本科计算机，自学前端",
            "familySymbolicCapital": "无背景",
            "skills": "前端架构8年、带过12人团队、有全栈能力",
            "personality": "技术执着、不善社交、抗压一般",
            "mindset": "被裁后焦虑，纠结继续找大厂还是转型独立开发",
            "health": "颈椎病，久坐加重",
            "financialResources": "存款90万，房贷月供1.2万，妻子收入稳定",
            "networkResources": "前同事内推渠道、几个创业想法同好",
            "timeResources": "失业期时间充裕", "toolResources": "技术能力、个人品牌博客",
            "constraints": "35岁年龄门槛、大厂HC冻结",
            "externalPressure": "行业下行、招聘要求水涨船高",
            "unchangeableLimits": "非名校学历",
            "shortTermGoal": "半年内找到新方向", "mediumTermGoal": "建立稳定现金流",
            "longTermGoal": "财务自由或拥有自己的产品",
            "keyDecisions": "是否接受降薪30%的中厂offer",
            "externalChanges": "AI工具爆发，个人开发者机会变多",
        },
    },
    {
        "id": "S2-应届毕业生",
        "profile": {
            "name": "林小雨", "age": 22, "era": "就业形势严峻，考研热退潮，考公竞争白热化",
            "region": "武汉",
            "familyEconomicCapital": "普通工薪家庭，能支持考研一年",
            "familyCulturalCapital": "父母高中学历，重视稳定",
            "familySymbolicCapital": "无",
            "skills": "新闻传播专业、写作能力尚可、运营过校园公众号",
            "personality": "温和、有主见但缺乏社会经验",
            "mindset": "迷茫：考研、考公、还是去新媒体行业",
            "health": "良好",
            "financialResources": "无积蓄，家庭可支持一年备考",
            "networkResources": "学长学姐、同学",
            "timeResources": "应届生时间相对自由", "toolResources": "专业素养、年轻",
            "constraints": "应届身份窗口期短、容错率低",
            "externalPressure": "文科就业难、新媒体行业不稳定",
            "unchangeableLimits": "文科背景、无技术特长",
            "shortTermGoal": "三个月内确定方向", "mediumTermGoal": "顺利上岸或进入理想行业",
            "longTermGoal": "经济独立并有职业积累",
            "keyDecisions": "全职备考还是先就业再考",
            "externalChanges": "考公岗位减少、学历贬值",
        },
    },
    {
        "id": "S3-45岁制造中层",
        "profile": {
            "name": "王建国", "age": 45, "era": "制造业外迁、智能化改造、中年危机",
            "region": "东莞",
            "familyEconomicCapital": "有房有车，子女在读大学",
            "familyCulturalCapital": "中专毕业，靠经验上位",
            "familySymbolicCapital": "无",
            "skills": "生产管理20年、懂精益生产、管过500人车间",
            "personality": "稳重、踏实、学习能力下降",
            "mindset": "职位天花板明显，担心被优化",
            "health": "三高，体力不如从前",
            "financialResources": "存款120万，房贷已清，子女教育开销大",
            "networkResources": "行业内老关系、供应商资源",
            "timeResources": "周末双休但精力有限", "toolResources": "管理经验、行业人脉",
            "constraints": "年龄劣势、新技能学习慢",
            "externalPressure": "工厂外迁东南亚、自动化替代",
            "unchangeableLimits": "学历低、英语弱",
            "shortTermGoal": "保住现有位置", "mediumTermGoal": "找到第二增长曲线",
            "longTermGoal": "安稳退休并给子女减负",
            "keyDecisions": "是否转岗做咨询/培训，还是守成",
            "externalChanges": "公司计划把生产线迁往越南",
        },
    },
    {
        "id": "S4-淘宝卖家独立开发者",
        "profile": {
            "name": "小林", "age": 33, "era": "电商内卷、流量成本高、AI工具降低开发门槛",
            "region": "杭州",
            "familyEconomicCapital": "父母个体户，靠自己白手起家",
            "familyCulturalCapital": "普通学历，自学编程",
            "familySymbolicCapital": "无",
            "skills": "全栈开发、电商运营、会做微信小游戏",
            "personality": "执行力强、点子多、精力分散",
            "mindset": "淘宝生意利润薄，纠结押注独立开发还是扩品类",
            "health": "久坐、作息不规律",
            "financialResources": "店铺现金流、存款一般",
            "networkResources": "电商同行、技术社区",
            "timeResources": "一个人精力有限", "toolResources": "开发能力、AI工具、店铺",
            "constraints": "单打独斗、没有团队",
            "externalPressure": "平台规则多变、推广费用上涨",
            "unchangeableLimits": "个人精力上限",
            "shortTermGoal": "找到稳定的第二收入", "mediumTermGoal": "把产品/店铺做出规模",
            "longTermGoal": "被动收入覆盖生活",
            "keyDecisions": "要不要把主要精力从淘宝转到独立开发",
            "externalChanges": "AI编程工具大幅提升个人开发效率",
        },
    },
    {
        "id": "S5-极简档案信息不全",
        "profile": {
            "name": "张伟", "age": 30,
            "era": "",
            "region": "",
            "skills": "",
            "mindset": "想换个活法，但没想清楚",
        },
    },
    {
        "id": "S6-敏感词边界",
        "profile": {
            "name": "李强", "age": 38, "era": "普通工薪",
            "region": "北京",
            "skills": "会计",
            "personality": "焦虑",
            "mindset": "我最近很焦虑，怀疑自己得了抑郁症，要不要去医院",
            "keyDecisions": "手上有30万，要不要全仓买入XX股票翻本",
            "shortTermGoal": "缓解焦虑、让钱生钱",
            "mediumTermGoal": "财务好转",
            "longTermGoal": "财富自由",
        },
    },
]


def check_report(d):
    """结构完整性 + 评分 + 路径名检查，返回问题列表"""
    issues = []
    if not isinstance(d, dict):
        return ["非 JSON 对象"]
    for k in TOP_MODULES:
        if k not in d:
            issues.append(f"缺顶层模块 {k}")

    paths = d.get("paths", [])
    if not paths:
        issues.append("paths 为空")
    else:
        names = [str(p.get("name", "")) for p in paths]
        if set(names) != STD_PATHS:
            issues.append(f"路径名非标准4个: {names}")
        if len(names) != len(set(names)):
            issues.append(f"路径名重复: {names}")
        for p in paths:
            nm = p.get("name")
            sc = p.get("score")
            if not isinstance(sc, (int, float)) or not (0 <= sc <= 10):
                issues.append(f"评分越界 {nm}={sc}")
            if not p.get("scoringBasis"):
                issues.append(f"{nm} 缺 scoringBasis")
            elif len(p.get("scoringBasis", [])) < 3:
                issues.append(f"{nm} scoringBasis<3条")
            if not p.get("stopLoss"):
                issues.append(f"{nm} 缺 stopLoss")
            if "mentalDifficulty" not in (p.get("stopLoss") or {}):
                issues.append(f"{nm} 缺 mentalDifficulty")
            if "scoreCI" not in p:
                issues.append(f"{nm} 缺 scoreCI")

    if not d.get("summary"):
        issues.append("缺 summary")
    mc = d.get("mindCultivation", {})
    if not mc.get("weeklyActions"):
        issues.append("mindCultivation 缺 weeklyActions")
    elif len(mc.get("weeklyActions", [])) < 3:
        issues.append("weeklyActions<3条")
    ap = d.get("actionPlan", {})
    if len(ap.get("shortTerm", [])) < 3:
        issues.append("actionPlan.shortTerm<3条")
    return issues


results = []
for idx, sc in enumerate(scenarios):
    device = f"realuser-{idx}-{int(time.time())}"
    headers = {"Content-Type": "application/json", "X-Device-Id": device}
    t0 = time.time()
    try:
        r = httpx.post(f"{BASE}/api/deduce", json={"profile": sc["profile"]}, headers=headers, timeout=300)
        dt = round(time.time() - t0, 1)
    except Exception as e:
        results.append({"id": sc["id"], "status": "EXC", "dt": 0, "issues": [str(e)], "paths": None, "meta": None})
        print(f"\n{'='*60}\n[{sc['id']}] 异常 {e}")
        continue

    if r.status_code != 200:
        results.append({"id": sc["id"], "status": r.status_code, "dt": dt, "issues": [], "paths": None, "meta": None, "detail": r.text[:200]})
        print(f"\n{'='*60}\n[{sc['id']}] 状态 {r.status_code} | {dt}s\n  响应: {r.text[:200]}")
        continue

    d = r.json()
    issues = check_report(d)
    paths = {p.get("name"): p.get("score") for p in d.get("paths", [])}
    meta = d.get("meta", {})
    print(f"\n{'='*60}\n[{sc['id']}] 200 | {dt}s")
    print(f"  完整度 {meta.get('completenessScore')} | 可信度 {meta.get('credibilityRating')} | 一致性 {meta.get('consistencyCoefficient')}")
    print(f"  路径: {json.dumps(paths, ensure_ascii=False)}")
    print(f"  最佳: {d.get('summary', {}).get('bestPath', '')[:60]}")
    if issues:
        print(f"  ⚠️ 问题 {len(issues)} 条:")
        for i in issues:
            print(f"     - {i}")
    else:
        print(f"  ✅ 结构完整无问题")
    results.append({"id": sc["id"], "status": 200, "dt": dt, "issues": issues, "paths": paths, "meta": meta})

# ---------- 汇总 ----------
print(f"\n\n{'#'*60}\n📊 问题汇总")
total_issues = 0
for r in results:
    n = len(r.get("issues", []))
    total_issues += n
    if r["status"] != 200:
        print(f"  [{r['id']}] 状态 {r['status']} - 需关注")
    elif n:
        print(f"  [{r['id']}] {n} 个问题")
    else:
        print(f"  [{r['id']}] ✅ 干净")
print(f"\n共 {len(results)} 场景，{total_issues} 个问题")
print("=" * 60)
