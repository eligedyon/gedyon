// ═══════════════════════════════════════════════════════════════════
// delete-account — lets a signed-in user permanently delete their
// account from inside the app (required by App Store guideline 5.1.1(v)
// for any app that lets people create an account).
//
// Client contract:
//   POST {}  Headers: Authorization: Bearer <user JWT>
//   → 200 { ok: true }
//   → 401 { code: 'AUTH_REQUIRED' }
//   → 500 { code: 'DELETE_FAILED', message }
//
// Every table created in supabase/*.sql references auth.users with
// ON DELETE CASCADE, so deleting the auth user removes those rows.
// user_data (the app's main JSON blob) is deleted explicitly first in
// case it was created without a cascade.
//
// Secrets: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY (set automatically
// by Supabase for deployed functions).
// Deploy:  supabase functions deploy delete-account
// ═══════════════════════════════════════════════════════════════════

import { createClient } from "npm:@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS, "Content-Type": "application/json" },
  });
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ code: "METHOD_NOT_ALLOWED" }, 405);

  const token = (req.headers.get("Authorization") ?? "").replace(/^Bearer\s+/i, "");
  if (!token) return json({ code: "AUTH_REQUIRED" }, 401);

  const admin = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  // Identify the caller from their own JWT — a user can only delete themselves.
  const { data: userData, error: userErr } = await admin.auth.getUser(token);
  const user = userData?.user;
  if (userErr || !user) return json({ code: "AUTH_REQUIRED" }, 401);

  try {
    await admin.from("user_data").delete().eq("user_id", user.id);
    const { error } = await admin.auth.admin.deleteUser(user.id);
    if (error) throw error;
    return json({ ok: true });
  } catch (e) {
    return json({ code: "DELETE_FAILED", message: String((e as Error)?.message ?? e) }, 500);
  }
});
