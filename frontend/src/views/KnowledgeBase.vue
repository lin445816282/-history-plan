<template>
  <div class="page">
    <div class="breadcrumb">
      <router-link to="/profiles">档案列表</router-link>
      <span class="sep">/</span>
      <span>知识库</span>
    </div>

    <h1 class="serif page-title">历史知识库</h1>
    <p class="sub">内置 {{ builtin.length }} 案例 · 自定义 {{ custom.length }} 案例，供推演时对标参考。</p>

    <!-- 搜索 + 筛选 -->
    <div class="toolbar">
      <input v-model="search" class="search" placeholder="搜索人物 / 背景 / 教训…" />
      <div class="filters">
        <div class="filter-group">
          <button v-for="s in sources" :key="s.v" class="chip" :class="{ active: sourceFilter === s.v }" @click="sourceFilter = s.v">{{ s.label }}</button>
        </div>
        <div class="filter-group">
          <button v-for="t in types" :key="t.v" class="chip" :class="{ active: typeFilter === t.v }" @click="typeFilter = t.v">{{ t.label }}</button>
        </div>
        <div class="filter-group">
          <button v-for="o in outcomes" :key="o.v" class="chip" :class="{ active: outcomeFilter === o.v }" @click="outcomeFilter = o.v">{{ o.label }}</button>
        </div>
      </div>
    </div>

    <!-- 案例卡片 -->
    <div v-if="filtered.length" class="case-grid">
      <div v-for="c in filtered" :key="c.key" class="case-card" :class="{ open: expanded === c.key }" @click="toggle(c)">
        <div class="case-head">
          <span class="case-name serif">{{ c.name }}</span>
          <span class="badge type">{{ c.type }}</span>
          <span v-if="c.outcome" class="badge" :class="c.outcome === 'success' ? 'ok' : 'fail'">{{ c.outcome === 'success' ? '成功' : '失败' }}</span>
          <span class="badge src" :class="c.source">{{ c.source === 'builtin' ? '内置' : '自定义' }}</span>
        </div>
        <div class="case-meta">{{ [c.era, c.industry].filter(Boolean).join(' · ') }}</div>
        <div class="case-context">{{ c.context }}</div>
        <div v-if="expanded === c.key" class="case-detail">
          <div class="detail-row"><label>行动原则</label><span>{{ c.principle || '—' }}</span></div>
          <div class="detail-row"><label>教训启示</label><span>{{ c.lesson || '—' }}</span></div>
          <div v-if="c.boundaryNote" class="detail-row"><label>古今边界</label><span>{{ c.boundaryNote }}</span></div>
        </div>
      </div>
    </div>
    <div v-else class="empty">
      <p>没有匹配的案例，试试调整筛选或搜索词。</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchKnowledge } from '../api/index.js'
import { listCustomCases } from '../services/profile-service.js'

const builtin = ref([])
const custom = ref([])
const search = ref('')
const sourceFilter = ref('all')
const typeFilter = ref('all')
const outcomeFilter = ref('all')
const expanded = ref(null)

const sources = [
  { v: 'all', label: '全部来源' },
  { v: 'builtin', label: '内置' },
  { v: 'custom', label: '自定义' },
]
const types = [
  { v: 'all', label: '全部类型' },
  { v: '古代', label: '古代' },
  { v: '现代', label: '现代' },
]
const outcomes = [
  { v: 'all', label: '全部结果' },
  { v: 'success', label: '成功' },
  { v: 'failure', label: '失败' },
]

function norm(c, source) {
  return {
    key: source + '-' + c.id,
    source,
    name: c.name || '',
    type: c.type === 'modern' ? '现代' : '古代',
    era: c.era || '',
    industry: c.industry || '',
    prototype: c.prototype || '',
    context: c.context || '',
    principle: c.principle || '',
    outcome: c.outcome || '',
    lesson: c.lesson || '',
    boundaryNote: c.boundaryNote || '',
  }
}

const allCases = computed(() => [
  ...builtin.value.map(c => norm(c, 'builtin')),
  ...custom.value.map(c => norm(c, 'custom')),
])

