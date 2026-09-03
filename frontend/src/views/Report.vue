<template>
  <div class="page" v-if="report">
    <!-- 面包屑 -->
    <div class="breadcrumb">
      <router-link to="/profiles">档案列表</router-link>
      <span class="sep">/</span>
      <router-link :to="`/profiles/${snapshot.profileId}`">{{ profileName }}</router-link>
      <span class="sep">/</span>
      <span>推演报告</span>
    </div>

    <!-- 元信息栏 -->
    <div class="meta-bar">
      <div class="meta-grid">
        <div class="meta-item"><span class="k">编号</span><span class="v">{{ report.reportId || '—' }}</span></div>
        <div class="meta-item"><span class="k">完整度</span><span class="v">{{ meta.completenessScore ?? '—' }}%</span></div>
        <div class="meta-item"><span class="k">可信度</span><span class="v" :class="'rate-' + (meta.credibilityRating || '中')">{{ meta.credibilityRating || '—' }}</span></div>
        <div class="meta-item"><span class="k">一致性</span><span class="v">{{ meta.consistencyCoefficient || '—' }}</span></div>
        <div class="meta-item"><span class="k">知识版本</span><span class="v">{{ meta.knowledgeVersion || '—' }}</span></div>
        <div class="meta-item"><span class="k">提示词版本</span><span class="v">{{ meta.promptVersion || '—' }}</span></div>
        <div class="meta-item"><span class="k">模型</span><span class="v">{{ meta.modelVersion || '—' }}</span></div>
      </div>
    </div>

    <!-- 低可信度警告 -->
    <div v-if="isLowCredibility" class="warn-box">
      ⚠️ 本报告可信度评级为「{{ meta.credibilityRating }}」，建议补充档案信息后重新推演。
    </div>

    <!-- 一分钟速览 -->
    <div class="summary-card">
      <div class="summary-head">
        <span class="summary-title">⏱ 一分钟速览</span>
        <div class="voice-controls">
          <button class="voice-btn" @click="toggleVoice">{{ voiceState }}</button>
          <button v-if="voiceState !== '🔊 语音播报'" class="voice-btn stop" @click="stopVoice">⏹ 停止</button>
        </div>
      </div>
      <div class="summary-body">
        <p v-if="report.summary?.bestPath" class="s-line">{{ report.summary.bestPath }}</p>
        <p v-if="report.summary?.maxRisk" class="s-line">{{ report.summary.maxRisk }}</p>
        <p v-if="report.summary?.topAction" class="s-line">{{ report.summary.topAction }}</p>
        <p v-if="report.summary?.credibilityReason" class="s-line">{{ report.summary.credibilityReason }}</p>
        <p v-if="report.summary?.mindReminder" class="s-line">{{ report.summary.mindReminder }}</p>
      </div>
    </div>

    <!-- 模块一：宏观处境分析 -->
    <section class="module">
      <h2 class="serif">一、宏观处境分析</h2>
      <div v-if="macro.historicalBenchmark" class="block">
        <h3>1. 历史对标分析</h3>
        <div v-if="macro.historicalBenchmark.ancientFigures?.length" class="figures">
          <h4 class="fig-label">【古代语境】</h4>
          <div v-for="(f, i) in macro.historicalBenchmark.ancientFigures" :key="'a' + i" class="figure">
            <b>{{ f.name }}</b>：{{ f.context }}
            <span v-if="f.transformationPrinciple" class="principle">→ {{ f.transformationPrinciple }}</span>
          </div>
        </div>
        <div v-if="macro.historicalBenchmark.modernFigures?.length" class="figures">
          <h4 class="fig-label">【近现代语境】</h4>
          <div v-for="(f, i) in macro.historicalBenchmark.modernFigures" :key="'m' + i" class="figure">
            <b>{{ f.name }}</b>（{{ f.industry }}）：{{ f.principle }}
          </div>
        </div>
        <p v-if="macro.historicalBenchmark.commonPrinciples" class="common">{{ macro.historicalBenchmark.commonPrinciples }}</p>
      </div>
      <div v-if="macro.cycleAnalysis" class="block">
        <h3>2. 大势周期分析</h3>
        <p><b>阶段：</b>{{ macro.cycleAnalysis.phase }} · <b>策略：</b>{{ macro.cycleAnalysis.strategy }}</p>
        <p>{{ macro.cycleAnalysis.analysis }}</p>
      </div>
      <div v-if="macro.peerReference" class="block">
        <h3>3. 同侪参照</h3>
        <p>{{ macro.peerReference.description }}</p>
        <p class="note">{{ macro.peerReference.note || '此为宏观统计，非个人评判' }}</p>
      </div>
    </section>

    <!-- 模块二：路径 -->
    <section class="module">
      <h2 class="serif">二、多条可选发展路径</h2>
      <div v-for="(p, i) in paths" :key="i" class="path-card">
        <div class="path-head">
          <h3 class="path-name">路径{{ ['一', '二', '三', '四'][i] || i + 1 }}：{{ p.name }}</h3>
          <div class="path-score">
            <span class="score-num">{{ p.score }}</span> 分
            <span class="score-ci" v-if="p.scoreCI">（95% CI: {{ p.scoreCI.lower }} ~ {{ p.scoreCI.upper }}）</span>
          </div>
        </div>
        <p v-if="p.emotionalBuffer" class="buffer">{{ p.emotionalBuffer }}</p>

        <div v-if="p.scoringBasis?.length" class="basis">
          <div class="basis-title">📊 评分依据</div>
          <div v-for="(b, j) in p.scoringBasis" :key="j" class="basis-item">
            {{ b.factor }}（{{ b.impact }}）：{{ b.reason }}
          </div>
        </div>

        <div class="kv-grid">
          <div v-if="p.advantages" class="kv"><span class="kv-k">路径优势</span><span class="kv-v">{{ p.advantages }}</span></div>
          <div v-if="p.tradeoff" class="kv">
            <span class="kv-k">得失权衡</span>
            <span class="kv-v">收益：{{ p.tradeoff.benefits }}<br>代价：{{ p.tradeoff.costs }}<br>是否宜行：{{ p.tradeoff.isWorth }}</span>
          </div>
          <div v-if="p.switchCost" class="kv"><span class="kv-k">转换成本</span><span class="kv-v">{{ p.switchCost }}</span></div>
          <div v-if="p.historicalRisk" class="kv"><span class="kv-k">历史风险陷阱</span><span class="kv-v">{{ p.historicalRisk }}</span></div>
          <div v-if="p.costs" class="kv">
            <span class="kv-k">需要付出的代价</span>
            <span class="kv-v">金钱：{{ p.costs.money }}<br>时间：{{ p.costs.time }}<br>机会：{{ p.costs.opportunity }}<br>情绪：{{ p.costs.emotion }}</span>
          </div>
          <div v-if="p.stopLoss" class="kv">
            <span class="kv-k">止损触发阈值</span>
            <span class="kv-v">
              <span v-for="(s, k) in p.stopLoss.signals" :key="k" class="signal">· {{ s }}</span>
              <span class="mental" v-if="p.stopLoss.mentalDifficulty">心理执行难度：{{ p.stopLoss.mentalDifficulty.level }}
                <span v-if="p.stopLoss.mentalDifficulty.level === '高' && p.stopLoss.mentalDifficulty.advice" class="mental-advice">{{ p.stopLoss.mentalDifficulty.advice }}</span>
              </span>
            </span>
          </div>
        </div>
      </div>
    </section>

    <!-- 模块三：心性修炼 -->
    <section class="module" v-if="mind.weaknesses?.length || mind.references?.length">
      <h2 class="serif">三、心性修炼建议</h2>
      <div v-if="mind.references?.length" class="block">
        <p class="lead">历史中与此心性相近的人物，曾用以下方式自修，供参考借鉴。</p>
        <div v-for="(r, i) in mind.references" :key="i" class="ref">{{ r.figure }}：{{ r.practice }}</div>
      </div>
      <div v-if="mind.weeklyActions?.length" class="weekly">
        <div class="weekly-title">每周微行动</div>
        <div v-for="(w, i) in mind.weeklyActions" :key="i" class="weekly-item">{{ w.source }} → {{ w.action }}</div>
      </div>
    </section>

    <!-- 模块四：分阶段行动计划 -->
    <section class="module" v-if="plan.shortTerm?.length || plan.mediumTerm?.length || plan.longTerm?.length">
      <h2 class="serif">四、分阶段行动计划</h2>
      <div v-if="plan.shortTerm?.length" class="block">
        <h3>短期（0-6个月）</h3>
        <div v-for="(s, i) in plan.shortTerm" :key="i" class="plan-item">{{ i + 1 }}. {{ s }}</div>
      </div>
      <div v-if="plan.mediumTerm?.length" class="block">
        <h3>中期（6-24个月）</h3>
        <div v-for="(s, i) in plan.mediumTerm" :key="i" class="plan-item">{{ i + 1 }}. {{ s }}</div>
      </div>
      <div v-if="plan.longTerm?.length" class="block">
        <h3>长期（2-10年）</h3>
        <div v-for="(s, i) in plan.longTerm" :key="i" class="plan-item">{{ i + 1 }}. {{ s }}</div>
      </div>
      <div v-if="plan.avoidList?.length" class="block avoid">
        <h3>需要规避的事项</h3>
        <div v-for="(s, i) in plan.avoidList" :key="i" class="plan-item">⚠️ {{ s }}</div>
      </div>
    </section>

    <!-- 模块五：风险与变量 -->
    <section class="module" v-if="risk.sensitivity?.length || risk.externalHints || risk.warnings?.length">
      <h2 class="serif">五、风险与变量分析</h2>
      <div v-if="risk.sensitivity?.length" class="block">
        <h3>关键变量敏感性分析</h3>
        <div v-for="(s, i) in risk.sensitivity" :key="i" class="plan-item">{{ s.variable }}：{{ s.impact }}</div>
      </div>
      <div v-if="risk.externalHints?.hints?.length" class="block">
        <h3>外部环境客观提示</h3>
        <p class="note">{{ risk.externalHints.prefix }}</p>
        <div v-for="(h, i) in risk.externalHints.hints" :key="i" class="plan-item">· {{ h }}</div>
      </div>
      <div v-if="risk.warnings?.length" class="block warn">
        <h3>风险预警条件</h3>
        <div v-for="(w, i) in risk.warnings" :key="i" class="plan-item">🚨 {{ w }}</div>
      </div>
    </section>

    <!-- 模块六：免责声明 -->
    <section class="module disclaimer">
      <p class="disc-line">{{ report.disclaimer?.boundaryStatement }}</p>
      <p class="disc-transition">{{ report.disclaimer?.transition }}</p>
      <p class="disc-main serif">{{ report.disclaimer?.historicalDisclaimer }}</p>
    </section>

    <!-- 参数微调·快速重算（行动计划跟踪器上方） -->
    <ParameterTuning :snapshot="snapshot" />

    <!-- 待办跟踪器 -->
    <TodoTracker :snapshot="snapshot" />

    <!-- 底部工具栏 -->
    <div class="toolbar">
      <button class="btn ghost" @click="exportMarkdown">导出 Markdown</button>
      <button class="btn ghost" @click="exportPdf">导出 PDF</button>
      <button class="btn ghost" @click="copyAll">复制全文</button>
      <router-link :to="`/review/${snapshot.id}`" class="btn ghost">进入复盘 →</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import TodoTracker from '../components/TodoTracker.vue'
