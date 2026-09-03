// 档案 CRUD 封装 —— 基于 db-utils.js 的 HistoryPlanDB
import { HistoryPlanDB } from '../db/db-utils.js'
import { emptyProfile } from '../constants/profile-fields.js'

const db = new HistoryPlanDB()

// ---------- 档案 ----------
export async function listProfiles() {
  const [profiles, snapshots] = await Promise.all([
    db.getAll('profiles'),
    db.getAll('snapshots'),
  ])
  const countMap = {}
  snapshots.forEach(s => { countMap[s.profileId] = (countMap[s.profileId] || 0) + 1 })
  return profiles
    .map(p => ({ ...p, deduceCount: countMap[p.id] || 0 }))
    .sort((a, b) => String(b.updatedAt || '').localeCompare(String(a.updatedAt || '')))
}

export function getProfile(id) {
  return db.get('profiles', id)
}

export async function createProfile(data) {
  const now = new Date().toISOString()
  const profile = { ...emptyProfile(), ...data, createdAt: now, updatedAt: now }
  const id = await db.add('profiles', profile)
  return { ...profile, id }
}

export async function updateProfile(id, data) {
  const existing = await db.get('profiles', id)
  const now = new Date().toISOString()
  // 记录变更日志（排除时间戳与日志自身字段）
  const changedFields = Object.keys(data).filter(k =>
    !['updatedAt', 'changeLog', 'createdAt'].includes(k) &&
    String(data[k] ?? '') !== String(existing[k] ?? '')
  )
  const changeLog = changedFields.length
    ? [...(existing.changeLog || []), { at: now, fields: changedFields }].slice(-50)
    : (existing.changeLog || [])
  const merged = { ...existing, ...data, changeLog, updatedAt: now }
  await db.update('profiles', merged)
  return merged
}

export async function duplicateProfile(id) {
  const src = await db.get('profiles', id)
  const now = new Date().toISOString()
  const copy = { ...src, id: undefined, name: (src.name || '') + '（副本）', createdAt: now, updatedAt: now }
  return db.add('profiles', copy)
}

export function deleteProfile(id) {
  return db.cascadeDeleteProfile(id)
}

// ---------- 推演快照 ----------
export async function listSnapshots(profileId) {
  const snapshots = await db.getByIndex('snapshots', 'by_profileId', profileId)
  return snapshots.sort((a, b) => String(b.timestamp || '').localeCompare(String(a.timestamp || '')))
}
export function getSnapshot(id) { return db.get('snapshots', id) }
export function saveSnapshot(data) { return db.add('snapshots', data) }
export async function updateSnapshot(id, data) {
  const existing = await db.get('snapshots', id)
  await db.update('snapshots', { ...existing, ...data })
  return db.get('snapshots', id)
}

// ---------- 待办 ----------
export async function listTodos(snapshotId) {
  const todos = await db.getByIndex('todos', 'by_snapshotId', snapshotId)
  return todos.sort((a, b) => String(a.createdAt || '').localeCompare(String(b.createdAt || '')))
}
export function saveTodo(data) { return db.add('todos', data) }
export async function updateTodo(id, data) {
  const existing = await db.get('todos', id)
  await db.update('todos', { ...existing, ...data, updatedAt: new Date().toISOString() })
}
export function deleteTodo(id) { return db.delete('todos', id) }

// ---------- 复盘 ----------
export async function listReviews(snapshotId) {
  return db.getByIndex('reviews', 'by_snapshotId', snapshotId)
}
export function saveReview(data) { return db.add('reviews', data) }

// ---------- 自定义历史案例 ----------
export async function listCustomCases() {
  const cases = await db.getAll('customCases')
  return cases.sort((a, b) => String(b.createdAt || '').localeCompare(String(a.createdAt || '')))
}
export async function saveCustomCase(data) {
  const now = new Date().toISOString()
  const c = { ...data, updatedAt: now }
  if (c.id) {
    await db.update('customCases', { ...c, createdAt: c.createdAt || now })
    return c.id
  }
  c.createdAt = now
  return db.add('customCases', c)
}
export function deleteCustomCase(id) { return db.delete('customCases', id) }

// ---------- 偏差聚合 ----------
export async function getDeviationSummary() {
  const [reviews, profiles] = await Promise.all([
    db.getAll('reviews'),
    db.getAll('profiles'),
  ])
  const nameMap = {}
  profiles.forEach(p => { nameMap[p.id] = p.name || '未命名' })

  const summary = {
    totalReviews: reviews.length,
    totalAccurate: 0,
    totalDeviated: 0,
    accuracyRate: 0,
    reasonDist: { '信息不全导致': 0, '外部变局冲击': 0, '模型推理局限': 0, '执行偏差': 0, '未注明原因': 0 },
    byProfile: [],
    byMonth: [],
  }
  const profileAgg = {}
  const monthAgg = {}

  reviews.forEach(r => {
    const dr = r.deviationReport || {}
    const accurate = (dr.accurate || []).length
    const deviatedArr = dr.deviated || []
    const deviated = deviatedArr.length
    summary.totalAccurate += accurate
    summary.totalDeviated += deviated

    deviatedArr.forEach(d => {
      const reason = d && d.reason ? d.reason : '未注明原因'
      summary.reasonDist[reason] = (summary.reasonDist[reason] || 0) + 1
    })

    const pid = r.profileId
    if (pid != null) {
      if (!profileAgg[pid]) profileAgg[pid] = { profileId: pid, name: nameMap[pid] || '未命名', reviews: 0, accurate: 0, deviated: 0 }
      profileAgg[pid].reviews++
      profileAgg[pid].accurate += accurate
      profileAgg[pid].deviated += deviated
    }

    const m = (r.createdAt || '').slice(0, 7)
    if (m) {
      if (!monthAgg[m]) monthAgg[m] = { month: m, accurate: 0, deviated: 0 }
      monthAgg[m].accurate += accurate
      monthAgg[m].deviated += deviated
    }
  })

  const total = summary.totalAccurate + summary.totalDeviated
  summary.accuracyRate = total ? Math.round(summary.totalAccurate / total * 100) : 0

  summary.byProfile = Object.values(profileAgg)
    .map(p => ({ ...p, rate: (p.accurate + p.deviated) ? Math.round(p.accurate / (p.accurate + p.deviated) * 100) : 0 }))
    .sort((a, b) => b.deviated - a.deviated || b.accurate - a.accurate)

  summary.byMonth = Object.values(monthAgg).sort((a, b) => a.month.localeCompare(b.month))

  return summary
}

// ---------- 备份 ----------
export const exportAllData = () => db.exportAllData()
export const importAllData = (data) => db.importAllData(data)

export default {
  listProfiles, getProfile, createProfile, updateProfile, duplicateProfile, deleteProfile,
  listSnapshots, getSnapshot, saveSnapshot,
  listTodos, saveTodo, updateTodo, deleteTodo,
  listReviews, saveReview, getDeviationSummary, exportAllData, importAllData,
}
