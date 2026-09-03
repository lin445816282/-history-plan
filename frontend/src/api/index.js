// 后端薄代理 API client
// 用 vite base 动态计算，生产环境为 /history-plan/api，避免绝对路径 /api 落到根域名
const API_BASE = (import.meta.env.BASE_URL || '/').replace(/\/$/, '') + '/api'
const PROVIDER_KEY = 'hp_provider'

async function post(path, body) {
  const res = await fetch(API_BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    let detail = '请求失败 ' + res.status
    try { detail = (await res.json()).detail || detail } catch (_) {}
    throw new Error(detail)
  }
  return res.json()
}

// 当前选中的模型 provider（存 localStorage）
export function getProvider() {
  return localStorage.getItem(PROVIDER_KEY) || 'deepseek'
}

export function setProvider(p) {
  localStorage.setItem(PROVIDER_KEY, p)
}

// 自然语言 → 结构化档案预览
export const parseProfile = (text) => post('/parse', { text, provider: getProvider() })

// 档案 + 知识上下文 → 推演报告
export const deduce = (profile, industry, customCases) => post('/deduce', { profile, industry, customCases, provider: getProvider() })

// 参数微调·快速重算 —— 复用原推演上下文，增量更新评分/风险
export const recalc = (profile, paths, adjustments) => post('/recalc', { profile, paths, adjustments, provider: getProvider() })

// 推演偏差自检 —— 对比预测与现实，LLM 输出准确项/偏差项/原因
export const deviation = (predictions, actualEvents) => post('/deviation', { predictions, actualEvents, provider: getProvider() })

// 二选一专项对比推演
export const compare = (profile, optionA, optionB, customCases) => post('/compare', { profile, optionA, optionB, customCases, provider: getProvider() })

// 健康检查
export async function health() {
  const res = await fetch(API_BASE + '/health')
  return res.json()
}

// 内置历史知识库（只读）
export async function fetchKnowledge() {
  const res = await fetch(API_BASE + '/knowledge')
  if (!res.ok) throw new Error('知识库加载失败 ' + res.status)
  return res.json()
}
