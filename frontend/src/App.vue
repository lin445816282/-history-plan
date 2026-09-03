<template>
  <div class="app-shell">
    <header class="global-nav">
      <router-link to="/profiles" class="brand serif">历史推演规划系统</router-link>
      <span class="motto serif">谋事在人，顺时知变</span>
      <router-link to="/knowledge" class="nav-link">知识库</router-link>
      <router-link to="/deviation" class="nav-link">偏差总览</router-link>
      <router-link to="/settings" class="nav-link">设置</router-link>
    </header>
    <main class="content">
      <router-view />
    </main>
    <footer class="global-footer">
      © 历史推演规划系统 · 仅作事理参考，非算命占卜
    </footer>
  </div>
</template>

<style scoped>
.app-shell { min-height: 100vh; display: flex; flex-direction: column; }
.global-nav {
  height: 64px; padding: 0 var(--sp-lg);
  display: flex; align-items: center; gap: var(--sp-md);
  background: var(--color-primary-700); color: #fff;
  position: sticky; top: 0; z-index: 200;
}
.brand { font-size: var(--fs-h3); font-weight: 700; color: #fff; }
.motto { color: var(--color-primary-100); font-size: var(--fs-small); flex: 1; }
.nav-link { color: #fff; font-size: var(--fs-small); }
.content { flex: 1; max-width: 960px; width: 100%; margin: 0 auto; padding: var(--sp-lg); }
.global-footer { text-align: center; padding: var(--sp-lg); color: var(--color-neutral-500); font-size: var(--fs-caption); }

@media print {
  .global-nav, .global-footer { display: none !important; }
  .content { max-width: none; padding: 0; }
}

@media (max-width: 480px) {
  .global-nav { padding: 0 var(--sp-sm); gap: var(--sp-sm); }
  .brand { font-size: 13px; white-space: nowrap; }
  .motto { display: none; }
  .nav-link { font-size: 12px; padding: var(--sp-xs); white-space: nowrap; }
}
</style>
