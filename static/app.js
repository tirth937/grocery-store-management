const webcam = document.getElementById('webcam');
const canvas = document.getElementById('outputCanvas');
const ctx = canvas.getContext('2d');
const webcamBtn = document.getElementById('webcamBtn');
const uploadBtn = document.getElementById('uploadBtn');
const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const statusText = document.getElementById('statusText');
const detectionsList = document.getElementById('detectionsList');

let isWebcamStarted = false;
let stream = null;
let intervalId = null;
let currentImage = null; // Store uploaded image for redrawing

// Initialize canvas size
function resizeCanvas() {
    const wasImage = currentImage;
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    // Redraw image after resize if one was loaded
    if (wasImage) {
        drawImageToCanvas(wasImage);
    }
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

// ─── Draw image scaled to fit canvas ───────────────────────────────
function drawImageToCanvas(img) {
    const hRatio = canvas.width / img.width;
    const vRatio = canvas.height / img.height;
    const ratio = Math.min(hRatio, vRatio);
    const cx = (canvas.width - img.width * ratio) / 2;
    const cy = (canvas.height - img.height * ratio) / 2;
    ctx.drawImage(img, 0, 0, img.width, img.height, cx, cy, img.width * ratio, img.height * ratio);
}

// ─── Webcam Logic ──────────────────────────────────────────────────
async function startWebcam() {
    currentImage = null;
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        webcam.srcObject = stream;
        webcam.hidden = false;
        dropZone.style.display = 'none';
        isWebcamStarted = true;
        webcamBtn.innerHTML = '<span class="icon">⏹</span> Stop';
        statusText.innerText = "Analyzing Live Feed...";

        intervalId = setInterval(processFrame, 600);
    } catch (err) {
        console.error("Webcam error:", err);
        alert("Could not access webcam.");
    }
}

function stopWebcam() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    clearInterval(intervalId);
    isWebcamStarted = false;
    webcam.hidden = true;
    webcamBtn.innerHTML = '<span class="icon">📷</span> Webcam';
    // Only re-show drop zone if no uploaded image is displayed
    if (!currentImage) {
        dropZone.style.display = 'flex';
    }
    statusText.innerText = "Ready";
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

// ─── Frame Processing ──────────────────────────────────────────────
async function processFrame() {
    if (!isWebcamStarted) return;

    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = webcam.videoWidth;
    tempCanvas.height = webcam.videoHeight;
    const tCtx = tempCanvas.getContext('2d');
    tCtx.drawImage(webcam, 0, 0);

    tempCanvas.toBlob(async (blob) => {
        await sendToPredict(blob, webcam.videoWidth, webcam.videoHeight);
    }, 'image/jpeg', 0.8);
}

// ─── API Logic ─────────────────────────────────────────────────────
async function sendToPredict(blob, originalWidth, originalHeight) {
    const formData = new FormData();
    formData.append('file', blob, 'frame.jpg');

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        renderDetections(data.detections, originalWidth, originalHeight);
    } catch (err) {
        console.error("Prediction error:", err);
    }
}

// ─── Quality Color Helper ──────────────────────────────────────────
function getQualityBadgeClass(label) {
    const l = label.toLowerCase();
    if (l === 'fresh' || l === 'ripe' || l === 'good') return 'quality-fresh';
    if (l === 'average' || l === 'overripe' || l === 'stale') return 'quality-average';
    return 'quality-spoiled';
}

