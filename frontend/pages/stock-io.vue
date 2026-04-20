<script setup>
const config = useRuntimeConfig()
const items = ref([])
const searchQuery = ref("")
const isLoading = ref(false)

const showConfirmModal = ref(false)
const confirmItem = ref(null)
const buyerForm = reactive({ name: '', phone: '', sellPrice: 0.0 })
const isSubmitting = ref(false)

const showAddModal = ref(false)
const addForm = reactive({ name: '', quantity: 1, price: 0.0, seller: '', phone: '', note: '' })
const isAdding = ref(false)

async function fetchAggregated() {
  isLoading.value = true
  try {
    const response = await fetch(`${config.public.apiBase}/inventory/aggregated`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    })
    if (response.status === 401) return navigateTo('/login')
    const data = await response.json()
    items.value = (data.inventory || []).map(i => ({ ...i, sellQty: 1 }))
  } catch (err) {
    console.error("Fetch Aggregated Error:", err)
  } finally {
    isLoading.value = false
  }
}

const filteredItems = computed(() => {
  if (!searchQuery.value) return items.value
  const q = searchQuery.value.toLowerCase()
  return items.value.filter(i => i.food_name.toLowerCase().includes(q))
})

function openSellModal(item) {
  if (item.sellQty > item.quantity) {
    alert("Cannot sell more than in stock!")
    return
  }
  confirmItem.value = item
  buyerForm.name = ''
  buyerForm.phone = ''
  buyerForm.sellPrice = item.avg_price
  showConfirmModal.value = true
}

function closeSellModal() {
  showConfirmModal.value = false
  confirmItem.value = null
}

async function confirmSell() {
  if (!confirmItem.value || isSubmitting.value) return
  isSubmitting.value = true
  
  try {
    const res = await fetch(`${config.public.apiBase}/inventory/sell_bulk`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify({
        food_name: confirmItem.value.food_name,
        quantity: confirmItem.value.sellQty,
        sell_price: buyerForm.sellPrice,
        buyer_name: buyerForm.name,
        buyer_phone: buyerForm.phone
      })
    })
    if (res.status === 401) return navigateTo('/login')
    closeSellModal()
    fetchAggregated()
  } catch (err) {
    console.error("Sell Bulk Error:", err)
  } finally {
    isSubmitting.value = false
  }
}

function openAddModal() {
  addForm.name = ''
  addForm.quantity = 1
  addForm.price = 0.0
  addForm.seller = ''
  addForm.phone = ''
  addForm.note = ''
  showAddModal.value = true
}

function closeAddModal() {
  showAddModal.value = false
}

async function confirmAddStock() {
  if (!addForm.name || isAdding.value) return
  isAdding.value = true
  
  try {
    // Format notes safely
    const notesArray = []
    if (addForm.seller) notesArray.push(`Seller Name: ${addForm.seller}`)
    if (addForm.phone) notesArray.push(`Seller Phone: ${addForm.phone}`)
    if (addForm.note) notesArray.push(addForm.note)

    const res = await fetch(`${config.public.apiBase}/inventory/add`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify({
        food_name: addForm.name,
        quantity: addForm.quantity,
        price_per_unit: addForm.price,
        notes: notesArray.join(' | '),
        freshness_score: 100,
        status: "Safe to Eat",
        expiry_days: 7
      })
    })
    if (res.status === 401) return navigateTo('/login')
    closeAddModal()
    fetchAggregated()
  } catch (err) {
    console.error("Add Stock Error:", err)
  } finally {
    isAdding.value = false
  }
}

onMounted(() => {
  fetchAggregated()
})
</script>

