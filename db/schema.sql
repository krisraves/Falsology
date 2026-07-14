-- Optional future persistence schema for Falsology.
-- The current MVP works without a database and stores guest progress locally.

create table if not exists profiles (
  id uuid primary key,
  email text unique not null,
  display_name text,
  score integer not null default 0,
  answered integer not null default 0,
  correct integer not null default 0,
  current_streak integer not null default 0,
  best_streak integer not null default 0,
  saved_claim_ids text[] not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists reports (
  id bigint generated always as identity primary key,
  claim_id text not null,
  reason text not null,
  details text,
  page_url text,
  status text not null default 'open',
  assigned_to text,
  resolution text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists reports_status_created_idx on reports(status, created_at desc);
