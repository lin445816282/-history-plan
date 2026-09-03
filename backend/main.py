"""
个人历史推演规划系统 History-Plan — 后端薄代理
职责：LLM 调用中转（解析 + 推演）、API Key 保密、限流、双层输出校验、SimHash 相似缓存
数据主权：所有用户数据（档案/快照/复盘/待办）存于前端 IndexedDB，本服务不落库、不存储
"""
import os
import time
import json
import hashlib
import re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import httpx

BASE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = BASE_DIR / "prompts"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"

app = FastAPI(title="History-Plan 推演代理", version="1.7.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 配置 ----------
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
MODEL = os.environ.get("HP_MODEL", "deepseek-chat")
DAILY_QUOTA = int(os.environ.get("HP_DAILY_QUOTA", "100"))

PROMPT_VERSION = "p-v1.7.0"
KNOWLEDGE_VERSION = "k-v1.0"

# 核心字段（用于完整度计算 + 一致性系数触发判断）
CORE_FIELDS = [
    "name", "age", "era", "region", "familyEconomicCapital", "familyCulturalCapital",
    "familySymbolicCapital", "skills", "personality", "mindset", "health",
    "financialResources", "networkResources", "timeResources", "toolResources",
    "constraints", "externalPressure", "unchangeableLimits", "shortTermGoal",
    "mediumTermGoal", "longTermGoal", "keyDecisions", "externalChanges",
]

# 定数类表述黑名单（第一层硬拦截）
FATAL_WORDS = [
    "注定", "天意不可违", "命中注定", "宿命", "一定成功", "必然失败",
    "无法改变", "命里注定", "天注定", "万无一失",
]
SENSITIVE_WORDS = [
    # 投资操作指令（避免误伤电商"买入/卖出商品"等正常用语）
    "买入股票", "卖出股票", "买入基金", "卖出基金", "买入币", "加仓", "满仓", "重仓",
    "建仓", "平仓", "加杠杆", "投资回报率", "年化收益", "配置比例", "推荐买入", "推荐卖出",
    "资产配置方案",
    # 医疗诊断（避免误伤"自我诊断/诊断处境"等自省用语）
    "抑郁症", "焦虑症", "精神分裂", "双相障碍", "开处方", "开具处方",
    # 法律意见
    "建议起诉", "建议索赔", "律师函", "应诉", "法律意见书",
]

_request_log: list[float] = []
_simhash_cache: dict[str, dict] = {}


def load_prompt(name: str) -> str:
    p = PROMPT_DIR / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


def load_knowledge() -> dict:
    kb_file = KNOWLEDGE_DIR / "cases.json"
    if kb_file.exists():
        return json.loads(kb_file.read_text(encoding="utf-8"))
    return {"version": KNOWLEDGE_VERSION, "cases": []}


def simhash(text: str, bits: int = 64) -> str:
    tokens = re.findall(r"[\u4e00-\u9fa5]{2,}|[a-zA-Z0-9]+", text)
    v = [0] * bits
    for tok in tokens:
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        for i in range(bits):
            v[i] += 1 if (h >> (i % 64)) & 1 else -1
    return "".join("1" if x > 0 else "0" for x in v)


def completeness(profile: dict) -> int:
    filled = [k for k in CORE_FIELDS if str(profile.get(k, "") or "").strip()]
    return round(len(filled) / len(CORE_FIELDS) * 100)


def hard_validate(text: str) -> Optional[str]:
    for w in FATAL_WORDS:
        if w in text:
            return "检测到定数类表述，已拦截。本系统仅作事理参考，不输出宿命结论。"
    for w in SENSITIVE_WORDS:
        if w in text:
            return "检测到专业咨询类表述，已拦截。本系统不提供投资/心理/法律建议。"
    return None


def enforce_quota() -> None:
    now = time.time()
    _request_log[:] = [t for t in _request_log if now - t < 86400]
    if len(_request_log) >= DAILY_QUOTA:
        raise HTTPException(status_code=429, detail="今日推演额度已用完，请联系管理员")


def parse_json_safe(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


async def call_llm(messages: list, temperature: float = 0.7) -> str:
    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json={
                "model": MODEL,
                "messages": messages,
                "response_format": {"type": "json_object"},
                "temperature": temperature,
            },
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"模型调用失败 {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        return data["choices"][0]["message"]["content"]


# ---------- 请求模型 ----------
class ParseRequest(BaseModel):
    text: str = Field(..., min_length=1)


class DeduceRequest(BaseModel):
    profile: dict = Field(...)
    industry: Optional[str] = None


class Adjustment(BaseModel):
    field: str
    label: str
    delta: float = Field(..., ge=-0.5, le=0.5)


class RecalcRequest(BaseModel):
    profile: dict = Field(...)
    paths: list[dict] = Field(...)
    adjustments: list[Adjustment] = Field(...)


# ---------- 端点 ----------
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "model": MODEL,
        "prompt_version": PROMPT_VERSION,
        "knowledge_version": KNOWLEDGE_VERSION,
        "api_key_configured": bool(DEEPSEEK_API_KEY),
    }


@app.post("/api/parse")
async def parse(req: ParseRequest):
    """自然语言 → 结构化档案预览（解析 Prompt，JSON mode）"""
    if not DEEPSEEK_API_KEY:
        raise HTTPException(status_code=503, detail="大模型 API Key 未配置")
    prompt = load_prompt("parse_prompt_v1.7.txt")
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": req.text},
    ]
    raw = await call_llm(messages, temperature=0.1)
    try:
        data = parse_json_safe(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="解析结果格式异常，请重试")
    return data


