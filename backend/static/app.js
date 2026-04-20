// DOM Elements - Navigation & Mobile
const sidebar = document.getElementById('sidebar');
const openMenuBtn = document.getElementById('openMenuBtn');
const closeMenuBtn = document.getElementById('closeMenuBtn');
const navLinks = document.querySelectorAll('.nav-link');
const pageViews = document.querySelectorAll('.page-view');

// DOM Elements - Camera & Detection
const webcam = document.getElementById('webcam');
const canvas = document.getElementById('outputCanvas');
const ctx = canvas.getContext('2d');
const webcamBtn = document.getElementById('webcamBtn');
const uploadBtn = document.getElementById('uploadBtn');
const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const statusText = document.getElementById('statusText');
const detectionsList = document.getElementById('detectionsList');

// Global State
let isWebcamStarted = false;
let stream = null;
let intervalId = null;
let currentImage = null;
let wasteChartInstance = null;
let activePageId = 'dashboard';

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    
    // Initial fetch for the active page
    if(activePageId === 'dashboard') {
        // Just UI setup, no data to fetch yet until stream starts
    }
});

// ─── SPA Navigation Logic ──────────────────────────────────────────
function navigateTo(targetId) {
    // Stop camera to save battery if we leave the dashboard
    if (activePageId === 'dashboard' && targetId !== 'dashboard' && isWebcamStarted) {
        stopWebcam();
    }
    
    activePageId = targetId;
    
    // Update active nav link
    navLinks.forEach(link => {
        if (link.dataset.target === targetId) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // Animate page transition
    pageViews.forEach(page => {
        page.classList.remove('active');
        if (page.id === `page-${targetId}`) {
            page.classList.add('active');
        }
    });

    // Close mobile menu on navigate
    sidebar.classList.remove('open');

    // Trigger specific page data fetch
    switch(targetId) {
        case 'inventory':
            fetchInventory();
            break;
        case 'grocery':
            fetchGrocery();
            break;
        case 'waste':
            fetchWaste();
            break;
        case 'stock':
            fetchTransactions();
            break;
    }
}

navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const target = link.dataset.target;
        navigateTo(target);
    });
});

// Mobile Menu toggles
openMenuBtn.addEventListener('click', () => sidebar.classList.add('open'));
closeMenuBtn.addEventListener('click', () => sidebar.classList.remove('open'));

// ─── Canvas Helper ─────────────────────────────────────────────────
function resizeCanvas() {
    if (!canvas || !canvas.offsetWidth) return;
    const wasImage = currentImage;
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    if (wasImage) drawImageToCanvas(wasImage);
}
window.addEventListener('resize', resizeCanvas);
setTimeout(resizeCanvas, 100);

function drawImageToCanvas(img) {
    const hRatio = canvas.width / img.width;
    const vRatio = canvas.height / img.height;
    const ratio = Math.min(hRatio, vRatio);
    const cx = (canvas.width - img.width * ratio) / 2;
    const cy = (canvas.height - img.height * ratio) / 2;
    ctx.drawImage(img, 0, 0, img.width, img.height, cx, cy, img.width * ratio, img.height * ratio);
}

// ─── Data Fetching ─────────────────────────────────────────────────

