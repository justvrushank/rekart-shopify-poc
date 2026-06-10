from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
import json, datetime
from datetime import date, timedelta

app = FastAPI(title="Rekart Mock Backend")

# In-memory store (replace with SQLite in Phase 3)
store = {"products": [], "orders": [], "sync_log": [], "subscriptions": [], "deliveries": []}

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


@app.post("/shopify/sync/subscription")
def sync_subscription(payload: dict):
    contract = payload.get("contract", {})
    topic = payload.get("topic", "")
    shop = payload.get("shop", "")

    contract_id = contract.get("admin_graphql_api_id") or contract.get("id")

    existing = next((s for s in store["subscriptions"] if s["shopify_contract_id"] == str(contract_id)), None)

    if existing:
        if "activate" in topic:
            existing["status"] = "ACTIVE"
        elif "pause" in topic:
            existing["status"] = "PAUSED"
        elif "cancel" in topic:
            existing["status"] = "CANCELLED"
        existing["updated_at"] = datetime.datetime.utcnow().isoformat()
    else:
        new_record = {
            "id": len(store["subscriptions"]) + 1,
            "shopify_contract_id": str(contract_id),
            "shopify_customer_id": str(contract.get("customer_id", "")),
            "selling_plan_id": str(contract.get("selling_plan_id", "")),
            "interval": "DAY",
            "interval_count": 1,
            "next_run_date": (date.today() + timedelta(days=1)).isoformat(),
            "status": "ACTIVE",
            "shop": shop,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }
        store["subscriptions"].append(new_record)

    return {"received": True, "topic": topic, "contract_id": contract_id}


@app.post("/rekart/run-daily-job")
def run_daily_job():
    today = date.today().isoformat()
    dispatched = []

    for sub in store["subscriptions"]:
        if sub["status"] == "ACTIVE" and sub["next_run_date"] <= today:
            delivery = {
                "id": len(store["deliveries"]) + 1,
                "contract_id": sub["id"],
                "shopify_contract_id": sub["shopify_contract_id"],
                "delivery_date": today,
                "status": "PENDING",
                "created_at": datetime.datetime.utcnow().isoformat(),
            }
            store["deliveries"].append(delivery)
            next_date = date.fromisoformat(sub["next_run_date"]) + timedelta(days=1)
            sub["next_run_date"] = next_date.isoformat()
            dispatched.append(delivery)

    return {"date": today, "deliveries_created": len(dispatched), "deliveries": dispatched}


@app.get("/rekart/subscriptions")
def get_subscriptions():
    return {"subscriptions": store["subscriptions"], "count": len(store["subscriptions"])}


@app.get("/rekart/deliveries")
def get_deliveries():
    return {"deliveries": store["deliveries"], "count": len(store["deliveries"])}
