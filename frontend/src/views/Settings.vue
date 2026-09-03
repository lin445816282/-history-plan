<template>
  <div class="page">
    <h1 class="serif page-title">系统设置</h1>

    <!-- 数据备份与恢复 -->
    <div class="block">
      <h3>数据备份与恢复</h3>
      <p class="hint">所有数据（档案/快照/复盘/待办）存于浏览器本地，建议定期导出备份。</p>
      <div class="btn-row">
        <button class="btn primary" @click="exportData">⬇️ 导出全部数据</button>
        <button class="btn ghost" @click="triggerImport">⬆️ 导入备份恢复</button>
        <input ref="fileInput" type="file" accept=".json" style="display:none" @change="onImportFile" />
      </div>
      <p v-if="lastMsg" class="msg">{{ lastMsg }}</p>
    </div>

    <!-- 后端状态 -->
    <div class="block">
      <h3>推演引擎（模型选择）</h3>
      <div class="model-select">
        <label v-for="(p, key) in providers" :key="key" class="model-opt" :class="{ active: selectedProvider === key }">
          <input type="radio" name="provider" :value="key" :checked="selectedProvider === key" @change="chooseProvider(key)" />
          <span class="model-name">{{ p.name }}</span>
          <span class="model-tag">{{ p.model }}</span>
          <span v-if="!p.configured" class="model-unconfigured">未配置Key</span>
        </label>
      </div>
      <div v-if="healthInfo" class="health">
        <div class="health-row"><span class="k">状态</span><span class="v" :class="healthInfo.status === 'ok' ? 'ok' : 'bad'">{{ healthInfo.status === 'ok' ? '正常' : '异常' }}</span></div>
        <div class="health-row"><span class="k">提示词版本</span><span class="v">{{ healthInfo.prompt_version }}</span></div>
        <div class="health-row"><span class="k">知识库版本</span><span class="v">{{ healthInfo.knowledge_version }}</span></div>
      </div>
      <p v-else class="hint">正在检测…</p>
    </div>

    <!-- 自定义历史案例 -->
    <div class="block">
      <h3>自定义历史案例</h3>
      <p class="hint">添加你自己的对标案例，推演时会优先参考。</p>
      <div v-if="customCases.length" class="case-list">
        <div v-for="c in customCases" :key="c.id" class="case-item">
          <div class="case-main">
            <span class="case-name">{{ c.name }}</span>
            <span class="case-tag">{{ c.industry || c.era || (c.type === 'ancient' ? '古代' : '近现代') }}</span>
            <span class="case-principle">{{ c.principle }}</span>
          </div>
          <button class="icon-btn" title="删除" @click="removeCase(c)">✕</button>
        </div>
      </div>
      <p v-else class="hint">暂无自定义案例。</p>
      <div class="case-form">
        <div class="case-row">
          <input v-model="newCase.name" class="case-input" placeholder="人物名（如 稻盛和夫）" />
          <select v-model="newCase.type" class="case-input">
            <option value="modern">近现代</option>
            <option value="ancient">古代</option>
          </select>
          <input v-model="newCase.industry" class="case-input" placeholder="行业（如 制造工匠）" />
          <input v-model="newCase.era" class="case-input" placeholder="时代（如 平成时代）" />
        </div>
        <textarea v-model="newCase.context" class="case-input" rows="2" placeholder="背景注解"></textarea>
        <textarea v-model="newCase.principle" class="case-input" rows="2" placeholder="古今转化行动原则（≤50字）"></textarea>
        <textarea v-model="newCase.lesson" class="case-input" rows="2" placeholder="教训/启示"></textarea>
        <button class="btn primary" @click="addCase">＋ 添加案例</button>
      </div>
    </div>

    <!-- 定位与边界 -->
    <div class="block disclaimer">
      <h3>系统定位</h3>
      <p class="serif motto">谋事在人，顺时知变</p>
      <p class="hint">本系统为历史事理决策辅助工具，不作命运预言。</p>
      <ul class="boundary">
        <li>不提供算命占卜、玄学预测</li>
        <li>不提供投资、理财、交易建议</li>
        <li>不提供心理诊断、法律意见</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { exportAllData, importAllData, listCustomCases, saveCustomCase, deleteCustomCase } from '../services/profile-service.js'
import { health, getProvider, setProvider } from '../api/index.js'

const fileInput = ref(null)
const lastMsg = ref('')
const healthInfo = ref(null)
const selectedProvider = ref(getProvider())
const providers = computed(() => healthInfo.value?.providers || {})
const customCases = ref([])
const newCase = reactive({ name: '', type: 'modern', industry: '', era: '', context: '', principle: '', lesson: '' })

function chooseProvider(key) {
  selectedProvider.value = key
  setProvider(key)
  lastMsg.value = `已切换模型，下次推演/解析将使用 ${providers.value[key]?.name || key}。`
}

async function loadCases() {
  customCases.value = await listCustomCases()
}

async function addCase() {
  if (!newCase.name.trim()) { alert('请填写人物名'); return }
  if (!newCase.principle.trim()) { alert('请填写古今转化行动原则'); return }
  await saveCustomCase({ ...newCase })
  newCase.name = newCase.industry = newCase.era = newCase.context = newCase.principle = newCase.lesson = ''
  newCase.type = 'modern'
  await loadCases()
  lastMsg.value = '案例已添加，推演时会优先参考。'
}

async function removeCase(c) {
  if (!confirm(`删除案例「${c.name}」？`)) return
  await deleteCustomCase(c.id)
  await loadCases()
}

