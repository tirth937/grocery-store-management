<script setup>
const config = useRuntimeConfig()
const transactions = ref([])
const isLoading = ref(false)

async function fetchTransactions() {
  isLoading.value = true
  try {
    const response = await fetch(`${config.public.apiBase}/transactions/list`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    })
    if (response.status === 401) return navigateTo('/login')
    const data = await response.json()
    transactions.value = data.transactions_log || []
  } catch (err) {
    console.error("Fetch Transactions Error:", err)
  } finally {
    isLoading.value = false
  }
}

const getTypeLabel = (type) => {
  switch(type) {
    case 'STOCK_IN': return 'Purchase'
    case 'STOCK_OUT_SALE': return 'Sale'
    case 'STOCK_OUT_WASTE': return 'Waste'
    default: return type
  }
}

const getTypeColor = (type) => {
  if (type === 'STOCK_OUT_SALE') return 'var(--success)'
  if (type === 'STOCK_IN') return 'var(--primary)'
  return 'var(--danger)'
}

const getTypeBg = (type) => {
  if (type === 'STOCK_OUT_SALE') return 'rgba(52, 211, 153, 0.1)'
  if (type === 'STOCK_IN') return 'rgba(255, 106, 61, 0.1)'
  return 'rgba(248, 113, 113, 0.1)'
}
const showDetailsModal = ref(false)
const detailsItem = ref(null)

const netValue = computed(() => {
  let net = 0
  transactions.value.forEach(tx => {
    if (tx.type === 'STOCK_OUT_SALE') net += tx.total_value
    else if (tx.type === 'STOCK_IN') net -= tx.total_value
  })
  return net
})

function openDetailsModal(tx) {
  detailsItem.value = tx
  showDetailsModal.value = true
}

function closeDetailsModal() {
  showDetailsModal.value = false
  detailsItem.value = null
}

onMounted(() => {
  fetchTransactions()
})
</script>

<template>
  <div class="stock-ledger-page">
    <div class="page-header">
      <div>
        <h1>Financial Ledger</h1>
        <p>Tracking inventory costs, revenue, and waste impacts.</p>
      </div>
      <div class="net-value-card" :class="netValue >= 0 ? 'positive' : 'negative'">
        <span class="net-label">Net Value</span>
        <span class="net-amount">{{ netValue >= 0 ? '+' : '-' }}₹{{ Math.abs(netValue).toFixed(2) }}</span>
      </div>
    </div>

    <div class="glass-card full-width">
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Date & Time</th>
              <th>Type</th>
              <th>Food Item</th>
              <th>Qty</th>
              <th>Total Value</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="tx in transactions" :key="tx._id">
              <td>
                <div class="date-cell">
                  <span>{{ new Date(tx.date).toLocaleDateString() }}</span>
                  <small>{{ new Date(tx.date).toLocaleTimeString() }}</small>
                </div>
              </td>
              <td>
                <span class="type-badge" :style="{ background: getTypeBg(tx.type), borderColor: getTypeColor(tx.type), color: getTypeColor(tx.type) }">
                  {{ getTypeLabel(tx.type) }}
                </span>
              </td>
              <td>
                <span class="food-cell">{{ tx.food_name }}</span>
              </td>
              <td>{{ tx.quantity }}</td>
              <td>
                <span class="value-cell" :style="{ color: getTypeColor(tx.type) }">
                  {{ tx.type.includes('SALE') ? '+' : '-' }}₹{{ tx.total_value.toFixed(2) }}
                </span>
              </td>
              <td>
                <button @click="openDetailsModal(tx)" class="btn-action details" title="View Details">📋 Details</button>
              </td>
            </tr>
            <tr v-if="transactions.length === 0 && !isLoading">
              <td colspan="6" class="empty-row">No transactions recorded yet.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ══ Details Modal ══ -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showDetailsModal" class="modal-overlay" @click.self="closeDetailsModal">
          <div class="modal-card">
            <div class="modal-header">
              <h2>📋 Transaction Details</h2>
              <button class="modal-x" @click="closeDetailsModal">✕</button>
            </div>
            <div v-if="detailsItem" class="modal-body">
              <div class="m-banner">
                <div class="m-banner-info">
                  <h3>{{ detailsItem.food_name }}</h3>
                  <span class="type-badge" :style="{ background: getTypeBg(detailsItem.type), borderColor: getTypeColor(detailsItem.type), color: getTypeColor(detailsItem.type) }">
                    {{ getTypeLabel(detailsItem.type) }}
                  </span>
                </div>
              </div>
              <div class="m-grid">
                <div class="m-cell"><span class="m-label">Quantity</span><span class="m-val">{{ detailsItem.quantity }}</span></div>
                <div class="m-cell"><span class="m-label">Unit Price</span><span class="m-val price-val">₹{{ detailsItem.unit_price.toFixed(2) }}</span></div>
                <div class="m-cell"><span class="m-label">Total Value</span><span class="m-val" :style="{ color: getTypeColor(detailsItem.type) }">₹{{ detailsItem.total_value.toFixed(2) }}</span></div>
                <div class="m-cell"><span class="m-label">Date</span><span class="m-val">{{ new Date(detailsItem.date).toLocaleDateString() }}</span></div>
              </div>
              <div v-if="detailsItem.buyer_name || detailsItem.buyer_phone" class="m-notes-list">
                <div v-if="detailsItem.buyer_name" class="m-note-item">
                  <div class="m-note-head">🏪 Buyer Name</div>
                  <p>{{ detailsItem.buyer_name }}</p>
                </div>
                <div v-if="detailsItem.buyer_phone" class="m-note-item">
                  <div class="m-note-head">📞 Buyer Phone</div>
                  <p><a :href="'tel:' + detailsItem.buyer_phone" class="phone-link">{{ detailsItem.buyer_phone }}</a></p>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-primary" @click="closeDetailsModal">Close</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.full-width {
  width: 100%;
}

