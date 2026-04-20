"""
Food Quality Analyzer Module
=============================
Provides quality classification for detected food items.

Two modes of operation:
1. Custom Model Mode: Parses compound class labels (e.g., 'fresh_apple' → food='apple', quality='fresh')
2. Heuristic Mode: Uses OpenCV color/texture analysis on cropped regions to estimate quality
"""

import cv2
import numpy as np

# ─── Quality Tiers ─────────────────────────────────────────────────
QUALITY_TIERS = {
    "fresh": {
        "label": "Fresh",
        "recommendation": "Safe to Eat",
        "color_code": "#4ade80",   # green
        "tier": 1,
    },
    "ripe": {
        "label": "Ripe",
        "recommendation": "Safe to Eat",
        "color_code": "#4ade80",
        "tier": 1,
    },
    "good": {
        "label": "Good",
        "recommendation": "Safe to Eat",
        "color_code": "#4ade80",
        "tier": 1,
    },
    "medium": {
        "label": "Average",
        "recommendation": "Sellable – Use Soon",
        "color_code": "#facc15",   # yellow
        "tier": 2,
    },
    "overripe": {
        "label": "Overripe",
        "recommendation": "Sellable – Use Soon",
        "color_code": "#facc15",
        "tier": 2,
    },
    "stale": {
        "label": "Stale",
        "recommendation": "Sellable – Use Soon",
        "color_code": "#facc15",
        "tier": 2,
    },
    "rotten": {
        "label": "Spoiled",
        "recommendation": "Not Safe for Consumption",
        "color_code": "#ef4444",   # red
        "tier": 3,
    },
    "spoiled": {
        "label": "Spoiled",
        "recommendation": "Not Safe for Consumption",
        "color_code": "#ef4444",
        "tier": 3,
    },
}

# ─── Shelf-life estimates (days) per food + quality ─────────────────
SHELF_LIFE = {
    "apple":     {"fresh": 14, "medium": 5,  "rotten": 0},
    "banana":    {"fresh": 7,  "medium": 2,  "rotten": 0},
    "orange":    {"fresh": 21, "medium": 7,  "rotten": 0},
    "sandwich":  {"fresh": 2,  "medium": 1,  "rotten": 0},
    "broccoli":  {"fresh": 7,  "medium": 3,  "rotten": 0},
    "carrot":    {"fresh": 21, "medium": 7,  "rotten": 0},
    "hot dog":   {"fresh": 5,  "medium": 2,  "rotten": 0},
    "pizza":     {"fresh": 3,  "medium": 1,  "rotten": 0},
    "donut":     {"fresh": 3,  "medium": 1,  "rotten": 0},
    "cake":      {"fresh": 5,  "medium": 2,  "rotten": 0},
    "mango":     {"fresh": 7,  "medium": 3,  "rotten": 0},
    "strawberry":{"fresh": 5,  "medium": 2,  "rotten": 0},
    "grape":     {"fresh": 10, "medium": 4,  "rotten": 0},
    "tomato":    {"fresh": 7,  "medium": 3,  "rotten": 0},
}

DEFAULT_SHELF_LIFE = {"fresh": 7, "medium": 3, "rotten": 0}


def parse_compound_class(class_name: str):
    """
    Parse compound class labels from custom-trained models.
    E.g. 'fresh_apple' → ('apple', 'fresh')
         'rotten_banana' → ('banana', 'rotten')
    """
    quality_prefixes = ["fresh", "ripe", "good", "medium", "overripe", "stale", "rotten", "spoiled"]
    lower = class_name.lower().replace("-", "_")

    for prefix in quality_prefixes:
        if lower.startswith(prefix + "_"):
            food_name = lower[len(prefix) + 1:]
            return food_name.replace("_", " "), prefix
        if lower.endswith("_" + prefix):
            food_name = lower[: -(len(prefix) + 1)]
            return food_name.replace("_", " "), prefix

    return class_name, None  # no quality info embedded


