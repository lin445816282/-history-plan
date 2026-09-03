<template>
  <div class="timeline">
    <div v-for="section in sections" :key="section.key" class="section">
      <h4 class="section-title" :class="section.cls">{{ section.label }}</h4>
      <div v-if="section.nodes.length === 0" class="empty-note">暂无记录</div>
      <div v-for="(node, i) in section.nodes" :key="i" class="node" @click="toggle(node)">
        <div class="dot" :class="section.cls"></div>
        <div class="node-body">
          <div class="node-title">{{ node.label }}</div>
          <div class="node-text" :class="{ clamp: !node.open }">{{ node.text }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'

const props = defineProps({ profile: { type: Object, required: true } })

// 三段时间轴：过往 / 当下 / 未来
const sections = computed(() => {
  const p = props.profile || {}
  const past = [
    { label: '过往关键抉择', text: p.keyDecisions },
    { label: '外部变局', text: p.externalChanges },
  ].filter(n => n.text && n.text.trim())
  const present = [
    { label: '当前困境', text: p.constraints },
    { label: '外部压力', text: p.externalPressure },
    { label: '不可改变限制', text: p.unchangeableLimits },
  ].filter(n => n.text && n.text.trim())
  const future = [
    { label: '短期目标（0-1年）', text: p.shortTermGoal },
    { label: '中期目标（1-3年）', text: p.mediumTermGoal },
    { label: '长期目标（3-10年）', text: p.longTermGoal },
  ].filter(n => n.text && n.text.trim())
  return [
    { key: 'past', label: '过往 · 经历', cls: 'past', nodes: past.map(n => reactive({ ...n, open: false })) },
    { key: 'present', label: '当下 · 处境', cls: 'present', nodes: present.map(n => reactive({ ...n, open: false })) },
    { key: 'future', label: '未来 · 目标', cls: 'future', nodes: future.map(n => reactive({ ...n, open: false })) },
  ]
})

function toggle(node) {
  node.open = !node.open
}
</script>

<style scoped>
.timeline { display: flex; flex-direction: column; gap: var(--sp-lg); }
.section { position: relative; padding-left: var(--sp-lg); }
.section::before {
  content: ''; position: absolute; left: 5px; top: 0; bottom: 0;
  width: 2px; background: var(--color-neutral-300);
}
.section-title { font-size: var(--fs-h3); color: var(--color-neutral-700); margin-bottom: var(--sp-md); }
.section-title.past { color: var(--color-neutral-500); }
.section-title.present { color: var(--color-primary-600); }
.section-title.future { color: var(--color-secondary-500); }
.empty-note { color: var(--color-neutral-500); font-size: var(--fs-small); }
.node { position: relative; display: flex; gap: var(--sp-md); margin-bottom: var(--sp-md); cursor: pointer; }
.dot { flex-shrink: 0; width: 12px; height: 12px; border-radius: 50%; margin-top: 6px; background: var(--color-neutral-300); }
.dot.past { background: var(--color-neutral-500); }
.dot.present { background: var(--color-primary-500); }
.dot.future { background: var(--color-secondary-500); }
.node-body { flex: 1; }
.node-title { font-size: var(--fs-small); font-weight: 600; color: var(--color-neutral-700); margin-bottom: 2px; }
.node-text { font-size: var(--fs-small); color: var(--color-neutral-900); line-height: 1.6; white-space: pre-wrap; }
.node-text.clamp { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>
