<script setup>
const config = useRuntimeConfig()
const video = ref(null)
const canvas = ref(null)
const fileInput = ref(null)
const isWebcamActive = ref(false)
const detections = ref([])
const status = ref('Ready')
const isProcessing = ref(false)
const showCanvas = ref(false)
const uploadedImageUrl = ref(null)

// Modal state
const showModal = ref(false)
const modalItem = ref(null)
const modalForm = reactive({
  quantity: 1,
  price: 0,
  note: '',
  sellerName: '',
  sellerPhone: ''
})

onMounted(() => {
  // idle on load
})

async function startWebcam() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
    if (video.value) {
      video.value.srcObject = stream
      isWebcamActive.value = true
      showCanvas.value = false
      uploadedImageUrl.value = null
      detections.value = []
      status.value = 'Webcam Active'

      // Wait for video metadata to be ready before starting loop
      video.value.onloadedmetadata = () => {
        video.value.play()
        startDetectionLoop()
      }
    }
  } catch (err) {
    console.error("Webcam Error:", err)
    status.value = 'Webcam Access Denied'
  }
}

function stopWebcam() {
  if (video.value && video.value.srcObject) {
    const tracks = video.value.srcObject.getTracks()
    tracks.forEach(track => track.stop())
    video.value.srcObject = null
  }
  isWebcamActive.value = false
}

async function startDetectionLoop() {
  if (!isWebcamActive.value) return

  if (!isProcessing.value) {
    await captureAndDetect()
  }

  if (isWebcamActive.value) {
    setTimeout(() => requestAnimationFrame(startDetectionLoop), 800)
  }
}

async function captureAndDetect() {
  if (!video.value || !canvas.value) return
  if (video.value.videoWidth === 0) return // not ready yet

  isProcessing.value = true

  const ctx = canvas.value.getContext('2d')
  canvas.value.width = video.value.videoWidth
  canvas.value.height = video.value.videoHeight
  ctx.drawImage(video.value, 0, 0)

  const blob = await new Promise(resolve => canvas.value.toBlob(resolve, 'image/jpeg', 0.8))
  if (!blob) { isProcessing.value = false; return }

  const formData = new FormData()
  formData.append('file', blob, 'frame.jpg')

  try {
    const response = await fetch(`${config.public.apiBase}/predict`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: formData
    })
    const data = await response.json()
    detections.value = data.detections || []
    // Re-draw frame + detection boxes
    ctx.drawImage(video.value, 0, 0)
    drawDetections()
    showCanvas.value = true
  } catch (err) {
    console.error("Detection Error:", err)
  } finally {
    isProcessing.value = false
  }
}

function drawDetections() {
  if (!canvas.value) return
  const ctx = canvas.value.getContext('2d')
  detections.value.forEach(det => {
    const [x1, y1, x2, y2] = det.box
    // Label background
    const label = `${det.food_name} ${Math.round(det.confidence * 100)}%`
    ctx.font = 'bold 14px Outfit, sans-serif'
    const textWidth = ctx.measureText(label).width

    ctx.fillStyle = 'rgba(255, 106, 61, 0.85)'
    ctx.fillRect(x1, y1 > 24 ? y1 - 24 : y1, textWidth + 12, 22)

    ctx.fillStyle = '#fff'
    ctx.fillText(label, x1 + 6, y1 > 24 ? y1 - 7 : y1 + 15)

    // Box
    ctx.strokeStyle = '#ff6a3d'
    ctx.lineWidth = 3
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)
  })
}

function triggerUpload() {
  fileInput.value.click()
}

function onViewportClick() {
  // If nothing is active, open file browser
  if (!isWebcamActive.value && detections.value.length === 0 && !uploadedImageUrl.value) {
    triggerUpload()
  }
}

