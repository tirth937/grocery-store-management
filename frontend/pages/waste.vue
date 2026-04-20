<script setup>
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

const config = useRuntimeConfig()
const wasteLogs = ref([])
const chartCanvas = ref(null)
let chartInstance = null

const totalValueLost = computed(() => {
  return wasteLogs.value.reduce((sum, log) => sum + (log.total_value || 0), 0)
})

async function fetchWaste() {
  try {
    const response = await fetch(`${config.public.apiBase}/waste/list`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    })
    if (response.status === 401) return navigateTo('/login')
    const data = await response.json()
    wasteLogs.value = data.waste_logs || []
    updateChart()
  } catch (err) {
    console.error("Fetch Waste Error:", err)
  }
}

function updateChart() {
  if (!chartCanvas.value || wasteLogs.value.length === 0) return
  
  if (chartInstance) chartInstance.destroy()
  
  const ctx = chartCanvas.value.getContext('2d')
  
  // Aggregate data for chart (e.g., by food name)
  const aggregation = {}
  wasteLogs.value.forEach(log => {
    aggregation[log.food_name] = (aggregation[log.food_name] || 0) + (log.total_value || 0)
  })
  
  const labels = Object.keys(aggregation)
  const data = Object.values(aggregation)
  
  chartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: [
          '#ff6a3d', '#ff2d2d', '#ff9a44', '#f87171', '#fbbf24', '#34d399', '#8a8f98'
        ],
        borderWidth: 0,
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#8a8f98',
            font: { family: 'Outfit', size: 12 },
            padding: 16,
            boxWidth: 12,
            boxHeight: 12,
            usePointStyle: true,
            pointStyle: 'circle'
          }
        }
      }
    }
  })
}

onMounted(() => {
  fetchWaste()
})
</script>

<template>
  <div class="waste-page">
    <div class="page-header">
      <div>
        <h1>Waste Analytics</h1>
        <p>Tracking food waste and financial losses over time.</p>
      </div>
      <div class="net-value-card negative">
        <span class="net-label">Total Cash Lost</span>
        <span class="net-amount">-₹{{ totalValueLost.toFixed(2) }}</span>
      </div>
    </div>

    <div class="waste-grid">
      <div class="chart-section glass-card">
        <h3>Waste Value Distribution</h3>
        <div class="chart-container">
          <canvas ref="chartCanvas"></canvas>
        </div>
      </div>

      <div class="logs-section glass-card">
        <h3>Recent Discards</h3>
        <div class="logs-list">
          <div v-for="log in wasteLogs" :key="log._id" class="log-item">
            <div class="log-main">
              <h4><span class="qty-badge">{{ log.quantity || 1 }}x</span> {{ log.food_name }}</h4>
              <p class="reason">{{ log.reason }}</p>
            </div>
            <div class="log-meta">
              <span class="value">-₹{{ (log.total_value || 0).toFixed(2) }}</span>
              <span class="date">{{ new Date(log.logged_date).toLocaleDateString() }}</span>
            </div>
          </div>
          <div v-if="wasteLogs.length === 0" class="empty-state">
            <div class="empty-icon">🎉</div>
            <p>No waste logs recorded yet. Great job!</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── Page Header ── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 1rem;
}

.net-value-card {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  background: rgba(248, 113, 113, 0.05);
  padding: 0.75rem 1.25rem;
  border-radius: 12px;
  border: 1px solid rgba(248, 113, 113, 0.3);
}

.net-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-dim);
  letter-spacing: 0.5px;
}

.net-amount {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--danger);
}

.waste-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.chart-container {
  height: 280px;
  position: relative;
  margin-top: 1.5rem;
}

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-top: 1.25rem;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 0.25rem;
}

.log-item {
  background: rgba(255, 255, 255, 0.03);
  padding: 0.85rem 1rem;
  border-radius: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  border: 1px solid transparent;
  transition: all 0.25s ease;
}

.log-item:hover {
  border-color: rgba(255, 106, 61, 0.2);
  background: rgba(255, 106, 61, 0.05);
  transform: translateX(4px);
}

.log-main {
  min-width: 0;
  flex: 1;
}

.log-main h4 {
  text-transform: capitalize;
  margin-bottom: 0.15rem;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.qty-badge {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 700;
}

.reason {
  font-size: 0.78rem;
  color: var(--text-dim);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.log-meta {
  text-align: right;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.value {
  color: var(--danger);
  font-weight: 700;
  font-size: 0.9rem;
}

.date {
  font-size: 0.72rem;
  color: var(--text-dim);
}

.empty-state {
  text-align: center;
  padding: 2rem 1rem;
  color: var(--text-dim);
}

.empty-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
  opacity: 0.5;
}

/* Responsive */
@media (max-width: 900px) {
  .waste-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .chart-container {
    height: 220px;
  }
}
</style>
