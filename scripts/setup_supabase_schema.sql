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
  content_type text check (content_type in ('producto','educativo','pregunta_comunidad','detras_de_camaras','refacciones')),
  caption text not null,
  media_url text,
  -- Generation metadata, kept alongside the post so engagement can eventually be correlated back
  -- to *how* the media was made, not just what it says. image: layout/reference_photo/
  -- media_generator/generation_prompt (the media_prompt sent to the generator, null if
  -- reference_photo was used instead). video: generation_prompt (the video_prompt) + narration;
  -- layout/reference_photo/media_generator stay null for video posts.
  layout text,
  reference_photo text,
  media_generator text,
  generation_prompt text,
  narration text,
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

create table growth_snapshots (
  id bigint generated always as identity primary key,
  platform text not null,
  followers_count integer not null,
  following_count integer not null,
  statuses_count integer not null,
  recorded_at timestamptz not null default now()
);
create index growth_snapshots_platform_idx on growth_snapshots (platform);

create table growth_actions (
  id bigint generated always as identity primary key,
  platform text not null,
  action_type text not null check (action_type in ('follow','reply','post','tick')),
  target_account_id text,
  target_status_id text,
  rationale text,
  result text not null default 'ok' check (result in ('ok','failed')),
  error text,
  created_at timestamptz not null default now()
);
create index growth_actions_platform_idx on growth_actions (platform);
-- Matches the exact filter used by get_followed_account_ids/get_replied_status_ids
-- (tools/supabase_tools.py) so those lookups don't need a full scan of the platform index as
-- growth_actions grows.
create index growth_actions_platform_type_result_idx on growth_actions (platform, action_type, result);
-- Backs the same dedup those functions do in application code with an actual DB guarantee: a
-- given account/status can only be successfully followed/replied-to once per platform, even if
-- the growth mission process ever ran duplicated.
create unique index growth_actions_unique_follow_idx
  on growth_actions (platform, target_account_id) where action_type = 'follow' and result = 'ok';
create unique index growth_actions_unique_reply_idx
  on growth_actions (platform, target_status_id) where action_type = 'reply' and result = 'ok';

-- Engagement (likes/comments/shares) for a single published post, recorded repeatedly over its
-- life — not just a final count — so there's an actual over-time signal to eventually train a
-- model on (does content_type X drive more engagement than Y, does it grow or fade quickly...).
create table post_engagement_snapshots (
  id bigint generated always as identity primary key,
  platform text not null,
  external_post_id text not null,
  likes integer not null default 0,
  comments integer not null default 0,
  shares integer not null default 0,
  impressions integer,
  recorded_at timestamptz not null default now()
);
create index post_engagement_snapshots_platform_post_idx on post_engagement_snapshots (platform, external_post_id);

-- Appends one step to agent_runs.steps atomically (single UPDATE, no read-modify-write race
-- between concurrent runs/nodes writing to the same run_id — see tools/supabase_tools.py).
create or replace function append_run_step(p_run_id bigint, p_step jsonb)
returns void
language sql
as $$
  update agent_runs set steps = steps || jsonb_build_array(p_step) where id = p_run_id;
$$;

alter table agent_runs enable row level security;
alter table weekly_strategy enable row level security;
alter table posts enable row level security;
alter table growth_snapshots enable row level security;
alter table growth_actions enable row level security;
alter table post_engagement_snapshots enable row level security;

-- If your `posts` table already existed before the columns above were added (this whole file
-- errors on `create table` for a table that already exists), run just this instead:
-- alter table posts
--   add column if not exists layout text,
--   add column if not exists reference_photo text,
--   add column if not exists media_generator text,
--   add column if not exists generation_prompt text,
--   add column if not exists narration text;

-- If your `posts` table already has the content_type check constraint from before 'refacciones'
-- was added as a value, run this to widen it (Postgres has no "alter constraint", so drop + re-add):
-- alter table posts drop constraint posts_content_type_check;
-- alter table posts add constraint posts_content_type_check
--   check (content_type in ('producto','educativo','pregunta_comunidad','detras_de_camaras','refacciones'));
