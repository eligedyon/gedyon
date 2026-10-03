// KODA WEEKLY REFLECTION — the sole writer of durable semantic memory.
// Out-of-band consolidation ("dreaming" pattern): reads the week's episodic
// records, recomputes readiness baselines deterministically, mines patterns
// with ONE AI call, applies low-risk writes directly, and parks anything
// consequential (VDOT moves, phase transitions) in koda_changesets for
// Eli's explicit approval. Never re-summarizes prior summaries.
//
// Deploy: supabase functions deploy koda-weekly
// Requires secrets: ANTHROPIC_API_KEY (SUPABASE_URL / SERVICE_ROLE auto-injected)
// Scheduled by pg_cron (see koda_learning_schema.sql), Sundays 21:00 UTC.

import { createClient } from "npm:@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const ANTHROPIC_API_KEY = Deno.env.get("ANTHROPIC_API_KEY")!;
const MODEL = "claude-sonnet-5";

const admin = createClient(SUPABASE_URL, SERVICE_KEY);

function json(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function daysAgo(n: number): string {
  return new Date(Date.now() - n * 864e5).toISOString().slice(0, 10);
}

Deno.serve(async (req) => {
  // Service-role callers only (the cron job)
  const auth = req.headers.get("Authorization") ?? "";
  if (!auth.includes(SERVICE_KEY)) return json(403, { error: "forbidden" });

  const today = new Date().toISOString().slice(0, 10);
  const results = { ok: 0, failed: 0, skipped: 0 };

  // Candidate users: anyone with readiness or session data in 14 days
  const { data: users } = await admin
    .from("readiness_daily")
    .select("user_id")
    .gte("reading_date", daysAgo(14));
  const userIds = [...new Set((users ?? []).map((u: any) => u.user_id))];

  for (const uid of userIds) {
    try {
      // ── 1. READINESS BASELINE (deterministic — no AI involved) ──────
      const { data: readiness } = await admin
        .from("readiness_daily")
        .select("*")
        .eq("user_id", uid)
        .gte("reading_date", daysAgo(14))
        .order("reading_date", { ascending: false });

      const rows = readiness ?? [];
      const last7 = rows.slice(0, 7).filter((r: any) => r.ln_rmssd != null);
      if (last7.length >= 3) {
        const vals = last7.map((r: any) => Number(r.ln_rmssd));
        const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
        const sd = Math.sqrt(
          vals.reduce((s, v) => s + (v - mean) ** 2, 0) / vals.length,
        );
        const swcLo = +(mean - 0.5 * sd).toFixed(3);
        const swcHi = +(mean + 0.5 * sd).toFixed(3);
        // Low-risk write: applied directly
        await admin
          .from("readiness_daily")
          .update({
            rolling7_ln_rmssd: +mean.toFixed(3),
            swc_lower: swcLo,
            swc_upper: swcHi,
          })
          .eq("user_id", uid)
          .eq("reading_date", rows[0].reading_date);
      }

      // ── 2. LESSON HYGIENE (deterministic) ───────────────────────────
      // Dormant: active lessons uncorroborated for >6 weeks
      await admin
        .from("lessons_learned")
        .update({ status: "dormant" })
        .eq("user_id", uid)
        .eq("status", "active")
        .lt("last_corroborated", daysAgo(42));

      // ── 3. GATHER THE WEEK for pattern mining ───────────────────────
      const [sessions, races, injuries, lessons, anchor, phase] =
        await Promise.all([
          admin.from("sessions_log").select("*").eq("user_id", uid)
            .gte("session_date", daysAgo(7)).order("session_date"),
          admin.from("race_results").select("*").eq("user_id", uid)
            .gte("race_date", daysAgo(7)),
          admin.from("injuries_niggles").select("*").eq("user_id", uid)
            .eq("status", "active"),
          admin.from("lessons_learned").select("*").eq("user_id", uid)
            .eq("status", "active").limit(30),
          admin.from("fitness_anchors").select("*").eq("user_id", uid)
            .eq("metric", "VDOT").is("superseded_at", null)
            .order("effective_date", { ascending: false }).limit(1),
          admin.from("phase_state").select("*").eq("user_id", uid)
            .maybeSingle(),
        ]);

      const weekHadData = (sessions.data?.length ?? 0) > 0 ||
        rows.length > 0;
      if (!weekHadData) { results.skipped++; continue; }

      // ── 4. ONE AI CALL: pattern mining + report + proposed changeset ─
      const inputs = {
        sessions: sessions.data ?? [],
        readiness_14d: rows,
        races: races.data ?? [],
        injuries: injuries.data ?? [],
        active_lessons: lessons.data ?? [],
        current_anchor: anchor.data?.[0] ?? null,
        phase: phase.data ?? null,
      };

      const system =
        `You are KODA's weekly reflection process (out-of-band consolidation). ` +
        `You are the ONLY writer of durable athlete-model facts. Work strictly from ` +
        `the structured records provided — never invent data. Rules: ` +
        `(1) PATTERN MINING: correlate readiness context_flags with next-day HRV deltas ` +
        `and session completion; a pattern needs >=3 consistent instances to become a lesson. ` +
        `(2) VDOT: only a clean race/time trial justifies an anchor move; workout-implied ` +
        `signals may at most raise confidence or suggest a test; any proposed move >0.5 ` +
        `point MUST go to the changeset, never applied. If racing at altitude, apply ~50% ` +
        `of the acute Daniels penalty (acclimatized resident) and flag the assumption. ` +
        `(3) Resolve lesson contradictions in favor of the most recent, marking the older superseded. ` +
        `(4) Output STRICT JSON only, matching: {"report": string (short, human, warm, direct), ` +
        `"new_lessons": [{"category": string, "lesson": string, "confidence": "low"|"medium", ` +
        `"evidence": string}], "corroborate_lesson_ids": [int], "supersede_lesson_ids": [int], ` +
        `"changeset": [{"what": string, "why": string, "confidence": string, "risk": string, ` +
        `"reversibility": string}]}`;

      const aiResp = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": ANTHROPIC_API_KEY,
          "anthropic-version": "2023-06-01",
        },
        body: JSON.stringify({
          model: MODEL,
          max_tokens: 1500,
          system,
          messages: [{ role: "user", content: JSON.stringify(inputs) }],
        }),
      });
      if (!aiResp.ok) throw new Error("anthropic " + aiResp.status);
      const ai = await aiResp.json();
      const text = (ai.content ?? []).filter((b: any) => b.type === "text")
        .map((b: any) => b.text).join("");
      const parsed = JSON.parse(text.slice(text.indexOf("{"), text.lastIndexOf("}") + 1));

      // ── 5. APPLY low-risk writes; PARK consequential ones ───────────
      for (const nl of parsed.new_lessons ?? []) {
        if (!nl.lesson) continue;
        await admin.from("lessons_learned").insert({
          user_id: uid,
          category: nl.category || "workout_response",
          lesson: nl.lesson,
          confidence: nl.confidence === "medium" ? "medium" : "low",
          source: "workout_implied",
          last_corroborated: today,
        });
      }
      for (const lid of parsed.corroborate_lesson_ids ?? []) {
        const cur = (lessons.data ?? []).find((l: any) => l.id === lid);
        if (!cur) continue;
        await admin.from("lessons_learned").update({
          evidence_count: (cur.evidence_count ?? 1) + 1,
          last_corroborated: today,
          confidence: (cur.evidence_count ?? 1) + 1 >= 3 && cur.confidence === "low"
            ? "medium" : cur.confidence,
        }).eq("id", lid).eq("user_id", uid);
      }
      for (const lid of parsed.supersede_lesson_ids ?? []) {
        await admin.from("lessons_learned").update({ status: "superseded" })
          .eq("id", lid).eq("user_id", uid);
      }

      // Weekly report + changeset → review queue (and the morning-message
      // channel, so the report surfaces as KODA's first bubble Monday)
      await admin.from("koda_changesets").insert({
        user_id: uid,
        week_of: daysAgo(7),
        changeset: parsed.changeset ?? [],
        report: parsed.report ?? "",
      });
      if (parsed.report) {
        await admin.from("koda_messages").upsert({
          user_id: uid,
          date: today,
          message: "WEEKLY REVIEW — " + parsed.report,
        }, { onConflict: "user_id,date", ignoreDuplicates: true });
      }

      results.ok++;
    } catch (e) {
      console.error("koda-weekly user failed", uid, e);
      results.failed++;
    }
  }

  return json(200, results);
});
