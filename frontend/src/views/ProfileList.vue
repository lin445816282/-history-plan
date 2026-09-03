<template>
  <div class="page">
    <div class="page-header">
      <h1 class="serif">人物档案</h1>
      <div class="new-dropdown">
        <button class="btn btn-primary" @click="menuOpen = !menuOpen">＋ 新建档案</button>
        <div v-if="menuOpen" class="dropdown" @click="menuOpen = false">
          <router-link to="/profiles/new?mode=quick" class="dd-item">
            <b>⚡ 极速建档</b><span class="dd-tip">（推荐，3 项即可开始）</span>
          </router-link>
          <router-link to="/profiles/new?mode=simple" class="dd-item">
            <b>💬 简易录入</b><span class="dd-tip">自然语言描述，AI 解析</span>
          </router-link>
          <router-link to="/profiles/new?mode=form" class="dd-item">
            <b>📋 完整表单</b><span class="dd-tip">一次性填写全部字段</span>
          </router-link>
        </div>
      </div>
    </div>

    <input v-model="keyword" class="search" type="text" placeholder="搜索档案名称…" />

    <p class="motto-line serif">谋事在人，顺时知变</p>

    <div v-if="filtered.length === 0" class="empty">
      <template v-if="profiles.length === 0">
        <p class="empty-title serif">还没有人物档案</p>
        <p class="empty-tip">点击右上角「新建档案」，3 项信息即可开始第一次推演。</p>
      </template>
      <template v-else>
        <p class="empty-tip">没有匹配「{{ keyword }}」的档案。</p>
      </template>
    </div>

    <div v-else class="card-list">
      <div v-for="p in filtered" :key="p.id" class="profile-card">
        <router-link :to="`/profiles/${p.id}`" class="card-main">
          <div class="card-name serif">{{ p.name || '未命名' }}</div>
          <div class="card-meta">
            <span>🕐 {{ fmt(p.updatedAt) }}</span>
            <span class="dot">·</span>
            <span>推演 {{ p.deduceCount }} 次</span>
          </div>
        </router-link>
        <div class="card-actions">
          <button class="icon-btn" title="复制档案" @click="onDuplicate(p)">⧉</button>
          <button class="icon-btn danger" title="删除档案" @click="onDelete(p)">🗑</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listProfiles, duplicateProfile, deleteProfile } from '../services/profile-service.js'

const router = useRouter()
const profiles = ref([])
const keyword = ref('')
const menuOpen = ref(false)

const filtered = computed(() => {
  const k = keyword.value.trim()
  if (!k) return profiles.value
  return profiles.value.filter(p => (p.name || '').includes(k))
})

function fmt(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  const p = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

async function refresh() {
  profiles.value = await listProfiles()
}

async function onDuplicate(p) {
  if (!confirm(`复制档案「${p.name}」？仅复制人物画像，不复制推演/复盘/待办。`)) return
  await duplicateProfile(p.id)
  await refresh()
}

async function onDelete(p) {
  if (!confirm(`确认删除档案「${p.name}」？将级联删除其全部推演、复盘、待办。`)) return
  await deleteProfile(p.id)
  await refresh()
}

onMounted(refresh)
</script>

<style scoped>
.page { padding: var(--sp-lg); }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--sp-md); }
.page-header h1 { font-size: var(--fs-h2); color: var(--color-primary-700); }
.new-dropdown { position: relative; }
.btn { padding: var(--sp-sm) var(--sp-md); border: none; border-radius: var(--radius-md); font-size: var(--fs-body); }
.btn-primary { background: var(--color-primary-500); color: #fff; }
.btn-primary:hover { background: var(--color-primary-600); }
.dropdown {
  position: absolute; right: 0; top: 100%; margin-top: var(--sp-xs);
  background: #fff; border-radius: var(--radius-md); box-shadow: var(--shadow-lg);
  min-width: 260px; z-index: 100; overflow: hidden;
}
.dd-item { display: flex; flex-direction: column; padding: var(--sp-md); border-bottom: 1px solid var(--color-neutral-100); }
.dd-item:hover { background: var(--color-primary-50); }
.dd-tip { font-size: var(--fs-caption); color: var(--color-neutral-500); }
.search {
  width: 100%; padding: var(--sp-sm) var(--sp-md); font-size: var(--fs-body);
  border: 1px solid var(--color-neutral-300); border-radius: var(--radius-md); margin-bottom: var(--sp-md);
}
.motto-line { text-align: center; color: var(--color-primary-500); margin: var(--sp-lg) 0; }
.empty { text-align: center; padding: var(--sp-3xl) var(--sp-md); }
.empty-title { font-size: var(--fs-h3); color: var(--color-neutral-700); margin-bottom: var(--sp-sm); }
.empty-tip { color: var(--color-neutral-500); }
.card-list { display: flex; flex-direction: column; gap: var(--sp-md); }
.profile-card {
  display: flex; align-items: center; background: #fff; border-radius: var(--radius-lg);
  padding: var(--sp-md); box-shadow: var(--shadow-sm);
}
.card-main { flex: 1; }
.card-name { font-size: var(--fs-h3); color: var(--color-neutral-900); margin-bottom: var(--sp-xs); }
.card-meta { font-size: var(--fs-small); color: var(--color-neutral-500); }
.dot { margin: 0 var(--sp-xs); }
.card-actions { display: flex; gap: var(--sp-sm); }
.icon-btn {
  min-width: var(--touch-min); min-height: var(--touch-min); padding: 0 var(--sp-sm);
  border: 1px solid var(--color-neutral-300); background: #fff; border-radius: var(--radius-md);
  font-size: var(--fs-body);
}
.icon-btn:hover { background: var(--color-neutral-50); }
.icon-btn.danger:hover { border-color: var(--color-error); color: var(--color-error); }
</style>
