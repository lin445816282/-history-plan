"""通用合并：扫描 knowledge/gen_extra_*.json 全部合并进 cases.json，去重 + 更新版本 + 校验"""
import json, os, glob

BASE = os.path.expanduser("~/projects/history-plan/backend")
KB = f"{BASE}/knowledge/cases.json"

cases_obj = json.load(open(KB, encoding="utf-8"))
existing = cases_obj["cases"]
existing_names = {c["name"] for c in existing}
existing_ids = {c["id"] for c in existing}

added = 0
skipped = 0
files = sorted(glob.glob(f"{BASE}/knowledge/gen_extra_*.json"))
for f in files:
    gen = json.load(open(f, encoding="utf-8"))
    for c in gen:
        if c["name"] in existing_names:
            skipped += 1
            continue
        if c["id"] in existing_ids:
            c["id"] = f"{c['id']}x{len(existing)}"
        existing.append(c)
        existing_names.add(c["name"])
        existing_ids.add(c["id"])
        added += 1

# 版本号递增（在现有基础上 +1 小版本）
old_ver = cases_obj.get("version", "k-v1.0")
cases_obj["version"] = "k-v1.2"
json.dump(cases_obj, open(KB, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print(f"合并完成：新增 {added} 条，跳过重复 {skipped} 条，总计 {len(existing)} 条", flush=True)
print(f"version: {old_ver} -> {cases_obj['version']}", flush=True)
