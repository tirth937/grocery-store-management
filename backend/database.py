import json
import os
import asyncio
from datetime import datetime, timedelta
import uuid
import bcrypt

DB_FILE = "local_db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "inventory": [],
            "waste_logs": [],
            "grocery_list": [],
            "transactions_log": [],
            "users": []
        }
    with open(DB_FILE, "r") as f:
        try:
            db_data = json.load(f)
            if "transactions_log" not in db_data:
                db_data["transactions_log"] = []
            if "users" not in db_data:
                db_data["users"] = []
            return db_data
        except:
            return {"inventory": [], "waste_logs": [], "grocery_list": [], "transactions_log": [], "users": []}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_db()

def _generate_id():
    return str(uuid.uuid4())

# --- User Management ---
def get_password_hash(password):
    # Hash a password for the first time
    # bcrypt.hashpw expects bytes, so we encode the string
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password, hashed_password):
    # Check hashed password. 
    # bcrypt.checkpw expects bytes for both arguments.
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

async def create_user(email, password, full_name):
    if any(u["email"] == email for u in db["users"]):
        return None
    
    user = {
        "_id": _generate_id(),
        "email": email,
        "password": get_password_hash(password),
        "full_name": full_name,
        "created_at": datetime.utcnow().isoformat()
    }
    db["users"].append(user)
    save_db(db)
    return user

async def get_user_by_email(email):
    for u in db["users"]:
        if u["email"] == email:
            return u
    return None

# --- Transactions Ledger ---
async def log_transaction(user_id: str, type_in_out: str, food_name: str, quantity: int, unit_price: float, total_value: float, buyer_name: str = "", buyer_phone: str = ""):
    item = {
        "_id": _generate_id(),
        "user_id": user_id,
        "type": type_in_out,
        "food_name": food_name,
        "quantity": quantity,
        "unit_price": unit_price,
        "total_value": total_value,
        "buyer_name": buyer_name,
        "buyer_phone": buyer_phone,
        "date": datetime.utcnow().isoformat()
    }
    db["transactions_log"].append(item)
    save_db(db)

async def get_transactions(user_id: str):
    return sorted([t for t in db["transactions_log"] if t.get("user_id") == user_id], 
                  key=lambda x: x["date"], reverse=True)

# --- Inventory Operations ---
async def add_to_inventory(user_id: str, food_name: str, freshness_score: int, status: str, expiry_days: int, quantity: int = 1, price_per_unit: float = 0.0, notes: str = ""):
    expiry_date = (datetime.utcnow() + timedelta(days=expiry_days)).isoformat()
    
    item = {
        "_id": _generate_id(),
        "user_id": user_id,
        "food_name": food_name,
        "quantity": quantity,
        "price_per_unit": price_per_unit,
        "freshness_score": freshness_score,
        "status": status,
        "expiry_date": expiry_date,
        "added_date": datetime.utcnow().isoformat(),
        "notes": notes
    }
    
    db["inventory"].append(item)
    
    # Financial log: Expense (Money Out)
    await log_transaction(user_id, "STOCK_IN", food_name, quantity, price_per_unit, quantity * price_per_unit)
    
    save_db(db)
    return item["_id"]

async def get_inventory(user_id: str):
    return [i for i in db["inventory"] if i.get("user_id") == user_id]

async def remove_from_inventory(user_id: str, item_id: str):
    removed_item = None
    new_inv = []
    for i in db["inventory"]:
        if i["_id"] == item_id and i.get("user_id") == user_id:
            removed_item = i
        else:
            new_inv.append(i)
    db["inventory"] = new_inv
    save_db(db)
    return removed_item

async def sell_from_inventory(user_id: str, item_id: str, sell_qty: int, sell_price: float, buyer_name: str = "", buyer_phone: str = ""):
    # Find the item
    item_ref = None
    for i in db["inventory"]:
        if i["_id"] == item_id and i.get("user_id") == user_id:
            item_ref = i
            break
            
    if not item_ref:
        return False
        
    actual_qty_sold = min(sell_qty, item_ref["quantity"])
    revenue = actual_qty_sold * sell_price
    
    # Log Sale Transaction
    await log_transaction(user_id, "STOCK_OUT_SALE", item_ref["food_name"], actual_qty_sold, sell_price, revenue, buyer_name, buyer_phone)
    
    # Adjust inventory
    if item_ref["quantity"] <= actual_qty_sold:
        await remove_from_inventory(user_id, item_id)
    else:
        item_ref["quantity"] -= actual_qty_sold
        save_db(db)
        
    return True

