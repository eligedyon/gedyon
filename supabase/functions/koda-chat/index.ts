// ═══════════════════════════════════════════════════════════════════
// koda-chat — KODA coaching chat proxy (complete replacement for the
// currently deployed function).
//
// Client contract (unchanged from the deployed version):
//   POST { messages: [{role, content}...], athleteContext: string }
//   Headers: Content-Type: application/json, Authorization: Bearer <user JWT>
//   → 200 { reply: string }
//
// New server-side behavior:
//   • 401 { code: 'AUTH_REQUIRED' }  — no valid authenticated user
//   • 200 { code: 'LIMIT_REACHED', used, limit } — free cap hit, no sub
//   • 200 { code: 'CAPACITY' }      — global daily circuit breaker tripped
//   • 502 { code: 'AI_ERROR' }      — Anthropic call failed
//
// Usage is incremented ONLY after a successful AI response. Internal
// callers (service-role key, or X-Koda-Internal secret) may pass
// { skipUsageCount: true } so server-initiated messages don't count.
//
// Secrets: ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
//          KODA_INTERNAL_SECRET (optional)
// ═══════════════════════════════════════════════════════════════════

import { createClient } from "npm:@supabase/supabase-js@2";

const ANTHROPIC_API_KEY = Deno.env.get("ANTHROPIC_API_KEY") ?? "";
const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
const KODA_INTERNAL_SECRET = Deno.env.get("KODA_INTERNAL_SECRET") ?? "";

const FREE_LIMIT = 25;      // free messages per user per month
const DAILY_GLOBAL_CAP = 2000; // circuit breaker across all users per day
const MODEL = "claude-sonnet-5";
const MAX_CONTEXT_CHARS = 30000;
const MAX_MESSAGES = 20;

// Server-owned system prompt — the client can no longer override it.
const SYSTEM_PROMPT =
  "You are KODA — elite AI performance coach for Elias Gedyon, " +
  "middle-distance runner targeting the 2028 Olympic Trials. " +
  "Direct, data-driven, warm, never generic.";

const CORS_HEADERS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-koda-internal",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
  });
}

// Admin client — service role bypasses RLS for usage/subscription reads + rpc.
const admin = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
  auth: { persistSession: false },
});

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: CORS_HEADERS });
  }
  if (req.method !== "POST") {
    return json(405, { code: "METHOD_NOT_ALLOWED" });
  }

  try {
    const body = await req.json().catch(() => ({}));

    // ── Auth ─────────────────────────────────────────────────────────
    const authHeader = req.headers.get("Authorization") ?? "";
    const token = authHeader.replace(/^Bearer\s+/i, "").trim();

    // Internal callers: the service-role key itself, or the shared secret
    // header (used by koda-morning). They skip user auth and metering when
    // skipUsageCount is set.
    const isInternal = (token !== "" && token === SERVICE_ROLE_KEY) ||
      (KODA_INTERNAL_SECRET !== "" &&
        req.headers.get("X-Koda-Internal") === KODA_INTERNAL_SECRET);
    const skipUsageCount = isInternal && body?.skipUsageCount === true;

    let userId: string | null = null;
    if (!isInternal) {
      if (!token) return json(401, { code: "AUTH_REQUIRED" });
      const { data, error } = await admin.auth.getUser(token);
      if (error || !data?.user) return json(401, { code: "AUTH_REQUIRED" });
      userId = data.user.id;
    }

    const today = new Date().toISOString().slice(0, 10); // 'YYYY-MM-DD'
    const month = today.slice(0, 7);                     // 'YYYY-MM'

    // ── Global circuit breaker (all users, per day) ──────────────────
    if (!skipUsageCount) {
      const { data: daily } = await admin
        .from("koda_daily")
        .select("total")
        .eq("date", today)
        .maybeSingle();
      if ((daily?.total ?? 0) >= DAILY_GLOBAL_CAP) {
        return json(200, { code: "CAPACITY" });
      }
    }

    // ── Per-user monthly cap (BEFORE calling Anthropic) ──────────────
    let usedThisMonth = 0;
    if (userId && !skipUsageCount) {
      const { data: usage } = await admin
        .from("koda_usage")
        .select("message_count")
        .eq("user_id", userId)
        .eq("month", month)
        .maybeSingle();
      usedThisMonth = usage?.message_count ?? 0;

      if (usedThisMonth >= FREE_LIMIT) {
        const { data: sub } = await admin
          .from("subscriptions")
          .select("status, expires_at")
          .eq("user_id", userId)
          .maybeSingle();

        const now = Date.now();
        const notExpired = !sub?.expires_at ||
          new Date(sub.expires_at).getTime() > now;
        // 'active' → unlimited; 'cancelled'/'grace' keep access until expires_at.
        const entitled = !!sub && notExpired &&
          (sub.status === "active" || sub.status === "cancelled" ||
            sub.status === "grace");

        if (!entitled) {
          return json(200, {
            code: "LIMIT_REACHED",
            used: usedThisMonth,
            limit: FREE_LIMIT,
          });
        }
      }
    }

    // ── Validate + shape the request for Anthropic ───────────────────
    const rawMessages = Array.isArray(body?.messages) ? body.messages : [];
    const messages = rawMessages
      .filter((m: any) =>
        m && (m.role === "user" || m.role === "assistant") &&
        typeof m.content === "string" && m.content.length > 0
      )
      .map((m: any) => ({ role: m.role, content: m.content }))
      .slice(-MAX_MESSAGES);

    if (messages.length === 0 || messages[0].role !== "user") {
      // Anthropic requires the first message to be a user turn.
      while (messages.length && messages[0].role !== "user") messages.shift();
      if (messages.length === 0) return json(400, { code: "BAD_REQUEST" });
    }

    let system = SYSTEM_PROMPT;
    if (typeof body?.athleteContext === "string" && body.athleteContext) {
      system += "\n\n--- ATHLETE CONTEXT ---\n" +
        body.athleteContext.slice(0, MAX_CONTEXT_CHARS);
    }

    // ── Call Anthropic Messages API ──────────────────────────────────
    const aiResp = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: MODEL,
        max_tokens: 1024,
        system,
        messages,
      }),
    });

    if (!aiResp.ok) {
      console.error("anthropic error", aiResp.status, await aiResp.text());
      return json(502, { code: "AI_ERROR" });
    }

    const data = await aiResp.json();
    const reply = (data.content ?? [])
      .filter((b: any) => b.type === "text")
      .map((b: any) => b.text)
      .join("");

    // ── Increment usage AFTER the successful AI response ─────────────
    if (!skipUsageCount && userId) {
      const [u, d] = await Promise.all([
        admin.rpc("increment_koda_usage", { p_user_id: userId, p_month: month }),
        admin.rpc("increment_koda_daily", { p_date: today }),
      ]);
      if (u.error) console.error("increment_koda_usage failed", u.error);
      if (d.error) console.error("increment_koda_daily failed", d.error);
    }

    // used reflects THIS message so the client counter is server-truth
    return json(200, {
      reply,
      used: skipUsageCount ? undefined : usedThisMonth + 1,
      limit: skipUsageCount ? undefined : FREE_LIMIT,
    });
  } catch (err) {
    console.error("koda-chat unhandled error", err);
    return json(502, { code: "AI_ERROR" });
  }
});
