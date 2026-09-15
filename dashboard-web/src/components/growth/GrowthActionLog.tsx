import { Badge } from "@/components/ui/badge";
import { formatDateTime } from "@/lib/format";
import type { GrowthAction } from "@/lib/types";

const ACTION_ICON: Record<GrowthAction["action_type"], string> = {
  follow: "➕",
  reply: "💬",
  post: "📣",
  tick: "🧠",
};

const ACTION_LABEL: Record<GrowthAction["action_type"], string> = {
  follow: "Nuevo follow",
  reply: "Respuesta",
  post: "Post extra",
  tick: "Razonamiento del ciclo",
};

export function GrowthActionLog({ actions }: { actions: GrowthAction[] }) {
  if (actions.length === 0) {
    return <p className="text-sm text-muted-foreground">Todavía no hay acciones registradas.</p>;
  }

  return (
    <ol className="divide-y divide-border">
      {actions.map((action) => (
        <li key={action.id} className="flex items-start gap-3 py-2.5 text-sm">
          <span className="mt-0.5 shrink-0">{ACTION_ICON[action.action_type] ?? "•"}</span>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium">{ACTION_LABEL[action.action_type] ?? action.action_type}</span>
              {(action.target_account_id || action.target_status_id) && (
                <span className="font-mono text-xs text-muted-foreground">
                  {action.target_account_id ?? action.target_status_id}
                </span>
              )}
              <Badge variant={action.result === "failed" ? "destructive" : "outline"}>
                {action.result === "failed" ? "falló" : "ok"}
              </Badge>
              <span className="ml-auto shrink-0 text-xs text-muted-foreground">{formatDateTime(action.created_at)}</span>
            </div>
            {action.rationale && (
              <p className={`mt-1 text-muted-foreground ${action.action_type === "tick" ? "" : "truncate"}`}>
                {action.rationale}
              </p>
            )}
            {action.error && <p className="mt-1 text-destructive">{action.error}</p>}
          </div>
        </li>
      ))}
    </ol>
  );
}
