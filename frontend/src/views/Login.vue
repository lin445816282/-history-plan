<template>
  <div class="page">
    <div class="login-card">
      <h1 class="serif page-title">账号登录</h1>
      <p class="sub">登录后推演额度与账号绑定，换设备不丢失。</p>

      <div class="tabs">
        <button :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
        <button :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
      </div>

      <div class="form">
        <input v-model="username" class="input" placeholder="用户名（2-32 字符）" autocomplete="username" />
        <input v-model="password" type="password" class="input" placeholder="密码（至少 4 位）" autocomplete="current-password" @keyup.enter="submit" />
        <button class="btn primary" :disabled="loading" @click="submit">
          {{ loading ? '处理中…' : (mode === 'login' ? '登录' : '注册并登录') }}
        </button>
        <p v-if="error" class="error">{{ error }}</p>
      </div>

      <p class="hint">未登录也可直接使用，免费额度 3 次（与当前设备绑定）。登录后额度跟账号走。</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login, register, setAuth } from '../api/index.js'

const router = useRouter()
const mode = ref('login')
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  if (!username.value.trim()) { error.value = '请输入用户名'; return }
  if (password.value.length < 4) { error.value = '密码至少 4 位'; return }
  loading.value = true
  try {
    const fn = mode.value === 'login' ? login : register
    const res = await fn(username.value.trim(), password.value)
    setAuth(res.token, res.username)
    router.push('/profiles')
  } catch (e) {
    error.value = e.message || '操作失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page { padding: var(--sp-lg); max-width: 440px; margin: 0 auto; }
.login-card { background: #fff; border-radius: var(--radius-lg); padding: var(--sp-xl); box-shadow: var(--shadow-md); }
.page-title { font-size: var(--fs-h2); color: var(--color-primary-700); margin-bottom: var(--sp-xs); }
.sub { color: var(--color-neutral-500); margin-bottom: var(--sp-lg); }

.tabs { display: flex; gap: var(--sp-sm); margin-bottom: var(--sp-md); }
.tabs button { flex: 1; padding: var(--sp-sm) var(--sp-md); border: 1px solid var(--color-neutral-300); border-radius: var(--radius-md); background: #fff; color: var(--color-neutral-700); font-size: var(--fs-body); }
.tabs button.active { background: var(--color-primary-500); color: #fff; border-color: var(--color-primary-500); }

.form { display: flex; flex-direction: column; gap: var(--sp-sm); }
.input { width: 100%; padding: var(--sp-sm) var(--sp-md); font-size: var(--fs-body); border: 1px solid var(--color-neutral-300); border-radius: var(--radius-md); }
.input:focus { outline: none; border-color: var(--color-primary-500); }
.btn { padding: var(--sp-sm) var(--sp-lg); border: none; border-radius: var(--radius-md); font-size: var(--fs-body); cursor: pointer; min-height: var(--touch-min); }
.btn.primary { background: var(--color-primary-500); color: #fff; }
.btn.primary:hover { background: var(--color-primary-600); }
.btn.primary:disabled { background: var(--color-neutral-300); cursor: not-allowed; }
.error { font-size: var(--fs-small); color: var(--color-error); }
.hint { margin-top: var(--sp-lg); font-size: var(--fs-caption); color: var(--color-neutral-500); line-height: 1.6; }
</style>
