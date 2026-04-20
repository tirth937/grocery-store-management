<script setup>
const config = useRuntimeConfig()
const stats = ref(null)
const isLoading = ref(true)

async function fetchDashboard() {
  isLoading.value = true
  try {
    const res = await fetch(`${config.public.apiBase}/dashboard/summary`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    })
    if (res.status === 401) return navigateTo('/login')
    stats.value = await res.json()
  } catch (err) {
    console.error('Dashboard fetch error:', err)
  } finally {
    isLoading.value = false
  }
}

function formatCurrency(val) {
  return '₹' + (val || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function txnIcon(type) {
  if (type === 'STOCK_IN') return '📥'
  if (type === 'STOCK_OUT_SALE') return '💰'
  if (type === 'STOCK_OUT_WASTE') return '🗑️'
  return '📋'
}

function txnLabel(type) {
  if (type === 'STOCK_IN') return 'Stock In'
  if (type === 'STOCK_OUT_SALE') return 'Sale'
  if (type === 'STOCK_OUT_WASTE') return 'Waste'
  return type
}

function txnColor(type) {
  if (type === 'STOCK_IN') return '#fbbf24'
  if (type === 'STOCK_OUT_SALE') return '#34d399'
  if (type === 'STOCK_OUT_WASTE') return '#f87171'
  return '#888'
}

function timeAgo(dateStr) {
  const now = new Date()
  const d = new Date(dateStr)
  const diff = Math.floor((now - d) / 1000)
  if (diff < 60) return 'Just now'
  if (diff < 3600) return Math.floor(diff / 60) + 'm ago'
  if (diff < 86400) return Math.floor(diff / 3600) + 'h ago'
  return Math.floor(diff / 86400) + 'd ago'
}

const healthTotal = computed(() => {
  if (!stats.value) return 1
  const h = stats.value.health
  return (h.fresh + h.warning + h.critical) || 1
})

function healthPercent(val) {
  return ((val / healthTotal.value) * 100).toFixed(0)
}

onMounted(() => { fetchDashboard() })
</script>

<template>
  <div class="dashboard-page">
    <div class="page-header">
      <div>
        <h1>Dashboard</h1>
        <p>Complete overview of your food inventory business.</p>
      </div>
      <button @click="fetchDashboard" class="btn btn-secondary" :disabled="isLoading">🔄 Refresh</button>
    </div>

    <!-- Loading state -->
    <div v-if="isLoading && !stats" class="loading-state glass-card">
      <div class="loader"></div>
      <p>Loading dashboard data...</p>
    </div>

    <template v-if="stats">
      <!-- KPI Cards Row -->
      <div class="kpi-grid">
        <div class="kpi-card glass-card kpi-blue">
          <div class="kpi-icon">📦</div>
          <div class="kpi-data">
            <span class="kpi-value">{{ stats.total_items }}</span>
            <span class="kpi-label">Total Stock Units</span>
          </div>
          <div class="kpi-sub">{{ stats.unique_products }} unique products</div>
        </div>

        <div class="kpi-card glass-card kpi-green">
          <div class="kpi-icon">💰</div>
          <div class="kpi-data">
            <span class="kpi-value">{{ formatCurrency(stats.total_revenue) }}</span>
            <span class="kpi-label">Total Revenue</span>
          </div>
          <div class="kpi-sub">{{ stats.sales_count }} sales completed</div>
        </div>

        <div class="kpi-card glass-card kpi-yellow">
          <div class="kpi-icon">🛒</div>
          <div class="kpi-data">
            <span class="kpi-value">{{ formatCurrency(stats.total_expenses) }}</span>
            <span class="kpi-label">Total Expenses</span>
          </div>
          <div class="kpi-sub">{{ stats.purchases_count }} purchases made</div>
        </div>

        <div class="kpi-card glass-card kpi-red">
          <div class="kpi-icon">🗑️</div>
          <div class="kpi-data">
            <span class="kpi-value">{{ formatCurrency(stats.total_waste_loss) }}</span>
            <span class="kpi-label">Waste Loss</span>
          </div>
          <div class="kpi-sub">{{ stats.total_wasted_items }} items wasted</div>
        </div>
      </div>

      <!-- Net Profit Banner -->
      <div class="profit-banner glass-card" :class="stats.net_profit >= 0 ? 'profit-positive' : 'profit-negative'">
        <div class="profit-left">
          <span class="profit-icon">{{ stats.net_profit >= 0 ? '📈' : '📉' }}</span>
          <div>
            <span class="profit-label">Net Profit / Loss</span>
            <span class="profit-formula">Revenue − Expenses − Waste</span>
          </div>
        </div>
        <span class="profit-value">{{ formatCurrency(stats.net_profit) }}</span>
      </div>

      <!-- Middle Row: Stock Value + Expiring + Health -->
      <div class="info-grid">
        <div class="info-card glass-card">
          <h3>📊 Stock Value</h3>
          <div class="info-big">{{ formatCurrency(stats.stock_value) }}</div>
          <p class="info-dim">Current inventory valuation</p>
        </div>

        <div class="info-card glass-card">
          <h3>⏰ Expiring Soon</h3>
          <div class="info-big" :class="stats.expiring_soon > 0 ? 'text-warn' : 'text-safe'">{{ stats.expiring_soon }}</div>
          <p class="info-dim">Items expiring within 48 hours</p>
        </div>

        <div class="info-card glass-card">
          <h3>🩺 Inventory Health</h3>
          <div class="health-bar-container">
            <div class="health-bar">
              <div class="health-segment fresh" :style="{ width: healthPercent(stats.health.fresh) + '%' }"></div>
              <div class="health-segment warn" :style="{ width: healthPercent(stats.health.warning) + '%' }"></div>
              <div class="health-segment crit" :style="{ width: healthPercent(stats.health.critical) + '%' }"></div>
            </div>
            <div class="health-legend">
              <span><i class="dot dot-fresh"></i> Fresh {{ healthPercent(stats.health.fresh) }}%</span>
              <span><i class="dot dot-warn"></i> Warning {{ healthPercent(stats.health.warning) }}%</span>
              <span><i class="dot dot-crit"></i> Critical {{ healthPercent(stats.health.critical) }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom Row: Top Sellers + Top Stock + Recent Transactions -->
      <div class="bottom-grid">
        <!-- Top Sellers -->
        <div class="list-card glass-card">
          <h3>🏆 Top Sellers</h3>
          <div v-if="stats.top_sellers.length === 0" class="empty-mini">No sales recorded yet.</div>
          <ul v-else>
            <li v-for="(s, idx) in stats.top_sellers" :key="s.name">
              <span class="rank">#{{ idx + 1 }}</span>
              <span class="item-name">{{ s.name }}</span>
              <span class="item-qty">{{ s.quantity }} sold</span>
            </li>
          </ul>
        </div>

        <!-- Top Stocked -->
        <div class="list-card glass-card">
          <h3>📦 Top Stocked</h3>
          <div v-if="stats.top_stocked.length === 0" class="empty-mini">No inventory yet.</div>
          <ul v-else>
            <li v-for="(s, idx) in stats.top_stocked" :key="s.name">
              <span class="rank">#{{ idx + 1 }}</span>
              <span class="item-name">{{ s.name }}</span>
              <span class="item-qty">{{ s.quantity }} units</span>
            </li>
          </ul>
        </div>

        <!-- Recent Transactions -->
        <div class="list-card glass-card txn-card">
          <h3>🕐 Recent Transactions</h3>
          <div v-if="stats.recent_transactions.length === 0" class="empty-mini">No transactions yet.</div>
          <ul v-else class="txn-list">
            <li v-for="t in stats.recent_transactions" :key="t._id">
              <span class="txn-icon">{{ txnIcon(t.type) }}</span>
              <div class="txn-info">
                <strong>{{ t.food_name }}</strong>
                <span class="txn-meta">{{ txnLabel(t.type) }} · {{ t.quantity }} units · {{ timeAgo(t.date) }}</span>
              </div>
              <span class="txn-amount" :style="{ color: txnColor(t.type) }">
                {{ t.type === 'STOCK_IN' ? '-' : '+' }}{{ formatCurrency(t.total_value) }}
              </span>
            </li>
          </ul>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
/* ── KPI Grid ── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.25rem;
  margin-bottom: 1.25rem;
}
.kpi-card {
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  position: relative;
  overflow: hidden;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.kpi-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.35);
}
.kpi-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 3px;
  border-radius: 4px 4px 0 0;
}
.kpi-blue::before  { background: linear-gradient(90deg, #60a5fa, #3b82f6); }
.kpi-green::before { background: linear-gradient(90deg, #34d399, #10b981); }
.kpi-yellow::before{ background: linear-gradient(90deg, #fbbf24, #f59e0b); }
.kpi-red::before   { background: linear-gradient(90deg, #f87171, #ef4444); }

.kpi-icon { font-size: 1.8rem; }
.kpi-data { display: flex; flex-direction: column; }
.kpi-value { font-size: 1.55rem; font-weight: 800; color: #fff; line-height: 1.1; }
.kpi-label { font-size: 0.78rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.15rem; }
.kpi-sub { font-size: 0.72rem; color: var(--text-dim); opacity: 0.7; }

/* ── Profit Banner ── */
.profit-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.15rem 1.5rem;
  margin-bottom: 1.25rem;
  border-left: 4px solid;
  transition: transform 0.25s ease;
}
.profit-banner:hover { transform: translateY(-2px); }
.profit-positive { border-left-color: var(--success); }
.profit-negative { border-left-color: var(--danger); }

.profit-left { display: flex; align-items: center; gap: 0.75rem; }
.profit-icon { font-size: 2rem; }
.profit-label { font-size: 1rem; font-weight: 700; color: #fff; display: block; }
.profit-formula { font-size: 0.72rem; color: var(--text-dim); }
.profit-value { font-size: 1.6rem; font-weight: 800; }
.profit-positive .profit-value { color: var(--success); }
.profit-negative .profit-value { color: var(--danger); }

/* ── Info Grid ── */
.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 2fr;
  gap: 1.25rem;
  margin-bottom: 1.25rem;
}
.info-card {
  padding: 1.25rem 1.5rem;
  transition: transform 0.25s ease;
}
.info-card:hover { transform: translateY(-3px); }
.info-card h3 { font-size: 0.85rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.6rem; }
.info-big { font-size: 2rem; font-weight: 800; color: #fff; }
.info-dim { font-size: 0.75rem; color: var(--text-dim); margin-top: 0.25rem; }
.text-warn { color: var(--warning); }
.text-safe { color: var(--success); }

/* Health bar */
.health-bar-container { margin-top: 0.6rem; }
.health-bar {
  display: flex;
  height: 14px;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(255,255,255,0.05);
}
.health-segment { transition: width 0.6s ease; min-width: 0; }
.health-segment.fresh { background: var(--success); }
.health-segment.warn  { background: var(--warning); }
.health-segment.crit  { background: var(--danger); }

.health-legend {
  display: flex;
  gap: 1rem;
  margin-top: 0.6rem;
  font-size: 0.72rem;
  color: var(--text-dim);
  flex-wrap: wrap;
}
.health-legend span { display: flex; align-items: center; gap: 0.3rem; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot-fresh { background: var(--success); }
.dot-warn  { background: var(--warning); }
.dot-crit  { background: var(--danger); }

/* ── Bottom Grid ── */
.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 2fr;
  gap: 1.25rem;
}

.list-card {
  padding: 1.25rem 1.5rem;
  transition: transform 0.25s ease;
}
.list-card:hover { transform: translateY(-3px); }
.list-card h3 {
  font-size: 0.85rem;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.8rem;
  padding-bottom: 0.6rem;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.list-card ul { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.55rem; }
.list-card li {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.5rem 0.6rem;
  border-radius: 10px;
  background: rgba(255,255,255,0.02);
  transition: background 0.2s ease;
}
.list-card li:hover { background: rgba(255,106,61,0.06); }

.rank {
  font-size: 0.7rem;
  font-weight: 800;
  color: var(--primary);
  background: rgba(255,106,61,0.12);
  padding: 2px 7px;
  border-radius: 6px;
  min-width: 26px;
  text-align: center;
}
.item-name { flex: 1; font-weight: 600; color: #fff; text-transform: capitalize; font-size: 0.88rem; }
.item-qty { font-size: 0.75rem; color: var(--text-dim); white-space: nowrap; }

/* ── Transaction List ── */
.txn-card { overflow: hidden; }
.txn-list { max-height: 280px; overflow-y: auto; padding-right: 0.3rem; }
.txn-list li {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.55rem 0.6rem;
  border-radius: 10px;
  background: rgba(255,255,255,0.02);
  transition: background 0.2s;
}
.txn-list li:hover { background: rgba(255,106,61,0.06); }
.txn-icon { font-size: 1.25rem; flex-shrink: 0; }
.txn-info { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.txn-info strong { font-size: 0.88rem; color: #fff; text-transform: capitalize; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.txn-meta { font-size: 0.7rem; color: var(--text-dim); }
.txn-amount { font-weight: 700; font-size: 0.85rem; white-space: nowrap; flex-shrink: 0; }

.empty-mini { color: var(--text-dim); font-size: 0.82rem; text-align: center; padding: 1.5rem 0; opacity: 0.6; }

/* ── Loading ── */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  gap: 1rem;
  color: var(--text-dim);
}
.loader {
  width: 36px; height: 36px;
  border: 3px solid rgba(255,255,255,0.1);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Responsive ── */
@media (max-width: 1100px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .info-grid { grid-template-columns: 1fr 1fr; }
  .info-grid > :last-child { grid-column: 1 / -1; }
  .bottom-grid { grid-template-columns: 1fr 1fr; }
  .bottom-grid > :last-child { grid-column: 1 / -1; }
}

@media (max-width: 640px) {
  .kpi-grid { grid-template-columns: 1fr; }
  .info-grid { grid-template-columns: 1fr; }
  .info-grid > :last-child { grid-column: auto; }
  .bottom-grid { grid-template-columns: 1fr; }
  .bottom-grid > :last-child { grid-column: auto; }
  .profit-banner { flex-direction: column; gap: 0.75rem; align-items: flex-start; }
  .profit-value { font-size: 1.3rem; }
  .kpi-value { font-size: 1.25rem; }
}
</style>
