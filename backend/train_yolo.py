"""
Train YOLOv11 for Food Quality Detection
==========================================
Trains a custom YOLO model on a food freshness dataset with quality labels.
The model learns to detect food AND classify its freshness simultaneously.

Usage:
    python train_yolo.py                     # Train quality model
    python train_yolo.py --epochs 50         # Custom epochs
    python train_yolo.py --device 0          # Use GPU
"""

from ultralytics import YOLO
import argparse
import os


def train_quality_model(epochs=30, device="cpu", imgsz=640):
    """
    Train a quality-aware food detection model.
    Uses compound class labels (fresh_apple, rotten_banana, etc.)
    """
    # Check which dataset config to use
    if os.path.exists("data_quality.yaml"):
        data_config = "data_quality.yaml"
        project_name = "food_quality_model"
        print("🍎 Training QUALITY model with freshness labels")
    elif os.path.exists("data.yaml"):
        data_config = "data.yaml"
        project_name = "food_detection_v11"
        print("📦 Training basic detection model (no quality labels)")
    else:
        print("❌ No data.yaml found! Run download_dataset.py first.")
        return

    # Load pretrained YOLOv11n
    model = YOLO("yolo11n.pt")

    print(f"   Dataset config: {data_config}")
    print(f"   Epochs: {epochs}")
    print(f"   Image size: {imgsz}")
    print(f"   Device: {device}")
    print()

    # Train with augmentation optimized for freshness detection
    results = model.train(
        data=data_config,
        epochs=epochs,
        imgsz=imgsz,
        device=device,
        project=project_name,
        name="weights",
        exist_ok=True,

        # ── Augmentation for freshness detection ──────────────
        # Color/brightness augmentation is critical for detecting
        # subtle freshness differences (brown spots, color changes)
        hsv_h=0.02,        # Hue augmentation
        hsv_s=0.7,         # Saturation augmentation (important!)
        hsv_v=0.4,         # Value/brightness augmentation
        degrees=15,         # Rotation
        translate=0.1,      # Translation
        scale=0.5,          # Scale
        fliplr=0.5,         # Horizontal flip
        flipud=0.0,         # No vertical flip (food orientation matters)
        mosaic=1.0,         # Mosaic augmentation
        mixup=0.1,          # MixUp augmentation

        # ── Training params ───────────────────────────────────
        batch=-1,           # Auto batch size
        patience=10,        # Early stopping
        optimizer="auto",
        lr0=0.01,
        lrf=0.01,
        warmup_epochs=3,
        cos_lr=True,        # Cosine LR schedule

        # ── Logging ───────────────────────────────────────────
        verbose=True,
        plots=True,
    )

    model_path = f"{project_name}/weights/weights/best.pt"
    if os.path.exists(model_path):
        print(f"\n✅ Training complete!")
        print(f"   Best model: {model_path}")
        print(f"   Restart web_server.py to use the new model.")
    else:
        # Try alternate path
        alt_path = f"{project_name}/weights/best.pt"
        if os.path.exists(alt_path):
            print(f"\n✅ Training complete!")
            print(f"   Best model: {alt_path}")
        else:
            print(f"\n⚠️  Training finished. Check {project_name}/ for model weights.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLOv11 Food Quality Model")
    parser.add_argument("--epochs", type=int, default=30, help="Number of training epochs")
    parser.add_argument("--device", type=str, default="cpu", help="Device: 'cpu' or '0' for GPU")
    parser.add_argument("--imgsz", type=int, default=640, help="Training image size")
    args = parser.parse_args()

    train_quality_model(epochs=args.epochs, device=args.device, imgsz=args.imgsz)
