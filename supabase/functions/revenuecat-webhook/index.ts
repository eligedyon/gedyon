// ═══════════════════════════════════════════════════════════════════
// revenuecat-webhook — minimal RevenueCat webhook receiver.
//
// RevenueCat → Project settings → Integrations → Webhooks:
//   URL:  https://qfmklkgvobfckcippwyh.supabase.co/functions/v1/revenuecat-webhook
//   Authorization header value: the same string set as REVENUECAT_WEBHOOK_SECRET
//
// IMPORTANT: deploy with --no-verify-jwt — RevenueCat does not send a
// Supabase JWT; auth is the shared secret comparison below.
//
// app_user_id is configured in the app to be the Supabase auth user id.
//
// Secrets: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, REVENUECAT_WEBHOOK_SECRET
// ═══════════════════════════════════════════════════════════════════

import { createClient } from "npm:@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
const WEBHOOK_SECRET = Deno.env.get("REVENUECAT_WEBHOOK_SECRET") ?? "";

const admin = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
  auth: { persistSession: false },
});

// RevenueCat event type → subscriptions.status
const STATUS_MAP: Record<string, string> = {
  INITIAL_PURCHASE: "active",
  RENEWAL: "active",
  UNCANCELLATION: "active",
  PRODUCT_CHANGE: "active",
  CANCELLATION: "cancelled", // access continues until expires_at
  EXPIRATION: "expired",
  BILLING_ISSUE: "grace",
};

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

Deno.serve(async (req: Request) => {
  try {
    if (req.method !== "POST") return json(405, { error: "method" });

    // Shared-secret auth. RevenueCat sends the configured value verbatim;
    // accept it bare or with a "Bearer " prefix.
    const auth = req.headers.get("Authorization") ?? "";
    const bare = auth.replace(/^Bearer\s+/i, "");
    if (!WEBHOOK_SECRET || (auth !== WEBHOOK_SECRET && bare !== WEBHOOK_SECRET)) {
      return json(401, { error: "unauthorized" });
    }

    const payload = await req.json().catch(() => null);
    const event = payload?.event;
    if (!event?.type) return json(400, { error: "no event" });

    const status = STATUS_MAP[event.type];
    if (!status) {
      // TEST, TRANSFER, SUBSCRIPTION_PAUSED, etc. — acknowledge, do nothing.
      return json(200, { ignored: event.type });
    }

    const userId: string | undefined = event.app_user_id;
    if (!userId || !UUID_RE.test(userId)) {
      // Anonymous RevenueCat id ($RCAnonymousID:...) — not a Supabase user.
      // Acknowledge so RevenueCat doesn't retry forever.
      console.warn("skipping non-uuid app_user_id", userId);
      return json(200, { skipped: "app_user_id is not a supabase uuid" });
    }

    const { error } = await admin.from("subscriptions").upsert({
      user_id: userId,
      status,
      product_id: event.product_id ?? null,
      expires_at: event.expiration_at_ms
        ? new Date(event.expiration_at_ms).toISOString()
        : null,
      environment: event.environment ?? null,
      updated_at: new Date().toISOString(),
    });

    if (error) {
      console.error("subscriptions upsert failed", error);
      return json(500, { error: "db" }); // RevenueCat will retry
    }

    return json(200, { ok: true, type: event.type, status });
  } catch (err) {
    console.error("revenuecat-webhook unhandled error", err);
    return json(500, { error: "internal" });
  }
});