// ─── Rendering ─────────────────────────────────────────────────────
function renderDetections(detections, originalWidth, originalHeight) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    let scaleX, scaleY, offsetX = 0, offsetY = 0;

    if (currentImage) {
        // Uploaded image mode: redraw the image first
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
        // Webcam mode
        scaleX = canvas.width / originalWidth;
        scaleY = canvas.height / originalHeight;
    }

    detectionsList.innerHTML = '';

    if (!detections || detections.length === 0) {
        detectionsList.innerHTML = '<p class="empty-state">No food detected</p>';
        return;
    }

    detections.forEach(det => {
        const [x1, y1, x2, y2] = det.box;
        const confidence = (det.confidence * 100).toFixed(1);
        const colorCode = det.color_code || '#ff4d00';
        const foodName = det.food_name || det.class;
        const qualityLabel = det.quality_label || 'Unknown';
        const recommendation = det.recommendation || '';
        const shelfLife = det.shelf_life_days;

        const rectX = x1 * scaleX + offsetX;
        const rectY = y1 * scaleY + offsetY;
        const rectW = (x2 - x1) * scaleX;
        const rectH = (y2 - y1) * scaleY;

        // ── Draw color-coded bounding box ──────────────────────
        ctx.strokeStyle = colorCode;
        ctx.lineWidth = 3;
        ctx.shadowColor = colorCode;
        ctx.shadowBlur = 8;
        ctx.strokeRect(rectX, rectY, rectW, rectH);
        ctx.shadowBlur = 0;

        // ── Draw label background ──────────────────────────────
        const labelText = `${foodName} · ${qualityLabel} ${confidence}%`;
        ctx.font = 'bold 13px Outfit';
        const textWidth = ctx.measureText(labelText).width;
        const labelHeight = 26;
        const labelY = rectY - labelHeight;

        // Rounded rect background
        ctx.fillStyle = colorCode;
        ctx.beginPath();
        const r = 6;
        ctx.moveTo(rectX + r, labelY);
        ctx.lineTo(rectX + textWidth + 14 - r, labelY);
        ctx.quadraticCurveTo(rectX + textWidth + 14, labelY, rectX + textWidth + 14, labelY + r);
        ctx.lineTo(rectX + textWidth + 14, labelY + labelHeight);
        ctx.lineTo(rectX, labelY + labelHeight);
        ctx.lineTo(rectX, labelY + r);
        ctx.quadraticCurveTo(rectX, labelY, rectX + r, labelY);
        ctx.fill();

        // ── Draw label text ────────────────────────────────────
        ctx.fillStyle = '#fff';
        ctx.fillText(labelText, rectX + 7, labelY + 17);

        // ── Add to sidebar ─────────────────────────────────────
        const badgeClass = getQualityBadgeClass(qualityLabel);
        const item = document.createElement('div');
        item.className = 'detection-item';
        item.style.borderLeftColor = colorCode;
        item.innerHTML = `
            <div class="det-header">
                <span class="det-label">${foodName}</span>
                <span class="quality-badge ${badgeClass}">${qualityLabel}</span>
            </div>
            <span class="det-meta">Confidence: ${confidence}%</span>
            <span class="det-recommendation">${recommendation}</span>
            ${shelfLife !== undefined ? `<span class="det-shelf">🕐 Shelf Life: ~${shelfLife} day${shelfLife !== 1 ? 's' : ''}</span>` : ''}
        `;
        detectionsList.appendChild(item);
    });
}

// ─── Event Listeners ───────────────────────────────────────────────
webcamBtn.addEventListener('click', () => {
    if (isWebcamStarted) stopWebcam();
    else startWebcam();
});

uploadBtn.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleImageUpload(file);
});

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('active');
});

dropZone.addEventListener('dragleave', () => dropZone.classList.remove('active'));

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('active');
    const file = e.dataTransfer.files[0];
    if (file) handleImageUpload(file);
});

dropZone.addEventListener('click', () => fileInput.click());

// ─── Image Upload Handler ──────────────────────────────────────────
async function handleImageUpload(file) {
    // Stop webcam without re-showing the drop zone
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    clearInterval(intervalId);
    isWebcamStarted = false;
    webcam.hidden = true;
    webcamBtn.innerHTML = '<span class="icon">📷</span> Webcam';

    // Hide drop zone IMMEDIATELY
    dropZone.style.display = 'none';
    statusText.innerText = "Processing Image...";

    const reader = new FileReader();
    reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
            currentImage = img;

            // Re-sync canvas buffer to display size
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;

            ctx.clearRect(0, 0, canvas.width, canvas.height);
            drawImageToCanvas(img);

            // Send to API
            sendToPredict(file, img.width, img.height);
            statusText.innerText = "Analysis Complete";
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}
