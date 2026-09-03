// 后端薄代理 API client
const API_BASE = '/api'

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

// 自然语言 → 结构化档案预览
export const parseProfile = (text) => post('/parse', { text })

// 档案 + 知识上下文 → 推演报告
export const deduce = (profile, industry) => post('/deduce', { profile, industry })

// 健康检查
export async function health() {
  const res = await fetch(API_BASE + '/health')
  return res.json()
}
