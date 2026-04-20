import os
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, Body, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import uvicorn
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from quality_analyzer import get_quality_info
import database as db
import jwt
from datetime import datetime, timedelta

# --- Background Task Scheduler ---
scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', hours=1)
async def scheduled_expiry_check():
    await db.process_expiries()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the scheduler
    scheduler.start()
    # Run an initial check on startup
    await db.process_expiries()
    yield
    scheduler.shutdown()

# --- Auth Configuration ---
SECRET_KEY = "super-secret-key-change-it" # In production use environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"id": user_id, "email": payload.get("sub")}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

app = FastAPI(lifespan=lifespan)

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; refine for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Model Loading ─────────────────────────────────────────────────
# Update paths to be relative to the script base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUALITY_MODEL_PATH = os.path.join(BASE_DIR, "food_quality_model/weights/best.pt")
DETECTION_MODEL_PATH = os.path.join(BASE_DIR, "food_detection_v11/train_run/weights/best.pt")
BASE_YOLO_PATH = os.path.join(BASE_DIR, "yolo11n.pt")

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
    print(f"⚠️ No custom model found. Loading base YOLOv11n model from {BASE_YOLO_PATH}")
    model = YOLO(BASE_YOLO_PATH)
    is_base_model = True

FOOD_CLASSES = {
    'banana', 'apple', 'sandwich', 'orange', 'broccoli',
    'carrot', 'hot dog', 'pizza', 'donut', 'cake'
}

# ─── Prediction API ────────────────────────────────────────────────
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        results = model.predict(img, conf=0.25)
        detections = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                b = box.xyxy[0].tolist()
                c = box.cls.item()
                s = box.conf.item()
                class_name = model.names[int(c)]

                if is_base_model and class_name not in FOOD_CLASSES:
                    continue

                quality_info = get_quality_info(
                    class_name=class_name,
                    img=img,
                    box=b,
                    is_custom_model=is_custom_quality_model,
                )

                # Return required JSON format
                detections.append({
                    "food_name": quality_info["food_name"],
                    "freshness_score": quality_info["freshness_score"],
                    "status": quality_info["status"],
                    "expiry_days": quality_info["expiry_days"],
                    # UI Helpers
                    "box": b,
                    "confidence": round(s, 3),
                    "color_code": quality_info["color_code"],
                    "quality_label": quality_info["quality_label"]
                })

        return JSONResponse(content={"detections": detections})
    except Exception as e:
        print(f"Error during prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ─── REST APIs for Management ──────────────────────────────────────

@app.post("/inventory/add")
async def add_inventory(payload: dict = Body(...), current_user: dict = Depends(get_current_user)):
    item_id = await db.add_to_inventory(
        current_user["id"],
        payload["food_name"],
        payload.get("freshness_score", 100),
        payload.get("status", "Safe to Eat"),
        payload.get("expiry_days", 7),
        int(payload.get("quantity", 1)),
        float(payload.get("price_per_unit", 0.0)),
        payload.get("notes", "")
    )
    return {"message": "Success", "id": item_id}

# ─── Auth APIs ─────────────────────────────────────────────────────

@app.post("/register")
async def register(payload: dict = Body(...)):
    email = payload.get("email")
    password = payload.get("password")
    full_name = payload.get("full_name")
    
    if not email or not password or not full_name:
        raise HTTPException(status_code=400, detail="Missing fields")
    
    user = await db.create_user(email, password, full_name)
    if not user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    return {"message": "User created successfully"}

@app.post("/login")
async def login(payload: dict = Body(...)):
    email = payload.get("email")
    password = payload.get("password")
    
    user = await db.get_user_by_email(email)
    if not user or not db.verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(data={"sub": user["email"], "name": user["full_name"], "id": user["_id"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": user["email"],
            "full_name": user["full_name"]
        }
    }

@app.get("/inventory/list")
async def list_inventory(current_user: dict = Depends(get_current_user)):
    items = await db.get_inventory(current_user["id"])
    return {"inventory": items}

@app.get("/inventory/aggregated")
async def list_aggregated_inventory(current_user: dict = Depends(get_current_user)):
    items = await db.get_aggregated_inventory(current_user["id"])
    return {"inventory": items}

@app.post("/inventory/sell")
async def sell_inventory(payload: dict = Body(...), current_user: dict = Depends(get_current_user)):
    success = await db.sell_from_inventory(
        current_user["id"],
        payload["item_id"],
        int(payload.get("quantity", 1)),
        float(payload.get("sell_price", 0.0)),
        payload.get("buyer_name", ""),
        payload.get("buyer_phone", "")
    )
    if success:
        return {"message": "Sale recorded successfully"}
    return {"message": "Sale failed, item not found"}

@app.post("/inventory/sell_bulk")
async def sell_inventory_bulk(payload: dict = Body(...), current_user: dict = Depends(get_current_user)):
    success = await db.sell_bulk_fifo(
        current_user["id"],
        payload["food_name"],
        int(payload.get("quantity", 1)),
        float(payload.get("sell_price", 0.0)),
        payload.get("buyer_name", ""),
        payload.get("buyer_phone", "")
    )
    if success:
        return {"message": "Bulk sale recorded successfully"}
    return {"message": "Sale failed, insufficient stock"}

@app.get("/transactions/list")
async def list_transactions(current_user: dict = Depends(get_current_user)):
    items = await db.get_transactions(current_user["id"])
    return {"transactions_log": items}

@app.post("/waste/add")
async def add_waste(payload: dict = Body(...), current_user: dict = Depends(get_current_user)):
    if "item_id" in payload:
        success = await db.discard_from_inventory(
            current_user["id"],
            payload["item_id"],
            int(payload.get("quantity", 1)),
            payload.get("reason", "user_discarded")
        )
        if success:
            return {"message": "Discarded from inventory and logged to waste"}
        else:
            return {"message": "Item not found in inventory"}
    else:
        await db.add_to_waste(
            current_user["id"],
            payload["food_name"], 
            payload.get("reason", "direct_waste"),
            int(payload.get("quantity", 1)),
            float(payload.get("total_value", 0.0))
        )
        return {"message": "Added to waste log directly"}

@app.get("/waste/list")
async def list_waste(current_user: dict = Depends(get_current_user)):
    items = await db.get_waste_logs(current_user["id"])
    return {"waste_logs": items}

@app.get("/recipes/suggest")
async def get_recipes(current_user: dict = Depends(get_current_user)):
    recipes = await db.suggest_recipes(current_user["id"])
    return {"recipes": recipes}

@app.get("/grocery/list")
async def list_grocery(current_user: dict = Depends(get_current_user)):
    items = await db.get_grocery_list(current_user["id"])
    return {"grocery_list": items}

@app.post("/grocery/add")
async def manual_add_grocery(payload: dict = Body(...), current_user: dict = Depends(get_current_user)):
    await db.add_to_grocery(
        current_user["id"],
        payload["food_name"],
        int(payload.get("quantity", 1)),
        float(payload.get("estimated_price", 0.0)),
        payload.get("notes", "")
    )
    return {"message": "Added to grocery list"}

@app.post("/grocery/update")
async def update_grocery(payload: dict = Body(...), current_user: dict = Depends(get_current_user)):
    await db.mark_grocery_purchased(current_user["id"], payload["item_id"])
    return {"message": "Marked as purchased"}

@app.get("/dashboard/summary")
async def dashboard_summary(current_user: dict = Depends(get_current_user)):
    data = await db.get_dashboard_summary(current_user["id"])
    return data

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Food Management API at http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
