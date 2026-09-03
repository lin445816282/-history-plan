<template>
  <div class="page" v-if="profile">
    <!-- 头部 -->
    <div class="header">
      <div class="header-main">
        <h1 class="serif">{{ profile.name || '未命名' }}</h1>
        <div class="meta">
          <span class="score" :class="scoreCls">完整度 {{ score }}%</span>
          <span class="meta-item">推演 {{ snapshots.length }} 次</span>
          <span class="meta-item">🕐 {{ fmt(profile.updatedAt) }}</span>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn primary" :disabled="deducing" @click="startDeduce">
          {{ deducing ? '推演中…' : '🔮 开始推演' }}
        </button>
        <button class="btn ghost" @click="viewMode = viewMode === 'view' ? 'edit' : 'view'">
          {{ viewMode === 'view' ? '✏️ 编辑' : '完成' }}
        </button>
        <button class="btn ghost" @click="onDuplicate">⧉ 复制</button>
        <button class="btn ghost danger" @click="onDelete">🗑 删除</button>
      </div>
    </div>

    <!-- 视图切换 -->
    <div class="tabs">
      <button :class="{ active: tab === 'table' }" @click="tab = 'table'">表格视图</button>
      <button :class="{ active: tab === 'timeline' }" @click="tab = 'timeline'">时间轴视图</button>
    </div>

    <!-- 定位语（推演按钮旁） -->
    <p class="motto-line serif">谋事在人，顺时知变</p>

    <!-- 表格视图 -->
    <div v-if="tab === 'table'">
      <div v-for="group in FIELD_GROUPS" :key="group.key" class="group">
        <div class="group-header" @click="toggleGroup(group.key)">
          <h3 class="group-title">{{ group.label }}</h3>
          <span class="toggle">{{ openGroups.has(group.key) ? '▾' : '▸' }}</span>
        </div>
        <div v-show="openGroups.has(group.key)" class="group-body">
          <div v-for="f in group.fields" :key="f.key" class="field">
            <label class="field-label">{{ f.label }}</label>
            <textarea
              v-if="viewMode === 'edit'"
              v-model="editForm[f.key]"
              class="field-input"
              :placeholder="f.placeholder || ''"
              rows="2"
            ></textarea>
            <p v-else class="field-value" :class="{ empty: !(profile[f.key] || '').trim() }">
              {{ (profile[f.key] || '').trim() || '—' }}
            </p>
          </div>
        </div>
      </div>
      <div v-if="viewMode === 'edit'" class="save-bar">
        <button class="btn primary" @click="saveEdit">保存修改</button>
      </div>
    </div>

    <!-- 时间轴视图 -->
    <TimelineView v-else :profile="profile" :snapshots="snapshots" />

    <!-- 推演历史 -->
    <div class="history">
      <h3 class="history-title">推演历史</h3>
      <div v-if="snapshots.length === 0" class="empty-note">还没有推演记录，点击「开始推演」生成第一份报告。</div>
      <div v-else class="history-list">
        <router-link
          v-for="s in snapshots"
          :key="s.id"
          :to="`/report/${s.id}`"
          class="history-item"
        >
          <span class="h-time">{{ fmtTime(s.timestamp) }}</span>
          <span class="h-report">推演报告 #{{ s.id }}</span>
          <span class="h-arrow">→</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import TimelineView from '../components/TimelineView.vue'
import { FIELD_GROUPS, completenessScore } from '../constants/profile-fields.js'
import {
  getProfile, updateProfile, duplicateProfile, deleteProfile, listSnapshots, saveSnapshot,
} from '../services/profile-service.js'
import { deduce } from '../api/index.js'

const route = useRoute()
const router = useRouter()
const profile = ref(null)
const snapshots = ref([])
const tab = ref('table')
const viewMode = ref('view')
const editForm = reactive({})
const deducing = ref(false)
const openGroups = ref(new Set(FIELD_GROUPS.filter(g => g.core).map(g => g.key)))

const score = computed(() => profile.value ? completenessScore(profile.value) : 0)
const scoreCls = computed(() => score.value < 60 ? 'low' : '')

function toggleGroup(key) {
  const s = new Set(openGroups.value)
  s.has(key) ? s.delete(key) : s.add(key)
  openGroups.value = s
}

function fmt(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  const p = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}
function fmtTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  const p = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

async function load() {
  profile.value = await getProfile(Number(route.params.id))
  if (!profile.value) { router.push('/profiles'); return }
  snapshots.value = await listSnapshots(profile.value.id)
  Object.assign(editForm, profile.value)
}

async function saveEdit() {
  const updated = await updateProfile(profile.value.id, { ...editForm })
  profile.value = updated
  viewMode.value = 'view'
}

async function onDuplicate() {
  if (!confirm('复制此档案？仅复制人物画像。')) return
  await duplicateProfile(profile.value.id)
  router.push('/profiles')
}

async function onDelete() {
  if (!confirm('确认删除此档案？将级联删除全部推演、复盘、待办。')) return
  await deleteProfile(profile.value.id)
  router.push('/profiles')
}