import ParameterTuning from '../components/ParameterTuning.vue'
import { getSnapshot, getProfile } from '../services/profile-service.js'

const route = useRoute()
const snapshot = ref(null)
const report = ref(null)
const profileName = ref('')
const voiceState = ref('🔊 语音播报')
let voicePlaying = false
let voicePaused = false
let voiceStopRequested = false

function summaryText() {
  const s = report.value?.summary || {}
  return Object.values(s).filter(Boolean).join('。')
}

function toggleVoice() {
  if (!('speechSynthesis' in window)) { alert('当前浏览器不支持语音播报'); return }
  const synth = window.speechSynthesis
  if (voicePlaying && !voicePaused) {
    synth.pause()
    voicePaused = true
    voiceState.value = '▶️ 继续'
  } else if (voicePlaying && voicePaused) {
    synth.resume()
    voicePaused = false
    voiceState.value = '⏸️ 暂停'
  } else {
    const u = new SpeechSynthesisUtterance(summaryText())
    u.lang = 'zh-CN'
    u.rate = 1.0
    u.onend = () => { voicePlaying = false; voicePaused = false; voiceState.value = '🔊 语音播报' }
    voiceStopRequested = false
    synth.cancel()
    synth.speak(u)
    voicePlaying = true
    voicePaused = false
    voiceState.value = '⏸️ 暂停'
  }
}

