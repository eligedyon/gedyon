-- ═══════════════════════════════════════════════════════════════════
-- KODA ADAPTIVE LEARNING — three-tier memory schema
-- Run once in Supabase Dashboard → SQL Editor (after earlier SQL files).
--
-- Tiers: episodic (sessions_log, race_results, readiness_daily,
-- injuries_niggles) · semantic (athlete_profile, fitness_anchors,
-- lessons_learned, phase_state) · procedural (KODA's system prompt —
-- NOT in the database, by design).
--
-- Write discipline: the live KODA chat is read-only except via the
-- constrained koda_log_session RPC. The weekly reflection agent
-- (koda-weekly edge function, service role) is the sole writer of
-- durable semantic memory. All facts versioned; never hard-delete.
-- ═══════════════════════════════════════════════════════════════════

create extension if not exists pg_cron with schema extensions;
create extension if not exists pg_net with schema extensions;

-- 1. ATHLETE PROFILE (semantic, mostly stable)
create table if not exists public.athlete_profile (
  user_id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  birthdate date,
  home_altitude_ft int default 5400,
  primary_wearables text[] default '{HealthKit,WHOOP}',
  goal_event text default '2028 US Olympic Trials 1500m',
  goal_date date default '2028-04-04',
  goal_vdot numeric default 79,
  notes text,
  updated_at timestamptz default now()
);

-- 2. FITNESS ANCHORS (semantic, versioned VDOT history)
create table if not exists public.fitness_anchors (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  metric text not null default 'VDOT',
  value numeric not null,
  effective_date date not null,
  superseded_at timestamptz,
  source text not null,               -- 'race' | 'time_trial' | 'workout_implied' | 'coach_review'
  confidence text not null default 'medium',
  altitude_adjusted boolean default false,
  raw_input jsonb,
  created_at timestamptz default now()
);
create index if not exists fitness_anchors_idx
  on public.fitness_anchors (user_id, metric, effective_date desc);

-- 3. SESSIONS LOG (episodic: prescribed vs actual vs feel)
create table if not exists public.sessions_log (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  session_date date not null,
  phase text,
  session_type text,
  prescribed jsonb,
  actual jsonb,
  feel_rpe int,
  feel_notes text,
  next_day_readiness_delta numeric,
  debrief_lesson text,
  created_at timestamptz default now()
);
create index if not exists sessions_log_idx
  on public.sessions_log (user_id, session_date desc);

-- 4. RACE RESULTS (episodic, high-trust fitness signal)
create table if not exists public.race_results (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  race_date date not null,
  distance_m int not null,
  time_s int not null,
  altitude_ft int,
  conditions text,
  computed_vdot numeric,
  vdot_altitude_adjusted numeric,
  is_clean boolean default true,
  created_at timestamptz default now()
);

-- 5. INJURIES / NIGGLES
create table if not exists public.injuries_niggles (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  onset_date date not null,
  region text not null,
  severity int,
  status text default 'active',
  suspected_cause text,
  preceding_load jsonb,
  resolved_date date,
  created_at timestamptz default now()
);

-- 6. LESSONS LEARNED (semantic, confidence/source-tagged, versioned)
create table if not exists public.lessons_learned (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  category text not null,
  lesson text not null,
  confidence text not null default 'low',
  source text not null,
  evidence_count int default 1,
  status text default 'active',
  superseded_by bigint references public.lessons_learned(id),
  last_corroborated date,
  created_at timestamptz default now()
);
create index if not exists lessons_learned_idx
  on public.lessons_learned (user_id, status, confidence);

-- 7. PHASE STATE (semantic, current periodization position)
create table if not exists public.phase_state (
  user_id uuid primary key references auth.users(id) on delete cascade,
  current_phase text not null,
  phase_start date not null,
  phase_week int,
  next_trigger text,
  strength_template_phase int,
  updated_at timestamptz default now()
);

-- 8. READINESS DAILY (episodic, live-data landing + context flags)
create table if not exists public.readiness_daily (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  reading_date date not null,
  ln_rmssd numeric,
  rmssd_ms numeric,
  resting_hr int,
  sleep_hours numeric,
  vo2max numeric,
  source text,
  context_flags text[],
  rolling7_ln_rmssd numeric,
  swc_lower numeric,
  swc_upper numeric,
  created_at timestamptz default now(),
  unique (user_id, reading_date, source)
);
create index if not exists readiness_daily_idx
  on public.readiness_daily (user_id, reading_date desc);

