"""
个人历史推演规划系统 History-Plan — 后端薄代理
职责：LLM 调用中转（解析 + 推演）、API Key 保密、限流、双层输出校验、SimHash 相似缓存
数据主权：所有用户数据（档案/快照/复盘/待办）存于前端 IndexedDB，本服务不落库、不存储
"""
import os
import time
import json
import hashlib
import secrets
import re
import asyncio
import sqlite3
import statistics
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import httpx

import funnel

BASE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = BASE_DIR / "prompts"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
DB_PATH = BASE_DIR / "history_plan.db"   # 用户配额持久化库（仅存用户身份+配额元数据，不存用户档案/报告）

app = FastAPI(title="History-Plan 推演代理", version="1.7.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 配置 ----------
PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        "api_key": os.environ.get("DEEPSEEK_API_KEY", ""),
        "model": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
    },
    "kimi": {
        "name": "Kimi（月之暗面）",
        "base_url": "https://api.moonshot.cn/v1",
        "api_key": os.environ.get("KIMI_API_KEY", ""),
        "model": "moonshot-v1-8k",
    },
}
DEFAULT_PROVIDER = os.environ.get("HP_PROVIDER", "deepseek")
DAILY_QUOTA = int(os.environ.get("HP_DAILY_QUOTA", "100"))
FREE_QUOTA = int(os.environ.get("HP_FREE_QUOTA", "3"))   # 免费推演总次数（终身，用完需付费）


def resolve_provider(provider: Optional[str]) -> str:
    """归一化 provider 名，非法值回退默认"""
    return provider if provider in PROVIDERS else DEFAULT_PROVIDER

def _content_version(files: list) -> str:
    """从文件内容 md5 生成版本号，修改文件即自动递增"""
    h = hashlib.md5()
    for p in files:
        if p.exists():
            h.update(p.read_bytes())
    return h.hexdigest()[:8]


PROMPT_VERSION = "p-" + _content_version([
    PROMPT_DIR / "system_prompt_v1.7.txt",
    PROMPT_DIR / "parse_prompt_v1.7.txt",
    PROMPT_DIR / "recalc_prompt_v1.7.txt",
    PROMPT_DIR / "consistency_prompt_v1.7.txt",
    PROMPT_DIR / "deviation_prompt_v2.txt",
    PROMPT_DIR / "compare_prompt_v2.txt",
    PROMPT_DIR / "continue_prompt_v1.txt",
])
KNOWLEDGE_VERSION = "k-" + _content_version([KNOWLEDGE_DIR / "cases.json"])

# 核心字段（用于完整度计算 + 一致性系数触发判断）
CORE_FIELDS = [
    "name", "age", "era", "region", "familyEconomicCapital", "familyCulturalCapital",
    "familySymbolicCapital", "skills", "personality", "mindset", "health",
    "financialResources", "networkResources", "timeResources", "toolResources",
    "constraints", "externalPressure", "unchangeableLimits", "shortTermGoal",
    "mediumTermGoal", "longTermGoal", "keyDecisions", "externalChanges",
]

# 4 个标准路径名 → 关键词别名（用于归一化 LLM 输出的带括号/别名变体，保证轨迹图聚合稳定）
PATH_NAME_ALIASES = {
    "进取突破": ["进取", "突破", "激进", "出击", "搏"],
    "折中改良": ["折中", "改良", "妥协", "平衡", "渐进"],
    "守正待时": ["守正", "守成", "稳健", "保守", "等待", "待时", "守势", "蛰伏"],
    "冒险开拓": ["冒险", "开拓", "破局", "闯", "allin", "孤注"],
}

# 近现代行业人物子库的 6 大领域 → 关键词（用于档案文本自动识别行业，优先注入匹配案例）
INDUSTRY_KEYWORDS = {
    "科技互联网": ["科技", "互联网", "程序员", "软件", "人工智能", "AI", "电商", "数字", "App", "产品经理", "代码", "IT", "开发", "技术", "网络"],
    "制造工匠": ["制造", "工厂", "工匠", "手艺", "生产", "机械", "加工", "工艺", "供应链", "实业"],
    "文化创意": ["文创", "设计", "艺术", "内容", "写作", "自媒体", "短视频", "影视", "游戏", "动漫", "创意", "文案", "博主"],
    "教育学术": ["教育", "培训", "老师", "教师", "学术", "研究", "学校", "学生", "升学", "考试", "教培"],
    "商业金融": ["商业", "创业", "金融", "投资", "生意", "开店", "销售", "市场", "贸易", "零售", "经商", "融资"],
    "医疗科研": ["医疗", "医生", "护士", "医院", "科研", "生物", "医药", "健康", "临床", "药"],
}


