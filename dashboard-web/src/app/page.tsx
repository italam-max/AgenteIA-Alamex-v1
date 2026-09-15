import Link from "next/link";

import { ActionBar } from "@/components/ActionBar";
import { LiveRunBanner } from "@/components/LiveRunBanner";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { readEditableEnv } from "@/lib/envFile";
import { STATUS_LABEL } from "@/lib/format";
import { getSupabaseServerClient } from "@/lib/supabaseServer";
import type { AgentRun, Post, WeeklyStrategy } from "@/lib/types";

export const dynamic = "force-dynamic";

async function getHomeData() {
  const supabase = getSupabaseServerClient();

  const [{ data: runs }, { data: strategies }, { data: posts }] = await Promise.all([
    supabase.from("agent_runs").select("*").order("started_at", { ascending: false }).limit(20),
    supabase.from("weekly_strategy").select("*").order("week_start", { ascending: false }).limit(1),
    supabase.from("posts").select("*").order("created_at", { ascending: false }).limit(6),
  ]);

  return {
    runs: (runs ?? []) as AgentRun[],
    latestStrategy: (strategies?.[0] ?? null) as WeeklyStrategy | null,
    recentPosts: (posts ?? []) as Post[],
  };
}

export default async function AgentesPage() {
  const { runs, latestStrategy, recentPosts } = await getHomeData();
  const env = readEditableEnv();

  const publishedCount = runs.reduce((total, run) => (run.status === "completed" ? total + 1 : total), 0);
  const platforms = env.ENABLED_PLATFORMS.split(",").map((p) => p.trim()).filter(Boolean);

  return (
    <div className="space-y-10">
      <header className="flex flex-col gap-6 border-b border-border pb-8 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="font-heading text-4xl leading-none tracking-tight">Agentes de Marketing</h1>
          <p className="mt-3 max-w-md text-muted-foreground">
            Qué hacen, qué publican y cómo están configurados los agentes de Alamex.
          </p>
        </div>
        <ActionBar />
      </header>

      <LiveRunBanner />

      <div className="grid gap-px overflow-hidden rounded-md bg-border sm:grid-cols-3">
        <FloorReadout label="Corridas registradas" value={runs.length} />
        <FloorReadout label="Corridas completadas" value={publishedCount} />
        <FloorReadout label="Plataformas activas" value={platforms.join(" · ") || "ninguna"} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="rounded-md border-l-4 border-l-navy shadow-none">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-xl">Gerente de Marketing</CardTitle>
              <Badge variant="outline">claude-sonnet-5</Badge>
            </div>
            <CardDescription>
              Analiza el desempeño reciente de cada plataforma y decide la estrategia de contenido
              de la semana: cuántos posts, sobre qué temas y con qué brief creativo.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {latestStrategy ? (
              <>
                <p className="text-sm font-medium">Semana del {latestStrategy.week_start}</p>
                <p className="text-sm text-muted-foreground line-clamp-4">{latestStrategy.rationale}</p>
                <div className="flex flex-wrap gap-1.5">
                  {(latestStrategy.themes ?? []).map((theme) => (
                    <Badge key={theme} variant="secondary">
                      {theme}
                    </Badge>
                  ))}
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">Todavía no ha decidido ninguna estrategia.</p>
            )}
            <Link href="/estrategia" className="text-sm font-medium text-navy hover:underline">
              Ver historial de estrategias
            </Link>
          </CardContent>
        </Card>

        <Card className="rounded-md border-l-4 border-l-gold shadow-none">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-xl">Social Media</CardTitle>
              <Badge variant="outline">claude-sonnet-5</Badge>
            </div>
            <CardDescription>
              Redacta el caption y el gráfico de cada post (foto + headline/bullets dibujados con
              código) a partir del brief del Gerente de Marketing, y publica en las plataformas
              activas.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {recentPosts.length > 0 ? (
              <div className="grid grid-cols-3 gap-2">
                {recentPosts.slice(0, 6).map((post) => (
                  <div key={post.id} className="overflow-hidden rounded-sm border border-border">
                    {post.media_url ? (
                      post.post_type === "video" ? (
                        <video src={post.media_url} muted preload="metadata" className="aspect-square w-full object-cover" />
                      ) : (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={post.media_url} alt="" className="aspect-square w-full object-cover" />
                      )
                    ) : (
                      <div className="aspect-square bg-muted" />
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Todavía no ha publicado nada.</p>
            )}
            <Link href="/posts" className="text-sm font-medium text-navy hover:underline">
              Ver todos los posts
            </Link>
          </CardContent>
        </Card>
      </div>

      <Card className="rounded-md shadow-none">
        <CardHeader>
          <CardTitle className="text-lg">Corridas recientes</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="divide-y divide-border">
            {runs.slice(0, 5).map((run) => (
              <li key={run.id} className="flex items-center justify-between py-2.5 text-sm">
                <span className="truncate pr-4">
                  <span className="text-muted-foreground">#{run.id}</span> {run.instruction}
                </span>
                <Badge variant={run.status === "failed" ? "destructive" : "outline"}>
                  {STATUS_LABEL[run.status] ?? run.status}
                </Badge>
              </li>
            ))}
            {runs.length === 0 && <p className="py-2 text-sm text-muted-foreground">Sin corridas todavía.</p>}
          </ul>
          <Link href="/corridas" className="mt-3 inline-block text-sm font-medium text-navy hover:underline">
            Ver bitácora completa
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}

function FloorReadout({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="bg-ink px-6 py-5 text-white">
      <p className="font-heading text-4xl leading-none tabular-nums text-gold">{value}</p>
      <p className="mt-2 text-sm text-white/50">{label}</p>
    </div>
  );
}
