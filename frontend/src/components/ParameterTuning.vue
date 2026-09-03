<template>
  <section class="tuning-card">
    <div class="tuning-head">
      <h2 class="tuning-title">⚙️ 参数微调 · 快速重算</h2>
      <span class="tuning-hint">拖动变量，重算各路径可行性评分（成本约为完整推演的 20%）</span>
    </div>

    <!-- 滑动条 -->
    <div class="sliders">
      <div v-for="s in sliders" :key="s.field" class="slider-row">
        <div class="slider-label">
          <span class="slider-name">{{ s.label }}</span>
          <span class="slider-val" :class="{ up: s.value > 0, down: s.value < 0 }">
            {{ fmtPct(s.value) }}
          </span>
        </div>
        <input
          type="range"
          min="-50"
          max="50"
          step="10"
          v-model.number="s.value"
          class="slider-input"
          :disabled="loading"
        />
        <div class="slider-scale"><span>-50%</span><span>0</span><span>+50%</span></div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="tuning-actions">
      <button class="btn primary" :disabled="loading || !dirty" @click="runRecalc">
        {{ loading ? '重算中…' : '🔁 重算' }}
      </button>
      <button class="btn ghost" :disabled="loading" @click="reset">重置</button>
    </div>

    <p v-if="!dirty" class="tuning-tip">请先拖动至少一个变量（离开 0 位置），再点击重算。</p>

    <!-- 结果区 -->
    <div v-if="result" class="result">
      <h3 class="result-title">📊 调整后分数变化</h3>
      <div v-for="(p, i) in result.paths" :key="i" class="result-row">
        <div class="result-path-name">路径{{ ['一', '二', '三', '四'][i] || i + 1 }}：{{ p.name }}</div>
        <div class="result-bar-wrap">
          <div class="result-bar old" :style="{ width: (p.originalScore / 10 * 100) + '%' }"></div>
          <div class="result-bar new" :style="{ width: (p.newScore / 10 * 100) + '%' }"></div>
        </div>
        <div class="result-scores">
          <span class="old-score">{{ p.originalScore }}</span>
          <span class="arrow">→</span>
          <span class="new-score">{{ p.newScore }}</span>
          <span class="delta" :class="deltaCls(p.delta)">{{ fmtDelta(p.delta) }}</span>
        </div>
        <p v-if="p.delta !== 0 && p.reason" class="result-reason">{{ p.reason }}</p>
      </div>

      <div v-if="result.riskUpdates?.length" class="result-risk">
        <div class="result-risk-title">⚠️ 风险提示更新</div>
        <div v-for="(r, i) in result.riskUpdates" :key="i" class="result-risk-item">· {{ r }}</div>
      </div>

      <p v-if="result.summary" class="result-summary">{{ result.summary }}</p>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import { recalc } from '../api/index.js'

const props = defineProps({
  snapshot: { type: Object, required: true },
})

const SLIDER_DEFS = [
  { field: 'financialResources', label: '资金储备' },
  { field: 'timeResources', label: '时间投入' },
  { field: 'networkResources', label: '人脉资源' },
  { field: 'toolResources', label: '工具/技术' },
]

const sliders = ref(SLIDER_DEFS.map(d => ({ ...d, value: 0 })))
const loading = ref(false)
const result = ref(null)

const dirty = computed(() => sliders.value.some(s => s.value !== 0))

function fmtPct(v) {
  return (v > 0 ? '+' : '') + v + '%'
}
function fmtDelta(d) {
  return (d > 0 ? '+' : '') + d.toFixed(1)
}
function deltaCls(d) {
  return d > 0 ? 'delta-up' : d < 0 ? 'delta-down' : 'delta-zero'
}

async function runRecalc() {
  const adjustments = sliders.value
    .filter(s => s.value !== 0)
    .map(s => ({ field: s.field, label: s.label, delta: s.value / 100 }))
  if (!adjustments.length) return

  const paths = (props.snapshot.fullReport?.paths || []).map(p => ({
    name: p.name || '',
    score: p.score,
  }))
  if (!paths.length) { alert('报告缺少路径数据，无法重算'); return }

  loading.value = true
  try {
    const res = await recalc(props.snapshot.profileSnapshot || {}, paths, adjustments)
    // 后端可能返回空 paths 或字段缺失，做兜底对齐
    if (res.paths) {
      res.paths = res.paths.map((p, i) => {
        const orig = paths[i] || {}
        return {
          name: p.name || orig.name || '',
          originalScore: typeof p.originalScore === 'number' ? p.originalScore : (orig.score ?? 0),
          newScore: typeof p.newScore === 'number' ? p.newScore : (p.originalScore ?? orig.score ?? 0),
          delta: typeof p.delta === 'number' ? p.delta : 0,
          reason: p.reason || '',
        }
      })
    }
    result.value = res
  } catch (e) {
    alert('重算失败：' + e.message)
  } finally {
    loading.value = false
  }
}