async function handleUpload(event) {
  const file = event.target.files[0]
  if (!file) return

  stopWebcam()
  status.value = 'Processing Image...'
  detections.value = []

  // Show the image immediately
  uploadedImageUrl.value = URL.createObjectURL(file)
  showCanvas.value = false

  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await fetch(`${config.public.apiBase}/predict`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: formData
    })
    const data = await response.json()
    detections.value = data.detections || []

    // Now draw the image on canvas with detection boxes
    const img = new Image()
    img.onload = () => {
      canvas.value.width = img.naturalWidth
      canvas.value.height = img.naturalHeight
      const ctx = canvas.value.getContext('2d')
      ctx.drawImage(img, 0, 0)
      drawDetections()
      showCanvas.value = true
      uploadedImageUrl.value = null // hide the <img>, show canvas instead
    }
    img.src = URL.createObjectURL(file)
    status.value = `Analysis Complete — ${detections.value.length} item(s) found`
  } catch (err) {
    console.error("Upload Prediction Error:", err)
    status.value = 'Error — Is the backend running?'
  }

  // Reset the input so the same file can be re-selected
  event.target.value = ''
}

function openAddModal(item) {
  modalItem.value = item
  modalForm.quantity = 1
  modalForm.price = 0
  modalForm.note = ''
  modalForm.sellerName = ''
  modalForm.sellerPhone = ''
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  modalItem.value = null
}

async function confirmAddToInventory() {
  if (!modalItem.value) return
  const item = modalItem.value

  try {
    const res = await fetch(`${config.public.apiBase}/inventory/add`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify({
        food_name: item.food_name,
        freshness_score: item.freshness_score,
        status: item.status,
        expiry_days: item.expiry_days,
        quantity: modalForm.quantity,
        price_per_unit: modalForm.price,
        notes: [modalForm.note, modalForm.sellerName ? `Seller: ${modalForm.sellerName}` : '', modalForm.sellerPhone ? `Phone: ${modalForm.sellerPhone}` : ''].filter(Boolean).join(' | ')
      })
    })
    if (res.status === 401) return navigateTo('/login')
    closeModal()
    status.value = `✅ ${item.food_name} added to inventory!`
  } catch (err) {
    console.error("Add to Inventory Error:", err)
  }
}
</script>

<template>
  <div class="dashboard">
    <div class="page-header">
      <h1>Food Analyser</h1>
      <p>AI-powered scanning for quality and shelf-life prediction.</p>
    </div>

    <div class="content-grid">
      <!-- Viewer -->
      <div class="viewer-card glass-card">
        <div class="viewer-header">
          <div class="actions">
            <button v-if="!isWebcamActive" @click="startWebcam" class="btn btn-secondary">
              📷 Webcam
            </button>
            <button v-else @click="stopWebcam" class="btn btn-secondary btn-stop">
              ⏹ Stop
            </button>
            <button @click="triggerUpload" class="btn btn-primary">
              📁 Upload Image
            </button>
            <input type="file" ref="fileInput" @change="handleUpload" hidden accept="image/*" />
          </div>
          <div class="status-badge">
            <span class="status-dot" :class="{ active: isWebcamActive, processing: isProcessing }"></span>
            <span class="status-text">{{ status }}</span>
          </div>
        </div>

        <div class="viewport" @click="onViewportClick" :class="{ clickable: !isWebcamActive && !uploadedImageUrl && detections.length === 0 }">
          <!-- Live webcam feed -->
          <video
            v-show="isWebcamActive && !showCanvas"
            ref="video"
            autoplay
            playsinline
            muted
            class="media-element"
          ></video>

          <!-- Uploaded image preview (before detection completes) -->
          <img
            v-if="uploadedImageUrl"
            :src="uploadedImageUrl"
            class="media-element"
            alt="Uploaded food image"
          />

          <!-- Canvas with detection overlays -->
          <canvas
            v-show="showCanvas"
            ref="canvas"
            class="media-element"
          ></canvas>

          <!-- Placeholder -->
          <div v-if="!isWebcamActive && !uploadedImageUrl && !showCanvas" class="placeholder">
            <div class="placeholder-icon">📷</div>
            <h3>Click here to upload an image</h3>
            <p>Or use the buttons above to start webcam / browse files</p>
          </div>
        </div>
      </div>

      <!-- Results -->
      <div class="results-card glass-card">
        <h3>Detected Items</h3>
        <div v-if="detections.length === 0" class="empty-state">
          <div class="empty-icon">🔍</div>
          <p>No food detected yet.</p>
          <p class="empty-hint">Upload an image or start your webcam to begin scanning.</p>
        </div>
        <div v-else class="results-list">
          <div v-for="(det, index) in detections" :key="index" class="det-item">
            <div class="det-info">
              <h4>{{ det.food_name }}</h4>
              <p class="det-quality" :style="{ color: det.color_code }">{{ det.quality_label }} • {{ det.status }}</p>
              <div class="meta">
                <span>🎯 {{ Math.round(det.confidence * 100) }}%</span>
                <span>📅 {{ det.expiry_days }} days</span>
              </div>
            </div>
            <button @click="openAddModal(det)" class="btn-add" title="Add to inventory">➕</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ══ Add to Inventory Modal ══ -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
          <div class="modal-card">
            <div class="modal-header">
              <h2>Add to Inventory</h2>
              <button class="modal-close" @click="closeModal">✕</button>
            </div>

            <div class="modal-detected" v-if="modalItem">
              <span class="modal-food-name">{{ modalItem.food_name }}</span>
              <span class="modal-quality" :style="{ color: modalItem.color_code }">{{ modalItem.quality_label }}</span>
            </div>

            <div class="modal-body">
              <div class="form-row">
                <div class="form-group">
                  <label for="m-qty">Quantity</label>
                  <input id="m-qty" v-model.number="modalForm.quantity" type="number" min="1" placeholder="1" />
                </div>
                <div class="form-group">
                  <label for="m-price">Price per unit (₹)</label>
                  <input id="m-price" v-model.number="modalForm.price" type="number" min="0" step="0.01" placeholder="0.00" />
                </div>
              </div>

              <div class="form-group">
                <label for="m-note">Note</label>
                <textarea id="m-note" v-model="modalForm.note" placeholder="e.g. Organic, from local farm" rows="2"></textarea>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="m-seller">Seller Name</label>
                  <input id="m-seller" v-model="modalForm.sellerName" type="text" placeholder="Seller name" />
                </div>
                <div class="form-group">
                  <label for="m-phone">Seller Phone</label>
                  <input id="m-phone" v-model="modalForm.sellerPhone" type="tel" placeholder="+91 XXXXX XXXXX" />
                </div>
              </div>
            </div>

            <div class="modal-footer">
              <button class="btn btn-secondary" @click="closeModal">Cancel</button>
              <button class="btn btn-primary" @click="confirmAddToInventory">➕ Add to Inventory</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.content-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 1.5rem;
  align-items: start;
}

