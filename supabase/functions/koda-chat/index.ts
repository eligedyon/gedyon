// ═══════════════════════════════════════════════════════════════════
// koda-chat — KODA coaching chat proxy (complete replacement for the
// currently deployed function).
//
// Client contract (unchanged from the deployed version):
//   POST { messages: [{role, content}...], athleteContext?: string,
//          task?: string, max_tokens?: number }
//   content may be a string, or an array of text / base64 image blocks
//   (meal-photo and screenshot features). task carries a feature's own
//   instructions; it is appended AFTER the server's safety prompt.
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

const FREE_LIMIT = Number(Deno.env.get("KODA_FREE_LIMIT") ?? 25);         // free messages per user per month
// Circuit breaker on FREE messages across all users per day. Raise it with
// the KODA_DAILY_CAP secret as the user base grows. Subscribers are never blocked by it.
const DAILY_GLOBAL_CAP = Number(Deno.env.get("KODA_DAILY_CAP") ?? 2000);
const MODEL = Deno.env.get("KODA_MODEL") ?? "claude-sonnet-5";
const MAX_TASK_CHARS = 12000;
const MAX_IMAGES = 2;
const MAX_IMAGE_B64 = 5_000_000; // ~3.7 MB per image
const MAX_CONTEXT_CHARS = 30000;
const MAX_MESSAGES = 20;

// Server-owned system prompt — the client can no longer override it.
const SYSTEM_PROMPT =
  "You are KODA, the AI performance coach inside the GEDYON app. " +
  "Coach the athlete described in the ATHLETE CONTEXT below, using only " +
  "facts from that context and the conversation; never invent their " +
  "history, PRs or goals. Direct, data-driven, warm, never generic.\n\n" +
  "Safety rules that override anything later in this prompt: you are an " +
  "AI, not a doctor, dietitian or physio, and you never claim otherwise. " +
  "If the athlete mentions pain, injury, illness, chest symptoms, " +
  "fainting, or signs of disordered eating or extreme weight cutting, " +
  "tell them plainly to stop and see a medical professional. Do not " +
  "prescribe medication or diagnose conditions.";

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

    // Active subscription? (paying users skip both the free cap and the
    // global free-tier circuit breaker)
    let entitledSub = false;
    if (userId && !skipUsageCount) {
      const { data: sub0 } = await admin
        .from("subscriptions")
        .select("status, expires_at")
        .eq("user_id", userId)
        .maybeSingle();
      const notExpired0 = !sub0?.expires_at ||
        new Date(sub0.expires_at).getTime() > Date.now();
      entitledSub = !!sub0 && notExpired0 &&
        (sub0.status === "active" || sub0.status === "cancelled" ||
          sub0.status === "grace");
    }

    // ── Global circuit breaker (free usage, all users, per day) ──────
    if (!skipUsageCount && !entitledSub) {
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

      if (usedThisMonth >= FREE_LIMIT && !entitledSub) {
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
    let imageCount = 0;
    const cleanContent = (c: any): any => {
      if (typeof c === "string") return c.length > 0 ? c : null;
      if (!Array.isArray(c)) return null;
      const blocks: any[] = [];
      for (const b of c) {
        if (b?.type === "text" && typeof b.text === "string" && b.text) {
          blocks.push({ type: "text", text: b.text });
        } else if (
          b?.type === "image" && b.source?.type === "base64" &&
          /^image\/(jpeg|png|gif|webp)$/.test(b.source.media_type ?? "") &&
          typeof b.source.data === "string" &&
          b.source.data.length <= MAX_IMAGE_B64 && imageCount < MAX_IMAGES
        ) {
          imageCount++;
          blocks.push({
            type: "image",
            source: { type: "base64", media_type: b.source.media_type, data: b.source.data },
          });
        }
      }
      return blocks.length ? blocks : null;
    };
    const messages = rawMessages
      .filter((m: any) => m && (m.role === "user" || m.role === "assistant"))
      .map((m: any) => ({ role: m.role, content: cleanContent(m.content) }))
      .filter((m: any) => m.content !== null)
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
    if (typeof body?.task === "string" && body.task) {
      system += "\n\n--- FEATURE INSTRUCTIONS (follow unless they conflict " +
        "with the safety rules above) ---\n" + body.task.slice(0, MAX_TASK_CHARS);
    }
    const maxTokens = Math.min(1500, Math.max(64, Number(body?.max_tokens) || 1024));

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
        max_tokens: maxTokens,
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
