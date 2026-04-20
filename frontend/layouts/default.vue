<script setup>
const user = ref(null)

onMounted(() => {
  const info = localStorage.getItem('user_info')
  if (info) {
    user.value = JSON.parse(info)
  }
})

function logout() {
  localStorage.removeItem('auth_token')
  localStorage.removeItem('user_info')
  navigateTo('/login')
}
</script>

<template>
  <div class="app-container">
    <aside class="sidebar">
      <div class="logo">
        <div class="ai-badge">AI</div>
        <div class="logo-text">
          <span class="main">Grocery</span>
          <span class="sub">Management</span>
        </div>
      </div>

      <div class="user-profile" v-if="user">
        <div class="user-avatar">
          {{ user.full_name.charAt(0).toUpperCase() }}
        </div>
        <div class="user-details">
          <span class="user-name">{{ user.full_name }}</span>
          <span class="user-role">Store Owner</span>
        </div>
      </div>
      
      <nav class="nav-links">
        <NuxtLink to="/" class="nav-link">
          <span class="icon">📊</span>
          <span class="label">Dashboard</span>
        </NuxtLink>
        <NuxtLink to="/analyzer" class="nav-link">
          <span class="icon">📷</span>
          <span class="label">Analyser</span>
        </NuxtLink>
        <NuxtLink to="/inventory" class="nav-link">
          <span class="icon">📦</span>
          <span class="label">Inventory</span>
        </NuxtLink>
        <NuxtLink to="/grocery" class="nav-link">
          <span class="icon">🛒</span>
          <span class="label">Grocery List</span>
        </NuxtLink>
        <NuxtLink to="/waste" class="nav-link">
          <span class="icon">🗑️</span>
          <span class="label">Waste Logs</span>
        </NuxtLink>
        <NuxtLink to="/stock-io" class="nav-link">
          <span class="icon">📦</span>
          <span class="label">Stock In/Out</span>
        </NuxtLink>
        <NuxtLink to="/stock" class="nav-link">
          <span class="icon">📈</span>
          <span class="label">Stock Ledger</span>
        </NuxtLink>
      </nav>

      <div class="sidebar-footer">
        <div class="legend">
          <div class="legend-item"><span class="dot fresh"></span> Fresh</div>
          <div class="legend-item"><span class="dot warning"></span> Soon</div>
          <div class="legend-item"><span class="dot danger"></span> Spoiled</div>
        </div>
        <button @click="logout" class="nav-link logout-btn">
          <span class="icon">🚪</span>
          <span class="label">Logout</span>
        </button>
      </div>
    </aside>

    <main class="main-content">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.user-profile {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 0.5rem;
  margin-bottom: 1rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.user-avatar {
  width: 36px;
  height: 36px;
  background: var(--primary-gradient);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  color: white;
  flex-shrink: 0;
}

.user-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.user-name {
  font-size: 0.9rem;
  font-weight: 700;
  color: white;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 0.7rem;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.logout-btn {
  background: none;
  border: none;
  width: 100%;
  text-align: left;
  cursor: pointer;
  margin-top: 1.5rem;
  color: #f87171 !important;
}

.logout-btn:hover {
  background: rgba(248, 113, 113, 0.1) !important;
}

.ai-badge {
  background: var(--primary-gradient);
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.65rem;
  font-weight: 800;
  color: white;
  letter-spacing: 1px;
  flex-shrink: 0;
}

.sidebar-footer {
  margin-top: auto;
  padding-top: 1.5rem;
  border-top: 1px solid var(--glass-border);
}

.legend {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: 0.8rem;
  color: var(--text-dim);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot.fresh   { background: var(--success); }
.dot.warning { background: var(--warning); }
.dot.danger  { background: var(--danger); }

/* On tablet, hide label text in sidebar */
@media (max-width: 1024px) {
  .label { display: none; }
  .logo h2 { display: none; }
  .logo { margin-bottom: 1.5rem; justify-content: center; }
  .user-details { display: none; }
  .user-profile { justify-content: center; padding: 0.75rem 0; }
}

/* On mobile, show labels again since sidebar is horizontal */
@media (max-width: 768px) {
  .label { display: inline; }
  .logo h2 { display: block; }
  .logo { margin-bottom: 0; }
  .user-details { display: flex; }
  .user-profile { padding: 1rem 0.5rem; justify-content: flex-start; }
}
</style>
