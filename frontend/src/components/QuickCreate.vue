<template>
  <div class="quick">
    <!-- 阶段1：3 项必填 -->
    <div v-if="stage === 'form'" class="card">
      <p class="sub serif">只需填写 3 项，即可开始推演</p>
      <div v-for="f in QUICK_REQUIRED" :key="f.key" class="field">
        <label class="field-label">{{ f.label }}</label>
        <textarea
          v-if="f.type === 'textarea'"
          v-model="quick[f.key]"
          class="field-input"
          :placeholder="f.placeholder || ''"
          rows="2"
        ></textarea>
        <input
          v-else
          v-model="quick[f.key]"
          class="field-input"
          type="text"
          :placeholder="f.placeholder || ''"
        />
      </div>
      <p class="hint">提交后系统会追问 2-3 个关联问题，逐步完善档案（可随时跳过）。</p>
      <div class="actions">
        <button class="btn ghost" @click="$router.back()">取消</button>
        <button class="btn primary" @click="start">创建档案 →</button>
      </div>
    </div>

    <!-- 阶段2：对话式追问 -->
    <div v-else-if="stage === 'followup'" class="card">
      <p class="sub serif">补全档案 · 第 {{ followupNo }} / {{ totalFollowups }} 项</p>
      <div class="field">
        <label class="field-label">{{ currentField.label }}</label>
        <textarea
          v-model="followupValue"
          class="field-input"
          :placeholder="currentField.placeholder || ''"
          rows="3"
        ></textarea>
      </div>
      <div class="actions">
        <button class="btn ghost" @click="skip">跳过</button>
        <button class="btn ghost" @click="finish">完成，不再追问</button>
        <button class="btn primary" @click="saveFollowup">保存并继续</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import {
  QUICK_REQUIRED, FOLLOWUP_ORDER, FIELD_MAP, emptyProfile,
} from '../constants/profile-fields.js'
import { createProfile, updateProfile } from '../services/profile-service.js'

const router = useRouter()
const stage = ref('form')
const quick = reactive({ name: '', shortTermGoal: '', constraints: '' })
const profileId = ref(null)
const followupIdx = ref(0)
const followupValue = ref('')
const filled = ref({})

// 过滤出还没问过的追问字段
const pendingFollowups = computed(() =>
  FOLLOWUP_ORDER.filter(k => !filled.value[k] && !Object.keys(quick.value || {}).includes(k))
)
const totalFollowups = computed(() => pendingFollowups.value.length)
const followupNo = computed(() => Math.min(followupIdx.value + 1, totalFollowups.value))
const currentKey = computed(() => pendingFollowups.value[followupIdx.value])
const currentField = computed(() => (currentKey.value ? FIELD_MAP[currentKey.value] : { label: '', placeholder: '' }))

async function start() {
  if (!quick.name || !quick.name.trim()) { alert('请填写人物名称'); return }
  if (!quick.shortTermGoal.trim() && !quick.constraints.trim()) { alert('请至少填写核心目标或当前困境'); return }
  const profile = await createProfile({ ...quick })
  profileId.value = profile.id
  filled.value = { name: true, shortTermGoal: !!quick.shortTermGoal.trim(), constraints: !!quick.constraints.trim() }
  stage.value = 'followup'
}

async function saveFollowup() {
  const k = currentKey.value
  if (followupValue.value.trim()) {
    await updateProfile(profileId.value, { [k]: followupValue.value.trim() })
    filled.value = { ...filled.value, [k]: true }
  }
  followupValue.value = ''
  advance()
}

function skip() {
  followupValue.value = ''
  advance()
}

function advance() {
  if (followupIdx.value + 1 >= totalFollowups.value) {
    finish()
  } else {
    followupIdx.value++
  }
}

function finish() {
  router.push(`/profiles/${profileId.value}`)
}
</script>

<style scoped>
.card { background: #fff; border-radius: var(--radius-lg); box-shadow: var(--shadow-md); padding: var(--sp-lg); display: flex; flex-direction: column; gap: var(--sp-md); }
.sub { font-size: var(--fs-body); color: var(--color-neutral-700); }
.field { display: flex; flex-direction: column; gap: var(--sp-xs); }
.field-label { font-size: var(--fs-small); color: var(--color-neutral-700); }
.field-input {
  width: 100%; padding: var(--sp-sm) var(--sp-md); font-size: var(--fs-body);
  border: 1px solid var(--color-neutral-300); border-radius: var(--radius-md);
  font-family: inherit; resize: vertical;
}
.field-input:focus { outline: none; border-color: var(--color-primary-500); }
.hint { font-size: var(--fs-caption); color: var(--color-neutral-500); }
.actions { display: flex; gap: var(--sp-sm); justify-content: flex-end; flex-wrap: wrap; }
.btn { padding: var(--sp-sm) var(--sp-md); border: none; border-radius: var(--radius-md); font-size: var(--fs-body); }
.btn.primary { background: var(--color-primary-500); color: #fff; }
.btn.primary:hover { background: var(--color-primary-600); }
.btn.ghost { background: #fff; border: 1px solid var(--color-neutral-300); color: var(--color-neutral-700); }
</style>
