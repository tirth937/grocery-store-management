import os
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from ultralytics import YOLO
import uvicorn
from quality_analyzer import get_quality_info

app = FastAPI()

# ─── Model Loading ─────────────────────────────────────────────────
# Priority: custom quality model > custom detection model > base YOLO
QUALITY_MODEL_PATH = "food_quality_model/weights/best.pt"
DETECTION_MODEL_PATH = "food_detection_v11/train_run/weights/best.pt"

is_custom_quality_model = False
is_base_model = True

if os.path.exists(QUALITY_MODEL_PATH):
    print(f"✅ Loading custom QUALITY model from {QUALITY_MODEL_PATH}")
    model = YOLO(QUALITY_MODEL_PATH)
    is_custom_quality_model = True
    is_base_model = False
elif os.path.exists(DETECTION_MODEL_PATH):
    print(f"📦 Loading custom DETECTION model from {DETECTION_MODEL_PATH}")
    model = YOLO(DETECTION_MODEL_PATH)
    is_base_model = False
else:
    print("⚠️  No custom model found. Loading base YOLOv11n model with heuristic quality analysis.")
    model = YOLO("yolo11n.pt")
    is_base_model = True

# Food classes in COCO that the base model can detect
FOOD_CLASSES = {
    'banana', 'apple', 'sandwich', 'orange', 'broccoli',
    'carrot', 'hot dog', 'pizza', 'donut', 'cake'
}

# Create static directory if it doesn't exist
if not os.path.exists("static"):
    os.makedirs("static")


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Run inference
        results = model.predict(img, conf=0.25)

        detections = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                b = box.xyxy[0].tolist()
                c = box.cls.item()
                s = box.conf.item()
                class_name = model.names[int(c)]

                # Filter non-food items when using base model
                if is_base_model and class_name not in FOOD_CLASSES:
                    continue

                # ── Quality Analysis ───────────────────────────────
                quality_info = get_quality_info(
                    class_name=class_name,
                    img=img,
                    box=b,
                    is_custom_model=is_custom_quality_model,
                )

                detections.append({
                    "food_name": quality_info["food_name"],
                    "box": b,
                    "confidence": round(s, 3),
                    "quality_label": quality_info["quality_label"],
                    "recommendation": quality_info["recommendation"],
                    "shelf_life_days": quality_info["shelf_life_days"],
                    "color_code": quality_info["color_code"],
                    # Keep legacy field for backward compat
                    "class": quality_info["food_name"],
                })

        return JSONResponse(content={"detections": detections})
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Serve static files (no-cache for development)
from starlette.staticfiles import StaticFiles as StarletteStatic
from starlette.responses import Response

class NoCacheStaticFiles(StarletteStatic):
    """Static files middleware that sets no-cache headers to prevent stale JS/CSS."""
    async def __call__(self, scope, receive, send):
        async def send_with_no_cache(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                # Add cache control headers
                new_headers = list(message.get("headers", []))
                new_headers.append((b"cache-control", b"no-cache, no-store, must-revalidate"))
                new_headers.append((b"pragma", b"no-cache"))
                message["headers"] = new_headers
            await send(message)
        await super().__call__(scope, receive, send_with_no_cache)

app.mount("/", NoCacheStaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Food Quality Detection Server at http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