const filtered = computed(() => {
  const kw = search.value.trim()
  return allCases.value.filter(c => {
    if (sourceFilter.value !== 'all' && c.source !== sourceFilter.value) return false
    if (typeFilter.value !== 'all' && c.type !== typeFilter.value) return false
    if (outcomeFilter.value !== 'all' && c.outcome !== outcomeFilter.value) return false
    if (kw) {
      const hay = [c.name, c.prototype, c.context, c.principle, c.lesson, c.era, c.industry].join(' ')
      if (!hay.includes(kw)) return false
    }
    return true
  })
})

function toggle(c) {
  expanded.value = expanded.value === c.key ? null : c.key
}

onMounted(async () => {
  try {
    const kb = await fetchKnowledge()
    builtin.value = kb.cases || []
  } catch (e) {
    console.warn('内置知识库加载失败', e)
  }
  custom.value = await listCustomCases()
})
</script>

<style scoped>
.page { padding: var(--sp-lg); }
.breadcrumb { font-size: var(--fs-small); color: var(--color-neutral-500); margin-bottom: var(--sp-md); }
.breadcrumb a { color: var(--color-primary-600); }
.sep { margin: 0 var(--sp-xs); }
.page-title { font-size: var(--fs-h2); color: var(--color-primary-700); margin-bottom: var(--sp-xs); }
.sub { color: var(--color-neutral-500); margin-bottom: var(--sp-lg); }

.toolbar { margin-bottom: var(--sp-lg); }
.search { width: 100%; padding: var(--sp-sm) var(--sp-md); font-size: var(--fs-body); border: 1px solid var(--color-neutral-300); border-radius: var(--radius-md); margin-bottom: var(--sp-sm); }
.search:focus { outline: none; border-color: var(--color-primary-500); }
.filters { display: flex; flex-direction: column; gap: var(--sp-xs); }
.filter-group { display: flex; gap: var(--sp-xs); flex-wrap: wrap; }
.chip { padding: var(--sp-xs) var(--sp-md); font-size: var(--fs-small); border: 1px solid var(--color-neutral-300); border-radius: 20px; background: #fff; color: var(--color-neutral-700); cursor: pointer; }
.chip.active { background: var(--color-primary-500); color: #fff; border-color: var(--color-primary-500); }

.case-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--sp-md); }
.case-card { background: #fff; border-radius: var(--radius-lg); padding: var(--sp-md); box-shadow: var(--shadow-sm); cursor: pointer; transition: box-shadow .2s; }
.case-card:hover { box-shadow: var(--shadow-md); }
.case-card.open { border: 1px solid var(--color-primary-300, #D6C3AE); }
.case-head { display: flex; align-items: center; gap: var(--sp-xs); flex-wrap: wrap; margin-bottom: var(--sp-xs); }
.case-name { font-size: var(--fs-h3); font-weight: 700; color: var(--color-neutral-900); }
.badge { font-size: var(--fs-caption); padding: 1px 8px; border-radius: 10px; }
.badge.type { background: var(--color-secondary-100); color: var(--color-secondary-500); }
.badge.ok { background: #E8F4EC; color: var(--color-success); }
.badge.fail { background: #F9E6E6; color: var(--color-error); }
.badge.src.builtin { background: var(--color-primary-100); color: var(--color-primary-600); }
.badge.src.custom { background: #EDE9FE; color: #6D28D9; }
.case-meta { font-size: var(--fs-caption); color: var(--color-neutral-500); margin-bottom: var(--sp-xs); }
.case-context { font-size: var(--fs-small); color: var(--color-neutral-700); line-height: 1.6; }
.case-detail { margin-top: var(--sp-sm); border-top: 1px dashed var(--color-neutral-200); padding-top: var(--sp-sm); }
.detail-row { display: flex; gap: var(--sp-sm); margin-bottom: var(--sp-xs); font-size: var(--fs-small); }
.detail-row label { flex-shrink: 0; width: 64px; color: var(--color-neutral-500); }
.detail-row span { color: var(--color-neutral-900); line-height: 1.6; flex: 1; }

.empty { text-align: center; padding: var(--sp-2xl); color: var(--color-neutral-500); }
</style>
