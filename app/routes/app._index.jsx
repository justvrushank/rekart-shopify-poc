import { useLoaderData } from "react-router";
import { useFetcher } from "react-router";
import { boundary } from "@shopify/shopify-app-react-router/server";
import { authenticate } from "../shopify.server";

export const loader = async ({ request }) => {
  await authenticate.admin(request);
  return null;
};

export const action = async ({ request }) => {
  const { admin, session } = await authenticate.admin(request);
  const formData = await request.formData();
  const syncType = formData.get("syncType");
  const shop = session.shop;

  if (syncType === "products") {
    const response = await admin.graphql(`
      {
        products(first: 50) {
          edges {
            node {
              id
              title
              status
              vendor
              variants(first: 10) {
                edges {
                  node {
                    sku
                    price
                    inventoryQuantity
                  }
                }
              }
            }
          }
        }
      }
    `);
    const { data } = await response.json();
    const products = data.products.edges.map(({ node }) => ({
      shopify_product_id: node.id,
      title: node.title,
      status: node.status,
      vendor: node.vendor,
      variants: node.variants.edges.map(({ node: v }) => ({
        sku: v.sku,
        price: v.price,
        inventory_quantity: v.inventoryQuantity,
      })),
    }));

    await fetch("http://localhost:8000/shopify/sync/products", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ shop, synced_at: new Date().toISOString(), products }),
    });

    return { success: true, type: "products", count: products.length };
  }

  if (syncType === "orders") {
    const response = await admin.graphql(`
      {
        orders(first: 50) {
          edges {
            node {
              id
              name
              createdAt
              displayFinancialStatus
              displayFulfillmentStatus
              customer {
                firstName
                lastName
                email
              }
              lineItems(first: 5) {
                edges {
                  node {
                    title
                    quantity
                  }
                }
              }
            }
          }
        }
      }
    `);
    const { data } = await response.json();
    const orders = data.orders.edges.map(({ node }) => ({
      shopify_order_id: node.id,
      name: node.name,
      created_at: node.createdAt,
      financial_status: node.displayFinancialStatus,
      fulfillment_status: node.displayFulfillmentStatus,
      customer: node.customer,
      line_items: node.lineItems.edges.map(({ node: li }) => ({
        title: li.title,
        quantity: li.quantity,
      })),
    }));

    await fetch("http://localhost:8000/shopify/sync/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ shop, synced_at: new Date().toISOString(), orders }),
    });

    return { success: true, type: "orders", count: orders.length };
  }

  return { success: false };
};

export default function Index() {
  const fetcher = useFetcher();
  const isLoading = fetcher.state !== "idle";
  const result = fetcher.data;

  return (
    <s-page heading="Rekart × Shopify Sync">

      {result?.success && (
        <s-section heading="✅ Sync Complete">
          <s-box padding="base" borderWidth="base" borderRadius="base" background="subdued">
            <s-paragraph>
              {result.count} {result.type} synced to Rekart backend successfully.
            </s-paragraph>
          </s-box>
        </s-section>
      )}

      {result?.success === false && (
        <s-section heading="❌ Sync Failed">
          <s-box padding="base" borderWidth="base" borderRadius="base" background="subdued">
            <s-paragraph>Something went wrong. Check the backend is running on port 8000.</s-paragraph>
          </s-box>
        </s-section>
      )}

      <s-section heading="Sync Controls">
        <s-stack direction="inline" gap="base">
          <fetcher.Form method="post">
            <input type="hidden" name="syncType" value="products" />
            <button type="submit" disabled={isLoading}>
              {isLoading && fetcher.formData?.get("syncType") === "products"
                ? "Syncing products..."
                : "Sync Products to Rekart"}
            </button>
          </fetcher.Form>

          <fetcher.Form method="post">
            <input type="hidden" name="syncType" value="orders" />
            <button type="submit" disabled={isLoading}>
              {isLoading && fetcher.formData?.get("syncType") === "orders"
                ? "Syncing orders..."
                : "Sync Orders to Rekart"}
            </button>
          </fetcher.Form>
        </s-stack>
      </s-section>

      <s-section heading="Backend Status">
        <s-box padding="base" borderWidth="base" borderRadius="base" background="subdued">
          <s-paragraph>Rekart backend: localhost:8000</s-paragraph>
          <s-paragraph>Docs: http://localhost:8000/docs</s-paragraph>
        </s-box>
      </s-section>

    </s-page>
  );
}

export const headers = (headersArgs) => boundary.headers(headersArgs);