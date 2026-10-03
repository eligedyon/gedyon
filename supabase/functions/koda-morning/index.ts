// ═══════════════════════════════════════════════════════════════════
// koda-morning — server-initiated daily KODA check-in.
//
// Triggered by pg_cron (see koda_morning.sql) at 11:30 UTC with the
// service-role key in the Authorization header. Can also be triggered
// manually with curl for testing (see supabase/DEPLOY.md).
//
// For each user with a HealthKit sync in the last 14 days (users with a
// 14+ day data gap are owned by the Gap Protocol, not the morning ping):
//   1. Skip if koda_messages already has a row for (user, today).
//   2. Gather 7d health metrics, 14d workouts, plan position, gap summary.
//   3. One Anthropic call → short morning check-in in KODA's voice.
//   4. Insert into koda_messages.
// Each user is wrapped in try/catch so one failure never kills the batch.
// Morning messages do NOT count against the user's 25 free chat messages
// (this function never touches koda_usage).
//
// Secrets: ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
// ═══════════════════════════════════════════════════════════════════

import { createClient } from "npm:@supabase/supabase-js@2";

const ANTHROPIC_API_KEY = Deno.env.get("ANTHROPIC_API_KEY") ?? "";
const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";

const MODEL = "claude-sonnet-5";

const SYSTEM_PROMPT =
  "You are KODA — elite AI performance coach for Elias Gedyon, " +
  "middle-distance runner targeting the 2028 Olympic Trials. " +
  "Write a short morning check-in (2-4 sentences) in KODA's voice: " +
  "today's call, adjusted for recovery and any recent gap. Direct, warm, " +
  'specific to the numbers. No greetings like "Good morning" every time — vary it.';

const admin = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
  auth: { persistSession: false },
});

function daysAgoISO(days: number): string {
  return new Date(Date.now() - days * 86400_000).toISOString().slice(0, 10);
}

async function generateCheckIn(context: string): Promise<string> {
  const resp = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: 300,
      system: SYSTEM_PROMPT,
      messages: [{ role: "user", content: context }],
    }),
  });
  if (!resp.ok) {
    throw new Error(`anthropic ${resp.status}: ${await resp.text()}`);
  }
  const data = await resp.json();
  const text = (data.content ?? [])
    .filter((b: any) => b.type === "text")
    .map((b: any) => b.text)
    .join("")
    .trim();
  if (!text) throw new Error("anthropic returned empty text");
  return text;
}

Deno.serve(async (req: Request) => {
  try {
    // ── Guard: service-role callers only ─────────────────────────────
    const token = (req.headers.get("Authorization") ?? "")
      .replace(/^Bearer\s+/i, "").trim();
    if (!SERVICE_ROLE_KEY || token !== SERVICE_ROLE_KEY) {
      return new Response(JSON.stringify({ error: "forbidden" }), {
        status: 403,
        headers: { "Content-Type": "application/json" },
      });
    }

    const today = new Date().toISOString().slice(0, 10);
    const cutoff14d = new Date(Date.now() - 14 * 86400_000).toISOString();

    // Users with recent HealthKit data (Gap Protocol owns the rest)
    const { data: synced, error: syncErr } = await admin
      .from("sync_state")
      .select("user_id, last_healthkit_sync")
      .gt("last_healthkit_sync", cutoff14d);
    if (syncErr) throw syncErr;

    let ok = 0;
    let failed = 0;
    let skipped = 0;

    for (const row of synced ?? []) {
      const userId = row.user_id as string;
      try {
        // Hard cap: one message per user per day
        const { data: existing } = await admin
          .from("koda_messages")
          .select("id")
          .eq("user_id", userId)
          .eq("date", today)
          .maybeSingle();
        if (existing) {
          skipped++;
          continue;
        }

        // ── Gather context ────────────────────────────────────────────
        const [metricsQ, workoutsQ, planQ] = await Promise.all([
          admin
            .from("health_metrics")
            .select("date, metric, value, unit")
            .eq("user_id", userId)
            .in("metric", ["hrv", "resting_hr", "sleep_hours"])
            .gte("date", daysAgoISO(7))
            .order("date", { ascending: true }),
          admin
            .from("workouts")
            .select("date, minutes, distance_mi, workout_type, effort")
            .eq("user_id", userId)
            .gte("date", daysAgoISO(14))
            .order("date", { ascending: true }),
          admin
            .from("plan_position")
            .select("plan_start, week_num, phase, last_adjustment")
            .eq("user_id", userId)
            .maybeSingle(),
        ]);

        const metrics = metricsQ.data ?? [];
        const workouts = workoutsQ.data ?? [];
        const plan = planQ.data;

        // Simple gap summary: days since the most recent workout
        let gapLine = "No workouts logged in the last 14 days.";
        if (workouts.length > 0) {
          const lastDate = workouts[workouts.length - 1].date as string;
          const gapDays = Math.floor(
            (Date.parse(today) - Date.parse(lastDate)) / 86400_000,
          );
          gapLine = `Days since last workout: ${gapDays} (last on ${lastDate}).`;
        }

        const context = [
          `Date: ${today}`,
          "",
          "PLAN POSITION: " + (plan
            ? `week ${plan.week_num ?? "?"} (${plan.phase ?? "unknown phase"}), ` +
              `plan started ${plan.plan_start}` +
              (plan.last_adjustment
                ? `, last adjustment: ${plan.last_adjustment}`
                : "")
            : "not set"),
          "",
          gapLine,
          "",
          "LAST 7 DAYS HEALTH METRICS (hrv / resting_hr / sleep_hours):",
          metrics.length
            ? metrics
              .map((m: any) => `- ${m.date} ${m.metric}: ${m.value}${m.unit ? " " + m.unit : ""}`)
              .join("\n")
            : "- none",
          "",
          "LAST 14 DAYS WORKOUTS:",
          workouts.length
            ? workouts
              .map((w: any) =>
                `- ${w.date}: ${w.workout_type ?? "workout"} ${w.minutes}min` +
                (w.distance_mi ? ` ${w.distance_mi}mi` : "") +
                (w.effort ? ` effort ${w.effort}/10` : "")
              )
              .join("\n")
            : "- none",
          "",
          "Write today's morning check-in.",
        ].join("\n");

        const message = await generateCheckIn(context);

        const { error: insErr } = await admin
          .from("koda_messages")
          .insert({ user_id: userId, date: today, message });
        if (insErr) throw insErr;

        ok++;
      } catch (err) {
        failed++;
        console.error(`koda-morning failed for user ${userId}`, err);
      }
    }

    return new Response(
      JSON.stringify({ ok, failed, skipped, candidates: synced?.length ?? 0 }),
      { headers: { "Content-Type": "application/json" } },
    );
  } catch (err) {
    console.error("koda-morning unhandled error", err);
    return new Response(JSON.stringify({ error: "internal" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
});
