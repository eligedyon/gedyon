-- ═══════════════════════════════════════════════════════════════════
-- PHASE 1 — HealthKit silent sync tables
-- Run once in Supabase Dashboard → SQL Editor (project qfmklkgvobfckcippwyh)
-- RLS: owner-only on every table. The app's anon key gets nothing
-- without an authenticated session.
-- ═══════════════════════════════════════════════════════════════════

-- Daily health metrics (HRV, resting HR, sleep hours, VO2max)
create table if not exists public.health_metrics (
  user_id    uuid not null references auth.users(id) on delete cascade,
  date       date not null,
  metric     text not null,          -- 'hrv' | 'resting_hr' | 'sleep_hours' | 'vo2max'
  value      numeric not null,
  unit       text,
  source     text not null default 'apple_health',
  updated_at timestamptz not null default now(),
  primary key (user_id, date, metric)
);

-- Workouts (HealthKit-sourced now; 'manual' source arrives in Phase 2)
create table if not exists public.workouts (
  id           bigint generated always as identity primary key,
  user_id      uuid not null references auth.users(id) on delete cascade,
  date         date not null,
  minutes      integer not null,
  distance_mi  numeric default 0,
  workout_type text,
  effort       smallint,             -- 1-10, athlete-reported (Phase 2)
  source       text not null,        -- 'apple_health' | 'strava' | 'manual' | ...
  verified     boolean not null default true,
  created_at   timestamptz not null default now(),
  unique (user_id, date, source, minutes)   -- matches client upsert onConflict
);

-- Sync bookkeeping — one row per user
create table if not exists public.sync_state (
  user_id             uuid primary key references auth.users(id) on delete cascade,
  last_healthkit_sync timestamptz,
  updated_at          timestamptz not null default now()
);

-- ── RLS: owner-only, all operations ─────────────────────────────────
alter table public.health_metrics enable row level security;
alter table public.workouts       enable row level security;
alter table public.sync_state     enable row level security;

drop policy if exists health_metrics_owner on public.health_metrics;
create policy health_metrics_owner on public.health_metrics
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists workouts_owner on public.workouts;
create policy workouts_owner on public.workouts
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists sync_state_owner on public.sync_state;
create policy sync_state_owner on public.sync_state
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Useful index for "last workout" and 14-day-window queries (Phase 2 reads)
create index if not exists workouts_user_date_idx on public.workouts (user_id, date desc);
