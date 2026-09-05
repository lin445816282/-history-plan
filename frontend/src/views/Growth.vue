<template>
  <div class="page" v-if="profile">
    <div class="breadcrumb">
      <router-link to="/profiles">档案列表</router-link>
      <span class="sep">/</span>
      <router-link :to="`/profiles/${profile.id}`">{{ profile.name || '未命名' }}</router-link>
      <span class="sep">/</span>
      <span>成长追踪</span>
    </div>

    <h1 class="serif page-title">成长追踪</h1>
    <p class="sub">基于多次推演复盘，观察预测准确率的演变轨迹。</p>

    <!-- 空态 -->
    <div v-if="!data || !data.totalReviews" class="empty">
      <div class="empty-icon">🌱</div>
      <p>该人物还没有复盘记录。</p>
      <p class="hint">完成推演后，在报告页点击「复盘」记录现实结果，即可看到准确率的成长曲线。</p>
    </div>

    <template v-else>
      <!-- 总览卡片 -->
      <div class="cards">
        <div class="card"><div class="card-num">{{ data.totalReviews }}</div><div class="card-label">复盘次数</div></div>
        <div class="card"><div class="card-num ok">{{ data.totalAccurate }}</div><div class="card-label">累计准确项</div></div>
        <div class="card"><div class="card-num bad">{{ data.totalDeviated }}</div><div class="card-label">累计偏差项</div></div>
        <div class="card"><div class="card-num">{{ data.latestRate != null ? data.latestRate + '%' : '—' }}</div><div class="card-label">最新准确率</div></div>
        <div class="card"><div class="card-num">{{ data.todoRate }}%</div><div class="card-label">待办完成率</div></div>
      </div>

      <!-- 准确率趋势 -->
      <div class="block">
        <h3>准确率趋势</h3>
        <div class="legend">
          <span class="lg"><i class="dot" style="background:#2D7D46"></i>≥70% 较准</span>
          <span class="lg"><i class="dot" style="background:#D48C2B"></i>40-70% 一般</span>
          <span class="lg"><i class="dot" style="background:#B33A3A"></i>&lt;40% 偏差大</span>
        </div>
        <div class="trend">
          <div v-for="(p, i) in data.points" :key="p.id" class="trend-col">
            <div class="trend-track">
              <div class="trend-bar" :style="{ height: (p.rate ?? 0) + '%', background: rateColor(p.rate) }" :title="`${fmt(p.createdAt)} 准确率 ${p.rate ?? '—'}%`"></div>
            </div>
            <span class="trend-label">{{ fmt(p.createdAt) }}</span>
          </div>
        </div>
      </div>

      <!-- 路径评分轨迹 -->
      <div v-if="trajPaths.length && trajectory.timePoints.length >= 2" class="block">
        <h3>路径评分轨迹</h3>
        <p class="hint">各发展路径评分随多次推演/再推演的演变，反映持仓式演算的校准过程。</p>
        <div class="legend">
          <span v-for="p in trajPaths" :key="p.name" class="lg">
            <i class="dot" :style="{ background: p.color }"></i>{{ p.name }}
          </span>
        </div>
        <svg :viewBox="trajViewBox" class="traj-svg" preserveAspectRatio="xMidYMid meet">
          <line v-for="g in [0, 2, 4, 6, 8, 10]" :key="'grid' + g" :x1="PLOT_LEFT" :x2="PLOT_LEFT + PLOT_W" :y1="PLOT_TOP + (10 - g) / 10 * PLOT_H" :y2="PLOT_TOP + (10 - g) / 10 * PLOT_H" class="grid" />
          <text v-for="g in [0, 2, 4, 6, 8, 10]" :key="'yt' + g" :x="PLOT_LEFT - 8" :y="PLOT_TOP + (10 - g) / 10 * PLOT_H + 4" class="axis-text" text-anchor="end">{{ g }}</text>
          <text v-for="(l, i) in trajXLabels" :key="'xt' + i" :x="l.x" :y="PLOT_TOP + PLOT_H + 20" class="axis-text" text-anchor="middle">{{ l.label }}</text>
          <polyline v-for="p in trajPaths" :key="p.name" :points="p.pointsStr" :stroke="p.color" class="traj-line" />
          <circle v-for="d in trajDots" :key="d.name + '-' + d.timestamp" :cx="d.x" :cy="d.y" :fill="d.color" r="3.5">
            <title>{{ d.name }} · {{ fmt(d.timestamp) }} · {{ d.score ?? '—' }}分</title>
          </circle>
        </svg>
      </div>

      <!-- 成长洞察 -->
      <div class="block insight">
        <h3>成长洞察</h3>
        <p v-if="data.points.length < 2" class="insight-text">复盘次数不足 2 次，暂无法判断趋势。持续复盘积累数据后，这里会给出准确率变化方向。</p>
        <p v-else class="insight-text">
          首次复盘准确率 <b>{{ data.firstRate }}%</b> → 最新 <b>{{ data.latestRate }}%</b>，
          <span v-if="data.trend > 0" class="up">上升 {{ data.trend }} 个百分点，推演越来越贴合现实 ✅</span>
          <span v-else-if="data.trend < 0" class="down">下降 {{ Math.abs(data.trend) }} 个百分点，建议关注偏差来源 ⚠️</span>
          <span v-else>持平，推演稳定性良好。</span>
        </p>
        <p v-if="data.todoTotal" class="insight-sub">行动落地：{{ data.todoDone }}/{{ data.todoTotal }} 项待办已完成。</p>
        <p class="insight-sub">📊 可信度：<b>{{ credibilityLevel.level }}</b> — {{ credibilityLevel.note }}</p>
        <p v-if="decliningAlert" class="insight-alert">⚠️ {{ decliningAlert }}</p>
      </div>

      <!-- 复盘时间线 -->
      <div class="block">
        <h3>复盘时间线</h3>
        <div v-for="p in data.points.slice().reverse()" :key="p.id" class="timeline-item">
          <div class="tl-time">{{ fmt(p.createdAt) }}</div>
          <div class="tl-body">
            <div class="tl-rate" :style="{ color: rateColor(p.rate) }">{{ p.rate != null ? p.rate + '%' : '—' }}</div>
            <div class="tl-stat">准确 {{ p.accurate }} · 偏差 {{ p.deviated }}</div>
            <div v-if="p.reasons.length" class="tl-reasons">
              <span v-for="r in p.reasons" :key="r" class="tag">{{ r }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getProfile, getGrowthData, getPathTrajectory } from '../services/profile-service.js'

