-- ═══════════════════════════════════════════════════════════════════
-- user_data — one row per account holding the app's saved data (JSON).
-- Safe to run more than once. Run in Supabase → SQL Editor.
-- Row Level Security makes sure every signed-in user can only read and
-- write their OWN row, no matter how many accounts exist.
-- ═══════════════════════════════════════════════════════════════════
create table if not exists public.user_data (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  data       text,
  updated_at timestamptz not null default now()
);

alter table public.user_data enable row level security;

drop policy if exists "user_data_select_own" on public.user_data;
drop policy if exists "user_data_insert_own" on public.user_data;
drop policy if exists "user_data_update_own" on public.user_data;
drop policy if exists "user_data_delete_own" on public.user_data;

create policy "user_data_select_own" on public.user_data
  for select to authenticated using ((select auth.uid()) = user_id);
create policy "user_data_insert_own" on public.user_data
  for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "user_data_update_own" on public.user_data
  for update to authenticated using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
create policy "user_data_delete_own" on public.user_data
  for delete to authenticated using ((select auth.uid()) = user_id);

-- Anonymous (signed-out) visitors get nothing.
revoke all on public.user_data from anon;

-- Check: this should list exactly the four policies above.
-- select policyname, cmd from pg_policies where tablename = 'user_data';
