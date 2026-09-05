"""免费3次 + 付费墙逻辑测试 — 不调 LLM，验证额度扣减与 402 拦截"""
import sys, sqlite3
sys.path.insert(0, '.')
import main

# 清空测试用户
conn = sqlite3.connect(main.DB_PATH)
conn.execute("DELETE FROM users WHERE device_id IN ('freetest', 'paidtest')")
conn.commit()
conn.close()

# 1. 新用户查询额度
q = main.get_quota("freetest")
assert q["freeRemaining"] == 3 and q["totalRemaining"] == 3, f"初始额度异常: {q}"
print(f"✅ 新用户额度：免费 {q['freeRemaining']} / {q['freeTotal']}")

# 2. 用满 3 次免费
for i in range(3):
    main.enforce_quota("freetest")
q = main.get_quota("freetest")
assert q["freeRemaining"] == 0 and q["totalRemaining"] == 0, f"3次后额度异常: {q}"
print(f"✅ 用满 3 次免费后：免费剩余 {q['freeRemaining']}，总计 {q['totalRemaining']}")

# 3. 第 4 次 → 402 付费墙
try:
    main.enforce_quota("freetest")
    print("❌ 第4次未被拦截")
except Exception as e:
    status = getattr(e, 'status_code', None)
    detail = getattr(e, 'detail', str(e))
    assert status == 402, f"应为 402，实际 {status}: {detail}"
    print(f"✅ 第4次被 402 拦截：{detail}")

# 4. 模拟付费（手动加 purchased 次数）
conn = sqlite3.connect(main.DB_PATH)
conn.execute("UPDATE users SET purchased = purchased + 10 WHERE device_id = 'freetest'")
conn.commit()
conn.close()
q = main.get_quota("freetest")
assert q["paidRemaining"] == 10 and q["totalRemaining"] == 10
print(f"✅ 模拟购买 10 次后：付费剩余 {q['paidRemaining']}")

# 5. 付费后能继续推演，优先扣免费（已0）→ 扣付费
main.enforce_quota("freetest")
q = main.get_quota("freetest")
assert q["paidRemaining"] == 9
print(f"✅ 付费后推演 1 次：付费剩余 {q['paidRemaining']}")

print("\n=== 免费3次 + 付费墙逻辑全部通过 ===")