const route = useRoute()
const profile = ref(null)
const data = ref(null)
const trajectory = ref(null)

const PATH_COLORS = ['#2D7D46', '#B33A3A', '#4A6A8B', '#D48C2B', '#7A5C8F', '#2B7A78', '#C98A4B']

function fmt(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  const p = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

function fmtShort(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const p = n => String(n).padStart(2, '0')
  return `${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

function rateColor(rate) {
  if (rate == null) return '#C4C4C4'
  if (rate >= 70) return '#2D7D46'
  if (rate >= 40) return '#D48C2B'
  return '#B33A3A'
}

// ---------- 路径评分轨迹 SVG ----------
const PLOT_LEFT = 46, PLOT_RIGHT = 14, PLOT_TOP = 16, PLOT_BOTTOM = 36, PLOT_W = 540, PLOT_H = 210

const trajPaths = computed(() => {
  if (!trajectory.value || !trajectory.value.timePoints.length) return []
  const n = trajectory.value.timePoints.length
  return trajectory.value.paths.map((p, i) => {
    const color = PATH_COLORS[i % PATH_COLORS.length]
    const pts = p.points.map((pt, j) => {
      const x = PLOT_LEFT + (n <= 1 ? PLOT_W / 2 : (j / (n - 1)) * PLOT_W)
      const y = PLOT_TOP + (pt.score == null ? PLOT_H : ((10 - pt.score) / 10) * PLOT_H)
      return { x, y, score: pt.score, timestamp: pt.timestamp }
    })
    return { name: p.name, color, pts, pointsStr: pts.map(pt => `${pt.x},${pt.y}`).join(' ') }
  })
})

const trajDots = computed(() => trajPaths.value.flatMap(p => p.pts.map(pt => ({ ...pt, color: p.color, name: p.name }))))

const trajXLabels = computed(() => {
  if (!trajectory.value) return []
  const n = trajectory.value.timePoints.length
  return trajectory.value.timePoints.map((t, i) => ({
    x: PLOT_LEFT + (n <= 1 ? PLOT_W / 2 : (i / (n - 1)) * PLOT_W),
    label: fmtShort(t.timestamp),
  }))
})

const trajViewBox = computed(() => `0 0 ${PLOT_LEFT + PLOT_W + PLOT_RIGHT} ${PLOT_TOP + PLOT_H + PLOT_BOTTOM}`)

// ---------- 可信度升级 + 阈值触发 ----------
const credibilityLevel = computed(() => {
  const n = data.value?.totalReviews || 0
  const rate = data.value?.latestRate
  if (n >= 3 && rate != null && rate >= 70) return { level: '高', note: `经 ${n} 次复盘验证，准确率稳定在 ${rate}%` }
  if (n >= 2) return { level: '中', note: `经 ${n} 次复盘，持续校准中` }
  if (n >= 1) return { level: '中', note: '已进行 1 次复盘，可信度开始建立' }
  return { level: '初评', note: '尚未复盘，可信度为模型初评' }
})

const decliningAlert = computed(() => {
  const pts = (data.value?.points || []).filter(p => p.rate != null)
  if (pts.length < 2) return null
  const last = pts[pts.length - 1].rate
  const prev = pts[pts.length - 2].rate
  if (last < prev) return `最近准确率 ${prev}% → ${last}% 下降，建议回到报告页「再推演」重新校准。`
  return null
})

onMounted(async () => {
  profile.value = await getProfile(Number(route.params.id))
  if (!profile.value) return
  data.value = await getGrowthData(Number(route.params.id))
  trajectory.value = await getPathTrajectory(Number(route.params.id))
})
</script>

<style scoped>
.page { padding: var(--sp-lg); }
.breadcrumb { font-size: var(--fs-small); color: var(--color-neutral-500); margin-bottom: var(--sp-md); }
.breadcrumb a { color: var(--color-primary-600); }
.sep { margin: 0 var(--sp-xs); }
.page-title { font-size: var(--fs-h2); color: var(--color-primary-700); margin-bottom: var(--sp-xs); }
.sub { color: var(--color-neutral-500); margin-bottom: var(--sp-lg); }

.empty { text-align: center; padding: var(--sp-2xl); color: var(--color-neutral-500); }
.empty-icon { font-size: 40px; margin-bottom: var(--sp-md); }
.empty .hint { font-size: var(--fs-caption); }

.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: var(--sp-md); margin-bottom: var(--sp-md); }
.card { background: #fff; border-radius: var(--radius-lg); padding: var(--sp-md); box-shadow: var(--shadow-sm); text-align: center; }
.card-num { font-size: var(--fs-h2); font-weight: 700; color: var(--color-neutral-900); }
.card-num.ok { color: var(--color-success); }
.card-num.bad { color: var(--color-error); }
.card-label { font-size: var(--fs-caption); color: var(--color-neutral-500); margin-top: var(--sp-xs); }

.block { background: #fff; border-radius: var(--radius-lg); padding: var(--sp-lg); box-shadow: var(--shadow-sm); margin-bottom: var(--sp-md); }
.block h3 { font-size: var(--fs-h3); color: var(--color-neutral-900); margin-bottom: var(--sp-md); }

.legend { display: flex; gap: var(--sp-md); margin-bottom: var(--sp-sm); font-size: var(--fs-caption); color: var(--color-neutral-500); flex-wrap: wrap; }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: var(--sp-xs); vertical-align: middle; }

.trend { display: flex; align-items: flex-end; gap: var(--sp-md); overflow-x: auto; padding-bottom: var(--sp-xs); }
.trend-col { flex: 1; min-width: 40px; display: flex; flex-direction: column; align-items: center; gap: var(--sp-xs); }
.trend-track { height: 120px; width: 100%; display: flex; align-items: flex-end; justify-content: center; }
.trend-bar { width: 20px; border-radius: 3px 3px 0 0; min-height: 2px; transition: height .4s; }
.trend-label { font-size: var(--fs-caption); color: var(--color-neutral-500); white-space: nowrap; }

.insight { background: #FBF6EE; border-left: 4px solid var(--color-accent-gold); }
.insight-text { font-size: var(--fs-body); line-height: 1.7; color: var(--color-neutral-700); }
.insight-text .up { color: var(--color-success); font-weight: 600; }
.insight-text .down { color: var(--color-error); font-weight: 600; }
.insight-sub { margin-top: var(--sp-sm); font-size: var(--fs-small); color: var(--color-neutral-500); }
.insight-alert { margin-top: var(--sp-sm); font-size: var(--fs-small); color: var(--color-error); background: #F9E6E6; padding: var(--sp-sm) var(--sp-md); border-radius: var(--radius-md); }

.timeline-item { display: flex; gap: var(--sp-md); padding: var(--sp-sm) 0; border-bottom: 1px solid var(--color-neutral-100); }
.timeline-item:last-child { border-bottom: none; }
.tl-time { flex-shrink: 0; width: 84px; font-size: var(--fs-small); color: var(--color-neutral-500); }
.tl-body { flex: 1; }
.tl-rate { font-size: var(--fs-h3); font-weight: 700; margin-bottom: 2px; }
.tl-stat { font-size: var(--fs-small); color: var(--color-neutral-700); margin-bottom: 2px; }
.tl-reasons { display: flex; gap: var(--sp-xs); flex-wrap: wrap; }
.tag { font-size: var(--fs-caption); padding: 1px 8px; border-radius: 10px; background: #F9E6E6; color: var(--color-error); }

/* 路径评分轨迹 */
.traj-svg { width: 100%; height: auto; display: block; }
.traj-line { fill: none; stroke-width: 2; }
.grid { stroke: #EDEDED; stroke-width: 1; }
.axis-text { font-size: 11px; fill: var(--color-neutral-500); }
</style>
