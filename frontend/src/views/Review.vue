<template>
  <div class="page" v-if="report">
    <div class="breadcrumb">
      <router-link to="/profiles">档案列表</router-link>
      <span class="sep">/</span>
      <router-link :to="`/report/${snapshot.id}`">推演报告</router-link>
      <span class="sep">/</span>
      <span>复盘</span>
    </div>

    <h1 class="serif page-title">复盘迭代</h1>
    <p class="sub">复盘不改动原始推演快照，仅记录现实结果与反思。</p>

    <!-- 现实发生情况 -->
    <div class="block">
      <h3>现实发生情况</h3>
      <p class="hint">已自动填入该推演关联的已完成待办，可编辑补充。</p>
      <textarea v-model="form.actualEvents" class="input" rows="4" placeholder="这段时间实际发生了什么？"></textarea>
    </div>

    <!-- 两类反思 -->
    <div class="block">
      <h3>人为抉择因素反思</h3>
      <textarea v-model="form.humanFactors" class="input" rows="3" placeholder="自身心性、取舍选择带来的影响"></textarea>
    </div>
    <div class="block">
      <h3>外部时运变局反思</h3>
      <textarea v-model="form.externalFactors" class="input" rows="3" placeholder="不可控环境变化带来的影响"></textarea>
    </div>

    <!-- 自我同情引导 -->
    <div class="block compassion">
      <h3>自我同情引导</h3>
      <p class="compassion-q">"如果这是你最好的朋友遇到的相同情况，你会如何劝慰他？请用同样语气对自己说。"</p>
      <textarea v-model="form.selfCompassion" class="input" rows="3" placeholder="对自己说的话…"></textarea>
    </div>

    <!-- 偏差自检报告 -->
    <div class="block">
      <h3>推演偏差自检报告</h3>
      <p class="hint">对比推演时的三条关键预测与你的现实情况，逐条判断「准确」或「偏差」。</p>
      <div v-for="(p, i) in predictions" :key="i" class="pred-item">
        <div class="pred-text">{{ p.text }}</div>
        <div class="pred-controls">
          <label class="radio"><input type="radio" :name="'pred' + i" :checked="p.status === 'accurate'" @change="setStatus(i, 'accurate')" /> ✅ 准确</label>
          <label class="radio"><input type="radio" :name="'pred' + i" :checked="p.status === 'deviated'" @change="setStatus(i, 'deviated')" /> ❌ 偏差</label>
          <select v-if="p.status === 'deviated'" v-model="p.reason" class="reason-select">
            <option value="">偏差原因…</option>
            <option value="信息不全导致">信息不全导致</option>
            <option value="外部变局冲击">外部变局冲击</option>
            <option value="模型推理局限">模型推理局限</option>
            <option value="执行偏差">执行偏差</option>
          </select>
        </div>
      </div>
      <div class="pred-correct">
        <label class="corr-label">✏️ 补充修正（可选）：对上述判定进行人工修正</label>
        <textarea v-model="form.userCorrection" class="input" rows="3" placeholder="对偏差分析的补充说明或修正…"></textarea>
      </div>
    </div>

    <div class="actions">
      <button class="btn ghost" @click="save">保存复盘</button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getSnapshot, listTodos, saveReview } from '../services/profile-service.js'

const route = useRoute()
const router = useRouter()
const snapshot = ref(null)
const report = ref(null)
const form = reactive({ actualEvents: '', humanFactors: '', externalFactors: '', selfCompassion: '', userCorrection: '' })

const predictions = ref([])

async function load() {
  snapshot.value = await getSnapshot(Number(route.params.snapshotId))
  if (!snapshot.value) { alert('推演记录不存在'); return }
  report.value = snapshot.value.fullReport

  // 三条关键预测
  const s = report.value.summary || {}
  predictions.value = [
    { text: s.bestPath || '', status: null, reason: '' },
    { text: s.maxRisk || '', status: null, reason: '' },
    { text: s.mindReminder || '', status: null, reason: '' },
  ].filter(p => p.text)

  // 预填已完成待办
  const todos = await listTodos(snapshot.value.id)
  const done = todos.filter(t => t.status === 'completed').map(t => t.description)
  if (done.length) {
    form.actualEvents = '已完成事项：\n· ' + done.join('\n· ')
  }
}

