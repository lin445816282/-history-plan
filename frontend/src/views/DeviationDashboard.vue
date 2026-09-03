<template>
  <div class="page">
    <div class="breadcrumb">
      <router-link to="/profiles">档案列表</router-link>
      <span class="sep">/</span>
      <span>偏差总览</span>
    </div>

    <h1 class="serif page-title">偏差总览</h1>
    <p class="sub">聚合全部复盘的推演准确度，看清预测偏差的规律与来源。</p>

    <!-- 空态 -->
    <div v-if="!summary.totalReviews" class="empty">
      <div class="empty-icon">📊</div>
      <p>暂无复盘数据。</p>
      <p class="hint">完成推演后，在报告页点击「复盘」记录现实结果，即可在此查看偏差统计。</p>
    </div>

    <template v-else>
      <!-- 总览卡片 -->
      <div class="cards">
        <div class="card">
          <div class="card-num">{{ summary.totalReviews }}</div>
          <div class="card-label">复盘总数</div>
        </div>
        <div class="card">
          <div class="card-num ok">{{ summary.totalAccurate }}</div>
          <div class="card-label">预测准确项</div>
        </div>
        <div class="card">
          <div class="card-num bad">{{ summary.totalDeviated }}</div>
          <div class="card-label">预测偏差项</div>
        </div>
        <div class="card">
          <div class="card-num">{{ summary.accuracyRate }}%</div>
          <div class="card-label">整体准确率</div>
        </div>
      </div>

      <!-- 偏差原因分布 -->
      <div class="block">
        <h3>偏差原因分布</h3>
        <div v-for="(count, reason) in summary.reasonDist" :key="reason" class="bar-row">
          <span class="bar-label">{{ reason }}</span>
          <div class="bar-track">
            <div class="bar-fill" :style="{ width: barWidth(count) }"></div>
          </div>
          <span class="bar-count">{{ count }}</span>
        </div>
      </div>

      <!-- 时间趋势 -->
      <div class="block">
        <h3>偏差趋势（按月）</h3>
        <div class="legend">
          <span class="lg"><i class="dot ok-dot"></i>准确</span>
          <span class="lg"><i class="dot bad-dot"></i>偏差</span>
        </div>
        <div class="trend">
          <div v-for="m in summary.byMonth" :key="m.month" class="trend-col">
            <div class="trend-bars">
              <div class="trend-bar bad" :style="{ height: barHeight(m.deviated) }" :title="`${m.month} 偏差 ${m.deviated} / 准确 ${m.accurate}`"></div>
              <div class="trend-bar ok" :style="{ height: barHeight(m.accurate) }" :title="`${m.month} 准确 ${m.accurate}`"></div>
            </div>
            <span class="trend-month">{{ m.month.slice(5) }}月</span>
          </div>
        </div>
      </div>

      <!-- 档案偏差排行 -->
      <div class="block">
        <h3>档案偏差排行</h3>
        <div v-for="p in summary.byProfile" :key="p.profileId" class="profile-row">
          <router-link :to="`/profiles/${p.profileId}`" class="p-name">{{ p.name }}</router-link>
          <span class="p-stat">复盘 {{ p.reviews }} · 准确 {{ p.accurate }} · 偏差 {{ p.deviated }}</span>
          <span class="p-rate" :class="rateClass(p.rate)">{{ p.rate }}%</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDeviationSummary } from '../services/profile-service.js'

const summary = ref({
  totalReviews: 0, totalAccurate: 0, totalDeviated: 0, accuracyRate: 0,
  reasonDist: {}, byProfile: [], byMonth: [],
})

function barWidth(count) {
  const max = Math.max(1, ...Object.values(summary.value.reasonDist))
  return Math.round(count / max * 100) + '%'
}

function barHeight(count) {
  const max = Math.max(1, ...summary.value.byMonth.flatMap(m => [m.accurate, m.deviated]))
  return Math.round(count / max * 100) + '%'
}

function rateClass(rate) {
  if (rate >= 70) return 'good'
  if (rate >= 40) return 'warn'
  return 'bad'
}

onMounted(async () => {
  summary.value = await getDeviationSummary()
})
</script>

