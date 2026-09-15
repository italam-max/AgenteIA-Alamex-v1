"use client";

import { useEffect, useState } from "react";

import { StepTimeline } from "@/components/StepTimeline";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { elapsedSince, NODE_ICON, STATUS_LABEL } from "@/lib/format";
import type { AgentRun } from "@/lib/types";

const POLL_MS = 4000;

export function LiveRunBanner() {
  const [run, setRun] = useState<AgentRun | null>(null);
  const [, forceTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const res = await fetch("/api/runs/latest", { cache: "no-store" });
        if (!cancelled && res.ok) setRun(await res.json());
      } catch {
        // silently retry on the next tick — a transient fetch failure shouldn't crash the banner
      }
    }
    poll();
    const dataInterval = setInterval(poll, POLL_MS);
    const tickInterval = setInterval(() => forceTick((t) => t + 1), 1000);

    // ActionBar fires this the instant a run is kicked off, so the banner doesn't wait out the
    // rest of the normal 4s poll interval — a couple of quick retries cover the ~2-3s the Python
    // process takes to import and write its first agent_runs row.
    let retries = 0;
    const onRunStarted = () => {
      retries = 0;
      const retryPoll = () => {
        poll();
        if (retries++ < 4) setTimeout(retryPoll, 1000);
      };
      retryPoll();
    };
    window.addEventListener("run-started", onRunStarted);

    return () => {
      cancelled = true;
      clearInterval(dataInterval);
      clearInterval(tickInterval);
      window.removeEventListener("run-started", onRunStarted);
    };
  }, []);

  if (!run) return null;

  if (run.status !== "running") {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Badge variant="outline">Corrida #{run.id}</Badge>
        <span>{STATUS_LABEL[run.status] ?? run.status}</span>
        <span className="truncate">{run.summary ?? run.instruction}</span>
      </div>
    );
  }

  const steps = run.steps ?? [];
  const lastStep = steps[steps.length - 1];

  return (
    <Card className="border-gold/50 bg-gold/[0.06]">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <span className="relative flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
          </span>
          Corriendo ahora
          <Badge variant="outline" className="font-body font-normal">
            #{run.id}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-2 text-sm">
          <Badge variant="secondary">{run.instruction}</Badge>
          {lastStep && (
            <Badge variant="outline">
              {NODE_ICON[lastStep.node] ?? ""} {lastStep.node}
            </Badge>
          )}
          <Badge variant="outline">hace {elapsedSince(run.started_at)}</Badge>
        </div>
        {lastStep && <p className="text-sm">Último paso: {lastStep.message}</p>}
        <StepTimeline steps={steps.slice(-8)} />
      </CardContent>
    </Card>
  );
}