function fmtDate(d) {
  const p = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}`
}

async function exportData() {
  const data = await exportAllData()
  const json = JSON.stringify(data, null, 2)
  const blob = new Blob([json], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `history-plan-backup-${fmtDate(new Date())}.json`
  a.click()
  URL.revokeObjectURL(url)
  lastMsg.value = '已导出，请妥善保存文件。'
}

function triggerImport() {
  fileInput.value.click()
}

async function onImportFile(e) {
  const file = e.target.files[0]
  if (!file) return
  if (!confirm('导入将采用合并策略（新数据追加，ID 冲突以导入数据为准）。确认继续？')) {
    e.target.value = ''
    return
  }
  try {
    const text = await file.text()
    const data = JSON.parse(text)
    // 格式校验
    if (!data.profiles || !Array.isArray(data.profiles)) {
      throw new Error('备份文件格式不正确（缺少 profiles 字段）')
    }
    const result = await importAllData(data)
    lastMsg.value = `导入完成：新增 ${result.added} 条，合并 ${result.merged} 条${result.errors ? `，失败 ${result.errors} 条` : ''}。`
  } catch (err) {
    lastMsg.value = '导入失败：' + err.message
  } finally {
    e.target.value = ''
  }
}

onMounted(async () => {
  loadCases()
  try {
    healthInfo.value = await health()
  } catch (_) {
    healthInfo.value = { status: 'error' }
  }
})
</script>

<style scoped>
.page { padding: var(--sp-lg); }
.page-title { font-size: var(--fs-h2); color: var(--color-primary-700); margin-bottom: var(--sp-lg); }
.block { background: #fff; border-radius: var(--radius-lg); padding: var(--sp-lg); box-shadow: var(--shadow-sm); margin-bottom: var(--sp-md); }
.block h3 { font-size: var(--fs-h3); color: var(--color-neutral-900); margin-bottom: var(--sp-sm); }
.hint { font-size: var(--fs-small); color: var(--color-neutral-500); margin-bottom: var(--sp-sm); }
.btn-row { display: flex; gap: var(--sp-md); flex-wrap: wrap; margin: var(--sp-md) 0; }
.btn { padding: var(--sp-sm) var(--sp-lg); border: none; border-radius: var(--radius-md); font-size: var(--fs-body); }
.btn.primary { background: var(--color-primary-500); color: #fff; }
.btn.primary:hover { background: var(--color-primary-600); }
.btn.ghost { background: #fff; border: 1px solid var(--color-neutral-300); color: var(--color-neutral-700); }
.msg { font-size: var(--fs-small); color: var(--color-info); }
.health { display: flex; flex-direction: column; gap: var(--sp-xs); }
.model-select { display: flex; flex-direction: column; gap: var(--sp-sm); margin-bottom: var(--sp-md); }
.model-opt { display: flex; align-items: center; gap: var(--sp-sm); padding: var(--sp-sm) var(--sp-md); border: 1px solid var(--color-neutral-300); border-radius: var(--radius-md); cursor: pointer; }
.model-opt.active { border-color: var(--color-primary-500); background: var(--color-primary-50); }
.model-name { font-size: var(--fs-small); font-weight: 600; color: var(--color-neutral-900); }
.model-tag { font-size: var(--fs-caption); color: var(--color-neutral-500); }
.model-unconfigured { font-size: var(--fs-caption); color: var(--color-error); }
.case-list { display: flex; flex-direction: column; gap: var(--sp-sm); margin-bottom: var(--sp-md); }
.case-item { display: flex; align-items: center; gap: var(--sp-sm); padding: var(--sp-sm) var(--sp-md); background: var(--color-neutral-50); border-radius: var(--radius-md); }
.case-main { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.case-name { font-size: var(--fs-small); font-weight: 600; color: var(--color-neutral-900); }
.case-tag { font-size: var(--fs-caption); color: var(--color-secondary-500, #4A6A8B); }
.case-principle { font-size: var(--fs-caption); color: var(--color-neutral-500); }
.case-form { display: flex; flex-direction: column; gap: var(--sp-sm); border-top: 1px dashed var(--color-neutral-200); padding-top: var(--sp-md); }
.case-row { display: flex; gap: var(--sp-sm); flex-wrap: wrap; }
.case-input { flex: 1; min-width: 120px; padding: var(--sp-xs) var(--sp-sm); font-size: var(--fs-small); border: 1px solid var(--color-neutral-300); border-radius: var(--radius-md); font-family: inherit; resize: vertical; }
.case-input:focus { outline: none; border-color: var(--color-primary-500); }
.icon-btn { min-width: 32px; min-height: 32px; padding: 0 var(--sp-sm); border: none; background: transparent; color: var(--color-neutral-500); border-radius: var(--radius-sm); font-size: var(--fs-small); cursor: pointer; }
.icon-btn:hover { background: var(--color-neutral-100); color: var(--color-error); }
.health-row { display: flex; gap: var(--sp-md); font-size: var(--fs-small); }
.health-row .k { width: 90px; color: var(--color-neutral-500); }
.health-row .v { color: var(--color-neutral-900); }
.health-row .ok { color: var(--color-success); font-weight: 600; }
.health-row .bad { color: var(--color-error); font-weight: 600; }
.disclaimer { background: var(--color-neutral-50); }
.motto { font-size: var(--fs-h3); color: var(--color-primary-600); margin-bottom: var(--sp-sm); }
.boundary { padding-left: var(--sp-lg); color: var(--color-neutral-700); font-size: var(--fs-small); }
</style>
