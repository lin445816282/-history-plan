<template>
  <div class="form">
    <div v-for="group in FIELD_GROUPS" :key="group.key" class="group">
      <div class="group-header" @click="toggleGroup(group.key)">
        <h3 class="group-title">
          {{ group.label }}
          <span v-if="group.core" class="core-tag">核心</span>
          <span v-else class="ext-tag">可选</span>
        </h3>
        <span class="toggle">{{ openGroups.has(group.key) ? '▾' : '▸' }}</span>
      </div>
      <div v-show="openGroups.has(group.key)" class="group-body">
        <div v-for="f in group.fields" :key="f.key" class="field">
          <label class="field-label">{{ f.label }}</label>
          <textarea
            v-if="f.type === 'textarea'"
            v-model="form[f.key]"
            class="field-input"
            :placeholder="f.placeholder || ''"
            rows="2"
          ></textarea>
          <input
            v-else
            v-model="form[f.key]"
            class="field-input"
            type="text"
            :placeholder="f.placeholder || ''"
          />
        </div>
      </div>
    </div>

    <div class="actions">
      <button class="btn ghost" @click="$router.back()">取消</button>
      <button class="btn primary" @click="save">保存档案</button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { FIELD_GROUPS, emptyProfile, completenessScore } from '../constants/profile-fields.js'
import { createProfile } from '../services/profile-service.js'

const router = useRouter()
const form = reactive(emptyProfile())

// 核心字段默认展开，扩展字段默认折叠
const openGroups = ref(new Set(FIELD_GROUPS.filter(g => g.core).map(g => g.key)))

function toggleGroup(key) {
  const s = new Set(openGroups.value)
  s.has(key) ? s.delete(key) : s.add(key)
  openGroups.value = s
}

const score = computed(() => completenessScore(form))

async function save() {
  if (!form.name || !form.name.trim()) {
    alert('请至少填写「人物名称」')
    return
  }
  const profile = await createProfile({ ...form })
  router.push(`/profiles/${profile.id}`)
}
</script>

<style scoped>
.form { display: flex; flex-direction: column; gap: var(--sp-md); }
.group { background: #fff; border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); overflow: hidden; }
.group-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: var(--sp-md); cursor: pointer; background: var(--color-neutral-50);
}
.group-title { font-size: var(--fs-body); color: var(--color-neutral-900); }
.core-tag { font-size: var(--fs-caption); color: var(--color-primary-600); background: var(--color-primary-100); padding: 2px 6px; border-radius: var(--radius-sm); margin-left: var(--sp-xs); }
.ext-tag { font-size: var(--fs-caption); color: var(--color-neutral-500); background: var(--color-neutral-100); padding: 2px 6px; border-radius: var(--radius-sm); margin-left: var(--sp-xs); }
.toggle { color: var(--color-neutral-500); }
.group-body { padding: var(--sp-md); display: flex; flex-direction: column; gap: var(--sp-md); }
.field { display: flex; flex-direction: column; gap: var(--sp-xs); }
.field-label { font-size: var(--fs-small); color: var(--color-neutral-700); }
.field-input {
  width: 100%; padding: var(--sp-sm) var(--sp-md); font-size: var(--fs-body);
  border: 1px solid var(--color-neutral-300); border-radius: var(--radius-md);
  font-family: inherit; resize: vertical;
}
.field-input:focus { outline: none; border-color: var(--color-primary-500); }
.actions { display: flex; gap: var(--sp-md); justify-content: flex-end; }
.btn { padding: var(--sp-sm) var(--sp-xl); border: none; border-radius: var(--radius-md); font-size: var(--fs-body); }
.btn.primary { background: var(--color-primary-500); color: #fff; }
.btn.primary:hover { background: var(--color-primary-600); }
.btn.ghost { background: #fff; border: 1px solid var(--color-neutral-300); color: var(--color-neutral-700); }
</style>
