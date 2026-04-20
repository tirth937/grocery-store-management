<script setup>
const config = useRuntimeConfig()
const inventory = ref([])
const isLoading = ref(false)

// Details modal
const showDetailsModal = ref(false)
const detailsItem = ref(null)

// Sell modal
const showSellModal = ref(false)
const sellModalItem = ref(null)
const sellForm = reactive({ quantity: 1, price: 0, buyerName: '', buyerPhone: '' })
const sellSubmitting = ref(false)

// Discard modal
const showDiscardModal = ref(false)
const discardItem = ref(null)
const discardForm = reactive({ quantity: 1, reason: '' })
const discardSubmitting = ref(false)

async function fetchInventory() {
  isLoading.value = true
  try {
    const response = await fetch(`${config.public.apiBase}/inventory/list`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    })
    if (response.status === 401) return navigateTo('/login')
    const data = await response.json()
    inventory.value = data.inventory || []
  } catch (err) {
    console.error("Fetch Inventory Error:", err)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchInventory()
})

const getStatusColor = (status) => {
  if (status.toLowerCase().includes('safe')) return 'var(--success)'
  if (status.toLowerCase().includes('soon')) return 'var(--warning)'
  return 'var(--danger)'
}

const getStatusBg = (status) => {
  if (status.toLowerCase().includes('safe')) return 'rgba(52, 211, 153, 0.1)'
  if (status.toLowerCase().includes('soon')) return 'rgba(251, 191, 36, 0.1)'
  return 'rgba(248, 113, 113, 0.1)'
}

function parseNotes(notes) {
  if (!notes) return { note: '', seller: '', phone: '' }
  const parts = notes.split(' | ')
  let note = '', seller = '', phone = ''
  parts.forEach(p => {
    if (p.startsWith('Seller: ')) seller = p.replace('Seller: ', '')
    else if (p.startsWith('Phone: ')) phone = p.replace('Phone: ', '')
    else note = p
  })
  return { note, seller, phone }
}

// ── Details ──
function openDetailsModal(item) {
  detailsItem.value = item
  showDetailsModal.value = true
}
function closeDetailsModal() {
  showDetailsModal.value = false
  detailsItem.value = null
}

// ── Sell ──
function openSellModal(item) {
  sellModalItem.value = item
  sellForm.quantity = 1
  sellForm.price = item.price_per_unit || 0
  sellForm.buyerName = ''
  sellForm.buyerPhone = ''
  showSellModal.value = true
}
function closeSellModal() {
  showSellModal.value = false
  sellModalItem.value = null
}
async function confirmSell() {
  if (!sellModalItem.value || sellSubmitting.value) return
  sellSubmitting.value = true
  try {
    const res = await fetch(`${config.public.apiBase}/inventory/sell`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify({
        item_id: sellModalItem.value._id,
        quantity: sellForm.quantity,
        sell_price: sellForm.price,
        buyer_name: sellForm.buyerName,
        buyer_phone: sellForm.buyerPhone
      })
    })
    if (res.status === 401) return navigateTo('/login')
    closeSellModal()
    fetchInventory()
  } catch (err) {
    console.error("Sell Error:", err)
  } finally {
    sellSubmitting.value = false
  }
}

// ── Discard ──
function openDiscardModal(item) {
  discardItem.value = item
  discardForm.quantity = 1
  discardForm.reason = ''
  showDiscardModal.value = true
}
function closeDiscardModal() {
  showDiscardModal.value = false
  discardItem.value = null
}
async function confirmDiscard() {
  if (!discardItem.value || discardSubmitting.value) return
  discardSubmitting.value = true
  try {
    const res = await fetch(`${config.public.apiBase}/waste/add`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify({
        item_id: discardItem.value._id,
        food_name: discardItem.value.food_name,
        quantity: discardForm.quantity,
        reason: discardForm.reason || "user_discarded"
      })
    })
    if (res.status === 401) return navigateTo('/login')
    closeDiscardModal()
    fetchInventory()
  } catch (err) {
    console.error("Waste Error:", err)
  } finally {
    discardSubmitting.value = false
  }
}
</script>