async function fetchInventory() {
    try {
        const res = await fetch('/inventory/list');
        const data = await res.json();
        const tbody = document.getElementById('inventoryBody');
        tbody.innerHTML = '';

        if (!data.inventory || data.inventory.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="empty-state">Inventory is empty</td></tr>';
            return;
        }

        data.inventory.forEach(item => {
            const expDate = new Date(item.expiry_date).toLocaleDateString();
            const fScore = item.freshness_score !== undefined ? item.freshness_score : 100; // fallback just in case
            const freshnessColor = fScore > 70 ? 'var(--quality-fresh)' : fScore > 30 ? 'var(--quality-avg)' : 'var(--quality-bad)';
            
            const price = parseFloat(item.price_per_unit) || 0.0;
            const totalVal = (price * item.quantity).toFixed(2);

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <strong style="font-size: 1.05rem;">${item.food_name}</strong>
                    <div style="font-size: 0.8rem; color: var(--text-dim)">Qty: ${item.quantity}</div>
                </td>
                <td>
                    <strong>$${totalVal}</strong>
                    <div style="font-size: 0.8rem; color: var(--text-dim)">$${price.toFixed(2)}/ea</div>
                </td>
                <td>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span>${fScore}%</span>
                        <div class="progress-container">
                            <div class="progress-bar" style="width: ${fScore}%; background: ${freshnessColor}"></div>
                        </div>
                    </div>
                </td>
                <td>
                    <div style="font-weight: 600;">${item.status}</div>
                    <div style="font-size: 0.85rem; color: var(--text-dim)">Exp: ${expDate}</div>
                </td>
                <td>
                    <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
                        <button class="btn-small" style="background:rgba(16,185,129,0.2); color:#10b981; border:1px solid #10b981;" onclick="openSellModal('${item._id}', '${item.food_name}', ${item.quantity})">💰 Sell</button>
                        ${item.notes ? `<button class="btn-small" style="background:rgba(59,130,246,0.2); color:#3b82f6; border:1px solid #3b82f6;" onclick="openNoteModal('${escapeString(item.notes)}')">📝 Note</button>` : ''}
                        <button class="btn-trash" onclick="moveToWaste('${item._id}', '${item.food_name}')">🗑️ Discard</button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) { console.error("Error fetching inventory", e); }
}

async function fetchGrocery() {
    try {
        const res = await fetch('/grocery/list');
        const data = await res.json();
        const ul = document.getElementById('groceryList');
        ul.innerHTML = '';

        if (!data.grocery_list || data.grocery_list.length === 0) {
            ul.innerHTML = '<p class="empty-state">Nothing to buy! Your kitchen is fully stocked.</p>';
            return;
        }

        let overallCost = 0;
        data.grocery_list.forEach(item => {
            let itemPrice = parseFloat(item.estimated_price) || 0.0;
            let totalItemPrice = itemPrice * item.quantity;
            overallCost += totalItemPrice;
            
            const li = document.createElement('li');
            li.innerHTML = `
                <div style="flex: 1;">
                   <div style="display:flex; justify-content:space-between; align-items:center;">
                       <span style="font-size: 1.1rem; font-weight:700; color:var(--text-main);">${item.food_name}</span>
                       <span style="font-weight:600; color:var(--accent);">x${item.quantity}</span>
                   </div>
                   <div style="font-size: 0.85rem; color: var(--text-dim); margin-top: 4px;">
                       Est. $${totalItemPrice.toFixed(2)} ($${itemPrice.toFixed(2)}/unit)
                   </div>
                   ${item.notes ? `<div style="font-size: 0.8rem; font-style: italic; color: var(--quality-avg); margin-top: 5px;">📝 ${item.notes}</div>` : ''}
                </div>
                <button class="btn-small" onclick="markPurchased('${item._id}')" style="margin-left: 15px;">✅ Purchased</button>
            `;
            ul.appendChild(li);
        });
        
        // Append Total Summary if items exist
        if (overallCost > 0) {
           const sumLi = document.createElement('li');
           sumLi.className = "summary-li";
           sumLi.style.borderTop = "2px solid var(--glass-border)";
           sumLi.style.marginTop = "15px";
           sumLi.style.paddingTop = "15px";
           sumLi.innerHTML = `
                <span style="font-weight:700;">TOTAL ESTIMATED BILL:</span>
                <span style="font-size: 1.2rem; font-weight:800; color:var(--quality-fresh);">$${overallCost.toFixed(2)}</span>
           `;
           ul.appendChild(sumLi);
        }
    } catch (e) { console.error(e); }
}

function initChart() {
    const ctxChart = document.getElementById('wasteChart');
    if(!ctxChart) return;
    
    wasteChartInstance = new Chart(ctxChart.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: ['Expired Naturally', 'User Discarded', 'Consumed Total'], 
            datasets: [{
                data: [1, 1, 1], // Placeholder until dynamic counts are generated in a future backend update
                backgroundColor: ['#ef4444', '#facc15', '#4ade80'],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'right', labels: {color: '#f0f0f5', font:{family:'Outfit'}} } }
        }
    });
}