function reset() {
  sliders.value.forEach(s => { s.value = 0 })
  result.value = null
}
</script>

<style scoped>
.tuning-card { background: #fff; border-radius: var(--radius-lg); padding: var(--sp-lg); box-shadow: var(--shadow-sm); margin-bottom: var(--sp-lg); }
.tuning-head { margin-bottom: var(--sp-md); }
.tuning-title { font-size: var(--fs-h3); color: var(--color-primary-700); margin-bottom: var(--sp-xs); }
.tuning-hint { font-size: var(--fs-caption); color: var(--color-neutral-500); }
.sliders { display: flex; flex-direction: column; gap: var(--sp-md); margin-bottom: var(--sp-md); }
.slider-row { display: flex; flex-direction: column; gap: var(--sp-xs); }
.slider-label { display: flex; justify-content: space-between; align-items: center; }
.slider-name { font-size: var(--fs-small); color: var(--color-neutral-700); font-weight: 600; }
.slider-val { font-size: var(--fs-small); font-weight: 700; color: var(--color-neutral-500); }
.slider-val.up { color: var(--color-success); }
.slider-val.down { color: var(--color-error); }
.slider-input { width: 100%; accent-color: var(--color-primary-500); }
.slider-scale { display: flex; justify-content: space-between; font-size: var(--fs-caption); color: var(--color-neutral-400); }
.tuning-actions { display: flex; gap: var(--sp-sm); margin-bottom: var(--sp-sm); }
.btn { padding: var(--sp-sm) var(--sp-md); border: none; border-radius: var(--radius-md); font-size: var(--fs-small); min-height: var(--touch-min); }
.btn.primary { background: var(--color-primary-500); color: #fff; }
.btn.primary:disabled { background: var(--color-neutral-300); cursor: not-allowed; }
.btn.ghost { background: #fff; border: 1px solid var(--color-neutral-300); color: var(--color-neutral-700); }
.tuning-tip { font-size: var(--fs-caption); color: var(--color-neutral-400); }
.result { margin-top: var(--sp-md); border-top: 1px dashed var(--color-neutral-200); padding-top: var(--sp-md); }
.result-title { font-size: var(--fs-small); font-weight: 600; color: var(--color-neutral-700); margin-bottom: var(--sp-md); }
.result-row { margin-bottom: var(--sp-md); }
.result-path-name { font-size: var(--fs-small); color: var(--color-neutral-900); font-weight: 600; margin-bottom: var(--sp-xs); }
.result-bar-wrap { position: relative; height: 14px; background: var(--color-neutral-100); border-radius: var(--radius-sm); overflow: hidden; }
.result-bar { position: absolute; top: 0; left: 0; height: 100%; border-radius: var(--radius-sm); }
.result-bar.old { background: var(--color-neutral-300); z-index: 1; }
.result-bar.new { background: var(--color-primary-500); z-index: 2; }
.result-scores { display: flex; align-items: center; gap: var(--sp-xs); font-size: var(--fs-small); margin-top: var(--sp-xs); }
.old-score { color: var(--color-neutral-500); }
.arrow { color: var(--color-neutral-400); }
.new-score { font-weight: 700; color: var(--color-primary-700); }
.delta { font-weight: 700; }
.delta-up { color: var(--color-success); }
.delta-down { color: var(--color-error); }
.delta-zero { color: var(--color-neutral-400); }
.result-reason { font-size: var(--fs-caption); color: var(--color-neutral-500); margin-top: 2px; padding-left: var(--sp-xs); }
.result-risk { background: #FFF8E1; border-radius: var(--radius-md); padding: var(--sp-md); margin-top: var(--sp-sm); }
.result-risk-title { font-size: var(--fs-small); font-weight: 600; color: var(--color-warning); margin-bottom: var(--sp-xs); }
.result-risk-item { font-size: var(--fs-small); color: var(--color-neutral-700); margin-bottom: 2px; }
.result-summary { margin-top: var(--sp-sm); font-size: var(--fs-small); color: var(--color-neutral-700); line-height: 1.6; }
</style>
