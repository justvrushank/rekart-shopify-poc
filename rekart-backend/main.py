from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional
import datetime
from datetime import date, timedelta

app = FastAPI(title="Rekart Backend - Shopify POC")

store = {
    "subscriptions": [],
    "deliveries": [],
    "sync_log": []
}

# ── Health ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.datetime.utcnow().isoformat()}

# ── Subscribe redirect landing page ─────────────────────────────────────────

@app.get("/subscribe", response_class=HTMLResponse)
def subscribe_landing(shop: str, product_id: str, plan: str = "daily"):
    """
    Customer lands here after clicking Subscribe on Shopify storefront.
    In production this would be a full checkout page.
    For POC it confirms the subscription and creates the record.
    """
    # Create subscription record
    sub_id = len(store["subscriptions"]) + 1
    new_sub = {
        "id": sub_id,
        "shop": shop,
        "shopify_product_id": product_id,
        "plan": plan,
        "interval": "DAY",
        "interval_count": 1,
        "next_run_date": (date.today() + timedelta(days=1)).isoformat(),
        "status": "ACTIVE",
        "created_at": datetime.datetime.utcnow().isoformat(),
        "updated_at": datetime.datetime.utcnow().isoformat(),
    }
    store["subscriptions"].append(new_sub)

    return f"""
    <html>
      <body style="font-family: sans-serif; max-width: 600px; margin: 60px auto; text-align: center;">
        <h1>🥛 Subscription Confirmed!</h1>
        <p>Your daily milk delivery subscription has been created.</p>
        <table style="margin: 20px auto; text-align: left; border-collapse: collapse;">
          <tr><td style="padding: 8px; font-weight: bold;">Subscription ID</td><td style="padding: 8px;">#{sub_id}</td></tr>
          <tr><td style="padding: 8px; font-weight: bold;">Shop</td><td style="padding: 8px;">{shop}</td></tr>
          <tr><td style="padding: 8px; font-weight: bold;">Product ID</td><td style="padding: 8px;">{product_id}</td></tr>
          <tr><td style="padding: 8px; font-weight: bold;">Plan</td><td style="padding: 8px;">Daily Delivery</td></tr>
          <tr><td style="padding: 8px; font-weight: bold;">First Delivery</td><td style="padding: 8px;">{new_sub['next_run_date']}</td></tr>
          <tr><td style="padding: 8px; font-weight: bold;">Status</td><td style="padding: 8px; color: green;">ACTIVE</td></tr>
        </table>
        <p style="margin-top: 30px;"><a href="/rekart/subscriptions" style="color: #2c6e49;">View all subscriptions →</a></p>
      </body>
    </html>
    """

# ── Subscription management ──────────────────────────────────────────────────

@app.get("/rekart/subscriptions")
def get_subscriptions():
    return {"subscriptions": store["subscriptions"], "count": len(store["subscriptions"])}

@app.get("/rekart/deliveries")
def get_deliveries():
    return {"deliveries": store["deliveries"], "count": len(store["deliveries"])}

@app.post("/rekart/run-daily-job")
def run_daily_job():
    today = date.today().isoformat()
    dispatched = []

    for sub in store["subscriptions"]:
        if sub["status"] == "ACTIVE" and sub["next_run_date"] <= today:
            delivery = {
                "id": len(store["deliveries"]) + 1,
                "subscription_id": sub["id"],
                "shop": sub["shop"],
                "shopify_product_id": sub["shopify_product_id"],
                "delivery_date": today,
                "status": "PENDING",
                "created_at": datetime.datetime.utcnow().isoformat(),
            }
            store["deliveries"].append(delivery)
            next_date = date.fromisoformat(sub["next_run_date"]) + timedelta(days=1)
            sub["next_run_date"] = next_date.isoformat()
            dispatched.append(delivery)

    return {
        "date": today,
        "deliveries_created": len(dispatched),
        "deliveries": dispatched
    }

@app.post("/rekart/subscriptions/{sub_id}/pause")
def pause_subscription(sub_id: int):
    sub = next((s for s in store["subscriptions"] if s["id"] == sub_id), None)
    if not sub:
        return {"error": "Not found"}, 404
    sub["status"] = "PAUSED"
    sub["updated_at"] = datetime.datetime.utcnow().isoformat()
    return {"status": "paused", "subscription": sub}

@app.post("/rekart/subscriptions/{sub_id}/cancel")
def cancel_subscription(sub_id: int):
    sub = next((s for s in store["subscriptions"] if s["id"] == sub_id), None)
    if not sub:
        return {"error": "Not found"}, 404
    sub["status"] = "CANCELLED"
    sub["updated_at"] = datetime.datetime.utcnow().isoformat()
    return {"status": "cancelled", "subscription": sub}

# ── Sync log ─────────────────────────────────────────────────────────────────

@app.get("/rekart/sync-log")
def get_sync_log():
    return {"log": store["sync_log"]}