async function fetchWaste() {
    try {
        const res = await fetch('/waste/list');
        const data = await res.json();
        const ul = document.getElementById('wasteList');
        ul.innerHTML = '';
        
        let expired = 0, discarded = 0;
        
        if (!data.waste_logs || data.waste_logs.length === 0) {
            ul.innerHTML = '<p class="empty-state">No waste logged yet. Great job!</p>';
            if(wasteChartInstance) {
               wasteChartInstance.data.datasets[0].data = [0, 0, 10]; // 100% consumed visually if no waste
               wasteChartInstance.update();
            }
            return;
        }

        let totalWasteValue = 0.0;
        data.waste_logs.forEach(item => {
            if(item.reason === "expired") expired++;
            if(item.reason === "user_discarded") discarded++;
            totalWasteValue += parseFloat(item.total_value) || 0.0;
        });

        // Update basic chart logic
        if(wasteChartInstance) {
            wasteChartInstance.data.datasets[0].data = [expired, discarded, Math.max(1, (expired+discarded)*3)];
            wasteChartInstance.update();
        }

        const summary = document.createElement('div');
        summary.innerHTML = `<h4 style="margin-bottom: 1rem; color: var(--quality-bad)">Total Value Wasted: $${totalWasteValue.toFixed(2)}</h4>`;
        ul.appendChild(summary);

        data.waste_logs.slice(0, 10).forEach(item => { 
            const date = new Date(item.logged_date).toLocaleDateString();
            const val = parseFloat(item.total_value) || 0.0;
            const reasonStyled = item.reason === 'expired' ? '<span style="color:var(--quality-bad)">Expired Auto-Removal</span>' : '<span style="color:var(--quality-avg)">Manual Discard</span>';
            const li = document.createElement('li');
            li.innerHTML = `
                <div style="display:flex; flex-direction:column; gap:0.2rem">
                    <span style="font-weight:600;">${item.food_name} (x${item.quantity || 1})</span>
                    <span style="color:var(--quality-bad); font-weight:700;">-$${val.toFixed(2)}</span>
                </div>
                <span style="font-size: 0.8rem; text-align:right;">${reasonStyled} <br> ${date}</span>
            `;
            ul.appendChild(li);
        });
    } catch (e) { console.error(e); }
}

let financeChartInstance = null;

