"""当代行业人物子库生成 —— modern 类型（industry 字段），用于行业对标
输出：knowledge/gen_extra_现代.json（合并时归入 modern 子库）
"""
import json, os, re, sys, time
import httpx

BASE = os.path.expanduser("~/projects/history-plan/backend")
API_KEY = ""
for line in open(os.path.expanduser("~/.keys.env"), encoding="utf-8"):
    if line.strip().startswith("DEEPSEEK_API_KEY="):
        API_KEY = line.strip().split("=", 1)[1].strip()

BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
MODEL = "deepseek-chat"

# 人物 -> industry（6 大领域，与后端 INDUSTRY_KEYWORDS 对齐）
GROUPS = [
    {"industry": "科技互联网", "names": ["任正非","马化腾","张一鸣","雷军","李彦宏","马云","刘强东","黄峥","王兴","丁磊","柳传志"]},
    {"industry": "制造工匠", "names": ["曹德旺","董明珠","宗庆后","张瑞敏","李书福","王传福","何享健"]},
    {"industry": "商业金融", "names": ["王健林","沈南鹏"]},
    {"industry": "医疗科研", "names": ["屠呦呦","钟南山","顾方舟","陈薇","吴孟超","施一公","钱七虎"]},
    {"industry": "文化创意", "names": ["莫言","刘慈欣","张艺谋","陈凯歌","吴京","郭德纲","李小龙","成龙","姚明","郎平"]},
    {"industry": "教育学术", "names": ["杨振宁","李政道","丘成桐","陈省身","吴文俊","俞敏洪"]},
]

SYSTEM_PROMPT = """你是一位中国近现代人物案例编纂专家。请为给定的人物各生成一条结构化案例，输出严格 JSON。

每个案例字段（全部必填，全中文）：
- name: 人物姓名。只填姓名本身，严禁写成事件或标题
- prototype: 人生原型/身份类型（2-6字）。可选：创新颠覆者/冒险拓荒者/长期价值投资者/匠心坚守者/文化守望者/梦想构建者/育人实践家/科研攻坚者/实业报国者/创业者/守成者/改革者。严禁填称号
- industry: 行业领域，固定填「{industry}」
- era: 时代，固定填「现代」
- worldTag: 世道标签（乱世/变革世/太平世 三选一）
- context: 现代白话简述（40-80字），点明此人的核心处境与最关键的一次抉择
- boundaryNote: 古今差异边界（20-40字，格式「古代靠X，现代靠Y」）
- principle: 提炼的核心事理原则（15-30字）
- outcome: success 或 failure（实事求是）
- lesson: 一句话教训（20-40字）

硬性要求：
1. 只输出一个 JSON 对象，格式 {{"cases": [{{...}}, ...]}}，不要 markdown 代码块，不要任何解释文字
2. name 必须与人物列表中的姓名逐字一致
3. 深度提炼，杜绝空话套话；principle 和 lesson 必须可迁移到现代个人决策
4. outcome 依据事实判定，不能全 success
5. 每一条 case 内字段名与上面一致，不要多也不要少"""

REQUIRED = ["name", "prototype", "industry", "era", "worldTag",
            "context", "boundaryNote", "principle", "outcome", "lesson"]


def call_deepseek(messages, retries=3):
    for attempt in range(retries):
        try:
            with httpx.Client(timeout=180) as client:
                resp = client.post(
                    f"{BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    json={"model": MODEL, "messages": messages,
                          "response_format": {"type": "json_object"}, "temperature": 0.7},
                )
            if resp.status_code != 200:
                print(f"    [API {resp.status_code}] {resp.text[:150]}", flush=True)
                time.sleep(3)
                continue
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"    [异常] {e}", flush=True)
            time.sleep(3)
    return None


def validate(case):
    for f in REQUIRED:
        if not str(case.get(f, "") or "").strip():
            return f"缺字段 {f}"
    if case["outcome"] not in ("success", "failure"):
        return f"outcome 非法 {case['outcome']}"
    if case["worldTag"] not in ("乱世", "变革世", "太平世"):
        return f"worldTag 非法 {case['worldTag']}"
    return None


def main():
    all_names = {n for g in GROUPS for n in g["names"]}
    out = []
    for g in GROUPS:
        industry, names = g["industry"], g["names"]
        print(f"\n===== {industry} 共 {len(names)} 人 =====", flush=True)
        sys_prompt = SYSTEM_PROMPT.format(industry=industry)
        for i in range(0, len(names), 10):
            batch = names[i:i + 10]
            user = "人物列表：\n" + "、".join(batch) + "\n\n请按以上人物逐一生成案例，输出 JSON。"
            print(f"  批次: {batch[0]} ~ {batch[-1]} ...", flush=True)
            raw = call_deepseek([
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user},
            ])
            if raw is None:
                print("  !! 批次失败，跳过", flush=True)
                continue
            try:
                raw = raw.strip()
                if raw.startswith("```"):
                    raw = re.sub(r"^```[a-zA-Z]*\s*", "", raw)
                    raw = re.sub(r"\s*```$", "", raw)
                data = json.loads(raw)
                items = data.get("cases", data if isinstance(data, list) else [])
            except Exception as e:
                print(f"  !! JSON 解析失败: {e}", flush=True)
                continue
            for c in items:
                err = validate(c)
                if c.get("name", "") not in all_names:
                    err = err or f"name 不在清单: {c.get('name')}"
                if err:
                    print(f"    [跳过] {c.get('name','?')}: {err}", flush=True)
                    continue
                c["id"] = f"m{len(out) + 19:02d}"  # 现有 modern 18 个 m01-m18，从 m19 续
                c["type"] = "modern"
                out.append(c)
            print(f"    累计有效: {len(out)}", flush=True)
    with open(f"{BASE}/knowledge/gen_extra_现代.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n===== 现代子库生成完成，共 {len(out)} 条 =====", flush=True)


if __name__ == "__main__":
    main()
