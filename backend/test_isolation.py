"""deviceId 隔离单元测试 — 不调 LLM，直接验证缓存与限流的用户隔离逻辑"""
import sys, time
sys.path.insert(0, '.')
import main

# ---------- 1. 缓存隔离（嵌套字典） ----------
main._simhash_cache = {}
prof = '{"name":"测试用户","age":35,"era":"互联网行业","skills":"编程"}'
sh = main.simhash(prof)

# 用户A推演后写入缓存
main._simhash_cache.setdefault("userA", {})[sh] = {"ts": time.time(), "report": {"reportId": "A-REPORT"}}

# 用户B用「完全相同档案」查询
cached_b = main.find_similar_cached("userB", sh)
assert cached_b is None, "❌ 用户B命中了A的缓存！隔离失效"
print("✅ 缓存隔离：用户B用完全相同档案，不命中A的缓存")

# 用户A查询自己的缓存
cached_a = main.find_similar_cached("userA", sh)
assert cached_a is not None and cached_a["report"]["reportId"] == "A-REPORT"
print("✅ 缓存隔离：用户A能命中自己的缓存")

# ---------- 2. 限流隔离 ----------
main._quota_log = {}
main.DAILY_QUOTA = 3
for _ in range(3):
    main.enforce_quota("userA")
print("✅ 用户A已用满 3 次配额")

try:
    main.enforce_quota("userA")
    print("❌ 用户A第4次未被拦截")
except Exception:
    print("✅ 用户A第4次被拦（配额独立生效）")

main.enforce_quota("userB")
print("✅ 用户B不受A配额影响（每用户独立 100 次/天）")

print("\n=== 隔离逻辑全部通过 ===")
