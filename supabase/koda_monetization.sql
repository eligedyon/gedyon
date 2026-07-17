-- ═══════════════════════════════════════════════════════════════════
-- KODA MONETIZATION — usage metering, global circuit breaker, subscriptions
-- Run once in Supabase Dashboard → SQL Editor (project qfmklkgvobfckcippwyh)
-- Requires: phase1_health_sync.sql already run.
--
-- Write model: ALL writes to these tables happen exclusively from edge
-- functions using the service-role key (which bypasses RLS). Authenticated
-- clients may only READ their own usage / subscription rows.
-- ═══════════════════════════════════════════════════════════════════

-- Per-user monthly KODA message counter
create table if not exists public.koda_usage (
  user_id       uuid not null references auth.users(id) on delete cascade,
  month         text not null,                    -- 'YYYY-MM'
  message_count integer not null default 0,
  updated_at    timestamptz not null default now(),
  primary key (user_id, month)
);

-- Global daily counter — circuit breaker across ALL users (service-role only)
create table if not exists public.koda_daily (
  date  date primary key,
  total integer not null default 0
);

-- Subscription state, written only by the RevenueCat webhook (service role)
create table if not exists public.subscriptions (
  user_id     uuid primary key references auth.users(id) on delete cascade,
  status      text not null,                      -- 'active' | 'expired' | 'cancelled' | 'grace'
  product_id  text,
  expires_at  timestamptz,
  environment text,                               -- 'PRODUCTION' | 'SANDBOX'
  updated_at  timestamptz not null default now()
);

-- ── RLS ──────────────────────────────────────────────────────────────
alter table public.koda_usage    enable row level security;
alter table public.koda_daily    enable row level security;   -- no policies: service-role only
alter table public.subscriptions enable row level security;

-- koda_usage: owner may SELECT only. No insert/update/delete policies —
-- writes go through the edge function with the service-role key.
drop policy if exists koda_usage_owner_select on public.koda_usage;
create policy koda_usage_owner_select on public.koda_usage
  for select using (auth.uid() = user_id);

-- subscriptions: owner may SELECT only (client shows "Pro" badge, paywall state)
drop policy if exists subscriptions_owner_select on public.subscriptions;
create policy subscriptions_owner_select on public.subscriptions
  for select using (auth.uid() = user_id);

-- Belt-and-braces: strip client grants so even a future permissive policy
-- couldn't open writes from the browser.
revoke insert, update, delete on public.koda_usage    from anon, authenticated;
revoke all                    on public.koda_daily    from anon, authenticated;
revoke insert, update, delete on public.subscriptions from anon, authenticated;

-- ── Atomic upsert-increment functions (called via rpc from edge functions) ──
-- security definer so they run as the table owner; execution is revoked from
-- client roles — only service_role may call them.

create or replace function public.increment_koda_usage(p_user_id uuid, p_month text)
returns void
language sql
security definer
set search_path = public
as $$
  insert into public.koda_usage (user_id, month, message_count, updated_at)
  values (p_user_id, p_month, 1, now())
  on conflict (user_id, month)
  do update set message_count = public.koda_usage.message_count + 1,
                updated_at    = now();
$$;

create or replace function public.increment_koda_daily(p_date date)
returns void
language sql
security definer
set search_path = public
as $$
  insert into public.koda_daily (date, total)
  values (p_date, 1)
  on conflict (date)
  do update set total = public.koda_daily.total + 1;
$$;

revoke all on function public.increment_koda_usage(uuid, text) from public, anon, authenticated;
revoke all on function public.increment_koda_daily(date)       from public, anon, authenticated;
grant execute on function public.increment_koda_usage(uuid, text) to service_role;
grant execute on function public.increment_koda_daily(date)       to service_role;
