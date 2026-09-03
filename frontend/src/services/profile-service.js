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
  const merged = { ...existing, ...data, updatedAt: new Date().toISOString() }
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

// ---------- 备份 ----------
export const exportAllData = () => db.exportAllData()
export const importAllData = (data) => db.importAllData(data)

export default {
  listProfiles, getProfile, createProfile, updateProfile, duplicateProfile, deleteProfile,
  listSnapshots, getSnapshot, saveSnapshot,
  listTodos, saveTodo, updateTodo, deleteTodo,
  listReviews, saveReview, exportAllData, importAllData,
}