def detect_industry(profile: dict) -> str:
    """从档案文本自动识别行业领域（关键词命中计数，返回命中最多者）"""
    text = " ".join(str(v) for v in profile.values() if isinstance(v, str))
    scores = {ind: sum(1 for kw in kws if kw in text) for ind, kws in INDUSTRY_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else ""


def reorder_cases_by_industry(cases: list, industry: str) -> list:
    """将匹配行业的近现代案例排到知识库上下文最前（其余保持原序），便于 LLM 优先对标"""
    if not industry:
        return cases
    matched = [c for c in cases if c.get("industry") == industry]
    rest = [c for c in cases if c.get("industry") != industry]
    return matched + rest


# 定数类表述黑名单（第一层硬拦截）
FATAL_WORDS = [
    "注定", "天意不可违", "命中注定", "宿命", "一定成功", "必然失败",
    "无法改变", "命里注定", "天注定", "万无一失",
]
SENSITIVE_WORDS = [
    # 证券/金融操作指令 —— 只拦「明确的建议式短语」，不拦风险警示语境的裸词
    # （LLM 输出"警惕重仓加杠杆""设置止损平仓"是风控警示，应放行；"建议加仓买入"才是投资建议）
    "买入股票", "卖出股票", "买入基金", "卖出基金", "买入币",
    "推荐买入", "推荐卖出", "建议买入", "建议卖出", "建议加仓", "建议满仓",
    "建议重仓", "建议建仓", "建议平仓", "建议加杠杆", "建议梭哈", "建议抄底",
    # 医疗诊断（避免误伤"自我诊断/诊断处境"等自省用语）
    "抑郁症", "焦虑症", "精神分裂", "双相障碍", "开处方", "开具处方",
    # 法律意见
    "建议起诉", "建议索赔", "律师函", "应诉", "法律意见书",
]

_simhash_cache: dict[str, dict] = {}      # deviceId -> {simhash_key: {ts, report}}（内存态，数据主权不落库）
_case_stats: dict[str, int] = {}       # 案例名 -> 引用次数（内存统计，重启重置）
_review_queue: list[dict] = []         # 软校验待审核队列（内存，最多 100 条）


def load_prompt(name: str) -> str:
    p = PROMPT_DIR / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


def load_knowledge() -> dict:
    kb_file = KNOWLEDGE_DIR / "cases.json"
    if kb_file.exists():
        return json.loads(kb_file.read_text(encoding="utf-8"))
    return {"version": KNOWLEDGE_VERSION, "cases": []}


def gen_report_id() -> str:
    """后端权威生成报告 ID（LLM 生成的 reportId 日期会幻觉，不可信）"""
    import datetime as _dt
    import uuid as _uuid
    return f"HP-{_dt.datetime.now().strftime('%Y%m%d')}-{_uuid.uuid4().hex[:6].upper()}"


def now_iso() -> str:
    """后端权威生成 ISO 时间戳"""
    import datetime as _dt
    return _dt.datetime.now().isoformat(timespec="seconds")


def simhash(text: str, bits: int = 64) -> str:
    tokens = re.findall(r"[\u4e00-\u9fa5]{2,}|[a-zA-Z0-9]+", text)
    v = [0] * bits
    for tok in tokens:
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        for i in range(bits):
            v[i] += 1 if (h >> (i % 64)) & 1 else -1
    return "".join("1" if x > 0 else "0" for x in v)


def hamming_distance(a: str, b: str) -> int:
    return sum(c1 != c2 for c1, c2 in zip(a, b))


def find_similar_cached(device_id: str, simhash_key: str, max_hamming: int = 3, max_age: int = 7 * 86400) -> Optional[dict]:
    """在指定 deviceId 的缓存子集里查找 7 天内、汉明距离 ≤ max_hamming 的相似档案推演（跨用户隔离）"""
    now = time.time()
    for k, v in _simhash_cache.get(device_id, {}).items():
        if now - v["ts"] < max_age and hamming_distance(simhash_key, k) <= max_hamming:
            return v
    return None


def normalize_path_names(report: dict) -> dict:
    """路径名归一化：把 LLM 输出的带括号/别名变体统一映射到 4 个固定标准名。

    保证轨迹图聚合与跨期对比稳定（否则「守正待时」与「守正待时（稳健守成）」会被拆成两条线）。
    """
    paths = report.get("paths")
    if not isinstance(paths, list):
        return report
    for p in paths:
        if not isinstance(p, dict):
            continue
        raw = str(p.get("name", "") or "").strip()
        if not raw:
            continue
        matched = None
        for std, keywords in PATH_NAME_ALIASES.items():
            if any(k in raw for k in keywords):
                matched = std
                break
        if matched and p.get("name") != matched:
            p["name"] = matched
    return report


def soft_validate(report: dict) -> list[str]:
    """第二层软校验（规则引擎，不调 LLM）—— 返回警告列表，供前端/后端记录"""
    warnings = []
    paths = report.get("paths", [])
    if not paths:
        warnings.append("未生成发展路径")
    elif len(paths) < 3:
        warnings.append("发展路径不足 3 条")
    risk = report.get("riskAnalysis", {})
    if not risk.get("warnings"):
        warnings.append("缺少风险预警条件")
    if not risk.get("sensitivity"):
        warnings.append("缺少关键变量敏感性分析")
    if not report.get("summary"):
        warnings.append("缺少一分钟速览摘要")
    # 谨慎性表述密度检查
    text = json.dumps(report, ensure_ascii=False)
    cautious = sum(text.count(w) for w in ["风险", "止损", "不确定", "代价", "谨慎", "可能"])
    if cautious < 5:
        warnings.append("谨慎性表述偏少")
    return warnings


def record_case_references(report: dict) -> None:
    """从报告提取被对标的历史人物名，累加引用频次统计（持久化到 case_stats 表）"""
    bench = report.get("macroAnalysis", {}).get("historicalBenchmark", {})
    figures = bench.get("ancientFigures", []) + bench.get("modernFigures", [])
    names = {fig.get("name", "") for fig in figures if fig.get("name")}
    if not names:
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        for name in names:
            conn.execute(
                "INSERT INTO case_stats (figure, ref_count, last_ref_at) VALUES (?, 1, ?) "
                "ON CONFLICT(figure) DO UPDATE SET ref_count = ref_count + 1, last_ref_at = excluded.last_ref_at",
                (name, now_iso()),
            )
        conn.commit()
    finally:
        conn.close()


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


def _init_db() -> None:
    """初始化 SQLite 用户表（仅存用户身份 + 额度元数据，不存用户档案/报告）"""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                device_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                last_active_at TEXT NOT NULL,
                free_used INTEGER NOT NULL DEFAULT 0,
                purchased INTEGER NOT NULL DEFAULT 0,
                purchased_used INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS case_stats (
                figure TEXT PRIMARY KEY,
                ref_count INTEGER NOT NULL DEFAULT 0,
                last_ref_at TEXT NOT NULL DEFAULT ''
            )
        """)
        conn.commit()
    finally:
        conn.close()


def get_quota(device_id: str) -> dict:
    """查询用户剩余次数（免费剩余 + 付费剩余 + 总计）"""
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            "SELECT free_used, purchased, purchased_used FROM users WHERE device_id = ?", (device_id,)
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return {
            "freeTotal": FREE_QUOTA, "freeRemaining": FREE_QUOTA,
            "paidRemaining": 0, "totalRemaining": FREE_QUOTA,
        }
    free_used, purchased, purchased_used = row
    free_remaining = max(0, FREE_QUOTA - free_used)
    paid_remaining = max(0, purchased - purchased_used)
    return {
        "freeTotal": FREE_QUOTA, "freeRemaining": free_remaining,
        "paidRemaining": paid_remaining, "totalRemaining": free_remaining + paid_remaining,
    }


def enforce_quota(device_id: str = "anonymous") -> None:
    """免费3次 + 付费次数 额度检查与扣减（免费额度终身固定，用完返回 402 需付费）"""
    from datetime import datetime
    now_iso = datetime.now().isoformat(timespec="seconds")
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            "SELECT free_used, purchased, purchased_used FROM users WHERE device_id = ?", (device_id,)
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO users (device_id, created_at, last_active_at, free_used, purchased, purchased_used) VALUES (?, ?, ?, 0, 0, 0)",
                (device_id, now_iso, now_iso),
            )
            free_used, purchased, purchased_used = 0, 0, 0
        else:
            free_used, purchased, purchased_used = row

        free_remaining = FREE_QUOTA - free_used
        paid_remaining = purchased - purchased_used

        if free_remaining <= 0 and paid_remaining <= 0:
            raise HTTPException(status_code=402, detail="免费次数已用完，请购买次数后继续推演")

        # 优先扣免费额度，再扣付费额度
        if free_remaining > 0:
            conn.execute(
                "UPDATE users SET free_used = free_used + 1, last_active_at = ? WHERE device_id = ?",
                (now_iso, device_id),
            )
        else:
            conn.execute(
                "UPDATE users SET purchased_used = purchased_used + 1, last_active_at = ? WHERE device_id = ?",
                (now_iso, device_id),
            )
        conn.commit()
    finally:
        conn.close()


_init_db()  # 模块加载时初始化用户表


# ---------- 登录 / 账号体系 ----------
_sessions: dict[str, str] = {}   # token -> username（内存态，重启需重新登录）


def _hash_password(password: str, salt_hex: str = "") -> tuple[str, str]:
    """pbkdf2_hmac 加密，返回 (hash_hex, salt_hex)"""
    salt = salt_hex or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000).hex()
    return h, salt


def _issue_token(username: str) -> str:
    token = secrets.token_hex(32)
    _sessions[token] = username
    return token


def register_account(username: str, password: str) -> dict:
    """注册账号，返回 {token, username}"""
    conn = sqlite3.connect(DB_PATH)
    try:
        exists = conn.execute("SELECT 1 FROM accounts WHERE username = ?", (username,)).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="用户名已存在")
        h, salt = _hash_password(password)
        conn.execute(
            "INSERT INTO accounts (username, password_hash, salt, created_at) VALUES (?, ?, ?, ?)",
            (username, h, salt, now_iso()),
        )
        conn.commit()
    finally:
        conn.close()
    return {"token": _issue_token(username), "username": username}


def login_account(username: str, password: str) -> dict:
    """登录账号，返回 {token, username}"""
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute("SELECT password_hash, salt FROM accounts WHERE username = ?", (username,)).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    h, _ = _hash_password(password, row[1])
    if not secrets.compare_digest(h, row[0]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return {"token": _issue_token(username), "username": username}


def resolve_identity(x_device_id: Optional[str], x_auth_token: Optional[str]) -> tuple[str, Optional[str]]:
    """解析身份键：(identity_key, username_or_None)。
    登录：identity = 'u:' + username；匿名：identity = device_id 或 anonymous。"""
    if x_auth_token:
        username = _sessions.get(x_auth_token)
        if username:
            return "u:" + username, username
    return x_device_id or "anonymous", None


def parse_json_safe(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


async def call_llm(messages: list, temperature: float = 0.7, provider: str = "deepseek") -> str:
    p = PROVIDERS[resolve_provider(provider)]
    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(
            f"{p['base_url']}/chat/completions",
            headers={"Authorization": f"Bearer {p['api_key']}"},
            json={
                "model": p["model"],
                "messages": messages,
                "response_format": {"type": "json_object"},
                "temperature": temperature,
            },
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"模型调用失败 {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def run_consistency(profile: dict, paths: list[dict], provider: str = "deepseek") -> str:
    """3 次低温并行推理，返回一致性等级「高/中/低」。

    一致性 = 3 次低温推理对各路径评分的吻合程度（标准差越小越一致），
    映射为三档字符串，与默认值「中」及前端渲染语义统一。
    """
    prompt = load_prompt("consistency_prompt_v1.7.txt")
    path_names = [p.get("name", "") for p in paths]
    user_content = json.dumps({"人物档案": profile, "路径列表": path_names}, ensure_ascii=False)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_content},
    ]

    async def one_run():
        raw = await call_llm(messages, temperature=0.3, provider=provider)
        return parse_json_safe(raw).get("scores", [])

    try:
        runs = await asyncio.gather(one_run(), one_run(), one_run())
    except Exception:
        return "中"

    # 收集每个路径的评分（主推演 1 个 + 3 次并行 3 个）
    name_to_scores: dict[str, list] = {p.get("name"): [float(p.get("score", 0) or 0)] for p in paths}
    for run in runs:
        for item in run:
            name = item.get("name")
            if name in name_to_scores:
                try:
                    name_to_scores[name].append(float(item.get("score", 0) or 0))
                except (TypeError, ValueError):
                    pass

    stds = [statistics.stdev(s) for s in name_to_scores.values() if len(s) >= 3]
    if not stds:
        return "中"
    avg_std = sum(stds) / len(stds)
    # 标准差越小 = 3 次低温推理越吻合 = 一致性越高（语义与字段名一致）
    if avg_std < 0.4:
        return "高"
    if avg_std < 0.9:
        return "中"
    return "低"


# ---------- 请求模型 ----------
class ParseRequest(BaseModel):
    text: str = Field(..., min_length=1)
    provider: Optional[str] = None


class DeduceRequest(BaseModel):
    profile: dict = Field(...)
    industry: Optional[str] = None
    provider: Optional[str] = None
    customCases: list[dict] = Field(default_factory=list)


class Adjustment(BaseModel):
    field: str
    label: str
    delta: float = Field(..., ge=-0.5, le=0.5)


class RecalcRequest(BaseModel):
    profile: dict = Field(...)
    paths: list[dict] = Field(...)
    adjustments: list[Adjustment] = Field(...)
    provider: Optional[str] = None


class DeviationRequest(BaseModel):
    predictions: list[str] = Field(..., min_length=1)
    actualEvents: str = Field(...)
    provider: Optional[str] = None


class CompareRequest(BaseModel):
    profile: dict = Field(...)
    optionA: str = Field(..., min_length=1)
    optionB: str = Field(..., min_length=1)
    provider: Optional[str] = None
    customCases: list[dict] = Field(default_factory=list)


class ContinueRequest(BaseModel):
    profile: dict = Field(...)
    previousReport: dict = Field(default_factory=dict)
    deviation: dict = Field(default_factory=dict)
    actualEvents: str = Field(default="")
    industry: Optional[str] = None
    provider: Optional[str] = None
    customCases: list[dict] = Field(default_factory=list)


class AuthRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=32)
    password: str = Field(..., min_length=4, max_length=64)


# ---------- 端点 ----------
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "providers": {
            k: {"name": v["name"], "model": v["model"], "configured": bool(v["api_key"])}
            for k, v in PROVIDERS.items()
        },
        "default_provider": DEFAULT_PROVIDER,
        "prompt_version": PROMPT_VERSION,
        "knowledge_version": KNOWLEDGE_VERSION,
    }


@app.post("/api/auth/register")
def auth_register(req: AuthRequest):
    """注册账号：用户名 + 密码"""
    username = req.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="用户名不能为空")
    return register_account(username, req.password)


@app.post("/api/auth/login")
def auth_login(req: AuthRequest):
    """登录账号：返回 token"""
    return login_account(req.username.strip(), req.password)


@app.post("/api/auth/logout")
def auth_logout(x_auth_token: Optional[str] = Header(None, alias="X-Auth-Token")):
    """登出：作废 token"""
    if x_auth_token:
        _sessions.pop(x_auth_token, None)
    return {"ok": True}


@app.get("/api/auth/me")
def auth_me(x_auth_token: Optional[str] = Header(None, alias="X-Auth-Token"),
            x_device_id: Optional[str] = Header(None, alias="X-Device-Id")):
    """查询当前登录状态：返回 username + 额度"""
    identity, username = resolve_identity(x_device_id, x_auth_token)
    return {"authenticated": username is not None, "username": username, "credits": get_quota(identity)}


@app.get("/api/credits")
def credits(x_device_id: Optional[str] = Header(None, alias="X-Device-Id"),
            x_auth_token: Optional[str] = Header(None, alias="X-Auth-Token")):
    """查询当前用户剩余推演次数（免费剩余 + 付费剩余 + 总计）"""
    identity, _ = resolve_identity(x_device_id, x_auth_token)
    return get_quota(identity)


@app.post("/api/orders")
async def create_order(x_device_id: Optional[str] = Header(None, alias="X-Device-Id")):
    """创建付费订单（支付接口预留，后续接入支付宝/微信后返回支付跳转链接/二维码）"""
    # TODO: 接入支付宝当面付 + 微信 Native 支付
    raise HTTPException(status_code=501, detail="支付功能即将上线，敬请期待")


@app.post("/api/payment/callback")
async def payment_callback():
    """支付异步回调（支付宝/微信支付接入后实现验签 + 加次数）"""
    # TODO: 验证签名 → 确认支付成功 → 增加用户 purchased 次数
    raise HTTPException(status_code=501, detail="支付回调未接入")


@app.get("/api/knowledge")
def knowledge():
    """返回内置历史知识库（只读），含版本号与全部案例"""
    kb = load_knowledge()
    cases = kb.get("cases", [])
    return {"version": KNOWLEDGE_VERSION, "count": len(cases), "cases": cases}


@app.post("/api/parse")
async def parse(req: ParseRequest):
    """自然语言 → 结构化档案预览（解析 Prompt，JSON mode）"""
    provider = resolve_provider(req.provider)
    if not PROVIDERS[provider]["api_key"]:
        raise HTTPException(status_code=503, detail=f"{PROVIDERS[provider]['name']} API Key 未配置")
    prompt = load_prompt("parse_prompt_v1.7.txt")
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": req.text},
    ]
    raw = await call_llm(messages, temperature=0.1, provider=provider)
    try:
        data = parse_json_safe(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="解析结果格式异常，请重试")
    return data


@app.post("/api/deduce")
async def deduce(req: DeduceRequest, x_device_id: Optional[str] = Header(None, alias="X-Device-Id"),
                 x_auth_token: Optional[str] = Header(None, alias="X-Auth-Token")):
    """档案 + 知识上下文 → 推演报告（推演 Prompt，JSON mode + 双层校验 + 一致性系数）"""
    provider = resolve_provider(req.provider)
    if not PROVIDERS[provider]["api_key"]:
        raise HTTPException(status_code=503, detail=f"{PROVIDERS[provider]['name']} API Key 未配置")
    identity, _ = resolve_identity(x_device_id, x_auth_token)
    enforce_quota(identity)

    comp = completeness(req.profile)

    # 相似档案 SimHash 缓存复用（完整度>80% 且命中近期相似档案时直接返回）
    if comp > 80:
        simhash_key = simhash(json.dumps(req.profile, ensure_ascii=False, sort_keys=True))
        cached = find_similar_cached(identity, simhash_key)
        if cached:
            reused = json.loads(json.dumps(cached["report"], ensure_ascii=False))
            reused.setdefault("meta", {})["reusedFromSimilar"] = True
            reused["meta"]["completenessScore"] = comp
            reused["reportId"] = gen_report_id()
            reused["timestamp"] = now_iso()
            return reused

    prompt = load_prompt("system_prompt_v1.7.txt")
    knowledge = load_knowledge()

    # 三级漏斗过滤知识库（行业自动识别 + 世道过滤 + 原型匹配 + 相关性 top-N）
    industry = req.industry or detect_industry(req.profile)
    builtin_cases = knowledge.get("cases", [])
    filtered_cases, funnel_stats = funnel.funnel_cases(req.profile, industry, builtin_cases)
    # 用户自定义案例排最前（优先对标），漏斗后的内置案例随后
    combined_cases = list(req.customCases) + filtered_cases

    user_content = json.dumps(
        {
            "人物档案": req.profile,
            "档案完整度": f"{comp}%（{'信息严重不足' if comp < 40 else '信息较完整' if comp < 70 else '信息充分'}）",
            "行业标签": industry,
            "历史知识库上下文": combined_cases,
        },
        ensure_ascii=False,
    )
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_content},
    ]

    # 主推演（温度 0.7）
    raw = await call_llm(messages, temperature=0.7, provider=provider)

    # 第一层硬拦截
    block = hard_validate(raw)
    if block:
        raise HTTPException(status_code=400, detail=block)

    try:
        report = parse_json_safe(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="推演结果格式异常，请重试")

    # 路径名归一化（在软校验与一致性系数之前执行，确保后续都基于标准名）
    report = normalize_path_names(report)

    # 第二层软校验（规则引擎，记录警告）
    soft_warnings = soft_validate(report)
    if soft_warnings:
        _review_queue.append({
            "ts": time.time(),
            "reportId": report.get("reportId", ""),
            "profileName": req.profile.get("name", ""),
            "warnings": soft_warnings,
        })
        _review_queue[:] = _review_queue[-100:]

    # 3 次低温并行一致性系数（完整度≥70% 才触发，控制成本）
    consistency = "中"
    if comp >= 70 and report.get("paths"):
        consistency = await run_consistency(req.profile, report["paths"], provider=provider)

    # 注入元信息（后端权威版本号）
    if "meta" not in report:
        report["meta"] = {}
    report["meta"].update({
        "knowledgeVersion": KNOWLEDGE_VERSION,
        "promptVersion": PROMPT_VERSION,
        "modelVersion": PROVIDERS[provider]["model"],
        "completenessScore": comp,
        "consistencyCoefficient": consistency,
        "detectedIndustry": industry,
        "softCheckWarnings": soft_warnings,
        "funnelStats": funnel_stats,
    })

    # 后端权威覆盖 reportId/timestamp（LLM 生成的日期会幻觉，不可信）
    report["reportId"] = gen_report_id()
    report["timestamp"] = now_iso()

    # 相似档案 SimHash 缓存（完整度>80% 才存储，按 deviceId 隔离）
    if comp > 80:
        simhash_key = simhash(json.dumps(req.profile, ensure_ascii=False, sort_keys=True))
        _simhash_cache.setdefault(device_id, {})[simhash_key] = {"ts": time.time(), "report": report}

    # 案例引用频次统计
    record_case_references(report)

    return report


@app.post("/api/recalc")
async def recalc(req: RecalcRequest, x_device_id: Optional[str] = Header(None, alias="X-Device-Id"),
                 x_auth_token: Optional[str] = Header(None, alias="X-Auth-Token")):
    """参数微调·快速重算 —— 复用原推演上下文，仅增量更新受影响的路径评分与风险提示"""
    provider = resolve_provider(req.provider)
    if not PROVIDERS[provider]["api_key"]:
        raise HTTPException(status_code=503, detail=f"{PROVIDERS[provider]['name']} API Key 未配置")
    enforce_quota(resolve_identity(x_device_id, x_auth_token)[0])

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

    raw = await call_llm(messages, temperature=0.3, provider=provider)

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


@app.post("/api/deviation")
async def deviation(req: DeviationRequest, x_device_id: Optional[str] = Header(None, alias="X-Device-Id"),
                    x_auth_token: Optional[str] = Header(None, alias="X-Auth-Token")):
    """推演偏差自检 —— 对比三条预测与现实情况，LLM 输出准确项/偏差项/原因"""
    provider = resolve_provider(req.provider)
    if not PROVIDERS[provider]["api_key"]:
        raise HTTPException(status_code=503, detail=f"{PROVIDERS[provider]['name']} API Key 未配置")
    enforce_quota(resolve_identity(x_device_id, x_auth_token)[0])

    prompt = load_prompt("deviation_prompt_v2.txt")
    user_content = json.dumps(
        {"predictions": req.predictions, "actualEvents": req.actualEvents},
        ensure_ascii=False,
    )
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_content},
    ]
    raw = await call_llm(messages, temperature=0.2, provider=provider)
    try:
        result = parse_json_safe(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="偏差分析结果格式异常，请重试")

    result.setdefault("accurate", [])
    result.setdefault("deviated", [])
    result.setdefault("analysis", "")
    return result


@app.post("/api/compare")
async def compare(req: CompareRequest, x_device_id: Optional[str] = Header(None, alias="X-Device-Id"),
                  x_auth_token: Optional[str] = Header(None, alias="X-Auth-Token")):
    """二选一专项对比推演 —— 对比两个选项的可行性/得失/风险，给出推荐"""
    provider = resolve_provider(req.provider)
    if not PROVIDERS[provider]["api_key"]:
        raise HTTPException(status_code=503, detail=f"{PROVIDERS[provider]['name']} API Key 未配置")
    enforce_quota(resolve_identity(x_device_id, x_auth_token)[0])

    prompt = load_prompt("compare_prompt_v2.txt")
    knowledge = load_knowledge()
    industry = detect_industry(req.profile)
    filtered_cases, _ = funnel.funnel_cases(req.profile, industry, knowledge.get("cases", []))
    combined_cases = list(req.customCases) + filtered_cases

    user_content = json.dumps(
        {
            "人物档案": req.profile,
            "选项A": req.optionA,
            "选项B": req.optionB,
            "历史知识库上下文": combined_cases,
        },
        ensure_ascii=False,
    )
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_content},
    ]
    raw = await call_llm(messages, temperature=0.5, provider=provider)

    block = hard_validate(raw)
    if block:
        raise HTTPException(status_code=400, detail=block)

    try:
        result = parse_json_safe(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="对比推演结果格式异常，请重试")

    result.setdefault("options", [])
    result.setdefault("recommendation", "")
    result.setdefault("keyDifference", "")
    return result


@app.post("/api/continue")
async def continue_deduce(req: ContinueRequest, x_device_id: Optional[str] = Header(None, alias="X-Device-Id"),
                          x_auth_token: Optional[str] = Header(None, alias="X-Auth-Token")):
    """持仓式增量再推演 —— 基于上次报告 + 偏差复盘 + 现实进展，输出校准后的新报告（结构同标准推演）"""
    provider = resolve_provider(req.provider)
    if not PROVIDERS[provider]["api_key"]:
        raise HTTPException(status_code=503, detail=f"{PROVIDERS[provider]['name']} API Key 未配置")
    enforce_quota(resolve_identity(x_device_id, x_auth_token)[0])

    comp = completeness(req.profile)

    # 三级漏斗过滤知识库
    industry = req.industry or detect_industry(req.profile)
    builtin_cases = load_knowledge().get("cases", [])
    filtered_cases, funnel_stats = funnel.funnel_cases(req.profile, industry, builtin_cases)
    combined_cases = list(req.customCases) + filtered_cases

    # 两条 system 消息：标准报告结构 + 校准语义
    user_content = json.dumps(
        {
            "人物档案": req.profile,
            "档案完整度": f"{comp}%（{'信息严重不足' if comp < 40 else '信息较完整' if comp < 70 else '信息充分'}）",
            "行业标签": industry,
            "历史知识库上下文": combined_cases,
            "上次推演报告": req.previousReport,
            "偏差复盘结果": req.deviation,
            "现实进展": req.actualEvents,
        },
        ensure_ascii=False,
    )
    messages = [
        {"role": "system", "content": load_prompt("system_prompt_v1.7.txt")},
        {"role": "system", "content": load_prompt("continue_prompt_v1.txt")},
        {"role": "user", "content": user_content},
    ]

    raw = await call_llm(messages, temperature=0.6, provider=provider)

    # 第一层硬拦截
    block = hard_validate(raw)
    if block:
        raise HTTPException(status_code=400, detail=block)

    try:
        report = parse_json_safe(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="校准推演结果格式异常，请重试")

    # 路径名归一化（确保校准推演与标准推演的路径名对齐，跨期对比稳定）
    report = normalize_path_names(report)

    # 第二层软校验
    soft_warnings = soft_validate(report)
    if soft_warnings:
        _review_queue.append({
            "ts": time.time(),
            "reportId": report.get("reportId", ""),
            "profileName": req.profile.get("name", ""),
            "warnings": soft_warnings,
        })
        _review_queue[:] = _review_queue[-100:]

    # 3 次低温并行一致性系数
    consistency = "中"
    if comp >= 70 and report.get("paths"):
        consistency = await run_consistency(req.profile, report["paths"], provider=provider)

    # 注入元信息
    if "meta" not in report:
        report["meta"] = {}
    report["meta"].update({
        "knowledgeVersion": KNOWLEDGE_VERSION,
        "promptVersion": PROMPT_VERSION,
        "modelVersion": PROVIDERS[provider]["model"],
        "completenessScore": comp,
        "consistencyCoefficient": consistency,
        "detectedIndustry": industry,
        "softCheckWarnings": soft_warnings,
        "funnelStats": funnel_stats,
        "continueFrom": req.previousReport.get("reportId", ""),
    })

    # 后端权威覆盖 reportId/timestamp
    report["reportId"] = gen_report_id()
    report["timestamp"] = now_iso()

    record_case_references(report)
    return report


# ---------- 前端静态托管（Vue3 SPA，hash 路由） ----------
if FRONTEND_DIST.exists():
    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIST / "index.html")

    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8023)