function stopVoice() {
  if (!('speechSynthesis' in window)) return
  window.speechSynthesis.cancel()
  voicePlaying = false
  voicePaused = false
  voiceState.value = '🔊 语音播报'
}

const meta = computed(() => report.value?.meta || {})
const macro = computed(() => report.value?.macroAnalysis || {})
const paths = computed(() => report.value?.paths || [])
const mind = computed(() => report.value?.mindCultivation || {})
const plan = computed(() => report.value?.actionPlan || {})
const risk = computed(() => report.value?.riskAnalysis || {})
const isLowCredibility = computed(() => ['低', '极低'].includes(meta.value.credibilityRating))

async function load() {
  snapshot.value = await getSnapshot(Number(route.params.snapshotId))
  if (!snapshot.value) { alert('报告不存在'); return }
  report.value = snapshot.value.fullReport
  const p = await getProfile(snapshot.value.profileId)
  profileName.value = p?.name || ''
}

function reportToMarkdown() {
  const r = report.value
  if (!r) return ''
  const lines = []
  lines.push(`# 推演报告 ${r.reportId || ''}`)
  lines.push(`> 生成时间：${r.timestamp || ''}`)
  lines.push('')
  if (r.summary) {
    lines.push('## 一分钟速览')
    Object.values(r.summary).forEach(v => v && lines.push(v))
    lines.push('')
  }
  lines.push('## 宏观处境分析')
  if (r.macroAnalysis?.cycleAnalysis) lines.push(`- 大势周期：${r.macroAnalysis.cycleAnalysis.phase} / ${r.macroAnalysis.cycleAnalysis.strategy}`)
  lines.push('')
  lines.push('## 可选发展路径')
  ;(r.paths || []).forEach((p, i) => {
    lines.push(`### 路径${i + 1}：${p.name}（${p.score}分）`)
    if (p.advantages) lines.push(`- 优势：${p.advantages}`)
    if (p.tradeoff) lines.push(`- 得失：${p.tradeoff.benefits} / ${p.tradeoff.costs}（${p.tradeoff.isWorth}）`)
    lines.push('')
  })
  lines.push('## 分阶段行动计划')
  ;(r.actionPlan?.shortTerm || []).forEach((s, i) => lines.push(`${i + 1}. ${s}`))
  lines.push('')
  if (r.disclaimer?.historicalDisclaimer) lines.push(`> ${r.disclaimer.historicalDisclaimer}`)
  return lines.join('\n')
}

