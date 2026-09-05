<template>
  <div class="page" v-if="profile">
    <!-- 头部 -->
    <div class="header">
      <div class="header-main">
        <h1 class="serif">{{ profile.name || '未命名' }}</h1>
        <div class="meta">
          <span class="score" :class="scoreCls">完整度 {{ score }}%</span>
          <span class="meta-item">推演 {{ snapshots.length }} 次</span>
          <span v-if="credits" class="meta-item" :class="{ 'quota-low': credits.totalRemaining === 0 }">🔑 剩余 {{ credits.totalRemaining }} 次</span>
          <span class="meta-item">🕐 {{ fmt(profile.updatedAt) }}</span>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn primary" :disabled="deducing" @click="startDeduce">
          {{ deducing ? '推演中…' : '🔮 开始推演' }}
        </button>
        <button class="btn ghost" @click="$router.push(`/profile/${profile.id}/growth`)">📈 成长追踪</button>
        <button class="btn ghost" @click="compareOpen = !compareOpen">⚖️ 对比推演</button>
        <button class="btn ghost" @click="viewMode = viewMode === 'view' ? 'edit' : 'view'">
          {{ viewMode === 'view' ? '✏️ 编辑' : '完成' }}
        </button>
        <button class="btn ghost" @click="onDuplicate">⧉ 复制</button>
        <button class="btn ghost danger" @click="onDelete">🗑 删除</button>
      </div>
    </div>

    <!-- 对比推演面板 -->
    <div v-if="compareOpen" class="compare-panel">
      <h3 class="compare-title">⚖️ 二选一对比推演</h3>
      <p class="compare-hint">输入两个具体选项，系统对比可行性、得失与风险。</p>
      <div class="compare-inputs">
        <input v-model="compareA" class="compare-input" placeholder="选项 A（如：全职创业开网店）" />
        <input v-model="compareB" class="compare-input" placeholder="选项 B（如：保留工作兼职试水）" />
      </div>
      <div class="compare-actions">
        <button class="btn primary" :disabled="comparing" @click="runCompare">{{ comparing ? '对比中…' : '开始对比' }}</button>
        <button class="btn ghost" @click="compareOpen = false">关闭</button>
      </div>
      <div v-if="compareResult" class="compare-result">
        <div v-for="(o, i) in compareResult.options" :key="i" class="compare-opt">
          <div class="co-head"><span class="co-name">{{ o.name }}</span><span class="co-score">{{ o.score }} 分</span></div>
          <div v-if="o.pros?.length" class="co-pros">✅ {{ o.pros.join('；') }}</div>
          <div v-if="o.cons?.length" class="co-cons">⚠️ {{ o.cons.join('；') }}</div>
          <div v-if="o.risk" class="co-risk">风险：{{ o.risk }}</div>
        </div>
        <div v-if="compareResult.keyDifference" class="co-diff">核心差异：{{ compareResult.keyDifference }}</div>
        <div v-if="compareResult.recommendation" class="co-rec">💡 {{ compareResult.recommendation }}</div>
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
          v-for="s in visibleSnapshots"
          :key="s.id"
          :to="`/report/${s.id}`"
          class="history-item"
        >
          <span class="h-time">{{ fmtTime(s.timestamp) }}</span>
          <span class="h-report">推演报告 #{{ s.id }}</span>
          <span class="h-arrow">→</span>
        </router-link>
      </div>
      <p v-if="snapshots.length > 50" class="archived-note">已归档 {{ snapshots.length - 50 }} 条更早的快照（仅展示最近 50 条）</p>
    </div>

    <!-- 档案变更日志 -->
    <div v-if="profile.changeLog?.length" class="history changelog">
      <h3 class="history-title">档案变更日志</h3>
      <div class="changelog-list">
        <div v-for="(c, i) in profile.changeLog.slice().reverse()" :key="i" class="changelog-item">
          <span class="cl-time">{{ fmtTime(c.at) }}</span>
          <span class="cl-fields">修改字段：{{ c.fields.join('、') }}</span>
        </div>
      </div>
    </div>

    <!-- 完整度不足提示弹窗（替代 confirm，两个明确按钮） -->
    <div v-if="showCompleteDialog" class="complete-mask" @click.self="showCompleteDialog = false">
      <div class="complete-dialog">
        <h3 class="cd-title">档案完整度偏低</h3>
        <p class="cd-text">档案完整度仅 <b>{{ score }}%</b>，低于最低可信门槛（60%）。<br />推演结果可信度将被评为「极低」，建议先补全信息。</p>
        <div class="cd-actions">
          <button class="btn ghost" @click="goComplete">前往补全</button>
          <button class="btn primary" @click="proceedDeduce">仍要推演</button>
        </div>
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
  getProfile, updateProfile, duplicateProfile, deleteProfile, listSnapshots, saveSnapshot, listCustomCases,
} from '../services/profile-service.js'
import { deduce, compare, fetchCredits } from '../api/index.js'

const route = useRoute()
const router = useRouter()
const profile = ref(null)
const snapshots = ref([])
const tab = ref('table')
const viewMode = ref('view')
const editForm = reactive({})
const deducing = ref(false)
const openGroups = ref(new Set(FIELD_GROUPS.filter(g => g.core).map(g => g.key)))
const compareOpen = ref(false)
const compareA = ref('')
const compareB = ref('')
const comparing = ref(false)
const compareResult = ref(null)
const credits = ref(null)
const showCompleteDialog = ref(false)

const score = computed(() => profile.value ? completenessScore(profile.value) : 0)
const scoreCls = computed(() => score.value < 60 ? 'low' : '')
const visibleSnapshots = computed(() => snapshots.value.slice(0, 50))

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
  refreshCredits()
}

