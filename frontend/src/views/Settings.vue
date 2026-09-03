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
      <h3>推演引擎状态</h3>
      <div v-if="healthInfo" class="health">
        <div class="health-row"><span class="k">状态</span><span class="v" :class="healthInfo.status === 'ok' ? 'ok' : 'bad'">{{ healthInfo.status === 'ok' ? '正常' : '异常' }}</span></div>
        <div class="health-row"><span class="k">模型</span><span class="v">{{ healthInfo.model }}</span></div>
        <div class="health-row"><span class="k">提示词版本</span><span class="v">{{ healthInfo.prompt_version }}</span></div>
        <div class="health-row"><span class="k">知识库版本</span><span class="v">{{ healthInfo.knowledge_version }}</span></div>
        <div class="health-row"><span class="k">API Key</span><span class="v">{{ healthInfo.api_key_configured ? '已配置' : '未配置' }}</span></div>
      </div>
      <p v-else class="hint">正在检测…</p>
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
import { ref, onMounted } from 'vue'
import { exportAllData, importAllData } from '../services/profile-service.js'
import { health } from '../api/index.js'

const fileInput = ref(null)
const lastMsg = ref('')
const healthInfo = ref(null)

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
.health-row { display: flex; gap: var(--sp-md); font-size: var(--fs-small); }
.health-row .k { width: 90px; color: var(--color-neutral-500); }
.health-row .v { color: var(--color-neutral-900); }
.health-row .ok { color: var(--color-success); font-weight: 600; }
.health-row .bad { color: var(--color-error); font-weight: 600; }
.disclaimer { background: var(--color-neutral-50); }
.motto { font-size: var(--fs-h3); color: var(--color-primary-600); margin-bottom: var(--sp-sm); }
.boundary { padding-left: var(--sp-lg); color: var(--color-neutral-700); font-size: var(--fs-small); }
</style>