<template>
  <div class="sell-page">
    <div class="page-header">
      <div>
        <h1>Stock In / Out Management</h1>
        <p>Manage inventory flow: securely add incoming stock or check out bulk outgoing units.</p>
      </div>
      <div class="header-actions">
        <button @click="fetchAggregated" class="btn btn-secondary" :disabled="isLoading">🔄 Refresh</button>
        <button @click="openAddModal" class="btn btn-primary">➕ Stock In</button>
      </div>
    </div>

    <div class="controls-bar glass-card">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input type="text" v-model="searchQuery" placeholder="Search Products by name..." />
      </div>
    </div>

    <div class="products-container glass-card">
      <div v-if="filteredItems.length === 0" class="empty-state">
         No products available. Add items from the dashboard.
      </div>
      <div class="table-responsive" v-else>
        <table>
          <thead>
            <tr>
              <th>Product</th>
              <th>Stock Quantity</th>
              <th>Avg Sale Price</th>
              <th>Quantity to Sell</th>
              <th style="text-align: right;">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredItems" :key="item._id">
              <td class="product-cell">
                <div class="icon-avatar">📦</div>
                <div class="product-info">
                  <strong>{{ item.food_name }}</strong>
                  <span>Batches: {{ item.batch_count }}</span>
                </div>
              </td>
              <td>
                <span class="stock-badge">{{ item.quantity }}</span>
              </td>
              <td>
                <strong>₹{{ item.avg_price.toFixed(2) }}</strong>
              </td>
              <td class="qty-cell">
                <input type="number" v-model.number="item.sellQty" min="1" :max="item.quantity" class="inline-qty" />
              </td>
              <td align="right" style="text-align: right;">
                <button class="btn btn-primary" @click="openSellModal(item)" :disabled="item.sellQty < 1 || item.sellQty > item.quantity">Sell Now</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Confirm Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showConfirmModal" class="modal-overlay" @click.self="closeSellModal">
          <div class="modal-card">
            <div class="modal-header">
              <h2>Confirm Sale Details</h2>
              <button class="modal-x" @click="closeSellModal">✕</button>
            </div>
            
            <div class="modal-preview">
              <div class="preview-item">
                <span>Product</span>
                <strong>{{ confirmItem?.food_name }}</strong>
              </div>
              <div class="preview-item">
                <span>Total Quantity</span>
                <strong>{{ confirmItem?.sellQty }} Units</strong>
              </div>
              <div class="preview-item">
                <span>Total Revenue</span>
                <strong class="success-val">₹{{ (confirmItem?.sellQty * buyerForm.sellPrice).toFixed(2) }}</strong>
              </div>
            </div>

            <div class="modal-body">
              <div class="form-group" style="margin-bottom: 0.5rem;">
                <label for="b-price">Sale Price per Unit (₹)</label>
                <input id="b-price" v-model.number="buyerForm.sellPrice" type="number" step="0.01" min="0" />
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label for="b-name">Buyer Name (Optional)</label>
                  <input id="b-name" v-model="buyerForm.name" type="text" placeholder="e.g. John Doe" />
                </div>
                <div class="form-group">
                  <label for="b-phone">Buyer Phone (Optional)</label>
                  <input id="b-phone" v-model="buyerForm.phone" type="tel" placeholder="+91 XXXXX XXXXX" />
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" @click="closeSellModal">Cancel</button>
              <button class="btn btn-primary" @click="confirmSell" :disabled="isSubmitting">
                {{ isSubmitting ? 'Processing...' : '✅ Complete Sale' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Add Stock Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showAddModal" class="modal-overlay" @click.self="closeAddModal">
          <div class="modal-card">
            <div class="modal-header">
              <h2>➕ Stock In (Receive New Items)</h2>
              <button class="modal-x" @click="closeAddModal">✕</button>
            </div>
            
            <div class="modal-body">
              <div class="form-group">
                <label for="add-name">Food Name</label>
                <input id="add-name" v-model="addForm.name" type="text" placeholder="e.g. Tomatoes" />
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label for="add-qty">Quantity</label>
                  <input id="add-qty" v-model.number="addForm.quantity" type="number" min="1" placeholder="1" />
                </div>
                <div class="form-group">
                  <label for="add-price">Price Per Unit (₹)</label>
                  <input id="add-price" v-model.number="addForm.price" type="number" min="0" step="0.01" placeholder="0.00" />
                </div>
              </div>
              
              <div class="form-group">
                <label for="add-note">Note</label>
                <textarea id="add-note" v-model="addForm.note" placeholder="Optional items notes..." rows="2"></textarea>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="add-seller">Seller Name</label>
                  <input id="add-seller" v-model="addForm.seller" type="text" placeholder="Optional" />
                </div>
                <div class="form-group">
                  <label for="add-s-phone">Seller Phone</label>
                  <input id="add-s-phone" v-model="addForm.phone" type="tel" placeholder="Optional" />
                </div>
              </div>
            </div>
            
            <div class="modal-footer">
              <button class="btn btn-secondary" @click="closeAddModal">Cancel</button>
              <button class="btn btn-primary" @click="confirmAddStock" :disabled="isAdding || !addForm.name">
                {{ isAdding ? 'Adding...' : '✅ Save to Inventory' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.5rem; }

.controls-bar { padding: 1rem 1.5rem; margin-bottom: 1.5rem; display: flex; }
.search-box { display: flex; align-items: center; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 0.5rem 1rem; flex: 1; transition: all 0.3s ease; }
.search-box:focus-within { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(255,106,61,0.1); }
.search-icon { margin-right: 0.75rem; opacity: 0.5; }
.search-box input { background: transparent; border: none; color: white; width: 100%; outline: none; font-size: 0.95rem; font-family: inherit; }

.products-container { padding: 0.5rem 1.5rem 1.5rem 1.5rem; }
.table-responsive { overflow-x: auto; -webkit-overflow-scrolling: touch; }

table { width: 100%; border-collapse: separate; border-spacing: 0 0.5rem; min-width: 600px; }
th { padding: 1rem; color: var(--text-dim); text-transform: uppercase; font-size: 0.75rem; letter-spacing: 1px; border-bottom: 1px solid rgba(255,255,255,0.06); text-align: left; }
td { padding: 1rem; background: rgba(255,255,255,0.02); vertical-align: middle; transition: background 0.25s ease; }
tr:hover td { background: rgba(255, 106, 61, 0.05); }

td:first-child { border-top-left-radius: 12px; border-bottom-left-radius: 12px; }
td:last-child  { border-top-right-radius: 12px; border-bottom-right-radius: 12px; }

.product-cell { display: flex; align-items: center; gap: 1rem; }
.icon-avatar { width: 44px; height: 44px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; }
.product-info { display: flex; flex-direction: column; }
.product-info strong { font-size: 1rem; color: #fff; text-transform: capitalize; }
.product-info span { font-size: 0.75rem; color: var(--text-dim); }

.stock-badge { padding: 4px 10px; background: rgba(255,106,61,0.15); color: var(--primary); font-weight: 700; border-radius: 8px; font-size: 0.85rem; border: 1px solid rgba(255,106,61,0.25); }

.qty-cell { max-width: 120px; }
.inline-qty { width: 100%; max-width: 90px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; padding: 0.5rem; color: white; text-align: center; font-family: inherit; font-weight: 700; outline: none; transition: border-color 0.25s ease; }
.inline-qty:focus { border-color: var(--primary); }
.inline-qty::-webkit-inner-spin-button { opacity: 1; margin-left: 5px; }

.empty-state { text-align: center; padding: 3rem; color: var(--text-dim); }

/* Modal */
.modal-overlay { position: fixed; inset: 0; z-index: 9999; background: rgba(0,0,0,0.75); backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; padding: 1rem; }
.modal-card { background: #1a1a1a; border: 1px solid rgba(255,106,61,0.25); border-radius: 20px; width: 100%; max-width: 440px; box-shadow: 0 24px 64px rgba(0,0,0,0.6); animation: pop 0.3s ease-out; }
@keyframes pop { from { opacity: 0; transform: scale(0.95) translateY(10px); } to { opacity: 1; transform: scale(1) translateY(0); } }

.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 1.1rem 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.06); }
.modal-header h2 { font-size: 1.1rem; font-weight: 700; background: var(--primary-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.modal-x { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); color: var(--text-dim); width: 30px; height: 30px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.modal-x:hover { background: rgba(248,113,113,0.15); color: #f87171; border-color: rgba(248,113,113,0.3); }

.modal-preview { background: rgba(52,211,153,0.05); padding: 1rem 1.5rem; display: flex; flex-direction: column; gap: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.05); }
.preview-item { display: flex; justify-content: space-between; font-size: 0.9rem; }
.preview-item span { color: var(--text-dim); }
.success-val { color: var(--success); font-size: 1.1rem; }

.modal-body { padding: 1.25rem 1.5rem; display: flex; flex-direction: column; gap: 1rem; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.form-group { display: flex; flex-direction: column; gap: 0.4rem; }
.form-group label { font-size: 0.75rem; font-weight: 600; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; }
.form-group input, .form-group textarea { width: 100%; box-sizing: border-box; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); padding: 0.7rem 0.9rem; border-radius: 10px; color: var(--text-main); font-family: inherit; font-size: 0.95rem; outline: none; transition: 0.2s; }
.form-group input:focus, .form-group textarea:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(255,106,61,0.1); }
.form-group textarea { resize: vertical; min-height: 60px; }

.modal-footer { display: flex; justify-content: flex-end; gap: 0.75rem; padding: 0.85rem 1.5rem; border-top: 1px solid rgba(255,255,255,0.06); }
.modal-footer .btn { padding: 0.55rem 1.3rem; font-size: 0.88rem; }

.modal-enter-active { transition: opacity 0.25s ease; }
.modal-leave-active { transition: opacity 0.2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }

@media (max-width: 520px) {
  .form-row { grid-template-columns: 1fr; }
  .modal-footer { flex-direction: column; }
  .modal-footer .btn { width: 100%; justify-content: center; }
  .table-responsive { min-width: 100%; }
}
</style>