.viewer-card {
  display: flex;
  flex-direction: column;
}

.viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.btn-stop {
  background: rgba(248, 113, 113, 0.15) !important;
  border-color: rgba(248, 113, 113, 0.3) !important;
  color: var(--danger) !important;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.82rem;
  color: var(--text-dim);
  background: rgba(255, 255, 255, 0.04);
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
  border: 1px solid var(--glass-border);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #475569;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.status-dot.active {
  background: var(--success);
  box-shadow: 0 0 8px var(--success);
}

.status-dot.processing {
  background: var(--warning);
  animation: pulse 1s infinite;
}

.status-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 220px;
}

/* ── Viewport ────────────────────────────── */
.viewport {
  background: rgba(0, 0, 0, 0.4);
  border-radius: 14px;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  aspect-ratio: 16 / 10;
  border: 2px dashed rgba(255, 255, 255, 0.08);
  transition: border-color 0.3s ease;
}

.viewport.clickable {
  cursor: pointer;
}

.viewport.clickable:hover {
  border-color: rgba(255, 106, 61, 0.4);
}

.media-element {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 14px;
}

/* ── Placeholder ────────────────────────── */
.placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-dim);
  text-align: center;
  padding: 2rem;
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.placeholder-icon {
  font-size: 3.5rem;
  margin-bottom: 1rem;
  opacity: 0.3;
}

.placeholder h3 {
  font-size: 1.05rem;
  font-weight: 600;
  margin-bottom: 0.4rem;
  color: var(--text-dim);
}

.placeholder p {
  font-size: 0.85rem;
  opacity: 0.6;
}

/* ── Results ─────────────────────────────── */
.results-card {
  display: flex;
  flex-direction: column;
}

.results-list {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  overflow-y: auto;
  max-height: 500px;
}

.det-item {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 12px;
  padding: 0.9rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  border: 1px solid transparent;
  transition: all 0.25s ease;
}

.det-item:hover {
  background: rgba(255, 106, 61, 0.06);
  border-color: rgba(255, 106, 61, 0.2);
  transform: translateX(3px);
}

.det-info {
  min-width: 0;
  flex: 1;
}