@app.post("/api/deduce")
async def deduce(req: DeduceRequest):
    """档案 + 知识上下文 → 推演报告（推演 Prompt，JSON mode + 双层校验）"""
    if not DEEPSEEK_API_KEY:
        raise HTTPException(status_code=503, detail="大模型 API Key 未配置")
    enforce_quota()
    _request_log.append(time.time())

    prompt = load_prompt("system_prompt_v1.7.txt")
    knowledge = load_knowledge()

    user_content = json.dumps(
        {
            "人物档案": req.profile,
            "行业标签": req.industry or "",
            "历史知识库上下文": knowledge.get("cases", []),
        },
        ensure_ascii=False,
    )
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_content},
    ]

    # 主推演（温度 0.7）
    raw = await call_llm(messages, temperature=0.7)

    # 第一层硬拦截
    block = hard_validate(raw)
    if block:
        raise HTTPException(status_code=400, detail=block)

    try:
        report = parse_json_safe(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="推演结果格式异常，请重试")

    # 注入元信息（后端权威版本号）
    if "meta" not in report:
        report["meta"] = {}
    report["meta"].update({
        "knowledgeVersion": KNOWLEDGE_VERSION,
        "promptVersion": PROMPT_VERSION,
        "modelVersion": MODEL,
        "completenessScore": completeness(req.profile),
        "consistencyCoefficient": report["meta"].get("consistencyCoefficient", "中"),
    })

    # 相似档案 SimHash 缓存（完整度>80% 才启用）
    comp = completeness(req.profile)
    if comp > 80:
        key = simhash(json.dumps(req.profile, ensure_ascii=False, sort_keys=True))
        _simhash_cache[key] = {"ts": time.time(), "report": report}

    return report


@app.post("/api/recalc")
async def recalc(req: RecalcRequest):
    """参数微调·快速重算 —— 复用原推演上下文，仅增量更新受影响的路径评分与风险提示"""
    if not DEEPSEEK_API_KEY:
        raise HTTPException(status_code=503, detail="大模型 API Key 未配置")
    enforce_quota()
    _request_log.append(time.time())

    if not req.adjustments:
        raise HTTPException(status_code=400, detail="请至少调整一个变量后再重算")

    prompt = load_prompt("recalc_prompt_v1.7.txt")

    # 提取档案核心资源现状简述（供模型判断影响方向）
    res_keys = {
        "financialResources": "资金储备",
        "networkResources": "人脉资源",
        "timeResources": "时间投入",
        "toolResources": "工具/技术",
    }
    profile_summary = "；".join(
        f"{label}:{req.profile.get(k) or '未填写'}"
        for k, label in res_keys.items()
    )

    user_content = json.dumps(
        {
            "paths": req.paths,
            "adjustments": [a.dict() for a in req.adjustments],
            "profileSummary": profile_summary,
        },
        ensure_ascii=False,
    )
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_content},
    ]

    raw = await call_llm(messages, temperature=0.3)

    block = hard_validate(raw)
    if block:
        raise HTTPException(status_code=400, detail=block)

    try:
        result = parse_json_safe(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="重算结果格式异常，请重试")

    # 后端兜底：强制 delta 保留一位小数、修正浮点误差
    for p in result.get("paths", []):
        orig = p.get("originalScore", 0)
        new = p.get("newScore", orig)
        p["originalScore"] = round(float(orig), 1)
        p["newScore"] = round(float(new), 1)
        p["delta"] = round(float(p.get("delta", p["newScore"] - p["originalScore"])), 1)

    return result


# ---------- 前端静态托管（Vue3 SPA，hash 路由） ----------
if FRONTEND_DIST.exists():
    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIST / "index.html")

    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8023)