async function startDeduce() {
  // 完整度<60% 强制引导补全（提供「前往补全」/「仍要推演」两选项）
  if (score.value < 60) {
    const go = confirm(
      `档案完整度仅 ${score.value}%，低于最低可信门槛（60%）。\n\n` +
      `推演结果可信度将被评为「极低」。\n\n` +
      `点击「确定」→ 前往补全信息；点击「取消」→ 仍直接推演。`
    )
    if (go) {
      viewMode.value = 'edit'
      return
    }
  }
  // 单档案 24 小时内推演超 5 次提示（软确认，不硬阻断）
  const dayAgo = Date.now() - 24 * 3600 * 1000
  const recent = snapshots.value.filter(s => new Date(s.timestamp).getTime() > dayAgo)
  if (recent.length >= 5) {
    const ok = confirm('该档案 24 小时内已推演超过 5 次，频繁推演可能降低参考价值。是否仍要继续？')
    if (!ok) return
  }
  deducing.value = true
  try {
    const report = await deduce(profile.value)
    // 后端返回完整报告对象（含 meta 等）
    const snapshotId = await saveSnapshot({
      profileId: profile.value.id,
      timestamp: new Date().toISOString(),
      knowledgeVersion: report.meta?.knowledgeVersion || 'k-v1.0',
      promptVersion: report.meta?.promptVersion || 'p-v1.7.0',
      consistencyCoefficient: report.meta?.consistencyCoefficient || '中',
      fullReport: report,
      profileSnapshot: { ...profile.value },
      todoIds: [],
      reviewId: null,
    })
    router.push(`/report/${snapshotId}`)
  } catch (e) {
    alert('推演失败：' + e.message)
  } finally {
    deducing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page { padding: var(--sp-lg); }
.header { display: flex; justify-content: space-between; align-items: flex-start; gap: var(--sp-md); margin-bottom: var(--sp-lg); flex-wrap: wrap; }
.header-main h1 { font-size: var(--fs-h2); color: var(--color-primary-700); margin-bottom: var(--sp-xs); }
.meta { display: flex; gap: var(--sp-md); align-items: center; font-size: var(--fs-small); color: var(--color-neutral-500); flex-wrap: wrap; }
.score { color: var(--color-success); font-weight: 600; }
.score.low { color: var(--color-warning); }
.header-actions { display: flex; gap: var(--sp-sm); flex-wrap: wrap; }
.btn { padding: var(--sp-sm) var(--sp-md); border: none; border-radius: var(--radius-md); font-size: var(--fs-small); min-height: var(--touch-min); }
.btn.primary { background: var(--color-primary-500); color: #fff; }
.btn.primary:hover { background: var(--color-primary-600); }
.btn.primary:disabled { background: var(--color-neutral-300); cursor: not-allowed; }
.btn.ghost { background: #fff; border: 1px solid var(--color-neutral-300); color: var(--color-neutral-700); }
.btn.ghost.danger:hover { border-color: var(--color-error); color: var(--color-error); }
.tabs { display: flex; gap: var(--sp-sm); margin-bottom: var(--sp-md); }
.motto-line { text-align: center; color: var(--color-primary-500); margin-bottom: var(--sp-md); font-size: var(--fs-small); }
.tabs button { padding: var(--sp-sm) var(--sp-lg); border: 1px solid var(--color-neutral-300); background: #fff; border-radius: var(--radius-md); font-size: var(--fs-small); }
.tabs button.active { background: var(--color-primary-500); color: #fff; border-color: var(--color-primary-500); }
.group { background: #fff; border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); overflow: hidden; margin-bottom: var(--sp-md); }
.group-header { display: flex; justify-content: space-between; align-items: center; padding: var(--sp-md); cursor: pointer; background: var(--color-neutral-50); }
.group-title { font-size: var(--fs-body); color: var(--color-neutral-900); }
.toggle { color: var(--color-neutral-500); }
.group-body { padding: var(--sp-md); display: flex; flex-direction: column; gap: var(--sp-md); }
.field { display: flex; flex-direction: column; gap: var(--sp-xs); }
.field-label { font-size: var(--fs-small); color: var(--color-neutral-700); }
.field-value { font-size: var(--fs-body); line-height: 1.7; white-space: pre-wrap; }
.field-value.empty { color: var(--color-neutral-300); }
.field-input { width: 100%; padding: var(--sp-sm) var(--sp-md); font-size: var(--fs-body); border: 1px solid var(--color-neutral-300); border-radius: var(--radius-md); font-family: inherit; resize: vertical; }
.save-bar { display: flex; justify-content: flex-end; margin: var(--sp-md) 0; }
.history { margin-top: var(--sp-lg); }
.history-title { font-size: var(--fs-h3); color: var(--color-neutral-700); margin-bottom: var(--sp-md); }
.empty-note { color: var(--color-neutral-500); }
.history-list { display: flex; flex-direction: column; gap: var(--sp-sm); }
.history-item { display: flex; align-items: center; gap: var(--sp-md); background: #fff; border-radius: var(--radius-md); padding: var(--sp-md); box-shadow: var(--shadow-sm); }
.h-time { color: var(--color-neutral-500); font-size: var(--fs-small); }
.h-report { flex: 1; color: var(--color-neutral-900); }
.h-arrow { color: var(--color-primary-500); }
</style>