.det-info h4 {
  text-transform: capitalize;
  margin-bottom: 0.2rem;
  font-size: 0.95rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.det-quality {
  font-size: 0.8rem;
  font-weight: 600;
}

.meta {
  display: flex;
  gap: 0.75rem;
  font-size: 0.72rem;
  color: var(--text-dim);
  margin-top: 0.35rem;
  flex-wrap: wrap;
}

.btn-add {
  background: var(--primary-gradient);
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  color: white;
  cursor: pointer;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s ease;
}

.btn-add:hover {
  transform: scale(1.15) rotate(5deg);
  box-shadow: 0 4px 16px rgba(255, 106, 61, 0.4);
}

.empty-state {
  margin-top: 2rem;
  text-align: center;
  color: var(--text-dim);
}

.empty-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
  opacity: 0.4;
}

.empty-hint {
  font-size: 0.78rem;
  opacity: 0.6;
  margin-top: 0.3rem;
}

/* ── Responsive ──────────────────────────── */
@media (max-width: 1100px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .viewer-header {
    flex-direction: column;
    align-items: stretch;
  }
  .actions {
    width: 100%;
  }
  .actions .btn {
    flex: 1;
    font-size: 0.85rem;
    padding: 0.6rem 1rem;
  }
  .viewport {
    min-height: 260px;
    aspect-ratio: 4 / 3;
  }
}

/* ── Animations ──────────────────────────── */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ═══════════════════════════════════════════
   Modal
   ═══════════════════════════════════════════ */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.modal-card {
  background: #1a1a1a;
  border: 1px solid rgba(255, 106, 61, 0.25);
  border-radius: 20px;
  width: 100%;
  max-width: 480px;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.6), 0 0 40px rgba(255, 106, 61, 0.08);
  animation: modalPop 0.3s ease-out;
}

@keyframes modalPop {
  from { opacity: 0; transform: scale(0.92) translateY(20px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.modal-header h2 {
  font-size: 1.15rem;
  font-weight: 700;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.modal-close {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-dim);
  width: 32px;
  height: 32px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.modal-close:hover {
  background: rgba(248, 113, 113, 0.15);
  border-color: rgba(248, 113, 113, 0.3);
  color: #f87171;
}

.modal-detected {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
  background: rgba(255, 106, 61, 0.06);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.modal-food-name {
  font-weight: 700;
  font-size: 1rem;
  text-transform: capitalize;
}

.modal-quality {
  font-size: 0.8rem;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  white-space: nowrap;
}

.modal-body {
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow: hidden;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  min-width: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-width: 0;
}

.form-group label {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-group input, .form-group textarea {
  width: 100%;
  box-sizing: border-box;
  min-width: 0;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 0.6rem 0.75rem;
  color: var(--text-main);
  font-family: inherit;
  font-size: 0.88rem;
  outline: none;
  transition: border-color 0.25s ease, box-shadow 0.25s ease;
}
.form-group textarea {
  resize: vertical;
  min-height: 60px;
}

.form-group input::placeholder, .form-group textarea::placeholder {
  color: rgba(255, 255, 255, 0.2);
}

.form-group input:focus, .form-group textarea:focus {
  border-color: rgba(255, 106, 61, 0.5);
  box-shadow: 0 0 0 3px rgba(255, 106, 61, 0.1);
}

/* Remove number input spinners for cleaner look */
.form-group input[type="number"]::-webkit-inner-spin-button,
.form-group input[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.form-group input[type="number"] {
  -moz-appearance: textfield;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.modal-footer .btn {
  padding: 0.6rem 1.3rem;
  font-size: 0.88rem;
}

/* Modal transitions */
.modal-enter-active { transition: opacity 0.25s ease; }
.modal-leave-active { transition: opacity 0.2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }

@media (max-width: 520px) {
  .modal-card { max-width: 100%; border-radius: 16px; }
  .modal-header { padding: 1rem 1.25rem; }
  .modal-detected { padding: 0.65rem 1.25rem; }
  .modal-body { padding: 1rem 1.25rem; }
  .form-row { grid-template-columns: 1fr; }
  .modal-footer {
    flex-direction: column;
    padding: 0.75rem 1.25rem;
  }
  .modal-footer .btn { width: 100%; justify-content: center; }
}
</style>
