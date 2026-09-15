"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";

type GrowthEnv = {
  GROWTH_TARGET_FOLLOWERS: string;
  GROWTH_TICK_MINUTES: string;
  GROWTH_MAX_FOLLOWS_PER_TICK: string;
  GROWTH_MAX_REPLIES_PER_TICK: string;
  GROWTH_HASHTAGS: string;
};

export function GrowthMissionEditor() {
  const [env, setEnv] = useState<GrowthEnv | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch("/api/config/settings")
      .then((res) => res.json())
      .then((data) =>
        setEnv({
          GROWTH_TARGET_FOLLOWERS: data.GROWTH_TARGET_FOLLOWERS,
          GROWTH_TICK_MINUTES: data.GROWTH_TICK_MINUTES,
          GROWTH_MAX_FOLLOWS_PER_TICK: data.GROWTH_MAX_FOLLOWS_PER_TICK,
          GROWTH_MAX_REPLIES_PER_TICK: data.GROWTH_MAX_REPLIES_PER_TICK,
          GROWTH_HASHTAGS: data.GROWTH_HASHTAGS,
        })
      );
  }, []);

  function set<K extends keyof GrowthEnv>(key: K, value: string) {
    setEnv((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  async function handleSave() {
    if (!env) return;
    setSaving(true);
    try {
      const res = await fetch("/api/config/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(env),
      });
      if (!res.ok) throw new Error((await res.json()).error ?? "Error al guardar");
      toast.success("Configuración actualizada — aplica en el próximo ciclo.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Configuración de la misión</CardTitle>
        <CardDescription>
          Los límites de follows/respuestas por ciclo existen para reducir el riesgo de que Mastodon
          marque la cuenta como spam — súbelos solo si la cuenta se mantiene saludable.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!env ? (
          <Skeleton className="h-32 w-full" />
        ) : (
          <>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div className="space-y-1.5">
                <Label>Meta de seguidores</Label>
                <Input
                  type="number"
                  min={0}
                  value={env.GROWTH_TARGET_FOLLOWERS}
                  onChange={(e) => set("GROWTH_TARGET_FOLLOWERS", e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Minutos por ciclo</Label>
                <Input
                  type="number"
                  min={1}
                  value={env.GROWTH_TICK_MINUTES}
                  onChange={(e) => set("GROWTH_TICK_MINUTES", e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Follows / ciclo</Label>
                <Input
                  type="number"
                  min={0}
                  value={env.GROWTH_MAX_FOLLOWS_PER_TICK}
                  onChange={(e) => set("GROWTH_MAX_FOLLOWS_PER_TICK", e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Respuestas / ciclo</Label>
                <Input
                  type="number"
                  min={0}
                  value={env.GROWTH_MAX_REPLIES_PER_TICK}
                  onChange={(e) => set("GROWTH_MAX_REPLIES_PER_TICK", e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Hashtags semilla (separados por coma, sin #)</Label>
              <Input
                value={env.GROWTH_HASHTAGS}
                onChange={(e) => set("GROWTH_HASHTAGS", e.target.value)}
                placeholder="elevadores,montacargas,arquitectura"
              />
            </div>
          </>
        )}
      </CardContent>
      <CardFooter>
        <Button onClick={handleSave} disabled={!env || saving}>
          {saving ? "Guardando..." : "Guardar"}
        </Button>
      </CardFooter>
    </Card>
  );
}