function exportMarkdown() {
  const md = reportToMarkdown()
  const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `推演报告-${report.value?.reportId || Date.now()}.md`
  a.click()
  URL.revokeObjectURL(url)
}

async function copyAll() {
  await navigator.clipboard.writeText(reportToMarkdown())
  alert('已复制到剪贴板')
}

function exportPdf() {
  window.print()
}

onMounted(load)
</script>

<style scoped>
.page { padding: var(--sp-lg); }
.breadcrumb { font-size: var(--fs-small); color: var(--color-neutral-500); margin-bottom: var(--sp-md); }
.breadcrumb a { color: var(--color-primary-600); }
.sep { margin: 0 var(--sp-xs); }
.meta-bar { background: var(--color-neutral-50); border-radius: var(--radius-lg); padding: var(--sp-md); margin-bottom: var(--sp-md); }
.meta-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: var(--sp-sm); }
.meta-item { display: flex; flex-direction: column; }
.meta-item .k { font-size: var(--fs-caption); color: var(--color-neutral-500); }
.meta-item .v { font-size: var(--fs-small); color: var(--color-neutral-900); font-weight: 600; }
.rate-低, .rate-极低 { color: var(--color-error); }
.rate-高 { color: var(--color-success); }
.rate-中 { color: var(--color-info); }
.warn-box { background: #FFF8E1; border-left: 4px solid var(--color-warning); padding: var(--sp-md); border-radius: var(--radius-md); margin-bottom: var(--sp-md); font-size: var(--fs-small); }
.summary-card { background: #FBF6EE; border-radius: var(--radius-lg); padding: var(--sp-lg); margin-bottom: var(--sp-lg); }
.summary-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--sp-md); }
.summary-title { font-size: var(--fs-h3); color: var(--color-primary-700); font-weight: 600; }
.voice-btn { padding: var(--sp-xs) var(--sp-md); border: 1px solid var(--color-primary-500); background: #fff; color: var(--color-primary-600); border-radius: var(--radius-md); font-size: var(--fs-small); }
.summary-body { display: flex; flex-direction: column; gap: var(--sp-sm); }
.s-line { font-size: var(--fs-body); line-height: 1.7; }
.module { margin-bottom: var(--sp-xl); }
.module h2 { font-size: var(--fs-h2); color: var(--color-primary-600); margin-bottom: var(--sp-md); }
.module h3 { font-size: var(--fs-h3); color: var(--color-neutral-900); margin: var(--sp-md) 0 var(--sp-sm); }
.module h4 { font-size: var(--fs-small); color: var(--color-neutral-700); margin: var(--sp-sm) 0; }
.block { margin-bottom: var(--sp-md); }
.figure { margin-bottom: var(--sp-xs); font-size: var(--fs-body); line-height: 1.7; }
.principle { color: var(--color-primary-600); background: var(--color-primary-100); padding: 1px 6px; border-radius: var(--radius-sm); }
.common { color: var(--color-neutral-700); margin-top: var(--sp-sm); }
.note { color: var(--color-neutral-500); font-size: var(--fs-small); margin-top: var(--sp-xs); }
.path-card { background: #fff; border-radius: var(--radius-lg); padding: var(--sp-lg); box-shadow: var(--shadow-sm); margin-bottom: var(--sp-md); }
.path-head { display: flex; justify-content: space-between; align-items: baseline; gap: var(--sp-md); flex-wrap: wrap; margin-bottom: var(--sp-sm); }
.path-name { font-size: var(--fs-h3); color: var(--color-primary-700); }
.path-score { font-size: var(--fs-small); color: var(--color-neutral-700); white-space: nowrap; }
.score-num { font-size: var(--fs-h2); font-weight: 700; color: var(--color-primary-600); }
.score-ci { color: var(--color-neutral-500); }
.buffer { color: var(--color-info); font-size: var(--fs-small); margin-bottom: var(--sp-sm); }
.basis { background: var(--color-neutral-50); border-radius: var(--radius-md); padding: var(--sp-md); margin-bottom: var(--sp-sm); }
.basis-title { font-size: var(--fs-small); font-weight: 600; margin-bottom: var(--sp-xs); }
.basis-item { font-size: var(--fs-small); color: var(--color-neutral-700); margin-bottom: 4px; }
.kv-grid { display: flex; flex-direction: column; gap: var(--sp-sm); }
.kv { display: flex; gap: var(--sp-sm); font-size: var(--fs-small); }
.kv-k { flex-shrink: 0; width: 110px; color: var(--color-neutral-500); }
.kv-v { flex: 1; color: var(--color-neutral-900); line-height: 1.6; }
.signal { display: block; }
.mental { display: inline-block; margin-top: var(--sp-xs); color: var(--color-warning); font-weight: 600; }
.mental-advice { color: var(--color-neutral-700); font-weight: 400; margin-left: var(--sp-xs); }
.lead { color: var(--color-neutral-700); font-style: italic; margin-bottom: var(--sp-sm); }
.ref { margin-bottom: var(--sp-xs); font-size: var(--fs-body); }
.weekly { background: #EDF5EE; border-radius: var(--radius-md); padding: var(--sp-md); margin-top: var(--sp-sm); }
.weekly-title { font-weight: 600; color: var(--color-success); margin-bottom: var(--sp-xs); }
.weekly-item { font-size: var(--fs-small); margin-bottom: 4px; }
.plan-item { margin-bottom: var(--sp-xs); font-size: var(--fs-body); line-height: 1.7; }
.avoid .plan-item { color: var(--color-warning); }
.warn .plan-item { color: var(--color-error); }
.disclaimer { background: var(--color-neutral-50); border-radius: var(--radius-lg); padding: var(--sp-lg); font-size: var(--fs-small); }
.disc-line { color: var(--color-neutral-700); margin-bottom: var(--sp-sm); }
.disc-transition { color: var(--color-neutral-500); margin-bottom: var(--sp-sm); }
.disc-main { color: var(--color-neutral-700); }
.toolbar { display: flex; gap: var(--sp-sm); margin-top: var(--sp-lg); flex-wrap: wrap; }
.btn { padding: var(--sp-sm) var(--sp-md); border: none; border-radius: var(--radius-md); font-size: var(--fs-small); text-decoration: none; display: inline-block; }
.btn.ghost { background: #fff; border: 1px solid var(--color-neutral-300); color: var(--color-neutral-700); }
.voice-controls { display: flex; gap: var(--sp-sm); align-items: center; }
.voice-btn.stop { border-color: var(--color-error); color: var(--color-error); }

@media print {
  .breadcrumb, .toolbar, .voice-controls { display: none !important; }
  :deep(.tuning-card) { display: none !important; }
  .page { padding: 0; }
}
</style>