async function fetchTransactions() {
    try {
        const res = await fetch('/transactions/list');
        const data = await res.json();
        
        const tbody = document.getElementById('transactionList');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (!data.transactions_log || data.transactions_log.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 2rem;">No financial data yet. Add or sell items to see history.</td></tr>';
            return;
        }

        let totalExpense = 0;
        let totalRevenue = 0;

        data.transactions_log.forEach(tx => {
            const date = new Date(tx.date).toLocaleDateString();
            const isRevenue = tx.type === 'STOCK_OUT_SALE';
            const isLoss = tx.type === 'STOCK_OUT_WASTE';
            const val = parseFloat(tx.total_value) || 0.0;

            if (tx.type === 'STOCK_IN') totalExpense += val;
            if (isRevenue) totalRevenue += val;

            const valStr = isRevenue ? `+$${val.toFixed(2)}` : `-$${val.toFixed(2)}`;
            const valColor = isRevenue ? '#10b981' : (isLoss ? 'var(--quality-bad)' : 'var(--quality-avg)');
            const typeStr = isRevenue ? 'SALE' : (tx.type === 'STOCK_IN' ? 'PURCHASE' : 'WASTE');

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${date}</td>
                <td style="font-weight:600; font-size:0.8rem;">${typeStr}</td>
                <td>${tx.food_name} (x${tx.quantity})</td>
                <td style="color:${valColor}; font-weight:bold;">${valStr}</td>
            `;
            tbody.appendChild(tr);
        });

        // Update Finance Chart
        const ctx = document.getElementById('financeChart');
        if (ctx) {
            if (financeChartInstance) {
                financeChartInstance.destroy();
            }
            financeChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Purchases (Out)', 'Sales (In)'],
                    datasets: [{
                        label: 'Amount ($)',
                        data: [totalExpense, totalRevenue],
                        backgroundColor: ['rgba(250, 204, 21, 0.7)', 'rgba(16, 185, 129, 0.7)'],
                        borderColor: ['#facc15', '#10b981'],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, ticks: { color: '#8892b0' } },
                        x: { ticks: { color: '#8892b0' } }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        }
    } catch (e) { console.error(e); }
}


// ─── Actions & Modals ──────────────────────────────────────────────

// Modal logic
const inventoryModal = document.getElementById('inventoryModal');
const modalTitle = document.getElementById('modalTitle');
const modalConfirmBtn = document.getElementById('modalConfirmBtn');
const modalQty = document.getElementById('modalQty');
const modalNotes = document.getElementById('modalNotes');

const sellModal = document.getElementById('sellModal');
const sellModalTitle = document.getElementById('sellModalTitle');
const sellModalQty = document.getElementById('sellModalQty');
const sellModalPrice = document.getElementById('sellModalPrice');
const sellModalConfirmBtn = document.getElementById('sellModalConfirmBtn');

const noteModal = document.getElementById('noteModal');
const noteModalText = document.getElementById('noteModalText');

const groceryModal = document.getElementById('groceryModal');
const gModalName = document.getElementById('gModalName');
const gModalQty = document.getElementById('gModalQty');
const gModalPrice = document.getElementById('gModalPrice');
const gModalNotes = document.getElementById('gModalNotes');
const gModalConfirmBtn = document.getElementById('gModalConfirmBtn');

let pendingInventoryItem = null;
let pendingSellItem = null;

function escapeString(str) {
    return str.replace(/'/g, "\\'").replace(/"/g, "&quot;");
}

function closeInventoryModal() {
    inventoryModal.classList.remove('active');
    pendingInventoryItem = null;
}

function closeSellModal() {
    sellModal.classList.remove('active');
    pendingSellItem = null;
}

function closeNoteModal() {
    noteModal.classList.remove('active');
}

function openNoteModal(message) {
    noteModalText.innerText = message;
    noteModal.classList.add('active');
}

function openGroceryModal() {
    gModalName.value = '';
    gModalQty.value = 1;
    gModalPrice.value = '0.00';
    gModalNotes.value = '';
    groceryModal.classList.add('active');
}

function closeGroceryModal() {
    groceryModal.classList.remove('active');
}

gModalConfirmBtn.addEventListener('click', async () => {
    const name = gModalName.value.trim();
    if(!name) {
        alert("Please enter an item name");
        return;
    }

    const qty = parseInt(gModalQty.value) || 1;
    const price = parseFloat(gModalPrice.value) || 0;
    const notes = gModalNotes.value.trim();

    try {
        await fetch('/grocery/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                food_name: name,
                quantity: qty,
                estimated_price: price,
                notes: notes
            })
        });
        closeGroceryModal();
        fetchGrocery();
    } catch (e) {
        console.error(e);
        alert("Failed to add grocery item");
    }
});

function openSellModal(id, name, maxQty) {
    pendingSellItem = { id, name };
    sellModalTitle.innerText = `Sell ${name}`;
    sellModalQty.max = maxQty;
    sellModalQty.value = 1;
    sellModalPrice.value = '0.00';
    sellModal.classList.add('active');
}

sellModalConfirmBtn.addEventListener('click', async () => {
    if(!pendingSellItem) return;
    
    const qtyToSell = parseInt(sellModalQty.value) || 1;
    let pricePerUnit = parseFloat(sellModalPrice.value);
    if(isNaN(pricePerUnit)) pricePerUnit = 0.0;
    
    try {
        const res = await fetch('/inventory/sell', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                item_id: pendingSellItem.id,
                quantity: qtyToSell,
                sell_price: pricePerUnit
            })
        });
        
        closeSellModal();
        if(activePageId === 'inventory') fetchInventory();
        else if(activePageId === 'stock') fetchTransactions();
        
    } catch (e) {
        console.error(e);
        alert("Failed to sell item.");
    }
});

function addToInventory(name, freshness, status, expiry) {
    pendingInventoryItem = { name, freshness, status, expiry };
    
    // Populate Modal Details
    modalTitle.innerText = `Add ${name} to Inventory`;
    modalQty.value = 1;
    if(modalNotes) modalNotes.value = '';
    document.getElementById('modalPrice').value = '0.00';
    
    // Show Modal
    inventoryModal.classList.add('active');
}

// Bind modal confirm button
modalConfirmBtn.addEventListener('click', async () => {
    if (!pendingInventoryItem) return;
    
    const quantity = parseInt(modalQty.value) || 1;
    let price = parseFloat(document.getElementById('modalPrice').value);
    if (isNaN(price)) price = 0.0;
    
    const notesValue = modalNotes ? modalNotes.value.trim() : "";
    const finalExpiry = pendingInventoryItem.expiry;
    const { name, freshness, status } = pendingInventoryItem;

    try {
        await fetch('/inventory/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                food_name: name,
                freshness_score: freshness,
                status: status,
                expiry_days: finalExpiry,
                quantity: quantity,
                price_per_unit: price,
                notes: notesValue
            })
        });
        
        closeInventoryModal();

        const toast = document.createElement('div');
        toast.innerHTML = `<span style="background:var(--quality-fresh); color:var(--bg-dark); padding:10px 20px; border-radius:10px; position:fixed; top:20px; right:20px; z-index:9999; font-weight:bold;">✅ Added ${quantity}x ${name} to Inventory!</span>`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);

        if(activePageId === 'inventory') fetchInventory();

    } catch (e) {
        console.error(e);
        alert("Failed to add to database.");
    }
});

async function moveToWaste(id, name) {
    if(!confirm(`Discard ${name}?`)) return;
    try {
        await fetch('/waste/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: id, food_name: name, reason: 'user_discarded' })
        });
        fetchInventory(); // refresh list
    } catch (e) { console.error(e); }
}

async function markPurchased(id) {
    try {
        await fetch('/grocery/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: id })
        });
        fetchGrocery();
    } catch (e) { console.error(e); }
}

// ─── Webcam & Frame Processing ─────────────────────────────────────
async function startWebcam() {
    currentImage = null;
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        webcam.srcObject = stream;
        webcam.hidden = false;
        dropZone.style.display = 'none';
        isWebcamStarted = true;
        webcamBtn.innerHTML = '<span class="icon">⏹</span> Stop Stream';
        webcamBtn.style.color = "var(--quality-bad)";
        webcamBtn.style.borderColor = "var(--quality-bad)";
        
        statusText.innerText = "Analyzing Live Feed...";
        intervalId = setInterval(processFrame, 800); 
    } catch (err) {
        console.error(err);
        alert("Could not access webcam.");
    }
}

function stopWebcam() {
    if (stream) stream.getTracks().forEach(track => track.stop());
    clearInterval(intervalId);
    isWebcamStarted = false;
    webcam.hidden = true;
    webcamBtn.innerHTML = '<span class="icon">📷</span> Webcam';
    webcamBtn.style.color = "";
    webcamBtn.style.borderColor = "";

    if (!currentImage) dropZone.style.display = 'flex';
    statusText.innerText = "Ready";
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

async function processFrame() {
    if (!isWebcamStarted || activePageId !== 'dashboard') return;
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = webcam.videoWidth;
    tempCanvas.height = webcam.videoHeight;
    const tCtx = tempCanvas.getContext('2d');
    tCtx.drawImage(webcam, 0, 0);

    tempCanvas.toBlob(async (blob) => {
        await sendToPredict(blob, webcam.videoWidth, webcam.videoHeight);
    }, 'image/jpeg', 0.8);
}

// ─── AI API Logic ──────────────────────────────────────────────────
async function sendToPredict(blob, originalWidth, originalHeight) {
    const formData = new FormData();
    formData.append('file', blob, 'frame.jpg');

    try {
        const response = await fetch('/predict', { method: 'POST', body: formData });
        const data = await response.json();
        renderDetections(data.detections, originalWidth, originalHeight);
    } catch (err) {
        console.error("Predict Error:", err);
    }
}

function getQualityBadgeClass(freshness) {
    const f = Number(freshness);
    if (isNaN(f) || f > 70) return 'quality-fresh';
    if (f > 30) return 'quality-average';
    return 'quality-spoiled';
}

function renderDetections(detections, originalWidth, originalHeight) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    let scaleX, scaleY, offsetX = 0, offsetY = 0;

    if (currentImage) {
        const hRatio = canvas.width / currentImage.width;
        const vRatio = canvas.height / currentImage.height;
        const ratio = Math.min(hRatio, vRatio);
        offsetX = (canvas.width - currentImage.width * ratio) / 2;
        offsetY = (canvas.height - currentImage.height * ratio) / 2;
        ctx.drawImage(currentImage, 0, 0, currentImage.width, currentImage.height,
            offsetX, offsetY, currentImage.width * ratio, currentImage.height * ratio);
        scaleX = ratio;
        scaleY = ratio;
    } else {
        scaleX = canvas.width / originalWidth;
        scaleY = canvas.height / originalHeight;
    }

    detectionsList.innerHTML = '';
    if (!detections || detections.length === 0) {
        detectionsList.innerHTML = '<p class="empty-state">No food detected</p>';
        return;
    }

    const uniqueDetections = {};

    detections.forEach(det => {
        const [x1, y1, x2, y2] = det.box;
        const colorCode = det.color_code || '#ff4d00';
        uniqueDetections[det.food_name] = det; 

        const rectX = x1 * scaleX + offsetX;
        const rectY = y1 * scaleY + offsetY;
        const rectW = (x2 - x1) * scaleX;
        const rectH = (y2 - y1) * scaleY;

        ctx.strokeStyle = colorCode;
        ctx.lineWidth = 3;
        ctx.strokeRect(rectX, rectY, rectW, rectH);

        const scoreSafe = det.freshness_score !== undefined ? det.freshness_score : '??';
        const labelText = `${det.food_name} ${scoreSafe}%`;
        ctx.font = 'bold 14px Outfit';
        const textWidth = ctx.measureText(labelText).width;
        ctx.fillStyle = colorCode;
        ctx.fillRect(rectX, rectY - 24, textWidth + 10, 24);
        ctx.fillStyle = '#fff';
        ctx.fillText(labelText, rectX + 5, rectY - 7);
    });

    // Render Sidebar list uniquely
    Object.values(uniqueDetections).forEach(det => {
        const scoreSafe = det.freshness_score !== undefined ? det.freshness_score : 100;
        const statusSafe = det.status || "Unknown Status";
        const expirySafe = det.expiry_days !== undefined ? det.expiry_days : '??';
        
        const badgeClass = getQualityBadgeClass(scoreSafe);
        const item = document.createElement('div');
        item.className = 'detection-item';
        item.style.borderLeftColor = det.color_code || '#4ade80';
        item.innerHTML = `
            <div class="det-header">
                <span class="det-label">${det.food_name}</span>
                <span class="quality-badge ${badgeClass}">${scoreSafe}% Fresh</span>
            </div>
            <span class="det-meta">Status: ${statusSafe} | Expiry: ~${expirySafe} days</span>
            <button class="btn-add" onclick="addToInventory('${det.food_name}', ${scoreSafe}, '${statusSafe}', ${expirySafe})">
                + Add to Inventory
            </button>
        `;
        detectionsList.appendChild(item);
    });
}

// ─── Files and Drag/Drop ───────────────────────────────────────────
if(webcamBtn) webcamBtn.addEventListener('click', () => isWebcamStarted ? stopWebcam() : startWebcam());
if(uploadBtn) uploadBtn.addEventListener('click', () => fileInput.click());

if(fileInput) {
    fileInput.addEventListener('change', (e) => {
        if (e.target.files[0]) handleImageUpload(e.target.files[0]);
    });
}

if(dropZone) {
    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('active'); });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('active'));
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('active');
        if (e.dataTransfer.files[0]) handleImageUpload(e.dataTransfer.files[0]);
    });
    dropZone.addEventListener('click', () => fileInput.click());
}

async function handleImageUpload(file) {
    if (stream) stream.getTracks().forEach(track => track.stop());
    clearInterval(intervalId);
    isWebcamStarted = false;
    webcam.hidden = true;
    webcamBtn.innerHTML = '<span class="icon">📷</span> Webcam';
    dropZone.style.display = 'none';
    statusText.innerText = "Processing Image...";

    const reader = new FileReader();
    reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
            currentImage = img;
            resizeCanvas(); // ensure dimensions fit
            drawImageToCanvas(img);
            sendToPredict(file, img.width, img.height);
            statusText.innerText = "Analysis Complete";
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}
