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
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getProfile, getGrowthData } from '../services/profile-service.js'

const route = useRoute()
const profile = ref(null)
const data = ref(null)

function fmt(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  const p = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

function rateColor(rate) {
  if (rate == null) return '#C4C4C4'
  if (rate >= 70) return '#2D7D46'
  if (rate >= 40) return '#D48C2B'
  return '#B33A3A'
}

onMounted(async () => {
  profile.value = await getProfile(Number(route.params.id))
  if (!profile.value) return
  data.value = await getGrowthData(Number(route.params.id))
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

.timeline-item { display: flex; gap: var(--sp-md); padding: var(--sp-sm) 0; border-bottom: 1px solid var(--color-neutral-100); }
.timeline-item:last-child { border-bottom: none; }
.tl-time { flex-shrink: 0; width: 84px; font-size: var(--fs-small); color: var(--color-neutral-500); }
.tl-body { flex: 1; }
.tl-rate { font-size: var(--fs-h3); font-weight: 700; margin-bottom: 2px; }
.tl-stat { font-size: var(--fs-small); color: var(--color-neutral-700); margin-bottom: 2px; }
.tl-reasons { display: flex; gap: var(--sp-xs); flex-wrap: wrap; }
.tag { font-size: var(--fs-caption); padding: 1px 8px; border-radius: 10px; background: #F9E6E6; color: var(--color-error); }
</style>
