import { authenticate } from "../shopify.server";

export const action = async ({ request }) => {
  const { topic, shop, payload } = await authenticate.webhook(request);

  console.log(`[Rekart] Webhook received: ${topic} from ${shop}`);
  console.log("[Rekart] Contract payload:", JSON.stringify(payload, null, 2));

  try {
    await fetch("http://localhost:8000/shopify/sync/subscription", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        shop,
        topic,
        contract: payload,
      }),
    });
  } catch (err) {
    console.error("[Rekart] Failed to mirror to backend:", err.message);
  }

  return new Response(null, { status: 200 });
};
