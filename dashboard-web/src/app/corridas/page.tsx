import { StepTimeline } from "@/components/StepTimeline";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { formatDateTime, STATUS_LABEL, STATUS_VARIANT } from "@/lib/format";
import { getSupabaseServerClient } from "@/lib/supabaseServer";
import type { AgentRun } from "@/lib/types";

const STATUS_BORDER: Record<AgentRun["status"], string> = {
  running: "border-l-gold",
  completed: "border-l-navy",
  failed: "border-l-destructive",
};

export const dynamic = "force-dynamic";

async function getRuns(): Promise<AgentRun[]> {
  const { data } = await getSupabaseServerClient()
    .from("agent_runs")
    .select("*")
    .order("started_at", { ascending: false })
    .limit(50);
  return (data ?? []) as AgentRun[];
}

export default async function CorridasPage() {
  const runs = await getRuns();

  return (
    <div className="space-y-4">
      <div>
        <h1 className="font-heading text-3xl tracking-tight">Corridas</h1>
        <p className="text-sm text-muted-foreground">Historial y bitácora de cada corrida de los agentes.</p>
      </div>

      {runs.length === 0 && <p className="text-sm text-muted-foreground">Todavía no hay corridas registradas.</p>}

      {runs.map((run) => (
        <Card key={run.id} className={`border-l-4 shadow-none ${STATUS_BORDER[run.status] ?? "border-l-border"}`}>
          <details open={run.status === "running"}>
            <summary className="cursor-pointer list-none p-4">
              <div className="flex flex-wrap items-center gap-3">
                <Badge variant={STATUS_VARIANT[run.status] ?? "outline"}>{STATUS_LABEL[run.status] ?? run.status}</Badge>
                <span className="font-medium">#{run.id}</span>
                <span className="text-sm text-muted-foreground">{run.instruction}</span>
                <span className="ml-auto text-xs text-muted-foreground">{formatDateTime(run.started_at)}</span>
              </div>
            </summary>
            <CardContent className="space-y-3 border-t pt-4">
              {run.error && <p className="text-sm text-destructive">{run.error}</p>}
              {run.summary && <p className="text-sm">{run.summary}</p>}
              <p className="text-xs text-muted-foreground">
                Modelos: {run.supervisor_model ?? "—"} / {run.social_media_model ?? "—"}
              </p>
              <div>
                <p className="mb-1.5 text-sm font-medium">Bitácora</p>
                <StepTimeline steps={run.steps ?? []} />
              </div>
            </CardContent>
          </details>
        </Card>
      ))}
    </div>
  );
}
