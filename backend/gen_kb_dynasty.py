"""知识库全朝代增量生成 —— 读 people.json，逐断代逐批调用 LLM 生成案例
用法：python3 gen_kb_dynasty.py [start] [end]   # 跑 people.json 第 start~end 个 group（默认全部）
输出：knowledge/gen_extra_<era>.json
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

PEOPLE = json.load(open(f"{BASE}/people.json", encoding="utf-8"))["groups"]

SYSTEM_PROMPT_TMPL = """你是一位中国历史人物推演案例编纂专家，精通二十四史。请为给定的人物各生成一条结构化推演案例，输出严格 JSON。

每个案例字段（全部必填，全中文）：
- name: 人物姓名。只填姓名本身（如「曹操」），严禁写成事件或标题（如「曹操挟天子令诸侯」「诸葛亮北伐」都是错误的）
- prototype: 人生原型/身份类型（2-6字）。必须选这类词：创业者/守成者/谋士/将才/权臣/改革者/失意者/冒险投机者/清流/循吏/隐士/世家子弟/寒门崛起/投机家/文人/匠人。严禁填称号（如枭雄/武圣/忠臣/奸雄都是错误的）
- era: 时代（固定填「{era}」）
- worldTag: 世道标签（乱世/变革世/太平世 三选一）
- context: 现代白话简述（40-80字），点明此人的核心处境与最关键的一次抉择
- ancientContext: 所处时代的制度与环境背景（30-60字）
- boundaryNote: 古今差异边界（20-40字，格式「古代靠X，现代靠Y」）
- principle: 提炼的核心事理原则（15-30字）
- outcome: success 或 failure（实事求是，不能全成功）
- lesson: 一句话教训（20-40字）

背景提示：{tag_hint}

硬性要求：
1. 只输出一个 JSON 对象，格式 {{"cases": [{{...}}, ...]}}，不要 markdown 代码块，不要任何解释文字
2. name 必须与人物列表中的姓名逐字一致
3. 深度提炼，杜绝空话套话；principle 和 lesson 必须可迁移到现代个人决策
4. outcome 依据史实判定，失败人物必须如实标 failure
5. 每一条 case 内字段名与上面一致，不要多也不要少"""

REQUIRED = ["name", "prototype", "era", "worldTag", "context",
            "ancientContext", "boundaryNote", "principle", "outcome", "lesson"]


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


def run_group(g):
    era, prefix, names, hint = g["era"], g["prefix"], g["names"], g["tag_hint"]
    print(f"\n===== {era} 共 {len(names)} 人 =====", flush=True)
    sys_prompt = SYSTEM_PROMPT_TMPL.format(era=era, tag_hint=hint)
    out = []
    BATCH = 10
    for i in range(0, len(names), BATCH):
        batch = names[i:i + BATCH]
        user = "人物列表：\n" + "、".join(batch) + "\n\n请按以上人物逐一生成案例，输出 JSON。"
        print(f"  批次 {i // BATCH + 1}: {batch[0]} ~ {batch[-1]} ...", flush=True)
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
            if c.get("name", "") not in names:
                err = err or f"name 不在清单: {c.get('name')}"
            if err:
                print(f"    [跳过] {c.get('name','?')}: {err}", flush=True)
                continue
            c["id"] = f"{prefix}{len(out) + 1}"
            c["type"] = "ancient"
            out.append(c)
        print(f"    累计有效: {len(out)}", flush=True)
    with open(f"{BASE}/knowledge/gen_extra_{era}.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"  {era} 完成，落盘 {len(out)} 条", flush=True)
    return era, len(out)


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else len(PEOPLE)
    groups = PEOPLE[start:end]
    total = 0
    for g in groups:
        era, n = run_group(g)
        total += n
    print(f"\n===== 本批完成，共 {total} 条 =====", flush=True)


if __name__ == "__main__":
    main()