async def get_aggregated_inventory(user_id: str):
    agg = {}
    user_inv = [i for i in db["inventory"] if i.get("user_id") == user_id]
    for item in user_inv:
        name = item["food_name"]
        if name not in agg:
            agg[name] = {
                "food_name": name,
                "quantity": 0,
                "total_price_pool": 0.0,
                "freshness_score_pool": 0,
                "batch_count": 0
            }
        qty = item.get("quantity", 1)
        agg[name]["quantity"] += qty
        agg[name]["total_price_pool"] += item.get("price_per_unit", 0.0) * qty
        agg[name]["freshness_score_pool"] += item.get("freshness_score", 100) * qty
        agg[name]["batch_count"] += 1
        
    result = []
    for name, data in agg.items():
        qty = data["quantity"]
        if qty > 0:
            avg_price = data["total_price_pool"] / qty
            avg_freshness = data["freshness_score_pool"] / qty
            result.append({
                "food_name": name,
                "quantity": qty,
                "avg_price": round(avg_price, 2),
                "avg_freshness": round(avg_freshness, 0),
                "batch_count": data["batch_count"],
                # Pass a generic id equivalent for frontend key
                "_id": f"agg_{name.replace(' ', '_')}"
            })
    return result

async def sell_bulk_fifo(user_id: str, food_name: str, sell_qty: int, sell_price: float, buyer_name: str = "", buyer_phone: str = ""):
    batches = [i for i in db["inventory"] if i["food_name"] == food_name and i.get("user_id") == user_id]
    
    total_qty = sum(b.get("quantity", 1) for b in batches)
    actual_qty_sold = min(sell_qty, total_qty)
    if actual_qty_sold <= 0:
        return False
        
    revenue = actual_qty_sold * sell_price
    
    await log_transaction(user_id, "STOCK_OUT_SALE", food_name, actual_qty_sold, sell_price, revenue, buyer_name, buyer_phone)
    
    qty_remaining_to_deduct = actual_qty_sold
    
    for batch in batches:
        if qty_remaining_to_deduct <= 0:
            break
            
        b_qty = batch.get("quantity", 1)
        if b_qty <= qty_remaining_to_deduct:
            qty_remaining_to_deduct -= b_qty
            await remove_from_inventory(user_id, batch["_id"])
        else:
            batch["quantity"] = b_qty - qty_remaining_to_deduct
            qty_remaining_to_deduct = 0
            
    save_db(db)
    return True

async def discard_from_inventory(user_id: str, item_id: str, discard_qty: int, reason: str):
    # Find the item
    item_ref = None
    for i in db["inventory"]:
        if i["_id"] == item_id and i.get("user_id") == user_id:
            item_ref = i
            break
            
    if not item_ref:
        return False
        
    actual_qty_discarded = min(discard_qty, item_ref["quantity"])
    total_value_lost = actual_qty_discarded * item_ref.get("price_per_unit", 0.0)
    
    # Log to waste
    await add_to_waste(user_id, item_ref["food_name"], reason, actual_qty_discarded, total_value_lost)
    
    # Adjust inventory
    if item_ref["quantity"] <= actual_qty_discarded:
        await remove_from_inventory(user_id, item_id)
    else:
        item_ref["quantity"] -= actual_qty_discarded
        save_db(db)
        
    return True

# --- Waste Operations ---
async def add_to_waste(user_id: str, food_name: str, reason: str, quantity: int = 1, total_value: float = 0.0):
    item = {
        "_id": _generate_id(),
        "user_id": user_id,
        "food_name": food_name,
        "quantity": quantity,
        "total_value": total_value,
        "reason": reason, # "expired", "user_discarded"
        "logged_date": datetime.utcnow().isoformat()
    }
    db["waste_logs"].append(item)
    
    unit_price = total_value / quantity if quantity > 0 else 0
    await log_transaction(user_id, "STOCK_OUT_WASTE", food_name, quantity, unit_price, total_value)
    
    save_db(db)

async def get_waste_logs(user_id: str):
    return sorted([w for w in db["waste_logs"] if w.get("user_id") == user_id], 
                  key=lambda x: x["logged_date"], reverse=True)

# --- Grocery List Operations ---
async def add_to_grocery(user_id: str, food_name: str, quantity: int = 1, estimated_price: float = 0.0, notes: str = ""):
    item = {
        "_id": _generate_id(),
        "user_id": user_id,
        "food_name": food_name,
        "quantity": quantity,
        "estimated_price": estimated_price,
        "notes": notes,
        "added_date": datetime.utcnow().isoformat(),
        "purchased": False
    }
    db["grocery_list"].append(item)
    save_db(db)

async def get_grocery_list(user_id: str):
    return [i for i in db["grocery_list"] if i.get("user_id") == user_id and not i.get("purchased")]

async def mark_grocery_purchased(user_id: str, item_id: str):
    for item in db["grocery_list"]:
        if item["_id"] == item_id and item.get("user_id") == user_id:
            item["purchased"] = True
            save_db(db)
            return

# --- Background Check Function (Expiries) ---
async def process_expiries():
    now = datetime.utcnow().isoformat()
    expired_items = [i for i in db["inventory"] if i["expiry_date"] < now]
    
    count = 0
    for item in expired_items:
        # Move to waste
        total_value = item.get("quantity", 1) * item.get("price_per_unit", 0.0)
        await add_to_waste(item["food_name"], "expired", item.get("quantity", 1), total_value)
        # Add to grocery
        await add_to_grocery(item["food_name"], item.get("quantity", 1), item.get("price_per_unit", 0.0), "Automatically added due to expiry")
        # Remove from inventory
        await remove_from_inventory(item["_id"])
        count += 1
    
    if count > 0:
        print(f"🔄 Expiry Tracker: Processed {count} expired items.")

