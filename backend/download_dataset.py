"""
Download Food Freshness Dataset from Roboflow
==============================================
Downloads a pre-annotated fruit freshness detection dataset
in YOLO format for training a quality-aware detection model.

Usage:
    pip install roboflow
    python download_dataset.py

If you don't have a Roboflow API key, you can also manually download from:
    https://universe.roboflow.com/search?q=fruit%20freshness%20rotten
"""

import os
import sys
import shutil


def download_from_roboflow(api_key: str = None):
    """Download dataset using Roboflow Python SDK."""
    try:
        from roboflow import Roboflow
    except ImportError:
        print("Installing roboflow package...")
        os.system(f"{sys.executable} -m pip install roboflow")
        from roboflow import Roboflow

    if not api_key:
        api_key = input("Enter your Roboflow API key (get one at https://app.roboflow.com/settings/api): ").strip()

    rf = Roboflow(api_key=api_key)

    # Fruit Freshness Detection dataset (fresh/rotten)
    # You can replace this with any dataset from Roboflow Universe
    project = rf.workspace().project("fruit-freshness-detection")
    version = project.version(1)
    dataset = version.download("yolov11", location="./food_quality_dataset")

    print(f"\n✅ Dataset downloaded to: ./food_quality_dataset")
    print(f"   Classes: {dataset.classes}")
    return dataset


def setup_manual_dataset():
    """
    Set up directory structure for manual dataset preparation.
    Use this if you prefer to manually collect and label images.
    """
    dirs = [
        "food_quality_dataset/train/images",
        "food_quality_dataset/train/labels",
        "food_quality_dataset/valid/images",
        "food_quality_dataset/valid/labels",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # Create data.yaml for the quality dataset
    data_yaml = """# Food Quality Detection Dataset
path: ./food_quality_dataset
train: train/images
val: valid/images

# Classes: food_quality combinations
names:
  0: fresh_apple
  1: rotten_apple
  2: fresh_banana
  3: rotten_banana
  4: fresh_orange
  5: rotten_orange
  6: fresh_mango
  7: rotten_mango
  8: fresh_strawberry
  9: rotten_strawberry
  10: fresh_grape
  11: rotten_grape
"""
    with open("data_quality.yaml", "w") as f:
        f.write(data_yaml)

    print("✅ Directory structure created!")
    print("   Place your images in food_quality_dataset/train/images/ and food_quality_dataset/valid/images/")
    print("   Place corresponding YOLO label files in the labels/ directories")
    print("   data_quality.yaml has been created with 12 classes")
    print()
    print("📌 Labeling tips:")
    print("   - Use https://app.roboflow.com or LabelImg to annotate images")
    print("   - Label format: <class_id> <x_center> <y_center> <width> <height>")
    print("   - All values normalized to [0, 1]")


if __name__ == "__main__":
    print("=" * 60)
    print("  Food Quality Dataset Downloader")
    print("=" * 60)
    print()
    print("Options:")
    print("  1. Download from Roboflow (recommended, requires API key)")
    print("  2. Set up manual dataset structure")
    print()

    choice = input("Choose option (1 or 2): ").strip()

    if choice == "1":
        download_from_roboflow()
    else:
        setup_manual_dataset()
