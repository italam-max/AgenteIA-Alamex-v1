export type RunStep = {
  ts: string;
  node: string;
  message: string;
  payload?: unknown;
};

export type AgentRun = {
  id: number;
  instruction: string;
  status: "running" | "completed" | "failed";
  supervisor_model: string | null;
  social_media_model: string | null;
  started_at: string;
  finished_at: string | null;
  summary: string | null;
  steps: RunStep[];
  error: string | null;
};

export type WeeklyStrategy = {
  id: number;
  agent_run_id: number;
  week_start: string;
  themes: string[];
  num_posts: number;
  content_mix: Record<string, number>;
  rationale: string;
  source_metrics: unknown;
  created_at: string;
};

export type Post = {
  id: number;
  agent_run_id: number;
  weekly_strategy_id: number | null;
  platform: string;
  post_type: "image" | "video";
  content_type: "producto" | "educativo" | "pregunta_comunidad" | "detras_de_camaras" | "refacciones" | null;
  caption: string;
  media_url: string | null;
  external_post_id: string | null;
  permalink: string | null;
  status: "draft" | "generated" | "published" | "failed";
  published_at: string | null;
  error: string | null;
  created_at: string;
};

export type ProductPhoto = {
  filename: string;
  tags: string[];
  description: string;
};

export type GrowthSnapshot = {
  id: number;
  platform: string;
  followers_count: number;
  following_count: number;
  statuses_count: number;
  recorded_at: string;
};

export type GrowthAction = {
  id: number;
  platform: string;
  action_type: "follow" | "reply" | "post" | "tick";
  target_account_id: string | null;
  target_status_id: string | null;
  rationale: string | null;
  result: "ok" | "failed";
  error: string | null;
  created_at: string;
};

export type PostEngagementSnapshot = {
  id: number;
  platform: string;
  external_post_id: string;
  likes: number;
  comments: number;
  shares: number;
  impressions: number | null;
  recorded_at: string;
};
