<script setup>
const config = useRuntimeConfig()
const groceryItems = ref([])
const isLoading = ref(false)

const showAddModal = ref(false)
const addSubmitting = ref(false)
const addForm = reactive({ name: '', quantity: 1, price: 0.0 })

async function fetchGrocery() {
  isLoading.value = true
  try {
    const response = await fetch(`${config.public.apiBase}/grocery/list`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    })
    if (response.status === 401) return navigateTo('/login')
    const data = await response.json()
    groceryItems.value = data.grocery_list || []
  } catch (err) {
    console.error("Fetch Grocery Error:", err)
  } finally {
    isLoading.value = false
  }
}

async function markPurchased(item) {
  try {
    const res = await fetch(`${config.public.apiBase}/grocery/update`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify({ item_id: item._id })
    })
    if (res.status === 401) return navigateTo('/login')
    fetchGrocery()
  } catch (err) {
    console.error("Update Grocery Error:", err)
  }
}

function openAddModal() {
  addForm.name = ''
  addForm.quantity = 1
  addForm.price = 0.0
  showAddModal.value = true
}

function closeAddModal() {
  showAddModal.value = false
}

async function confirmAddItem() {
  if (!addForm.name || addSubmitting.value) return
  addSubmitting.value = true
  
  try {
    const res = await fetch(`${config.public.apiBase}/grocery/add`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify({
        food_name: addForm.name,
        quantity: addForm.quantity,
        estimated_price: addForm.price
      })
    })
    if (res.status === 401) return navigateTo('/login')
    closeAddModal()
    fetchGrocery()
  } catch (err) {
    console.error("Add Grocery Error:", err)
  } finally {
    addSubmitting.value = false
  }
}

onMounted(() => {
  fetchGrocery()
})
</script>

<template>
  <div class="grocery-page">
    <div class="page-header">
      <div>
        <h1>Grocery List</h1>
        <p>Items generated from low stock or expired waste.</p>
      </div>
      <div class="header-actions">
        <button @click="fetchGrocery" class="btn btn-secondary" :disabled="isLoading">🔄</button>
        <button @click="openAddModal" class="btn btn-primary">➕ Add Item</button>
      </div>
    </div>

    <div class="list-container">
      <div v-if="groceryItems.length === 0" class="empty-state glass-card">
        <div class="empty-icon">🛒</div>
        <p>Your grocery list is empty. Everything is tip-top!</p>
      </div>
      <div v-else class="grocery-grid">
        <div v-for="item in groceryItems" :key="item._id" class="grocery-card glass-card">
          <div class="item-info">
            <span class="qty-badge">{{ item.quantity }}x</span>
            <h3>{{ item.food_name }}</h3>
            <p v-if="item.notes" class="notes">{{ item.notes }}</p>
            <p class="price">Est. ₹{{ item.estimated_price }}</p>
          </div>
          <button @click="markPurchased(item)" class="btn-check" title="Mark purchased">✓</button>
        </div>
      </div>
    </div>

    <!-- ══ Add Item Modal ══ -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showAddModal" class="modal-overlay" @click.self="closeAddModal">
          <div class="modal-card">
            <div class="modal-header">
              <h2>🛒 Add Grocery Item</h2>
              <button class="modal-x" @click="closeAddModal">✕</button>
            </div>
            <div class="modal-body">
              <div class="form-group">
                <label for="add-name">Item Name</label>
                <input id="add-name" v-model="addForm.name" type="text" placeholder="e.g. Apples, Milk" />
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label for="add-qty">Quantity</label>
                  <input id="add-qty" v-model.number="addForm.quantity" type="number" min="1" placeholder="1" />
                </div>
                <div class="form-group">
                  <label for="add-price">Est. Price (₹)</label>
                  <input id="add-price" v-model.number="addForm.price" type="number" min="0" step="0.01" placeholder="0.00" />
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" @click="closeAddModal">Cancel</button>
              <button class="btn btn-primary" @click="confirmAddItem" :disabled="addSubmitting || !addForm.name">
                {{ addSubmitting ? 'Adding...' : '➕ Add Item' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 1rem;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.list-container {
  margin-top: 1.5rem;
}

.grocery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
}

.grocery-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
}

.item-info {
  min-width: 0;
  flex: 1;
}

.item-info h3 {
  text-transform: capitalize;
  margin: 0.3rem 0;
  font-size: 1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.qty-badge {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--primary);
  background: rgba(255, 106, 61, 0.1);
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid rgba(255, 106, 61, 0.2);
}

.notes {
  font-size: 0.82rem;
  color: var(--text-dim);
  font-style: italic;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.price {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--success);
  margin-top: 0.4rem;
}

.btn-check {
  background: rgba(52, 211, 153, 0.08);
  border: 1px solid rgba(52, 211, 153, 0.2);
  color: var(--success);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  font-size: 1.1rem;
  cursor: pointer;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.btn-check:hover {
  background: var(--success);
  color: #111;
  transform: rotate(15deg) scale(1.15);
  box-shadow: 0 0 16px rgba(52, 211, 153, 0.4);
}

.empty-state {
  text-align: center;
  padding: 3rem 2rem;
  color: var(--text-dim);
}

.empty-icon {
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
  opacity: 0.5;
}

/* Responsive */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }
  .header-actions {
    width: 100%;
  }
  .header-actions .btn {
    flex: 1;
  }
  .grocery-grid {
    grid-template-columns: 1fr;
  }
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
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.form-group { display: flex; flex-direction: column; gap: 0.4rem; }
.form-group label { font-size: 0.75rem; font-weight: 600; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; }
.form-group input { width: 100%; box-sizing: border-box; min-width: 0; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); padding: 0.7rem 0.9rem; border-radius: 10px; color: var(--text-main); font-family: inherit; font-size: 0.95rem; transition: all 0.25s ease; outline: none; }
.form-group input:focus { border-color: var(--primary); background: rgba(255,106,61,0.05); box-shadow: 0 0 0 3px rgba(255,106,61,0.1); }

.modal-footer { display: flex; justify-content: flex-end; gap: 0.75rem; padding: 0.85rem 1.5rem; border-top: 1px solid rgba(255,255,255,0.06); }
.modal-footer .btn { padding: 0.55rem 1.3rem; font-size: 0.88rem; }

.modal-enter-active { transition: opacity 0.25s ease; }
.modal-leave-active { transition: opacity 0.2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }

@media (max-width: 520px) {
  .modal-card { max-width: 100%; border-radius: 16px; }
  .modal-body { padding: 1rem 1.25rem; }
  .modal-header { padding: 1rem 1.25rem; }
  .form-row { grid-template-columns: 1fr; }
  .modal-footer { padding: 0.75rem 1.25rem; flex-direction: column; }
  .modal-footer .btn { width: 100%; justify-content: center; }
}
</style>