-- 9. COACH REVIEW CHANGESETS (extension to the blueprint: where the
-- weekly agent parks proposals that need Eli's approval)
create table if not exists public.koda_changesets (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  week_of date not null,
  changeset jsonb not null,           -- [{what, why, confidence, risk, reversibility}]
  report text,                        -- human-readable weekly report
  status text default 'pending',      -- 'pending' | 'approved' | 'rejected' | 'partial'
  decided_at timestamptz,
  created_at timestamptz default now()
);

-- RLS: enable + owner-only policies on ALL tables
do $$
declare t text;
begin
  foreach t in array array[
    'athlete_profile','fitness_anchors','sessions_log','race_results',
    'injuries_niggles','lessons_learned','phase_state','readiness_daily',
    'koda_changesets']
  loop
    execute format('alter table public.%I enable row level security;', t);
    begin
      execute format($p$create policy "owner_all_%1$s" on public.%1$I
        for all to authenticated
        using (user_id = auth.uid()) with check (user_id = auth.uid());$p$, t);
    exception when duplicate_object then null;
    end;
  end loop;
end $$;

-- ── Consolidated read RPC: ONE tool call, one compact JSON package ──
create or replace function public.koda_session_context()
returns jsonb
language sql
security invoker
stable
as $$
  select jsonb_build_object(
    'profile', (select to_jsonb(p) from public.athlete_profile p
                where p.user_id = auth.uid()),
    'current_anchor', (select to_jsonb(a) from public.fitness_anchors a
                where a.user_id = auth.uid() and a.metric='VDOT'
                  and a.superseded_at is null
                order by a.effective_date desc limit 1),
    'phase', (select to_jsonb(ps) from public.phase_state ps
                where ps.user_id = auth.uid()),
    'recent_sessions', (select jsonb_agg(s order by s.session_date desc)
                from (select session_date, session_type, prescribed, actual,
                             feel_rpe, debrief_lesson
                      from public.sessions_log
                      where user_id = auth.uid()
                      order by session_date desc limit 10) s),
    'active_lessons', (select jsonb_agg(l)
                from (select category, lesson, confidence, source, evidence_count
                      from public.lessons_learned
                      where user_id = auth.uid() and status='active'
                      order by (case confidence when 'high' then 3
                                when 'medium' then 2 else 1 end) desc,
                               last_corroborated desc nulls last
                      limit 7) l),
    'readiness_7d', (select jsonb_agg(r order by r.reading_date desc)
                from (select reading_date, ln_rmssd, rolling7_ln_rmssd,
                             swc_lower, swc_upper, resting_hr, sleep_hours,
                             context_flags
                      from public.readiness_daily
                      where user_id = auth.uid()
                      order by reading_date desc limit 7) r)
  );
$$;

-- ── Constrained write RPC: the ONLY write path for the live coach ──
create or replace function public.koda_log_session(
  p_session_date date,
  p_phase text,
  p_session_type text,
  p_prescribed jsonb,
  p_actual jsonb,
  p_feel_rpe int,
  p_feel_notes text default null,
  p_debrief_lesson text default null
)
returns bigint
language plpgsql
security invoker
as $$
declare new_id bigint;
begin
  insert into public.sessions_log
    (user_id, session_date, phase, session_type, prescribed, actual,
     feel_rpe, feel_notes, debrief_lesson)
  values
    (auth.uid(), p_session_date, p_phase, p_session_type, p_prescribed,
     p_actual, p_feel_rpe, p_feel_notes, p_debrief_lesson)
  returning id into new_id;

  if p_debrief_lesson is not null then
    insert into public.lessons_learned
      (user_id, category, lesson, confidence, source)
    values (auth.uid(), 'workout_response', p_debrief_lesson, 'low', 'self_report');
  end if;

  return new_id;
end $$;

-- ── Weekly reflection schedule (Sunday 21:00 UTC) ──────────────────
-- Paste the service-role key before running; requires koda-weekly deployed.
select cron.unschedule('koda-weekly-reflection')
  where exists (select 1 from cron.job where jobname = 'koda-weekly-reflection');
select cron.schedule(
  'koda-weekly-reflection',
  '0 21 * * 0',
  $$
  select net.http_post(
    url := 'https://qfmklkgvobfckcippwyh.supabase.co/functions/v1/koda-weekly',
    headers := jsonb_build_object(
      'Content-Type','application/json',
      'Authorization','Bearer <SERVICE_ROLE_KEY>')
  );
  $$
);
