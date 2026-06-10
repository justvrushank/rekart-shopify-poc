# Rekart Shopify POC (Milk Subscription)

A proof-of-concept Shopify embedded app for a **daily milk subscription** service, mirroring order and product data from Shopify into the Rekart backend in real time.

---

## Overview

This POC demonstrates:
- Installing a Shopify embedded app using the React Router + Shopify CLI template
- Syncing products and orders from Shopify Admin GraphQL to a FastAPI backend
- Receiving live `orders/create` webhooks and appending new orders without duplicates
- A debug/control panel in the app home for manual sync triggers

---

## Tech Stack

| Layer | Technology |
|---|---|
| Shopify CLI | `@shopify/cli` v3 |
| Frontend framework | React Router v7 (Shopify template) |
| Shopify API client | `@shopify/shopify-app-react-router` |
| UI components | Polaris Web Components (`s-page`, `s-section`, …) |
| Backend (POC) | FastAPI (Python 3) — in-memory store |
| Backend (production) | FastAPI + PostgreSQL (Phase 3) |
| ORM / local DB | Prisma + SQLite (dev) |
| GraphQL | Shopify Admin GraphQL API |

---

## Project Structure

```
rekart-dev-app/
├── app/
│   ├── routes/
│   │   ├── app._index.jsx          # Sync control panel
│   │   └── webhooks.orders.create.jsx  # orders/create webhook handler
│   └── shopify.server.js           # Shopify SDK config
├── rekart-backend/
│   └── main.py                     # FastAPI backend (POC)
├── shopify.app.toml                # App config & scopes
├── shopify.web.toml                # Web process config
├── prisma/                         # DB schema & migrations
└── .env.example                    # Required env vars template
```

---

## Setup Instructions

### Prerequisites
- Node.js ≥ 18
- Python ≥ 3.10
- Shopify Partners account + development store
- [Shopify CLI](https://shopify.dev/docs/apps/tools/cli) installed globally (`npm i -g @shopify/cli`)

### 1. Clone and install dependencies

```bash
git clone https://github.com/justvrushank/rekart-shopify-poc.git
cd rekart-shopify-poc
npm install
```

### 2. Set up environment variables

```bash
cp .env.example .env
# Fill in SHOPIFY_API_KEY, SHOPIFY_API_SECRET, etc.
```

### 3. Set up the database

```bash
npx prisma generate
npx prisma migrate deploy
```

### 4. Start the FastAPI backend

```bash
cd rekart-backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install fastapi uvicorn
uvicorn main:app --reload --port 8000
```

Backend docs available at: `http://localhost:8000/docs`

### 5. Start the Shopify app (dev tunnel)

```bash
# From project root
shopify app dev
```

Follow the prompts to select your Partners org and dev store. The CLI opens a tunnel and installs the app on your dev store.

### 6. Reinstall after scope changes

If `shopify.app.toml` scopes are updated:

```bash
shopify app deploy   # push new scopes to Partners dashboard
shopify app dev      # triggers OAuth reinstall in browser
```

---

## API Endpoints (FastAPI backend)

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/shopify/sync/products` | Receive & store product list |
| POST | `/shopify/sync/orders` | Append new orders (deduped by ID) |
| GET | `/rekart/products` | View stored products |
| GET | `/rekart/orders` | View stored orders |
| GET | `/rekart/sync-log` | View sync history |

---

## Shopify Scopes

```
read_products, write_products,
read_metaobjects, write_metaobjects,
read_metaobject_definitions, write_metaobject_definitions,
read_orders, read_inventory, read_customers
```

---

## Roadmap

- [x] Phase 1: Shopify app install + GraphQL access verified
- [x] Phase 2: Manual product/order sync + `orders/create` webhook
- [ ] Phase 3: PostgreSQL persistence + Rekart backend integration
- [ ] Phase 4: Subscription plan UI + recurring order logic
- [ ] Phase 5: Production deploy

---

## Security Notes

- `.env` is excluded from git via `.gitignore` — **never commit real credentials**
- Use `.env.example` as the template for all required variables
- Shopify webhook authenticity is verified via `authenticate.webhook(request)` in the route handler
