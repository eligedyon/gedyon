-- ═══════════════════════════════════════════════════════════════════
-- GAP PROTOCOL — plan position + gap reasons
-- Run once in Supabase Dashboard → SQL Editor (project qfmklkgvobfckcippwyh)
-- Requires: phase1_health_sync.sql already run (workouts, sync_state).
-- RLS: owner-only on every table.
-- ═══════════════════════════════════════════════════════════════════

-- Authoritative plan position (week 1-110 of the Trials plan).
-- The app derives week from plan_start via getWk(); this table makes the
-- rolled-back position durable across devices.
create table if not exists public.plan_position (
  user_id         uuid primary key references auth.users(id) on delete cascade,
  plan_start      date not null,
  week_num        smallint,
  phase           text,
  last_adjustment text,              -- 'roll_back_weeks' | 'drop_phase' | 'assessment_week' | ...
  updated_at      timestamptz not null default now()
);

-- Athlete-stated reasons for training gaps (changes KODA's tone, not the math)
create table if not exists public.gap_responses (
  id        bigint generated always as identity primary key,
  user_id   uuid not null references auth.users(id) on delete cascade,
  reason    text not null,
  noted_at  timestamptz not null default now()
);

alter table public.plan_position enable row level security;
alter table public.gap_responses enable row level security;

drop policy if exists plan_position_owner on public.plan_position;
create policy plan_position_owner on public.plan_position
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists gap_responses_owner on public.gap_responses;
create policy gap_responses_owner on public.gap_responses
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
