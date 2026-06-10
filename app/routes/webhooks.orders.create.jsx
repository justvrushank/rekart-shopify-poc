import { authenticate } from "../shopify.server";

export const action = async ({ request }) => {
    try {
        const { topic, shop, payload } = await authenticate.webhook(request);

        console.log("Webhook authenticated:", topic, shop);

        const backendPayload = {
            shop,
            synced_at: new Date().toISOString(),
            orders: [
                {
                    shopify_order_id: payload.admin_graphql_api_id || `gid://shopify/Order/${payload.id}`,
                    name: payload.name,
                    created_at: payload.created_at,
                    financial_status: payload.financial_status,
                    fulfillment_status: payload.fulfillment_status,
                    customer: payload.customer
                        ? {
                            firstName: payload.customer.first_name,
                            lastName: payload.customer.last_name,
                            email: payload.customer.email,
                        }
                        : null,
                    line_items: (payload.line_items || []).map((item) => ({
                        title: item.title,
                        quantity: item.quantity,
                    })),
                },
            ],
        };

        console.log("Sending to backend:", JSON.stringify(backendPayload, null, 2));

        const res = await fetch("http://127.0.0.1:8000/shopify/sync/orders", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(backendPayload),
        });

        const text = await res.text();
        console.log("Backend response:", res.status, text);

        return new Response("Webhook processed", { status: 200 });
    } catch (error) {
        console.error("Webhook error:", error);
        return new Response("Webhook failed", { status: 500 });
    }
};