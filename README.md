Grocery Store Management Project Details
This project is a sophisticated Food Management & Quality Analysis System designed for grocery stores. It leverages AI for real-time food detection and quality assessment, integrated with a full inventory management backend.

🏗️ Architecture Overview
The system follows a classic Client-Server architecture with an AI processing layer.

1. Backend (Python / FastAPI)
Framework: FastAPI, a high-performance Python web framework.
Entry Point: backend/web_server.py
Database:
Primary: local_db.json (A file-based storage for easy deployment).
Ready for: MongoDB (using database.py abstractions).
Core logic:
Auth: JWT-based authentication for secure access.
Scheduler: An AsyncIOScheduler runs every hour to automatically check for expiring stock.
2. Frontend (Nuxt.js / Vue 3)
Framework: Nuxt 3, a modern Vue.js meta-framework.
Language: TypeScript.
Styling: Tailwind CSS for a modern, responsive UI.
Core Views:
Dashboard: Real-time summary of stock levels, waste, and sales.
AI Analyzer: Upload or take photos of food to detect type and freshness.
Inventory: Complete management of items, including price and quantity.
Stock In/Out: Bulk inventory management with FIFO (First-In, First-Out) logic.
Waste Tracking: Detailed logs of expired or discarded items.
3. AI Layer (YOLOv11)
Engine: Ultralytics YOLOv11.
Models:
yolo11n.pt: Base architecture.
Supports custom-trained models for better accuracy on specific produce.
Functionality:
Object detection (Identifying "Apples", "Bananas", etc.).
Quality analysis (Estimating freshness and remaining shelf life).
🔥 Key Features
🍏 Smart Food Analysis
Utilizes the camera to identify food items and automatically calculate:

Freshness Score: Percentage-based quality assessment.
Estimated Expiry: Predicted days left until the item is unfit for sale.
Status Classification: "Safe to Eat", "Eat Soon", or "Expired".
📦 Inventory & Stock Management
Aggregated View: Groups identical items to show total stock while maintaining individual batch IDs.
FIFO Sales: Automatically sells the oldest stock first to minimize waste.
Bulk Operations: "Stock In" for adding new shipments and "Stock Out" for recording sales.
📊 Business Intelligence
Dashboard Summary: Total investment vs. potential revenue.
Transaction Logs: Every sale and stock movement is recorded for audit.
Waste Analytics: Tracks why and what items were wasted to help optimize future orders.
🛒 Utility Features
Grocery List: An auto-generating shopping list based on low-stock items.
Recipe Suggestions: Suggests recipes based on what's currently in your inventory.
🛠️ Technical Stack
Backend: Python 3.9+, FastAPI, Ultralytics YOLO, APScheduler, PyJWT.
Frontend: Nuxt 3, Vue 3, Tailwind CSS, Lucide Icons.
Database: JSON (Local) / MongoDB.
Deployment: Docker support provided via Dockerfile.