def analyze_quality_heuristic(img_crop: np.ndarray, food_name: str) -> str:
    """
    Estimate food freshness using OpenCV colour & texture heuristics.
    Works on the cropped bounding-box region of the detected food.

    Returns one of: 'fresh', 'medium', 'rotten'
    """
    if img_crop is None or img_crop.size == 0:
        return "fresh"  # fallback

    # Resize for consistency
    crop_resized = cv2.resize(img_crop, (128, 128))
    hsv = cv2.cvtColor(crop_resized, cv2.COLOR_BGR2HSV)

    # ── 1. Brown / dark spot ratio ──────────────────────────────────
    # Brown pixels: low-mid hue (8-25), moderate saturation, low-mid value
    lower_brown = np.array([8, 50, 30])
    upper_brown = np.array([25, 255, 150])
    brown_mask = cv2.inRange(hsv, lower_brown, upper_brown)
    brown_ratio = np.sum(brown_mask > 0) / brown_mask.size

    # ── 2. Dark / black spot ratio (mold, decay) ───────────────────
    lower_dark = np.array([0, 0, 0])
    upper_dark = np.array([180, 255, 50])
    dark_mask = cv2.inRange(hsv, lower_dark, upper_dark)
    dark_ratio = np.sum(dark_mask > 0) / dark_mask.size

    # ── 3. Saturation analysis (faded = stale) ─────────────────────
    mean_saturation = np.mean(hsv[:, :, 1])

    # ── 4. Texture roughness (more edges = more wrinkled/decayed) ──
    gray = cv2.cvtColor(crop_resized, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_ratio = np.sum(edges > 0) / edges.size

    # ── 5. Color vibrancy (high vibrancy = fresh) ──────────────────
    mean_value = np.mean(hsv[:, :, 2])

    # ── Scoring Process ────────────────────────────────────────────────
    # Higher score = worse quality. Base is 0.
    score = 0.0
    score += brown_ratio * 30       # brown spots contribute heavily
    score += dark_ratio * 40        # dark/black spots are strong decay signal
    score += edge_ratio * 10        # texture roughness
    score += max(0, (80 - mean_saturation) / 80) * 10   # low saturation = faded
    score += max(0, (100 - mean_value) / 100) * 10      # very dark image overall

    # Map heuristic score to a 0-100 freshness score (100 is perfectly fresh)
    freshness_score = max(0, int(100 - (score * 2.5)))
    
    quality_category = "fresh"
    if freshness_score >= 80:
        quality_category = "fresh"
    elif freshness_score >= 40:
        quality_category = "medium"
    else:
        quality_category = "rotten"

    return quality_category, freshness_score


def get_quality_info(class_name: str, img: np.ndarray = None, box: list = None, is_custom_model: bool = False):
    """
    Main entry point: returns a complete quality assessment dict.
    Returns format matches requirements:
    { "food_name", "freshness_score", "status", "expiry_days", "color_code", "quality_label" }
    """
    food_name = class_name
    quality_key = None
    freshness_score = 100

    # ── Try compound label parsing first ───────────────────────────
    if is_custom_model:
        food_name, quality_key = parse_compound_class(class_name)
        if quality_key in ["fresh", "ripe", "good"]:
            freshness_score = 95
        elif quality_key in ["rotten", "spoiled"]:
            freshness_score = 10
        else:
            freshness_score = 50

    # ── Fallback to heuristic ──────────────────────────────────────
    if quality_key is None and img is not None and box is not None:
        x1, y1, x2, y2 = [int(v) for v in box]
        h, w = img.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        crop = img[y1:y2, x1:x2]
        quality_key, freshness_score = analyze_quality_heuristic(crop, food_name)

    # ── Final fallback ─────────────────────────────────────────────
    if quality_key is None:
        quality_key = "fresh"
        freshness_score = 90

    # ── Look up tier info ──────────────────────────────────────────
    tier_info = QUALITY_TIERS.get(quality_key, QUALITY_TIERS["fresh"])

    # ── Shelf life ─────────────────────────────────────────────────
    shelf_map = SHELF_LIFE.get(food_name.lower(), DEFAULT_SHELF_LIFE)
    if quality_key in ("fresh", "ripe", "good"):
        shelf_days = shelf_map.get("fresh", 7)
    elif quality_key in ("medium", "overripe", "stale"):
        shelf_days = shelf_map.get("medium", 3)
    else:
        shelf_days = shelf_map.get("rotten", 0)

    # Further tune shelf days based on exact freshness score
    adjusted_expiry = round(shelf_days * (freshness_score / 100))

    return {
        "food_name": food_name.title(),
        "freshness_score": freshness_score,
        "status": tier_info["recommendation"], 
        "expiry_days": max(0, adjusted_expiry),
        "quality_label": tier_info["label"],
        "color_code": tier_info["color_code"]
    }
