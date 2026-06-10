from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
import json, datetime

app = FastAPI(title="Rekart Mock Backend")

# In-memory store (replace with SQLite in Phase 3)
store = {"products": [], "orders": [], "sync_log": []}

class SyncPayload(BaseModel):
    shop: str
    synced_at: str = None
    data: Any

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.datetime.utcnow().isoformat()}

@app.post("/shopify/sync/products")
def sync_products(payload: dict):
    products = payload.get("products", [])
    store["products"] = products
    store["sync_log"].append({"type": "products", "count": len(products), "at": datetime.datetime.utcnow().isoformat()})
    return {"received": True, "type": "products", "count": len(products)}

@app.post("/shopify/sync/orders")
def sync_orders(payload: dict):
    incoming_orders = payload.get("orders", [])
    existing_ids = {o["shopify_order_id"] for o in store["orders"]}
    new_orders = [o for o in incoming_orders if o["shopify_order_id"] not in existing_ids]

    store["orders"].extend(new_orders)
    store["sync_log"].append({
        "type": "orders",
        "count": len(new_orders),
        "at": datetime.datetime.utcnow().isoformat()
    })

    return {"received": True, "type": "orders", "count": len(new_orders)}

@app.get("/rekart/products")
def get_products():
    return {"products": store["products"], "count": len(store["products"])}

@app.get("/rekart/orders")
def get_orders():
    return {"orders": store["orders"], "count": len(store["orders"])}

@app.get("/rekart/sync-log")
def get_sync_log():
    return {"log": store["sync_log"]}