<template>
  <div class="inventory-page">
    <div class="page-header">
      <div class="header-content">
        <h1>Live Inventory</h1>
        <p>Manage all food items stored in your smart kitchen.</p>
      </div>
      <button @click="fetchInventory" class="btn btn-secondary" :disabled="isLoading">
        {{ isLoading ? 'Refreshing...' : '🔄 Refresh' }}
      </button>
    </div>

    <!-- Empty State -->
    <div v-if="inventory.length === 0 && !isLoading" class="empty-card glass-card">
      <div class="empty-icon">📦</div>
      <p>No items in inventory yet.</p>
      <p class="empty-hint">Go to Dashboard and scan food items to add them here.</p>
    </div>

    <!-- Inventory Cards Grid -->
    <div v-else class="inventory-grid">
      <div v-for="item in inventory" :key="item._id" class="inv-card glass-card">
        <div class="card-top">
          <div class="card-name">
            <span class="food-emoji">🍎</span>
            <h3>{{ item.food_name }}</h3>
          </div>
          <span class="status-badge" :style="{ color: getStatusColor(item.status), background: getStatusBg(item.status) }">
            {{ item.status }}
          </span>
        </div>

        <div class="card-stats">
          <div class="stat">
            <span class="stat-label">Qty</span>
            <span class="stat-value">{{ item.quantity }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Price</span>
            <span class="stat-value price-val">₹{{ item.price_per_unit }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Freshness</span>
            <span class="stat-value">{{ item.freshness_score }}%</span>
          </div>
        </div>

        <div class="freshness-bar-wrap">
          <div class="freshness-bar">
            <div class="freshness-fill" :style="{ width: item.freshness_score + '%', background: getStatusColor(item.status) }"></div>
          </div>
        </div>

        <div class="card-expiry">
          <span>📅 Expires: {{ new Date(item.expiry_date).toLocaleDateString() }}</span>
          <span class="added-date">Added: {{ new Date(item.added_date).toLocaleDateString() }}</span>
        </div>

        <div class="card-actions">
          <button @click="openDetailsModal(item)" class="btn-action details" title="View Details">
            📋 Details
          </button>
          <div class="action-right">
            <button @click="openSellModal(item)" class="btn-action sell" title="Sell Item">💰 Sell</button>
            <button @click="openDiscardModal(item)" class="btn-action waste" title="Discard">🗑️</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════
         MODAL 1: Details
         ══════════════════════════════════════ -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showDetailsModal" class="modal-overlay" @click.self="closeDetailsModal">
          <div class="modal-card">
            <div class="modal-header">
              <h2>📋 Item Details</h2>
              <button class="modal-x" @click="closeDetailsModal">✕</button>
            </div>
            <div v-if="detailsItem" class="modal-body">
              <div class="m-banner">
                <span class="m-emoji">🍎</span>
                <div class="m-banner-info">
                  <h3>{{ detailsItem.food_name }}</h3>
                  <span class="m-status" :style="{ color: getStatusColor(detailsItem.status) }">{{ detailsItem.status }}</span>
                </div>
              </div>
              <div class="m-grid">
                <div class="m-cell"><span class="m-label">Quantity</span><span class="m-val">{{ detailsItem.quantity }}</span></div>
                <div class="m-cell"><span class="m-label">Unit Price</span><span class="m-val price-val">₹{{ detailsItem.price_per_unit }}</span></div>
                <div class="m-cell"><span class="m-label">Freshness</span><span class="m-val">{{ detailsItem.freshness_score }}%</span></div>
                <div class="m-cell"><span class="m-label">Expiry</span><span class="m-val">{{ new Date(detailsItem.expiry_date).toLocaleDateString() }}</span></div>
              </div>
              <div v-if="detailsItem.notes" class="m-notes-list">
                <div v-if="parseNotes(detailsItem.notes).note" class="m-note-item">
                  <div class="m-note-head">📋 Note</div>
                  <p>{{ parseNotes(detailsItem.notes).note }}</p>
                </div>
                <div v-if="parseNotes(detailsItem.notes).seller" class="m-note-item">
                  <div class="m-note-head">🏪 Seller</div>
                  <p>{{ parseNotes(detailsItem.notes).seller }}</p>
                </div>
                <div v-if="parseNotes(detailsItem.notes).phone" class="m-note-item">
                  <div class="m-note-head">📞 Phone</div>
                  <p><a :href="'tel:' + parseNotes(detailsItem.notes).phone" class="phone-link">{{ parseNotes(detailsItem.notes).phone }}</a></p>
                </div>
                <div v-if="!parseNotes(detailsItem.notes).note && !parseNotes(detailsItem.notes).seller && !parseNotes(detailsItem.notes).phone" class="m-note-item">
                  <div class="m-note-head">📋 Note</div>
                  <p>{{ detailsItem.notes }}</p>
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

    <!-- ══════════════════════════════════════
         MODAL 2: Sell
         ══════════════════════════════════════ -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showSellModal" class="modal-overlay" @click.self="closeSellModal">
          <div class="modal-card">
            <div class="modal-header">
              <h2>💰 Sell Item</h2>
              <button class="modal-x" @click="closeSellModal">✕</button>
            </div>
            <div v-if="sellModalItem" class="modal-body">
              <div class="m-banner sell-banner">
                <span class="m-emoji">🍎</span>
                <div class="m-banner-info">
                  <h3>{{ sellModalItem.food_name }}</h3>
                  <span class="m-sub">Available: {{ sellModalItem.quantity }} units • ₹{{ sellModalItem.price_per_unit }} each</span>
                </div>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label for="sell-qty">Quantity to Sell</label>
                  <input id="sell-qty" v-model.number="sellForm.quantity" type="number" min="1" :max="sellModalItem.quantity" :placeholder="'Max ' + sellModalItem.quantity" />
                </div>
                <div class="form-group">
                  <label for="sell-price">Selling Price (₹)</label>
                  <input id="sell-price" v-model.number="sellForm.price" type="number" min="0" step="0.01" placeholder="0.00" />
                </div>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label for="sell-buyer">Buyer Name <small>(Optional)</small></label>
                  <input id="sell-buyer" v-model="sellForm.buyerName" type="text" placeholder="Buyer name" />
                </div>
                <div class="form-group">
                  <label for="sell-phone">Buyer Phone <small>(Optional)</small></label>
                  <input id="sell-phone" v-model="sellForm.buyerPhone" type="tel" placeholder="+91 XXXXX XXXXX" />
                </div>
              </div>
              <div class="sell-summary">
                <span class="summary-label">Total Revenue</span>
                <span class="summary-value">₹{{ (sellForm.quantity * sellForm.price).toFixed(2) }}</span>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" @click="closeSellModal">Cancel</button>
              <button class="btn btn-sell" @click="confirmSell" :disabled="sellSubmitting || sellForm.quantity < 1">
                {{ sellSubmitting ? 'Selling...' : '💰 Confirm Sale' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ══════════════════════════════════════
         MODAL 3: Discard Confirmation
         ══════════════════════════════════════ -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showDiscardModal" class="modal-overlay" @click.self="closeDiscardModal">
          <div class="modal-card discard-modal">
            <div class="modal-header discard-header">
              <h2>🗑️ Discard Item</h2>
              <button class="modal-x" @click="closeDiscardModal">✕</button>
            </div>
            <div v-if="discardItem" class="modal-body">
              <div class="discard-warning">
                <div class="discard-icon">⚠️</div>
                <p>Are you sure you want to discard <strong>{{ discardItem.food_name }}</strong>?</p>
                <p class="discard-sub">This will move the selected units to waste logs and remove them from inventory. This action cannot be undone.</p>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label for="discard-qty">Quantity to Discard</label>
                  <input id="discard-qty" v-model.number="discardForm.quantity" type="number" min="1" :max="discardItem.quantity" :placeholder="'Max ' + discardItem.quantity" />
                </div>
                <div class="form-group">
                  <label for="discard-reason">Reason</label>
                  <textarea id="discard-reason" v-model="discardForm.reason" placeholder="e.g. Expired, Spilled" rows="2"></textarea>
                </div>
              </div>
              <div class="discard-item-preview">
                <div class="m-cell"><span class="m-label">Item</span><span class="m-val">{{ discardItem.food_name }}</span></div>
                <div class="m-cell"><span class="m-label">Qty to Discard</span><span class="m-val">{{ discardForm.quantity }}</span></div>
                <div class="m-cell"><span class="m-label">Value Lost</span><span class="m-val danger-val">₹{{ (discardForm.quantity * discardItem.price_per_unit).toFixed(2) }}</span></div>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" @click="closeDiscardModal">Cancel</button>
              <button class="btn btn-danger" @click="confirmDiscard" :disabled="discardSubmitting || discardForm.quantity < 1">
                {{ discardSubmitting ? 'Discarding...' : '🗑️ Confirm Discard' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
/* ══ Page Header ══ */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 1rem;
}
.header-content h1 { margin-bottom: 0.25rem; }

/* ══ Empty State ══ */
.empty-card { text-align: center; padding: 3rem 2rem; color: var(--text-dim); }
.empty-icon { font-size: 3rem; margin-bottom: 0.75rem; opacity: 0.4; }
.empty-hint { font-size: 0.82rem; opacity: 0.6; margin-top: 0.3rem; }

/* ══ Inventory Grid ══ */
.inventory-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.25rem;
}

/* ══ Cards ══ */
.inv-card { display: flex; flex-direction: column; gap: 0.85rem; padding: 1.25rem; }
.inv-card:hover { transform: translateY(-4px); }

.card-top { display: flex; justify-content: space-between; align-items: center; gap: 0.75rem; }
.card-name { display: flex; align-items: center; gap: 0.5rem; min-width: 0; }
.food-emoji { font-size: 1.3rem; flex-shrink: 0; }
.card-name h3 { font-size: 1.05rem; font-weight: 700; text-transform: capitalize; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin: 0; }
.status-badge { font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 20px; white-space: nowrap; flex-shrink: 0; text-transform: uppercase; letter-spacing: 0.3px; }

.card-stats { display: flex; gap: 0.5rem; }
.stat { flex: 1; background: rgba(255,255,255,0.03); border-radius: 10px; padding: 0.5rem 0.65rem; display: flex; flex-direction: column; align-items: center; gap: 0.15rem; min-width: 0; }
.stat-label { font-size: 0.65rem; font-weight: 600; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; }
.stat-value { font-size: 1rem; font-weight: 700; }
.price-val { color: var(--success); }

.freshness-bar-wrap { padding: 0 0.15rem; }
.freshness-bar { width: 100%; height: 5px; background: rgba(255,255,255,0.06); border-radius: 3px; overflow: hidden; }
.freshness-fill { height: 100%; border-radius: 3px; transition: width 0.6s ease; }

.card-expiry { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; font-size: 0.78rem; color: var(--text-dim); }
.added-date { opacity: 0.6; }

.card-actions { display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; padding-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.05); }
.action-right { display: flex; gap: 0.4rem; }

.btn-action { padding: 0.4rem 0.75rem; border-radius: 8px; border: 1px solid var(--glass-border); background: rgba(255,255,255,0.04); color: var(--text-dim); font-size: 0.78rem; font-family: inherit; cursor: pointer; display: inline-flex; align-items: center; gap: 0.3rem; transition: all 0.25s ease; white-space: nowrap; }
.btn-action:hover { transform: translateY(-2px); }
.btn-action.details { color: var(--primary); border-color: rgba(255,106,61,0.2); }
.btn-action.details:hover { background: rgba(255,106,61,0.1); border-color: rgba(255,106,61,0.4); }
.btn-action.sell:hover { background: rgba(52,211,153,0.1); border-color: rgba(52,211,153,0.3); color: var(--success); }
.btn-action.waste:hover { background: rgba(248,113,113,0.1); border-color: rgba(248,113,113,0.3); color: var(--danger); }

/* ══════════════════════════════════════════
   Shared Modal Styles
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

/* ── Shared modal elements ── */
.m-banner { display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 1rem; background: rgba(255,106,61,0.06); border-radius: 12px; border: 1px solid rgba(255,106,61,0.12); }
.m-emoji { font-size: 1.5rem; flex-shrink: 0; }
.m-banner-info h3 { font-size: 1rem; font-weight: 700; text-transform: capitalize; margin-bottom: 0.1rem; }
.m-status { font-size: 0.78rem; font-weight: 600; }
.m-sub { font-size: 0.78rem; color: var(--text-dim); }

.m-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; }
.m-cell { background: rgba(255,255,255,0.03); border-radius: 10px; padding: 0.6rem 0.75rem; display: flex; flex-direction: column; gap: 0.15rem; min-width: 0; }
.m-label { font-size: 0.65rem; font-weight: 600; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; }
.m-val { font-size: 0.95rem; font-weight: 700; word-break: break-word; }

.m-notes-list { display: flex; flex-direction: column; gap: 0.6rem; }
.m-note-item { background: rgba(255,255,255,0.03); border-radius: 10px; padding: 0.65rem 0.9rem; border-left: 3px solid var(--primary); }
.m-note-head { font-size: 0.7rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.2rem; }
.m-note-item p { font-size: 0.9rem; color: var(--text-main); word-break: break-word; line-height: 1.5; }

.phone-link { color: var(--primary); text-decoration: none; font-weight: 600; transition: opacity 0.2s; }
.phone-link:hover { opacity: 0.8; text-decoration: underline; }

/* ══ Sell Modal ══ */
.sell-banner { background: rgba(52,211,153,0.06); border-color: rgba(52,211,153,0.15); }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; min-width: 0; }
.form-group { display: flex; flex-direction: column; gap: 0.35rem; min-width: 0; }
.form-group label { font-size: 0.72rem; font-weight: 600; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; }
.form-group input, .form-group textarea {
  width: 100%; box-sizing: border-box; min-width: 0;
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
  border-radius: 10px; padding: 0.6rem 0.75rem;
  color: var(--text-main); font-family: inherit; font-size: 0.88rem;
  outline: none; transition: border-color 0.25s ease, box-shadow 0.25s ease;
}
.form-group textarea { resize: vertical; min-height: 50px; }
.form-group input::placeholder, .form-group textarea::placeholder { color: rgba(255,255,255,0.2); }
.form-group input:focus, .form-group textarea:focus { border-color: rgba(255,106,61,0.5); box-shadow: 0 0 0 3px rgba(255,106,61,0.1); }
.form-group input[type="number"]::-webkit-inner-spin-button,
.form-group input[type="number"]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
.form-group input[type="number"] { -moz-appearance: textfield; }

.sell-summary {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.75rem 1rem; background: rgba(52,211,153,0.06);
  border-radius: 10px; border: 1px solid rgba(52,211,153,0.15);
}
.summary-label { font-size: 0.82rem; font-weight: 600; color: var(--text-dim); }
.summary-value { font-size: 1.2rem; font-weight: 800; color: var(--success); }

.btn-sell {
  background: linear-gradient(135deg, #34d399 0%, #10b981 100%);
  color: #111; border: none; font-weight: 700;
  box-shadow: 0 4px 14px rgba(52,211,153,0.25);
}
.btn-sell:hover { box-shadow: 0 6px 24px rgba(52,211,153,0.45); transform: translateY(-2px); }
.btn-sell:disabled { opacity: 0.5; cursor: not-allowed; transform: none !important; }

/* ══ Discard Modal ══ */
.discard-modal { border-color: rgba(248,113,113,0.3); }
.discard-header h2 { background: linear-gradient(135deg, #f87171 0%, #ef4444 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

.discard-warning { text-align: center; padding: 0.5rem 0; }
.discard-icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
.discard-warning p { font-size: 0.95rem; line-height: 1.5; }
.discard-warning strong { color: var(--text-main); }
.discard-sub { font-size: 0.8rem !important; color: var(--text-dim); margin-top: 0.4rem; }

.discard-item-preview { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.5rem; }
.danger-val { color: var(--danger); }

.btn-danger {
  background: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
  color: #fff; border: none; font-weight: 700;
  box-shadow: 0 4px 14px rgba(248,113,113,0.25);
}
.btn-danger:hover { box-shadow: 0 6px 24px rgba(248,113,113,0.45); transform: translateY(-2px); }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; transform: none !important; }

/* ══ Responsive ══ */
@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: stretch; }
  .inventory-grid { grid-template-columns: 1fr; }
}

@media (max-width: 520px) {
  .card-stats { flex-wrap: wrap; }
  .stat { flex: 1 1 calc(33% - 0.35rem); min-width: 80px; }
  .card-actions { flex-direction: column; align-items: stretch; }
  .action-right { justify-content: flex-end; }
  .modal-card { max-width: 100%; border-radius: 16px; }
  .modal-body { padding: 1rem 1.25rem; }
  .modal-header { padding: 1rem 1.25rem; }
  .modal-footer { padding: 0.75rem 1.25rem; flex-direction: column; }
  .modal-footer .btn { width: 100%; justify-content: center; }
  .form-row { grid-template-columns: 1fr; }
  .discard-item-preview { grid-template-columns: 1fr; }
}
</style>