function setStatus(i, status) {
  predictions.value[i].status = status
  if (status === 'accurate') predictions.value[i].reason = ''
}

async function save() {
  const deviationReport = {
    accurate: predictions.value.filter(p => p.status === 'accurate').map(p => p.text),
    deviated: predictions.value.filter(p => p.status === 'deviated').map(p => ({ item: p.text, reason: p.reason || '未注明原因' })),
    userCorrection: form.userCorrection,
  }
  const now = new Date().toISOString()
  await saveReview({
    snapshotId: snapshot.value.id,
    profileId: snapshot.value.profileId,
    actualEvents: form.actualEvents,
    humanFactors: form.humanFactors,
    externalFactors: form.externalFactors,
    selfCompassion: form.selfCompassion,
    deviationReport,
    createdAt: now,
    updatedAt: now,
  })
  alert('复盘已保存')
  router.push(`/report/${snapshot.value.id}`)
}

onMounted(load)
</script>

<style scoped>
.page { padding: var(--sp-lg); }
.breadcrumb { font-size: var(--fs-small); color: var(--color-neutral-500); margin-bottom: var(--sp-md); }
.breadcrumb a { color: var(--color-primary-600); }
.sep { margin: 0 var(--sp-xs); }
.page-title { font-size: var(--fs-h2); color: var(--color-primary-700); margin-bottom: var(--sp-xs); }
.sub { color: var(--color-neutral-500); margin-bottom: var(--sp-lg); }
.block { background: #fff; border-radius: var(--radius-lg); padding: var(--sp-lg); box-shadow: var(--shadow-sm); margin-bottom: var(--sp-md); }
.block h3 { font-size: var(--fs-h3); color: var(--color-neutral-900); margin-bottom: var(--sp-sm); }
.hint { font-size: var(--fs-caption); color: var(--color-neutral-500); margin-bottom: var(--sp-sm); }
.input { width: 100%; padding: var(--sp-sm) var(--sp-md); font-size: var(--fs-body); border: 1px solid var(--color-neutral-300); border-radius: var(--radius-md); font-family: inherit; resize: vertical; }
.input:focus { outline: none; border-color: var(--color-primary-500); }
.compassion { background: #FBF6EE; border-left: 4px solid var(--color-accent-gold); }
.compassion-q { font-style: italic; color: var(--color-neutral-700); margin-bottom: var(--sp-sm); }
.pred-item { padding: var(--sp-md); border: 1px solid var(--color-neutral-100); border-radius: var(--radius-md); margin-bottom: var(--sp-sm); }
.pred-text { font-size: var(--fs-body); margin-bottom: var(--sp-sm); line-height: 1.6; }
.pred-controls { display: flex; align-items: center; gap: var(--sp-md); flex-wrap: wrap; }
.radio { display: flex; align-items: center; gap: var(--sp-xs); font-size: var(--fs-small); cursor: pointer; }
.reason-select { padding: var(--sp-xs); font-size: var(--fs-small); border: 1px solid var(--color-neutral-300); border-radius: var(--radius-sm); }
.pred-correct { margin-top: var(--sp-md); border-top: 1px dashed var(--color-neutral-200); padding-top: var(--sp-md); }
.corr-label { display: block; font-size: var(--fs-small); color: var(--color-neutral-700); margin-bottom: var(--sp-xs); }
.actions { display: flex; justify-content: flex-end; }
.btn { padding: var(--sp-sm) var(--sp-xl); border: none; border-radius: var(--radius-md); font-size: var(--fs-body); }
.btn.ghost { background: var(--color-primary-500); color: #fff; }
.btn.ghost:hover { background: var(--color-primary-600); }
</style>
