"""全行业推演综合测试 v2 — 6 大领域 + 边缘情况，验证 reportId 修复 + 性能 + 结构"""
import json, time, httpx

BASE = "http://127.0.0.1:8023"

def base_profile(name, skills, mindset, goal):
    return {
        "name": name, "age": 30, "era": "现代", "region": "北京",
        "familyEconomicCapital": "普通家庭", "familyCulturalCapital": "本科",
        "familySymbolicCapital": "无", "skills": skills, "personality": "踏实",
        "mindset": mindset, "health": "良好", "financialResources": "存款30万",
        "networkResources": "一般人脉", "timeResources": "业余时间充足",
        "toolResources": "电脑手机", "constraints": "行业竞争", "externalPressure": "经济下行",
        "unchangeableLimits": "无背景", "shortTermGoal": goal, "mediumTermGoal": "稳步提升",
        "longTermGoal": "事业有成", "keyDecisions": "关键抉择未定", "externalChanges": "技术变革"
    }

CASES = [
    ("科技互联网", "程序员", base_profile("张伟", "Java/Go后端", "想转管理", "一年晋升")),
    ("商业金融", "淘宝卖家", base_profile("李芳", "选品运营直播", "单店做品牌", "月销翻倍")),
    ("教育学术", "教师", base_profile("王强", "教学课程设计", "教培转型", "找方向")),
    ("医疗科研", "医生", base_profile("赵敏", "临床诊断", "考主治", "晋升主治")),
    ("制造工匠", "工厂主", base_profile("陈刚", "生产管理", "扩产能", "开分厂")),
    ("文化创意", "自媒体", base_profile("刘洋", "剪辑文案", "做IP", "十万粉")),
]

def deduce(profile, industry):
    t0 = time.time()
    try:
        r = httpx.post(f"{BASE}/api/deduce", json={"profile": profile, "industry": industry}, timeout=300)
        dt = time.time() - t0
        return r.status_code, dt, r.text
    except Exception as e:
        return "EXC", time.time()-t0, str(e)

results = []
for industry, label, profile in CASES:
    st, dt, body = deduce(profile, industry)
    info = {"label": label, "industry": industry, "status": st, "time": round(dt,1)}
    if st == 200:
        try:
            d = json.loads(body)
            info["reportId"] = d.get("reportId")
            info["timestamp"] = d.get("timestamp")
            info["paths"] = len(d.get("paths", []))
            info["reused"] = d.get("meta", {}).get("reusedFromSimilar", False)
            info["consistency"] = d.get("meta", {}).get("consistencyCoefficient")
            # 结构完整性检查
            missing = []
            for k in ["summary", "macroAnalysis", "paths", "mindCultivation", "actionPlan", "riskAnalysis", "disclaimer"]:
                if k not in d: missing.append(k)
            info["missing_modules"] = missing
        except Exception as e:
            info["parse_err"] = str(e)
    else:
        info["error"] = body[:200]
    results.append(info)
    print(json.dumps(info, ensure_ascii=False), flush=True)

print("\n===== 汇总 =====")
for r in results:
    print(f"[{r['label']}] 状态={r['status']} 耗时={r['time']}s reportId={r.get('reportId','N/A')} 路径={r.get('paths','-')} reused={r.get('reused','-')} 缺失={r.get('missing_modules', r.get('error','-'))}")

# 检查 reportId 日期是否正确
print("\n===== reportId 日期检查（应为 20260904）=====")
for r in results:
    rid = r.get("reportId", "")
    if rid:
        date_part = rid.split("-")[1] if len(rid.split("-")) > 1 else "?"
        ok = "✅" if date_part == "20260904" else "❌ 错误日期"
        print(f"  {r['label']}: {rid} → 日期 {date_part} {ok}")
