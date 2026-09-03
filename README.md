# 个人历史推演规划系统（History-Plan）V1.7

B/S 决策辅助工具：录入多人物档案 → 借历史知识库 + 大模型 → 输出结构化推演报告。
定位：自省谋事，谋事在人，顺时知变。非算命占卜、非投资/心理/法律建议。

## 架构
- **前端**：Vue3 + Vite 静态 SPA，数据存 IndexedDB（HistoryPlanDB v3，5 store），符合数据主权
- **后端**：FastAPI 薄代理（:8010），仅做 LLM 中转——藏 API Key、限流、双层输出校验、SimHash 相似缓存
- **模型**：DeepSeek（JSON mode 结构化输出）

## 目录
```
backend/
  main.py                    # FastAPI 薄代理（/api/parse + /api/deduce）
  prompts/                   # system_prompt_v1.7.txt + parse_prompt_v1.7.txt
  knowledge/cases.json       # 知识库（30-50 精选案例，M3 填充）
frontend/
  design-tokens/design-tokens.json   # UI Design Token 源
  src/db/db-schema.js        # IndexedDB Schema（可直接用）
  src/db/db-utils.js         # IndexedDB CRUD 工具类
  src/views/                 # 页面（骨架占位）
  src/styles/tokens.css      # Design Token → CSS 变量
docs/                        # 三份原始文档存档（需求/保障/配套）
```

## 里程碑
- **M1 基础加固** ✅ 骨架 + IndexedDB Schema + Design Token + Prompt 落地
- **M2 执行闭环**：档案 CRUD + 推演引擎对接 + 报告渲染 + 待办跟踪器
- **M3 信任闭环**：复盘 + 偏差自检 + 时间轴 + 导出
- **M4 验收打磨**：走查清单验收 + Bug 修复 + 部署 ct256.cn

## 启动
```bash
# 后端
cd backend && pip install -r requirements.txt
DEEPSEEK_API_KEY=xxx uvicorn main:app --port 8010
# 前端
cd frontend && npm install && npm run dev
```