.date-cell {
  display: flex;
  flex-direction: column;
  white-space: nowrap;
}

.date-cell small {
  color: var(--text-dim);
  font-size: 0.72rem;
}

.type-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  border: 1px solid;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.food-cell {
  text-transform: capitalize;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
  max-width: 180px;
}

.value-cell {
  font-weight: 700;
  white-space: nowrap;
}

.empty-row {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--text-dim);
}

/* ── Net Value Card ── */
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
  background: rgba(255, 255, 255, 0.03);
  padding: 0.75rem 1.25rem;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.net-value-card.positive {
  border-color: rgba(52, 211, 153, 0.3);
  background: rgba(52, 211, 153, 0.05);
}

.net-value-card.positive .net-amount { color: var(--success); }

.net-value-card.negative {
  border-color: rgba(248, 113, 113, 0.3);
  background: rgba(248, 113, 113, 0.05);
}

.net-value-card.negative .net-amount { color: var(--danger); }

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
}

/* ── Buttons ── */
.btn-action {
  padding: 0.4rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-dim);
  font-size: 0.78rem;
  font-family: inherit;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  transition: all 0.25s ease;
  white-space: nowrap;
}

.btn-action:hover {
  transform: translateY(-2px);
}

.btn-action.details {
  color: var(--primary);
  border-color: rgba(255, 106, 61, 0.2);
}

.btn-action.details:hover {
  background: rgba(255, 106, 61, 0.1);
  border-color: rgba(255, 106, 61, 0.4);
}

/* ══════════════════════════════════════════
   Modal Styles
   ══════════════════════════════════════════ */
.modal-overlay { position: fixed; inset: 0; z-index: 9999; background: rgba(0,0,0,0.75); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; padding: 1rem; }
.modal-card { background: #1a1a1a; border: 1px solid rgba(255,106,61,0.25); border-radius: 20px; width: 100%; max-width: 440px; overflow: hidden; box-shadow: 0 24px 64px rgba(0,0,0,0.6), 0 0 40px rgba(255,106,61,0.08); animation: modalPop 0.3s ease-out; }

@keyframes modalPop {
  from { opacity: 0; transform: scale(0.92) translateY(20px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}

.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 1.1rem 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.06); }
.modal-header h2 { font-size: 1.1rem; font-weight: 700; background: var(--primary-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

.modal-x { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); color: var(--text-dim); width: 30px; height: 30px; border-radius: 8px; cursor: pointer; font-size: 0.9rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: all 0.2s ease; }
.modal-x:hover { background: rgba(248,113,113,0.15); border-color: rgba(248,113,113,0.3); color: #f87171; }

.modal-body { padding: 1.25rem 1.5rem; display: flex; flex-direction: column; gap: 1rem; overflow: hidden; }
.modal-footer { display: flex; justify-content: flex-end; gap: 0.75rem; padding: 0.85rem 1.5rem; border-top: 1px solid rgba(255,255,255,0.06); }
.modal-footer .btn { padding: 0.55rem 1.3rem; font-size: 0.88rem; }

.modal-enter-active { transition: opacity 0.25s ease; }
.modal-leave-active { transition: opacity 0.2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }

.m-banner { display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 1rem; background: rgba(255,106,61,0.06); border-radius: 12px; border: 1px solid rgba(255,106,61,0.12); justify-content: space-between;}
.m-banner-info h3 { font-size: 1.1rem; font-weight: 700; text-transform: capitalize; margin-bottom: 0.2rem; }

.m-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; }
.m-cell { background: rgba(255,255,255,0.03); border-radius: 10px; padding: 0.6rem 0.75rem; display: flex; flex-direction: column; gap: 0.15rem; min-width: 0; }
.m-label { font-size: 0.65rem; font-weight: 600; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; }
.m-val { font-size: 0.95rem; font-weight: 700; word-break: break-word; }

.m-notes-list { display: flex; flex-direction: column; gap: 0.6rem; }
.m-note-item { background: rgba(255,255,255,0.03); border-radius: 10px; padding: 0.65rem 0.9rem; border-left: 3px solid var(--primary); }
.m-note-head { font-size: 0.7rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.2rem; }
.m-note-item p { font-size: 0.9rem; color: var(--text-main); word-break: break-word; line-height: 1.5; }

.price-val { color: var(--success); }
.phone-link { color: var(--primary); text-decoration: none; font-weight: 600; transition: opacity 0.2s; }
.phone-link:hover { opacity: 0.8; text-decoration: underline; }

/* ── Responsive ── */
@media (max-width: 520px) {
  .modal-card { max-width: 100%; border-radius: 16px; }
  .modal-body { padding: 1rem 1.25rem; }
  .modal-header { padding: 1rem 1.25rem; }
  .modal-footer { padding: 0.75rem 1.25rem; flex-direction: column; }
  .modal-footer .btn { width: 100%; justify-content: center; }
}
</style>
