import cv2
from ultralytics import YOLO
import os
from quality_analyzer import get_quality_info

def run_detection():
    # Base directory is where this script is located
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Model paths
    custom_model_path = os.path.join(BASE_DIR, "food_detection_v11/train_run/weights/best.pt")
    base_model_path = os.path.join(BASE_DIR, "yolo11n.pt")
    
    if os.path.exists(custom_model_path):
        print(f"📦 Loading CUSTOM model: {custom_model_path}")
        model = YOLO(custom_model_path)
        is_custom = True
    elif os.path.exists(base_model_path):
        print(f"⚠️ Custom model not found. Fallback to BASE model: {base_model_path}")
        model = YOLO(base_model_path)
        is_custom = False
    else:
        print(f"❌ Error: No YOLO model found at {base_model_path}")
        return

    # Path to test images
    test_image_dir = os.path.join(BASE_DIR, "yolo_dataset/images/val")
    if not os.path.exists(test_image_dir):
        print(f"❌ Error: Test image directory not found at {test_image_dir}")
        return
        
    test_images = [os.path.join(test_image_dir, f) for f in os.listdir(test_image_dir) 
                   if f.lower().endswith((".jpg", ".jpeg", ".png"))]

    if not test_images:
        print(f"❌ No test images found in {test_image_dir}")
        return

    print(f"🔍 Running detection on {min(5, len(test_images))} sample images...\n")
    
    # Loop through first 5 images for demo
    for img_path in test_images[:5]:
        print(f"--- Processing: {os.path.basename(img_path)} ---")
        img = cv2.imread(img_path)
        if img is None:
            print(f"Failed to load image: {img_path}")
            continue
            
        results = model.predict(source=img, save=False, show=False, verbose=False)
        
        found = False
        for r in results:
            boxes = r.boxes
            for box in boxes:
                found = True
                b = box.xyxy[0].tolist()
                c = box.cls.item()
                conf = box.conf.item()
                class_name = model.names[int(c)]
                
                # Get quality info
                q = get_quality_info(class_name, img, b, is_custom_model=is_custom)
                
                print(f"  ✅ Detected: {q['food_name']}")
                print(f"     Confidence: {conf:.2f}")
                print(f"     Quality: {q['quality_label']} ({q['status']})")
                print(f"     Freshness Score: {q['freshness_score']}/100")
                print(f"     Est. Shelf Life: {q['expiry_days']} days")
                print("-" * 30)
        
        if not found:
            print("  ❌ No food items detected in this image.")
        print("\n")

if __name__ == "__main__":
    run_detection()
