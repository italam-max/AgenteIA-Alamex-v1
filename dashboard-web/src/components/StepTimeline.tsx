import { NODE_ICON, timeOnly } from "@/lib/format";
import type { RunStep } from "@/lib/types";

export function StepTimeline({ steps }: { steps: RunStep[] }) {
  if (steps.length === 0) {
    return <p className="text-sm text-muted-foreground">Todavía no hay pasos registrados.</p>;
  }

  return (
    <ol className="space-y-1.5">
      {steps.map((step, index) => (
        <li key={`${step.ts}-${index}`} className="flex items-start gap-2 text-sm">
          <span className="mt-0.5 shrink-0 font-mono text-xs text-muted-foreground">{timeOnly(step.ts)}</span>
          <span className="shrink-0">{NODE_ICON[step.node] ?? "•"}</span>
          <span className="font-medium">{step.node}</span>
          <span className="text-muted-foreground">— {step.message}</span>
        </li>
      ))}
    </ol>
  );
}
