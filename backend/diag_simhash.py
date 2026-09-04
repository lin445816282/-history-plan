"""复现 SimHash，验证不同档案的汉明距离是否会被误判为相似"""
import json, hashlib, re

def simhash(text, bits=64):
    tokens = re.findall(r"[\u4e00-\u9fa5]{2,}|[a-zA-Z0-9]+", text)
    v = [0] * bits
    for tok in tokens:
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        for i in range(bits):
            v[i] += 1 if (h >> (i % 64)) & 1 else -1
    return "".join("1" if x > 0 else "0" for x in v)

def hamming(a, b):
    return sum(c1 != c2 for c1, c2 in zip(a, b))

profiles = {
    "程序员": {"name":"张伟","skills":"Java/Go 后端、系统设计","mindset":"想从纯技术转管理","financialResources":"存款40万","shortTermGoal":"一年内晋升技术经理","keyDecisions":"是否接受晋升 offer 放弃编码","externalChanges":"AI 辅助编程冲击"},
    "淘宝卖家": {"name":"李芳","skills":"选品、运营、直播","mindset":"想把单店做成品牌","financialResources":"流动资金20万","shortTermGoal":"月销翻倍","keyDecisions":"是否压货扩品","externalChanges":"直播电商红利退坡"},
    "教培老师": {"name":"王强","skills":"教学、课程设计","mindset":"教培受政策冲击想转型","financialResources":"存款30万","shortTermGoal":"找到转型方向","keyDecisions":"转型知识付费还是考编","externalChanges":"AI 教育产品崛起"},
}

shs = {}
for name, p in profiles.items():
    sh = simhash(json.dumps(p, ensure_ascii=False, sort_keys=True))
    shs[name] = sh
    print(f"{name}: {sh}")

print("\n两两汉明距离:")
names = list(profiles.keys())
for i in range(len(names)):
    for j in range(i+1, len(names)):
        d = hamming(shs[names[i]], shs[names[j]])
        print(f"  {names[i]} vs {names[j]}: {d}")

print("\n=== 关键：simhash 对 token 数的敏感性 ===")
# 测试：同一个档案，字段略有不同（1个字不同）
p_base = profiles["程序员"]
p_var = dict(p_base); p_var["skills"] = "Java/Go 后端、系统设计、架构"
d = hamming(simhash(json.dumps(p_base, ensure_ascii=False, sort_keys=True)), simhash(json.dumps(p_var, ensure_ascii=False, sort_keys=True)))
print(f"  程序员(原) vs 程序员(改1字段): 汉明距离 {d}")

# 测试：完全不同的两个短档案
p_a = {"name":"张三","skills":"写作"}
p_b = {"name":"李四","skills":"销售"}
d = hamming(simhash(json.dumps(p_a, ensure_ascii=False, sort_keys=True)), simhash(json.dumps(p_b, ensure_ascii=False, sort_keys=True)))
print(f"  {{张三,写作}} vs {{李四,销售}}: 汉明距离 {d}")

# 测试：空档案 vs 有内容
d = hamming(simhash(""), simhash(json.dumps(p_base, ensure_ascii=False, sort_keys=True)))
print(f"  空 vs 程序员: 汉明距离 {d}")
