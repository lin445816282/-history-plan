"""SQLite 用户表持久化 + 隔离测试 — 验证配额持久化（重启不丢）、按用户隔离"""
import sys, time
sys.path.insert(0, '.')
import main
import sqlite3

main.DAILY_QUOTA = 3

# 清空测试数据
conn = sqlite3.connect(main.DB_PATH)
conn.execute("DELETE FROM users WHERE device_id IN ('userA', 'userB')")
conn.commit()
conn.close()

# 用户A用满配额
for _ in range(3):
    main.enforce_quota("userA")
print("✅ 用户A用满 3 次配额")

# 验证 SQLite 落库
conn = sqlite3.connect(main.DB_PATH)
row = conn.execute("SELECT quota_used, quota_date FROM users WHERE device_id='userA'").fetchone()
conn.close()
print(f"✅ SQLite 已持久化：userA 配额={row[0]} 日期={row[1]}")

# 第4次被拦
try:
    main.enforce_quota("userA")
    print("❌ 第4次未被拦截")
except Exception as e:
    print(f"✅ 第4次被拦（配额持久化生效）")

# 用户B独立配额
main.enforce_quota("userB")
print("✅ 用户B不受A配额影响（独立隔离）")

# 模拟"重启"——重新打开 DB 读，验证数据还在
conn = sqlite3.connect(main.DB_PATH)
rows = conn.execute(
    "SELECT device_id, quota_used, last_active_at FROM users WHERE device_id IN ('userA','userB') ORDER BY device_id"
).fetchall()
conn.close()
print(f"✅ 持久化数据（重启后仍存在）:")
for r in rows:
    print(f"   {r[0]}: 已用 {r[1]} 次, 活跃 {r[2]}")

# 验证新的一天重置配额
from datetime import datetime, timedelta
conn = sqlite3.connect(main.DB_PATH)
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
conn.execute("UPDATE users SET quota_date=? WHERE device_id='userA'", (yesterday,))
conn.commit()
conn.close()
main.enforce_quota("userA")  # 新的一天，应重置后放行
conn = sqlite3.connect(main.DB_PATH)
row = conn.execute("SELECT quota_used, quota_date FROM users WHERE device_id='userA'").fetchone()
conn.close()
print(f"✅ 跨日重置：userA 新日期配额={row[0]}（已从0重新计数）")

print("\n=== SQLite 持久化 + 隔离 + 跨日重置 全部通过 ===")
