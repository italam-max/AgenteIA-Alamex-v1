"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { GrowthMissionEditor } from "@/components/config/GrowthMissionEditor";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FollowerChart } from "@/components/growth/FollowerChart";
import { GrowthActionLog } from "@/components/growth/GrowthActionLog";
import { elapsedSince } from "@/lib/format";
import type { GrowthAction, GrowthSnapshot } from "@/lib/types";

const STATUS_POLL_MS = 10_000;
const DATA_POLL_MS = 30_000;

type Status = { running: boolean; pid: number | null; startedAt: string | null };

export function GrowthDashboard({
  initialSnapshots,
  initialActions,
  targetFollowers,
}: {
  initialSnapshots: GrowthSnapshot[];
  initialActions: GrowthAction[];
  targetFollowers: number;
}) {
  const [status, setStatus] = useState<Status | null>(null);
  const [snapshots, setSnapshots] = useState(initialSnapshots);
  const [actions, setActions] = useState(initialActions);
  const [log, setLog] = useState("");
  const [busy, setBusy] = useState(false);
  const [, forceTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    async function pollStatus() {
      try {
        const res = await fetch("/api/growth/status", { cache: "no-store" });
        if (!cancelled && res.ok) setStatus(await res.json());
      } catch {
        // silently retry next tick
      }
    }
    pollStatus();
    const interval = setInterval(pollStatus, STATUS_POLL_MS);
    const tickInterval = setInterval(() => forceTick((t) => t + 1), 1000);
    return () => {
      cancelled = true;
      clearInterval(interval);
      clearInterval(tickInterval);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function pollData() {
      try {
        const [snapshotsRes, actionsRes, logRes] = await Promise.all([
          fetch("/api/growth/snapshots", { cache: "no-store" }),
          fetch("/api/growth/actions", { cache: "no-store" }),
          fetch("/api/growth/log", { cache: "no-store" }),
        ]);
        if (!cancelled && snapshotsRes.ok) setSnapshots(await snapshotsRes.json());
        if (!cancelled && actionsRes.ok) setActions(await actionsRes.json());
        if (!cancelled && logRes.ok) setLog((await logRes.json()).log);
      } catch {
        // silently retry next tick
      }
    }
    pollData();
    const interval = setInterval(pollData, DATA_POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  async function handleStart() {
    setBusy(true);
    try {
      const res = await fetch("/api/growth/start", { method: "POST" });
      if (!res.ok) throw new Error((await res.json()).error ?? "No se pudo iniciar");
      toast.success("Misión de crecimiento iniciada.");
      setStatus(await (await fetch("/api/growth/status")).json());
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "No se pudo iniciar");
    } finally {
      setBusy(false);
    }
  }

  async function handleStop() {
    setBusy(true);
    try {
      const res = await fetch("/api/growth/stop", { method: "POST" });
      if (!res.ok) throw new Error((await res.json()).error ?? "No se pudo detener");
      toast.success("Misión de crecimiento detenida — el ciclo en curso se corta de inmediato.");
      setStatus(await (await fetch("/api/growth/status")).json());
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "No se pudo detener");
    } finally {
      setBusy(false);
    }
  }

  const latest = snapshots[snapshots.length - 1] ?? null;
  const progress = latest ? Math.min(100, (latest.followers_count / targetFollowers) * 100) : 0;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle className="flex items-center gap-2 text-base">
              {status?.running ? (
                <span className="relative flex h-2.5 w-2.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
                </span>
              ) : (
                <span className="h-2.5 w-2.5 rounded-full bg-muted-foreground/40" />
              )}
              {status?.running ? "Corriendo" : "Detenida"}
              {status?.running && status.startedAt && (
                <Badge variant="outline" className="font-normal">
                  desde hace {elapsedSince(status.startedAt)}
                </Badge>
              )}
            </CardTitle>
            <div className="flex gap-2">
              <Button onClick={handleStart} disabled={busy || !!status?.running} className="bg-navy hover:bg-navy/90">
                Iniciar
              </Button>
              <Button onClick={handleStop} disabled={busy || !status?.running} variant="outline">
                Detener
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-px overflow-hidden rounded-md bg-border sm:grid-cols-3">
            <FloorReadout label="Seguidores" value={latest?.followers_count ?? "—"} />
            <FloorReadout label="Siguiendo" value={latest?.following_count ?? "—"} />
            <FloorReadout label="Posts" value={latest?.statuses_count ?? "—"} />
          </div>
          <div className="space-y-1.5">
            <div className="h-2 overflow-hidden rounded-full bg-muted">
              <div className="h-full rounded-full bg-gold transition-all" style={{ width: `${progress}%` }} />
            </div>
            <p className="text-xs text-muted-foreground">
              {latest?.followers_count ?? 0} / {targetFollowers} seguidores
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Log del proceso</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="max-h-64 overflow-auto rounded-md bg-ink p-3 font-mono text-xs whitespace-pre-wrap text-white/80">
            {log || "Sin salida todavía."}
          </pre>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Seguidores en el tiempo</CardTitle>
        </CardHeader>
        <CardContent>
          <FollowerChart snapshots={snapshots} target={targetFollowers} />
        </CardContent>
      </Card>

      <GrowthMissionEditor />

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Bitácora de acciones</CardTitle>
        </CardHeader>
        <CardContent>
          <GrowthActionLog actions={actions} />
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
