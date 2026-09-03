<template>
  <div class="simple">
    <!-- 输入阶段 -->
    <div v-if="stage === 'input'" class="card">
      <p class="sub serif">用自然语言描述这个人的情况，AI 帮你解析成结构化档案</p>
      <textarea
        v-model="text"
        class="field-input big"
        rows="8"
        placeholder="例如：我是做电商的，28岁，在杭州，想扩大规模但资金不足，性格有点急躁，家里能帮一点忙但不多，去年踩过坑亏了一笔…"
      ></textarea>
      <p class="hint">💡 建议补充：心性取舍、遇事抉择倾向、过往关键抉择</p>
      <div class="actions">
        <button class="btn ghost" @click="$router.back()">取消</button>
        <button class="btn primary" :disabled="loading" @click="parse">
          {{ loading ? '解析中…' : 'AI 解析 →' }}
        </button>
      </div>
    </div>

    <!-- 预览阶段 -->
    <div v-else class="card">
      <p class="sub serif">解析完成，请核对修正（蓝色=AI提取，灰色=待补，红色=存疑请复核）</p>
      <div v-for="group in FIELD_GROUPS" :key="group.key" class="group">
        <h4 class="group-title">{{ group.label }}</h4>
        <div v-for="f in group.fields" :key="f.key" class="field">
          <label class="field-label" :class="statusClass(f.key)">{{ f.label }}</label>
          <textarea
            v-if="f.type === 'textarea'"
            v-model="form[f.key]"
            class="field-input"
            :class="statusClass(f.key)"
            :placeholder="f.placeholder || ''"
            rows="2"
          ></textarea>
          <input
            v-else
            v-model="form[f.key]"
            class="field-input"
            :class="statusClass(f.key)"
            type="text"
            :placeholder="f.placeholder || ''"
          />
        </div>
      </div>
      <div class="actions">
        <button class="btn ghost" @click="stage = 'input'">返回修改</button>
        <button class="btn primary" @click="save">保存档案</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { FIELD_GROUPS, emptyProfile } from '../constants/profile-fields.js'
import { parseProfile } from '../api/index.js'
import { createProfile } from '../services/profile-service.js'

const router = useRouter()
const stage = ref('input')
const text = ref('')
const loading = ref(false)
const form = reactive(emptyProfile())

async function parse() {
  if (!text.value.trim()) { alert('请先输入描述'); return }
  loading.value = true
  try {
    const result = await parseProfile(text.value)
    // 解析结果可能是 { profile: {...} } 或直接是 profile
    const parsed = result.profile || result
    Object.keys(form).forEach(k => { form[k] = parsed[k] ?? '' })
    stage.value = 'preview'
  } catch (e) {
    alert('解析失败：' + e.message)
  } finally {
    loading.value = false
  }
}

function statusClass(key) {
  const v = form[key] || ''
  if (!v.trim()) return 'missing'
  return v.includes('【待确认】') ? 'ambiguous' : 'extracted'
}

async function save() {
  if (!form.name || !form.name.trim()) { alert('请填写人物名称'); return }
  const profile = await createProfile({ ...form })
  router.push(`/profiles/${profile.id}`)
}
</script>

<style scoped>
.card { background: #fff; border-radius: var(--radius-lg); box-shadow: var(--shadow-md); padding: var(--sp-lg); display: flex; flex-direction: column; gap: var(--sp-md); }
.sub { font-size: var(--fs-body); color: var(--color-neutral-700); }
.field-input {
  width: 100%; padding: var(--sp-sm) var(--sp-md); font-size: var(--fs-body);
  border: 1px solid var(--color-neutral-300); border-radius: var(--radius-md);
  font-family: inherit; resize: vertical;
}
.field-input.big { min-height: 160px; }
.field-input:focus { outline: none; border-color: var(--color-primary-500); }
.hint { font-size: var(--fs-caption); color: var(--color-neutral-500); }
.group { border-top: 1px solid var(--color-neutral-100); padding-top: var(--sp-md); }
.group-title { font-size: var(--fs-small); color: var(--color-neutral-700); margin-bottom: var(--sp-sm); }
.field { display: flex; flex-direction: column; gap: var(--sp-xs); margin-bottom: var(--sp-sm); }
.field-label { font-size: var(--fs-small); }
/* 状态色 */
.extracted { color: var(--color-ai-extracted); }
.extracted.field-input { border-color: var(--color-ai-extracted); }
.missing { color: var(--color-ai-missing); }
.ambiguous { color: var(--color-ai-ambiguous); }
.ambiguous.field-input { border-color: var(--color-ai-ambiguous); }
.actions { display: flex; gap: var(--sp-sm); justify-content: flex-end; }
.btn { padding: var(--sp-sm) var(--sp-md); border: none; border-radius: var(--radius-md); font-size: var(--fs-body); }
.btn.primary { background: var(--color-primary-500); color: #fff; }
.btn.primary:hover { background: var(--color-primary-600); }
.btn.primary:disabled { background: var(--color-neutral-300); cursor: not-allowed; }
.btn.ghost { background: #fff; border: 1px solid var(--color-neutral-300); color: var(--color-neutral-700); }
</style>