async function refreshCredits() {
  try {
    credits.value = await fetchCredits()
  } catch (e) {
    credits.value = null
  }
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

async function runCompare() {
  if (!compareA.value.trim() || !compareB.value.trim()) { alert('请填写选项 A 和选项 B'); return }
  comparing.value = true
  compareResult.value = null
  try {
    const customCases = await listCustomCases()
    compareResult.value = await compare(profile.value, compareA.value.trim(), compareB.value.trim(), customCases)
  } catch (e) {
    alert('对比推演失败：' + e.message)
  } finally {
    comparing.value = false
  }
}

async function startDeduce() {
  // 完整度<60% 引导补全（自定义弹窗，两个明确按钮，避免 confirm 语义反直觉）
  if (score.value < 60) {
    showCompleteDialog.value = true
    return
  }
  await doDeduce()
}

function goComplete() {
  showCompleteDialog.value = false
  viewMode.value = 'edit'
}

function proceedDeduce() {
  showCompleteDialog.value = false
  doDeduce()
}

async function doDeduce() {
  // 单档案 24 小时内推演超 5 次提示（软确认，不硬阻断）
  const dayAgo = Date.now() - 24 * 3600 * 1000
  const recent = snapshots.value.filter(s => new Date(s.timestamp).getTime() > dayAgo)
  if (recent.length >= 5) {
    const ok = confirm('该档案 24 小时内已推演超过 5 次，频繁推演可能降低参考价值。是否仍要继续？')
    if (!ok) return
  }
  deducing.value = true
  try {
    const customCases = await listCustomCases()
    const report = await deduce(profile.value, undefined, customCases)
    // 后端返回完整报告对象（含 meta 等）
    const snapshotId = await saveSnapshot({
      profileId: profile.value.id,
      timestamp: new Date().toISOString(),
      knowledgeVersion: report.meta?.knowledgeVersion || 'k-v1.0',
      promptVersion: report.meta?.promptVersion || 'p-v1.7.0',
      consistencyCoefficient: report.meta?.consistencyCoefficient || '中',
      fullReport: report,
      profileSnapshot: JSON.parse(JSON.stringify(profile.value)),
      todoIds: [],
      reviewId: null,
    })
    router.push(`/report/${snapshotId}`)
  } catch (e) {
    if (e.message && e.message.includes('免费次数已用完')) {
      alert('🔒 免费 20 次已用完。\n\n付费功能即将上线，敬请期待。\n如需继续使用，请联系管理员开通。')
      refreshCredits()
    } else {
      alert('推演失败：' + e.message)
    }
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
.quota-low { color: var(--color-error); font-weight: 600; }
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
.archived-note { font-size: var(--fs-caption); color: var(--color-neutral-500); margin-top: var(--sp-sm); text-align: center; }
.changelog-list { display: flex; flex-direction: column; gap: var(--sp-xs); }
.changelog-item { display: flex; gap: var(--sp-md); font-size: var(--fs-small); padding: var(--sp-xs) var(--sp-sm); background: var(--color-neutral-50); border-radius: var(--radius-sm); }
.cl-time { color: var(--color-neutral-500); white-space: nowrap; }
.cl-fields { color: var(--color-neutral-700); }
.compare-panel { background: #fff; border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); padding: var(--sp-lg); margin-bottom: var(--sp-lg); }
.compare-title { font-size: var(--fs-h3); color: var(--color-primary-700); margin-bottom: var(--sp-xs); }
.compare-hint { font-size: var(--fs-caption); color: var(--color-neutral-500); margin-bottom: var(--sp-md); }
.compare-inputs { display: flex; flex-direction: column; gap: var(--sp-sm); margin-bottom: var(--sp-md); }
.compare-input { width: 100%; padding: var(--sp-sm) var(--sp-md); font-size: var(--fs-body); border: 1px solid var(--color-neutral-300); border-radius: var(--radius-md); }
.compare-input:focus { outline: none; border-color: var(--color-primary-500); }
.compare-actions { display: flex; gap: var(--sp-sm); margin-bottom: var(--sp-md); }
.compare-result { border-top: 1px dashed var(--color-neutral-200); padding-top: var(--sp-md); }
.compare-opt { background: var(--color-neutral-50); border-radius: var(--radius-md); padding: var(--sp-md); margin-bottom: var(--sp-sm); }
.co-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--sp-xs); }
.co-name { font-size: var(--fs-body); font-weight: 600; color: var(--color-neutral-900); }
.co-score { font-size: var(--fs-h3); font-weight: 700; color: var(--color-primary-600); }
.co-pros { font-size: var(--fs-small); color: var(--color-success); margin-bottom: 2px; }
.co-cons { font-size: var(--fs-small); color: var(--color-warning); margin-bottom: 2px; }
.co-risk { font-size: var(--fs-small); color: var(--color-error); }
.co-diff { font-size: var(--fs-small); color: var(--color-neutral-700); margin-bottom: var(--sp-xs); }
.co-rec { font-size: var(--fs-body); color: var(--color-primary-700); font-weight: 600; }
.complete-mask {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 100; padding: var(--sp-lg);
}
.complete-dialog {
  background: #fff; border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md); padding: var(--sp-lg);
  width: 100%; max-width: 360px;
}
.cd-title { font-size: var(--fs-h3); color: var(--color-primary-700); margin-bottom: var(--sp-sm); }
.cd-text { font-size: var(--fs-body); color: var(--color-neutral-700); line-height: 1.6; margin-bottom: var(--sp-md); }
.cd-text b { color: var(--color-warning); }
.cd-actions { display: flex; gap: var(--sp-sm); }
.cd-actions .btn { flex: 1; }
</style>