# --- Dashboard Summary ---
async def get_dashboard_summary(user_id: str):
    now = datetime.utcnow()
    user_inv = [i for i in db["inventory"] if i.get("user_id") == user_id]
    user_txns = [t for t in db["transactions_log"] if t.get("user_id") == user_id]
    user_waste = [w for w in db["waste_logs"] if w.get("user_id") == user_id]
    
    # Inventory stats
    total_items = sum(i.get("quantity", 1) for i in user_inv)
    unique_products = len(set(i["food_name"] for i in user_inv))
    stock_value = sum(i.get("quantity", 1) * i.get("price_per_unit", 0.0) for i in user_inv)
    
    # Expiring soon (within 2 days)
    expiring_soon = 0
    for i in user_inv:
        try:
            exp = datetime.fromisoformat(i["expiry_date"])
            if exp - now < timedelta(days=2) and exp > now:
                expiring_soon += i.get("quantity", 1)
        except:
            pass
    
    # Transaction stats
    total_revenue = 0.0
    total_expenses = 0.0
    total_waste_loss = 0.0
    sales_count = 0
    purchases_count = 0
    
    for t in user_txns:
        tv = t.get("total_value", 0.0)
        if t["type"] == "STOCK_OUT_SALE":
            total_revenue += tv
            sales_count += 1
        elif t["type"] == "STOCK_IN":
            total_expenses += tv
            purchases_count += 1
        elif t["type"] == "STOCK_OUT_WASTE":
            total_waste_loss += tv
    
    net_profit = total_revenue - total_expenses - total_waste_loss
    
    # Waste stats
    total_wasted_items = sum(w.get("quantity", 1) for w in user_waste)
    
    # Top selling products (by quantity sold)
    sales_by_product = {}
    for t in user_txns:
        if t["type"] == "STOCK_OUT_SALE":
            name = t["food_name"]
            sales_by_product[name] = sales_by_product.get(name, 0) + t.get("quantity", 1)
    top_sellers = sorted(sales_by_product.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Top stocked products
    stock_by_product = {}
    for i in user_inv:
        name = i["food_name"]
        stock_by_product[name] = stock_by_product.get(name, 0) + i.get("quantity", 1)
    top_stocked = sorted(stock_by_product.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Recent transactions (last 8)
    recent = sorted(user_txns, key=lambda x: x["date"], reverse=True)[:8]
    
    # Inventory health distribution
    fresh_count = 0
    warning_count = 0
    critical_count = 0
    for i in user_inv:
        fs = i.get("freshness_score", 100)
        qty = i.get("quantity", 1)
        if fs >= 70:
            fresh_count += qty
        elif fs >= 40:
            warning_count += qty
        else:
            critical_count += qty
    
    return {
        "total_items": total_items,
        "unique_products": unique_products,
        "stock_value": round(stock_value, 2),
        "expiring_soon": expiring_soon,
        "total_revenue": round(total_revenue, 2),
        "total_expenses": round(total_expenses, 2),
        "total_waste_loss": round(total_waste_loss, 2),
        "net_profit": round(net_profit, 2),
        "sales_count": sales_count,
        "purchases_count": purchases_count,
        "total_wasted_items": total_wasted_items,
        "top_sellers": [{"name": n, "quantity": q} for n, q in top_sellers],
        "top_stocked": [{"name": n, "quantity": q} for n, q in top_stocked],
        "recent_transactions": recent,
        "health": {
            "fresh": fresh_count,
            "warning": warning_count,
            "critical": critical_count
        }
    }

# --- Simple Recipe Suggestion Logic ---
async def suggest_recipes(user_id: str):
    user_inv = [i for i in db["inventory"] if i.get("user_id") == user_id]
    available_foods = set([item["food_name"].lower() for item in user_inv])
    recipes = [
        {"name": "Fruit Salad", "ingredients": ["apple", "banana", "orange"], "match": 0},
        {"name": "Healthy Snack", "ingredients": ["apple", "carrot"], "match": 0},
        {"name": "Smoothie", "ingredients": ["banana", "orange"], "match": 0},
        {"name": "Steamed Veggies", "ingredients": ["broccoli", "carrot"], "match": 0},
        {"name": "Junk Food Feast", "ingredients": ["pizza", "hot dog", "donut"], "match": 0}
    ]
    
    suggestions = []
    for r in recipes:
        needed = set(r["ingredients"])
        overlap = needed.intersection(available_foods)
        if len(overlap) > 0:
            match_percent = int((len(overlap) / len(needed)) * 100)
            r["match"] = match_percent
            suggestions.append(r)
            
    suggestions.sort(key=lambda x: x["match"], reverse=True)
    return suggestions
