import cv2
from ultralytics import YOLO
import os

def run_detection():
    # Load the best model from training
    model_path = "food_detection_v11/train_run/weights/best.pt"
    
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}. Please run train_yolo.py first.")
        # Fallback to base model just for demo if needed
        # model = YOLO("yolo11n.pt")
        return

    model = YOLO(model_path)

    # Path to some test images
    test_image_dir = "yolo_dataset/images/val"
    test_images = [os.path.join(test_image_dir, f) for f in os.listdir(test_image_dir) if f.endswith(".jpg")]

    if test_images:
        print(f"Running detection on {len(test_images)} test images...")
        results = model.predict(source=test_images[0], save=True, show=False)
        print(f"Detection results saved to {results[0].save_dir}")
    else:
        print("No test images found in yolo_dataset/images/val")

    # Optional: WebCam Detection
    # print("Starting Webcam detection... Press 'q' to quit.")
    # results = model.predict(source="0", show=True)

if __name__ == "__main__":
    run_detection()
