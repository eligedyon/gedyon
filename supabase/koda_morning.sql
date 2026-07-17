-- ═══════════════════════════════════════════════════════════════════
-- KODA MORNING — proactive daily check-in messages + cron trigger
-- Run once in Supabase Dashboard → SQL Editor (project qfmklkgvobfckcippwyh)
-- Requires: phase1_health_sync.sql, gap_protocol.sql, koda_monetization.sql.
--
-- Write model: rows are INSERTED only by the koda-morning edge function
-- (service role). The owner may SELECT their messages and UPDATE only
-- read_at (mark-as-read).
-- ═══════════════════════════════════════════════════════════════════

create table if not exists public.koda_messages (
  id         bigint generated always as identity primary key,
  user_id    uuid not null references auth.users(id) on delete cascade,
  date       date not null,
  message    text not null,
  read_at    timestamptz,
  created_at timestamptz not null default now(),
  unique (user_id, date)                 -- hard cap: one morning message per day
);

alter table public.koda_messages enable row level security;

-- Owner reads their own messages
drop policy if exists koda_messages_owner_select on public.koda_messages;
create policy koda_messages_owner_select on public.koda_messages
  for select using (auth.uid() = user_id);

-- Owner may UPDATE their own rows...
drop policy if exists koda_messages_owner_update on public.koda_messages;
create policy koda_messages_owner_update on public.koda_messages
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ...but column-level grants restrict that update to read_at only.
-- (RLS gates rows; grants gate columns. Together: owner can only flip read_at.)
revoke insert, update, delete on public.koda_messages from anon, authenticated;
grant update (read_at) on public.koda_messages to authenticated;

create index if not exists koda_messages_user_date_idx
  on public.koda_messages (user_id, date desc);

-- ── Daily cron: call the koda-morning edge function ──────────────────
-- Requires the pg_cron and pg_net extensions (available on Supabase;
-- also enableable under Dashboard → Database → Extensions).
create extension if not exists pg_cron;
create extension if not exists pg_net;

-- Schedule: 11:30 UTC = 5:30 AM America/Denver during MDT (summer).
-- NOTE: pg_cron cannot express timezones. During MST (winter, UTC-7),
-- 5:30 AM Denver would be 12:30 UTC. Recommendation: keep 11:30 UTC
-- year-round (message lands 4:30 AM in winter — still pre-run), or
-- adjust the schedule seasonally by re-running this block with '30 12 * * *'.
--
-- ⚠ Replace <SERVICE_ROLE_KEY> with the project's service-role key
--   (Dashboard → Settings → API) before running.

-- Unschedule a previous version if it exists (safe to re-run)
do $do$
begin
  perform cron.unschedule('koda-morning-daily');
exception when others then
  null; -- job didn't exist yet
end
$do$;

select cron.schedule(
  'koda-morning-daily',
  '30 11 * * *',
  $cron$
  select net.http_post(
    url     := 'https://qfmklkgvobfckcippwyh.supabase.co/functions/v1/koda-morning',
    headers := jsonb_build_object(
      'Content-Type',  'application/json',
      'Authorization', 'Bearer <SERVICE_ROLE_KEY>'
    ),
    body    := '{}'::jsonb
  );
  $cron$
);
