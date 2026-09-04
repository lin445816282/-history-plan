"""合并增量案例到 cases.json：去重 + 追加 + 更新 version + 校验"""
import json, os

BASE = os.path.expanduser("~/projects/history-plan/backend")
KB = f"{BASE}/knowledge/cases.json"

cases_obj = json.load(open(KB, encoding="utf-8"))
existing = cases_obj["cases"]
existing_names = {c["name"] for c in existing}
existing_ids = {c["id"] for c in existing}

added = 0
skipped = 0
for era in ["三国", "东汉", "西汉"]:
    f = f"{BASE}/knowledge/gen_extra_{era}.json"
    if not os.path.exists(f):
        print(f"!! 缺文件 {f}", flush=True)
        continue
    gen = json.load(open(f, encoding="utf-8"))
    for c in gen:
        if c["name"] in existing_names:
            skipped += 1
            continue
        if c["id"] in existing_ids:
            print(f"  !! id 冲突 {c['id']} ({c['name']})，重编号", flush=True)
            c["id"] = f"{c['id']}x{len(existing)}"
        existing.append(c)
        existing_names.add(c["name"])
        existing_ids.add(c["id"])
        added += 1

# 更新版本号
cases_obj["version"] = "k-v1.1"
json.dump(cases_obj, open(KB, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print(f"合并完成：新增 {added} 条，跳过重复 {skipped} 条，总计 {len(existing)} 条", flush=True)
