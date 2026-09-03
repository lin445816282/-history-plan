<template>
  <div class="page">
    <div class="tabs">
      <button :class="{ active: mode === 'quick' }" @click="setMode('quick')">⚡ 极速建档</button>
      <button :class="{ active: mode === 'simple' }" @click="setMode('simple')">💬 简易录入</button>
      <button :class="{ active: mode === 'form' }" @click="setMode('form')">📋 完整表单</button>
    </div>
    <QuickCreate v-if="mode === 'quick'" />
    <SimpleParse v-else-if="mode === 'simple'" />
    <ProfileForm v-else />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import QuickCreate from '../components/QuickCreate.vue'
import SimpleParse from '../components/SimpleParse.vue'
import ProfileForm from '../components/ProfileForm.vue'

const route = useRoute()
const mode = ref(['quick', 'simple', 'form'].includes(route.query.mode) ? route.query.mode : 'quick')

function setMode(m) {
  mode.value = m
}
</script>

<style scoped>
.page { padding: var(--sp-lg); }
.tabs { display: flex; gap: var(--sp-sm); margin-bottom: var(--sp-lg); }
.tabs button {
  flex: 1; padding: var(--sp-sm); border: 1px solid var(--color-neutral-300);
  background: #fff; border-radius: var(--radius-md); font-size: var(--fs-small);
}
.tabs button.active { background: var(--color-primary-500); color: #fff; border-color: var(--color-primary-500); }
</style>
