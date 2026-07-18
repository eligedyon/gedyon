# KODA Adaptive Learning — what was built and how to turn it on

Implements the three-tier memory blueprint: doctrine stays in KODA's system
prompt, evolving athlete facts live in queryable Supabase tables read at
session start, live health data is computed fresh — never baked into prompts.

## The pieces

| Piece | File | Role |
|---|---|---|
| Memory schema (9 tables, RLS, 2 RPCs, cron) | `supabase/koda_learning_schema.sql` | Episodic + semantic memory, versioned, owner-only |
| Weekly reflection agent | `supabase/functions/koda-weekly/index.ts` | Sole writer of durable memory. Sundays: recomputes HRV baselines (deterministic), mines patterns (one AI call, ≥3-instance rule), lesson hygiene, writes report + approval changeset |
| Session-start read | `index.html` → `kodaInit` | One `koda_session_context` RPC → compact athlete-model block in KODA's context (anchor, phase, SWC band, top-7 lessons, last 10 sessions) |
| Session write | `index.html` → `analyzeWorkout` | One `koda_log_session` RPC per analyzed workout (prescribed vs actual) — the live coach's ONLY write path |
| Readiness ingestion | `index.html` → `syncHealthData` | Daily HRV/RHR/sleep rows into `readiness_daily` |
| Review queue | `koda_changesets` table | VDOT moves & phase transitions wait here for Eli's approval — never auto-applied |

## Turn it on (Supabase dashboard)

1. SQL Editor → run `supabase/koda_learning_schema.sql` (after the earlier
   SQL files). Paste the service-role key into the `cron.schedule` block first.
2. `supabase functions deploy koda-weekly`
3. Optional first-run test:
   `curl -X POST .../functions/v1/koda-weekly -H "Authorization: Bearer <SERVICE_ROLE_KEY>"`
4. The Monday after data starts flowing, the weekly report arrives as KODA's
   first chat bubble (it rides the koda_messages channel).

## Deliberate divergences from the blueprint

- "FORGE agent" = our KODA chat (the live coach); it is read-only + the one RPC.
- Added `koda_changesets` (the blueprint described the approval queue but had
  no table for it). Approval UI is a future session — until then changesets
  accumulate as pending, harming nothing.
- HRV source is WHOOP RMSSD or HealthKit SDNN depending on device; the lnRMSSD
  math treats whichever arrives as the athlete's own baseline (self-consistent,
  but don't mix sources in one band — rows are keyed by source).
- Monthly coach-review prompt (blueprint §G) is documented here for the future
  approval UI; the weekly agent already routes consequential changes to the
  queue, which is the part that matters for safety.

## Guardrails in force

- VDOT never moves >0.5 point without a race → changeset only
- Lessons need ≥3 corroborating instances to reach medium confidence
- Contradictions resolve by recency; old facts marked superseded, never deleted
- Weekly agent distills from structured rows, never from prior summaries
- Everything owner-scoped by RLS; the live coach cannot write doctrine
