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

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import httpx

BASE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = BASE_DIR / "prompts"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"

app = FastAPI(title="History-Plan 推演代理", version="1.7.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产按 ct256.cn 收紧
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 配置 ----------
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
MODEL = os.environ.get("HP_MODEL", "deepseek-chat")

# 单日全局推演配额（默认100次/天）
DAILY_QUOTA = int(os.environ.get("HP_DAILY_QUOTA", "100"))

# ---------- 提示词版本 ----------
PROMPT_VERSION = "p-v1.7.0"
KNOWLEDGE_VERSION = "k-v1.0"

# 定数类表述黑名单（第一层硬拦截）
FATAL_WORDS = [
    "注定", "天意不可违", "命中注定", "宿命", "一定成功", "必然失败",
    "无法改变", "命里注定", "天注定",
]
# 投资/心理/法律类敏感词
SENSITIVE_WORDS = [
    "买入", "卖出", "投资回报率", "仓位", "加杠杆", "配置比例",
    "诊断", "处方", "抑郁症", "焦虑症", "确诊",
    "起诉", "赔偿", "律师函",
]

# ---------- 运行时状态 ----------
_request_log: list[float] = []  # 当日推演时间戳，用于配额
_simhash_cache: dict[str, dict] = {}  # simhash -> {ts, result}


def load_prompt(name: str) -> str:
    p = PROMPT_DIR / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


def load_knowledge() -> dict:
    """加载知识库（30-50 精选案例）。V1 先读空壳，M3 填充案例。"""
    kb_file = KNOWLEDGE_DIR / "cases.json"
    if kb_file.exists():
        return json.loads(kb_file.read_text(encoding="utf-8"))
    return {"version": KNOWLEDGE_VERSION, "cases": []}


def simhash(text: str, bits: int = 64) -> str:
    """简单 SimHash：用于相似档案复用判断（M3 完善）。"""
    tokens = re.findall(r"[\u4e00-\u9fa5]{2,}|[a-zA-Z0-9]+", text)
    v = [0] * bits
    for tok in tokens:
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        for i in range(bits):
            v[i] += 1 if (h >> (i % 64)) & 1 else -1
    return "".join("1" if x > 0 else "0" for x in v)


def hard_validate(text: str) -> Optional[str]:
    """第一层硬拦截：命中定数/敏感词返回拦截话术，否则 None。"""
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


# ---------- 请求/响应模型 ----------
class ParseRequest(BaseModel):
    text: str = Field(..., min_length=1, description="用户自由文本描述")


class DeduceRequest(BaseModel):
    profile: dict = Field(..., description="人物档案（完整字段）")
    industry: Optional[str] = Field(None, description="行业标签，用于匹配近现代人物")
    knowledge_version: Optional[str] = None
    prompt_version: Optional[str] = None


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
    """自然语言 → 结构化档案（解析 Prompt）。M2 对接。"""
    if not DEEPSEEK_API_KEY:
        raise HTTPException(status_code=503, detail="大模型 API Key 未配置")
    # TODO(M2): 调用解析 Prompt + JSON mode，返回 profile 预览
    raise HTTPException(status_code=501, detail="解析引擎 M2 阶段接入")


@app.post("/api/deduce")
async def deduce(req: DeduceRequest):
    """档案 + 知识上下文 → 推演报告（推演 Prompt）。M3 对接。"""
    if not DEEPSEEK_API_KEY:
        raise HTTPException(status_code=503, detail="大模型 API Key 未配置")
    enforce_quota()
    # TODO(M3): 组装知识上下文 + 3次低温并行一致性 + JSON mode 输出 + 双层校验 + SimHash 缓存
    raise HTTPException(status_code=501, detail="推演引擎 M3 阶段接入")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
