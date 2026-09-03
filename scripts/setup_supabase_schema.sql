create table agent_runs (
  id bigint generated always as identity primary key,
  instruction text not null,
  triggered_by text default 'cli',
  status text not null default 'running'
    check (status in ('running','completed','failed')),
  supervisor_model text,
  social_media_model text,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  summary text,
  steps jsonb not null default '[]'::jsonb,
  error text
);

create table weekly_strategy (
  id bigint generated always as identity primary key,
  agent_run_id bigint not null references agent_runs(id) on delete cascade,
  week_start date not null,
  themes jsonb not null,
  num_posts integer not null,
  content_mix jsonb not null,
  rationale text not null,
  source_metrics jsonb,
  created_at timestamptz not null default now()
);
create index weekly_strategy_agent_run_id_idx on weekly_strategy (agent_run_id);

create table posts (
  id bigint generated always as identity primary key,
  agent_run_id bigint not null references agent_runs(id) on delete cascade,
  weekly_strategy_id bigint references weekly_strategy(id) on delete set null,
  platform text not null,
  post_type text not null check (post_type in ('image','video')),
  caption text not null,
  media_url text,
  external_post_id text,
  permalink text,
  status text not null default 'draft'
    check (status in ('draft','generated','published','failed')),
  published_at timestamptz,
  error text,
  created_at timestamptz not null default now()
);
create index posts_agent_run_id_idx on posts (agent_run_id);
create index posts_weekly_strategy_id_idx on posts (weekly_strategy_id);
create index posts_platform_idx on posts (platform);

alter table agent_runs enable row level security;
alter table weekly_strategy enable row level security;
alter table posts enable row level security;
