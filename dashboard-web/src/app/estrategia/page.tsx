import { Badge } from "@/components/ui/badge";
import { getSupabaseServerClient } from "@/lib/supabaseServer";
import type { WeeklyStrategy } from "@/lib/types";

export const dynamic = "force-dynamic";

async function getStrategies(): Promise<WeeklyStrategy[]> {
  const { data } = await getSupabaseServerClient()
    .from("weekly_strategy")
    .select("*")
    .order("week_start", { ascending: false })
    .limit(20);
  return (data ?? []) as WeeklyStrategy[];
}

export default async function EstrategiaPage() {
  const strategies = await getStrategies();
  const [current, ...history] = strategies;

  return (
    <div className="space-y-10">
      <div>
        <h1 className="font-heading text-3xl tracking-tight">Estrategia semanal</h1>
        <p className="text-sm text-muted-foreground">
          Qué decidió el Gerente de Marketing cada semana, y por qué.
        </p>
      </div>

      {!current && <p className="text-sm text-muted-foreground">Todavía no hay estrategias registradas.</p>}

      {current && (
        <section className="overflow-hidden rounded-lg bg-ink text-white">
          <div className="flex flex-wrap items-baseline justify-between gap-2 px-6 pt-6">
            <p className="font-heading text-2xl">Esta semana, desde el {current.week_start}</p>
            <div className="flex flex-wrap gap-1.5">
              {(current.themes ?? []).map((theme) => (
                <Badge key={theme} variant="outline" className="border-white/25 text-white/80">
                  {theme}
                </Badge>
              ))}
            </div>
          </div>
          <p className="max-w-2xl px-6 pt-4 text-sm leading-relaxed text-white/70">{current.rationale}</p>
          <div className="mt-6 grid gap-px overflow-hidden bg-white/10 sm:grid-cols-3">
            <ReadoutTile label="Posts planeados" value={current.num_posts} />
            {Object.entries(current.content_mix ?? {}).slice(0, 2).map(([type, count]) => (
              <ReadoutTile key={type} label={type} value={count} />
            ))}
          </div>
        </section>
      )}

      {history.length > 0 && (
        <div>
          <p className="mb-1 text-sm font-medium text-muted-foreground">Semanas anteriores</p>
          <ul className="divide-y divide-border border-t border-border">
            {history.map((strategy) => (
              <li key={strategy.id} className="grid gap-3 py-5 sm:grid-cols-[10rem_1fr] sm:gap-6">
                <p className="text-sm font-medium">Semana del {strategy.week_start}</p>
                <div className="space-y-2">
                  <div className="flex flex-wrap gap-1.5">
                    {(strategy.themes ?? []).map((theme) => (
                      <Badge key={theme} variant="secondary">
                        {theme}
                      </Badge>
                    ))}
                  </div>
                  <p className="text-sm text-muted-foreground">{strategy.rationale}</p>
                  <p className="text-xs text-muted-foreground">Posts planeados: {strategy.num_posts}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function ReadoutTile({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="bg-ink px-6 py-5">
      <p className="font-heading text-3xl leading-none tabular-nums text-gold">{value}</p>
      <p className="mt-2 text-sm capitalize text-white/50">{label}</p>
    </div>
  );
}
