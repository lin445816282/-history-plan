<template>
  <div class="tracker">
    <div class="tracker-header">
      <h3 class="tracker-title">📋 行动计划跟踪器</h3>
      <button class="btn ghost sm" @click="addNew">＋ 新增待办</button>
    </div>

    <div v-if="todos.length" class="tracker-progress">
      <div class="progress-info">
        <span>完成进度</span>
        <span class="progress-num">{{ doneCount }}/{{ todos.length }}（{{ progressPct }}%）</span>
      </div>
      <div class="progress-bar"><div class="progress-fill" :style="{ width: progressPct + '%' }"></div></div>
    </div>

    <div v-if="todos.length === 0" class="empty-note">暂无待办行动项。</div>

    <div v-else class="todo-list">
      <div v-for="t in todos" :key="t.id" class="todo-item" :class="{ done: t.status === 'completed' }">
        <label class="checkbox">
          <input type="checkbox" :checked="t.status === 'completed'" @change="toggle(t)" />
          <span class="checkmark"></span>
        </label>
        <div class="todo-main">
          <template v-if="editingId === t.id">
            <input v-model="editText" class="edit-input" type="text" @keyup.enter="saveEdit(t)" />
            <div class="edit-actions">
              <button class="btn ghost sm" @click="saveEdit(t)">保存</button>
              <button class="btn ghost sm" @click="editingId = null">取消</button>
            </div>
          </template>
          <template v-else>
            <div class="todo-desc" @dblclick="startEdit(t)">{{ t.description }}</div>
            <div class="todo-meta">
              <span class="path-tag">{{ t.sourcePath }}</span>
              <span v-if="t.status === 'completed'" class="done-time">✓ {{ fmt(t.completedAt) }}</span>
            </div>
          </template>
        </div>
        <button class="icon-btn" title="删除" @click="remove(t)">✕</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { listTodos, saveTodo, updateTodo, deleteTodo, updateSnapshot } from '../services/profile-service.js'

const props = defineProps({ snapshot: { type: Object, required: true } })

const todos = ref([])
const editingId = ref(null)
const editText = ref('')

const doneCount = computed(() => todos.value.filter(t => t.status === 'completed').length)
const progressPct = computed(() => todos.value.length ? Math.round(doneCount.value / todos.value.length * 100) : 0)

function fmt(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const p = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

async function ensureTodos() {
  const snap = props.snapshot
  // 若还没提取过待办，从报告短期行动计划提取
  if (!snap.todoIds || snap.todoIds.length === 0) {
    const shortTerms = snap.fullReport?.actionPlan?.shortTerm || []
    const ids = []
    for (const desc of shortTerms.slice(0, 5)) {
      const now = new Date().toISOString()
      const id = await saveTodo({
        snapshotId: snap.id,
        profileId: snap.profileId,
        description: desc,
        sourcePath: '短期行动计划',
        status: 'pending',
        completedAt: null,
        createdAt: now,
        updatedAt: now,
      })
      ids.push(id)
    }
    if (ids.length > 0) {
      await updateSnapshot(snap.id, { todoIds: ids })
    }
  }
  todos.value = await listTodos(snap.id)
}

async function toggle(t) {
  const completed = t.status !== 'completed'
  await updateTodo(t.id, {
    status: completed ? 'completed' : 'pending',
    completedAt: completed ? new Date().toISOString() : null,
  })
  todos.value = await listTodos(props.snapshot.id)
}

function startEdit(t) {
  editingId.value = t.id
  editText.value = t.description
}

async function saveEdit(t) {
  if (editText.value.trim()) {
    await updateTodo(t.id, { description: editText.value.trim() })
  }
  editingId.value = null
  todos.value = await listTodos(props.snapshot.id)
}

async function remove(t) {
  await deleteTodo(t.id)
  todos.value = await listTodos(props.snapshot.id)
}

async function addNew() {
  const now = new Date().toISOString()
  const id = await saveTodo({
    snapshotId: props.snapshot.id,
    profileId: props.snapshot.profileId,
    description: '新待办',
    sourcePath: '自定义',
    status: 'pending',
    completedAt: null,
    createdAt: now,
    updatedAt: now,
  })
  todos.value = await listTodos(props.snapshot.id)
  editingId.value = id
  editText.value = '新待办'
}

onMounted(ensureTodos)
</script>

<style scoped>
.tracker { background: #fff; border: 1px solid var(--color-secondary-100); border-radius: var(--radius-lg); padding: var(--sp-lg); }
.tracker-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--sp-md); }
.tracker-title { font-size: var(--fs-h3); color: var(--color-secondary-500); }
.tracker-progress { margin-bottom: var(--sp-md); }
.progress-info { display: flex; justify-content: space-between; align-items: center; font-size: var(--fs-small); color: var(--color-neutral-700); margin-bottom: var(--sp-xs); }
.progress-num { font-weight: 600; color: var(--color-secondary-500); }
.progress-bar { height: 8px; background: var(--color-neutral-100); border-radius: var(--radius-sm); overflow: hidden; }
.progress-fill { height: 100%; background: var(--color-secondary-500); border-radius: var(--radius-sm); transition: width 0.3s ease; }
.btn { padding: var(--sp-sm) var(--sp-md); border: none; border-radius: var(--radius-md); font-size: var(--fs-small); }
.btn.ghost { background: #fff; border: 1px solid var(--color-neutral-300); color: var(--color-neutral-700); }
.btn.sm { padding: var(--sp-xs) var(--sp-sm); }
.empty-note { color: var(--color-neutral-500); font-size: var(--fs-small); }
.todo-list { display: flex; flex-direction: column; gap: var(--sp-sm); }
.todo-item { display: flex; align-items: flex-start; gap: var(--sp-sm); padding: var(--sp-sm); border-radius: var(--radius-md); background: var(--color-neutral-50); }
.todo-item.done { opacity: 0.6; }
.checkbox { position: relative; display: flex; align-items: center; }
.checkbox input { width: 20px; height: 20px; margin-top: 2px; cursor: pointer; }
.todo-main { flex: 1; }
.todo-desc { font-size: var(--fs-body); color: var(--color-neutral-900); line-height: 1.6; }
.todo-item.done .todo-desc { text-decoration: line-through; }
.todo-meta { display: flex; gap: var(--sp-sm); align-items: center; margin-top: var(--sp-xs); }
.path-tag { font-size: var(--fs-caption); color: var(--color-secondary-500); background: var(--color-secondary-100); padding: 1px 6px; border-radius: var(--radius-sm); }
.done-time { font-size: var(--fs-caption); color: var(--color-success); }
.edit-input { width: 100%; padding: var(--sp-xs) var(--sp-sm); font-size: var(--fs-body); border: 1px solid var(--color-primary-500); border-radius: var(--radius-md); }
.edit-actions { display: flex; gap: var(--sp-sm); margin-top: var(--sp-xs); }
.icon-btn { min-width: 32px; min-height: 32px; padding: 0 var(--sp-sm); border: none; background: transparent; color: var(--color-neutral-500); border-radius: var(--radius-sm); font-size: var(--fs-small); }
.icon-btn:hover { background: var(--color-neutral-100); color: var(--color-error); }
</style>
