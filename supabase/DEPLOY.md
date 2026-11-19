# GEDYON — Supabase Deploy Runbook (KODA monetization + morning check-in)

Project: `qfmklkgvobfckcippwyh`

## 0. Prereqs

```sh
supabase login
supabase link --project-ref qfmklkgvobfckcippwyh
```

## 1. Run the SQL files (in order)

Dashboard → SQL Editor, paste and run each file **in this order** (all are
safe to re-run):

0. `supabase/user_data.sql`            — the app's saved data, one row per account, locked to its owner (RLS)
1. `supabase/phase1_health_sync.sql`   — health_metrics, workouts, sync_state
2. `supabase/gap_protocol.sql`         — plan_position, gap_responses
3. `supabase/koda_monetization.sql`    — koda_usage, koda_daily, subscriptions, increment rpcs
4. `supabase/koda_morning.sql`         — koda_messages + pg_cron schedule

**Before running `koda_morning.sql`:** replace `<SERVICE_ROLE_KEY>` in the
`cron.schedule(...)` statement with the project's service-role key
(Dashboard → Settings → API → `service_role`). The cron job runs daily at
**11:30 UTC** (5:30 AM Denver during MDT; pg_cron has no timezone support —
keep 11:30 UTC year-round or bump to `30 12 * * *` for winter/MST).

## 1b. Before public sign-ups (Dashboard, no code)

- **Custom SMTP (required).** Supabase's built-in email only sends to your
  own team's addresses, about 2 emails an hour. Every other person's
  confirmation and password-reset email will fail. Authentication → Emails →
  SMTP Settings: connect a sender such as Resend, Postmark, SendGrid or
  Brevo, then raise Authentication → Rate Limits → emails per hour.
- **Confirm email: on.** The app handles it (shows "check your email").
- **URL Configuration:** Site URL = the public web address; add it and
  `https://eligedyon.github.io/gedyon/` to Redirect URLs, so confirmation and
  reset links land back in the app.
- **Password minimum: 8** (Authentication → Policies), to match the app.
- **KODA caps:** optional secrets `KODA_DAILY_CAP` (free messages per day
  across all users, default 2000; subscribers are never blocked by it) and
  `KODA_FREE_LIMIT` (free messages per user per month, default 25).

## 2. Set edge function secrets

```sh
supabase secrets set \
  ANTHROPIC_API_KEY=sk-ant-... \
  KODA_INTERNAL_SECRET=$(openssl rand -hex 32) \
  REVENUECAT_WEBHOOK_SECRET=$(openssl rand -hex 32)
```

(`SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are injected automatically
into every edge function — no need to set them.)

## 3. Deploy the functions

```sh
supabase functions deploy koda-chat
supabase functions deploy koda-morning
supabase functions deploy revenuecat-webhook --no-verify-jwt
```

Notes:
- `koda-chat` replaces the currently deployed function; the client contract
  (`{messages, athleteContext}` → `{reply}`) is unchanged, but the client
  should now also handle `{code: 'LIMIT_REACHED'|'CAPACITY'}` (HTTP 200) and
  `AUTH_REQUIRED` (401) / `AI_ERROR` (502).
- `revenuecat-webhook` **must** be deployed with `--no-verify-jwt` —
  RevenueCat authenticates with the shared secret, not a Supabase JWT.
- `koda-morning` keeps default JWT verification; the cron job calls it with
  the service-role key, which passes.

## 4. RevenueCat dashboard setup

1. RevenueCat → your project → **Integrations → Webhooks → Add webhook**.
2. URL: `https://qfmklkgvobfckcippwyh.supabase.co/functions/v1/revenuecat-webhook`
3. **Authorization header value**: paste the exact `REVENUECAT_WEBHOOK_SECRET`
   value from step 2.
4. In the app, configure the RevenueCat SDK with
   `appUserID = <supabase auth user id>` — the webhook maps `app_user_id`
   straight onto `subscriptions.user_id` (anonymous `$RCAnonymousID:` events
   are acknowledged and skipped).
5. Send a test event from the RevenueCat dashboard; expect HTTP 200 with
   `{"ignored":"TEST"}`.

## 5. Manually trigger koda-morning (testing)

```sh
SERVICE_ROLE_KEY='<service role key>'

curl -s -X POST \
  "https://qfmklkgvobfckcippwyh.supabase.co/functions/v1/koda-morning" \
  -H "Authorization: Bearer $SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
# → {"ok":1,"failed":0,"skipped":0,"candidates":1}
```

Re-running the same day returns `skipped` for users already messaged
(one message per user per day, enforced by `unique(user_id, date)`).

## 6. Quick verification checklist

- [ ] `select * from cron.job;` shows `koda-morning-daily` at `30 11 * * *`.
- [ ] Chat as a logged-in user → reply works; `koda_usage.message_count`
      increments; `koda_daily.total` increments.
- [ ] 26th message in a month without a subscription → `LIMIT_REACHED`.
- [ ] RevenueCat test purchase (sandbox) → row appears in `subscriptions`.
- [ ] Manual koda-morning trigger → row appears in `koda_messages`.