<style scoped>
.page { padding: var(--sp-lg); }
.breadcrumb { font-size: var(--fs-small); color: var(--color-neutral-500); margin-bottom: var(--sp-md); }
.breadcrumb a { color: var(--color-primary-600); }
.sep { margin: 0 var(--sp-xs); }
.page-title { font-size: var(--fs-h2); color: var(--color-primary-700); margin-bottom: var(--sp-xs); }
.sub { color: var(--color-neutral-500); margin-bottom: var(--sp-lg); }

.empty { text-align: center; padding: var(--sp-2xl) var(--sp-lg); color: var(--color-neutral-500); }
.empty-icon { font-size: 40px; margin-bottom: var(--sp-md); }
.empty .hint { font-size: var(--fs-caption); }

/* 总览卡片 */
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: var(--sp-md); margin-bottom: var(--sp-md); }
.card { background: #fff; border-radius: var(--radius-lg); padding: var(--sp-lg); box-shadow: var(--shadow-sm); text-align: center; }
.card-num { font-size: var(--fs-h1); font-weight: 700; color: var(--color-neutral-900); }
.card-num.ok { color: var(--color-success); }
.card-num.bad { color: var(--color-error); }
.card-label { font-size: var(--fs-small); color: var(--color-neutral-500); margin-top: var(--sp-xs); }

/* 通用块 */
.block { background: #fff; border-radius: var(--radius-lg); padding: var(--sp-lg); box-shadow: var(--shadow-sm); margin-bottom: var(--sp-md); }
.block h3 { font-size: var(--fs-h3); color: var(--color-neutral-900); margin-bottom: var(--sp-md); }

/* 偏差原因分布 */
.bar-row { display: flex; align-items: center; gap: var(--sp-sm); margin-bottom: var(--sp-sm); }
.bar-label { width: 96px; font-size: var(--fs-small); color: var(--color-neutral-700); flex-shrink: 0; }
.bar-track { flex: 1; height: 14px; background: var(--color-neutral-100); border-radius: 7px; overflow: hidden; }
.bar-fill { height: 100%; background: var(--color-warning); border-radius: 7px; transition: width .4s; }
.bar-count { width: 24px; text-align: right; font-size: var(--fs-small); color: var(--color-neutral-700); }

/* 时间趋势 */
.legend { display: flex; gap: var(--sp-md); margin-bottom: var(--sp-sm); font-size: var(--fs-caption); color: var(--color-neutral-500); }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: var(--sp-xs); vertical-align: middle; }
.ok-dot { background: var(--color-success); }
.bad-dot { background: var(--color-error); }
.trend { display: flex; align-items: flex-end; gap: var(--sp-md); overflow-x: auto; padding-bottom: var(--sp-xs); }
.trend-col { flex: 1; min-width: 36px; display: flex; flex-direction: column; align-items: center; gap: var(--sp-xs); }
.trend-bars { height: 120px; width: 100%; display: flex; align-items: flex-end; justify-content: center; gap: 4px; }
.trend-bar { width: 14px; border-radius: 3px 3px 0 0; min-height: 2px; }
.trend-bar.ok { background: var(--color-success); }
.trend-bar.bad { background: var(--color-error); }
.trend-month { font-size: var(--fs-caption); color: var(--color-neutral-500); }

/* 档案排行 */
.profile-row { display: flex; align-items: center; gap: var(--sp-sm); padding: var(--sp-sm) 0; border-bottom: 1px solid var(--color-neutral-100); }
.profile-row:last-child { border-bottom: none; }
.p-name { flex: 1; font-size: var(--fs-body); color: var(--color-neutral-900); }
.p-name:hover { color: var(--color-primary-600); }
.p-stat { font-size: var(--fs-caption); color: var(--color-neutral-500); }
.p-rate { font-size: var(--fs-small); font-weight: 700; padding: 2px 10px; border-radius: var(--radius-sm); }
.p-rate.good { color: var(--color-success); background: #E8F4EC; }
.p-rate.warn { color: var(--color-warning); background: #FBF0E0; }
.p-rate.bad { color: var(--color-error); background: #F9E6E6; }
</style>
