"""边缘情况测试 — 空档案/低完整度/股票投资者（硬校验误拦风险）"""
import json, time, httpx

BASE = "http://127.0.0.1:8023"

def deduce(profile, industry=None, tag=""):
    t0 = time.time()
    body = {"profile": profile}
    if industry: body["industry"] = industry
    try:
        r = httpx.post(f"{BASE}/api/deduce", json=body, timeout=300)
        dt = time.time() - t0
        try:
            d = r.json()
            meta = d.get("meta", {})
            return {"tag": tag, "status": r.status_code, "time": round(dt,1),
                    "completeness": meta.get("completenessScore"),
                    "reportId": d.get("reportId"),
                    "paths": len(d.get("paths", [])),
                    "consistency": meta.get("consistencyCoefficient"),
                    "error": d.get("detail", "")}
        except Exception:
            return {"tag": tag, "status": r.status_code, "time": round(dt,1), "raw": r.text[:200]}
    except Exception as e:
        return {"tag": tag, "status": "EXC", "time": round(time.time()-t0,1), "error": str(e)}

# 1. 空档案
r1 = deduce({"name": "空档案测试"}, None, "空档案")

# 2. 低完整度（3字段）
r2 = deduce({"name": "低完整度", "skills": "编程", "shortTermGoal": "找到工作"}, None, "低完整度")

# 3. 股票投资者（可能触发硬校验）
stock_profile = {
    "name": "股民老王", "age": 45, "era": "现代", "region": "上海",
    "familyEconomicCapital": "中产", "familyCulturalCapital": "本科",
    "familySymbolicCapital": "无", "skills": "K线分析、基本面研究、量化",
    "personality": "稳健", "mindset": "想做职业投资者", "health": "良好",
    "financialResources": "可投资金100万", "networkResources": "有炒股群",
    "timeResources": "全职", "toolResources": "交易软件",
    "constraints": "A股波动大", "externalPressure": "家庭开支压力",
    "unchangeableLimits": "本金有限", "shortTermGoal": "年化收益20%",
    "mediumTermGoal": "本金翻倍", "longTermGoal": "财务自由",
    "keyDecisions": "是否全职炒股", "externalChanges": "注册制改革"
}
r3 = deduce(stock_profile, "商业金融", "股票投资者")

for r in [r1, r2, r3]:
    print(json.dumps(r, ensure_ascii=False), flush=True)
