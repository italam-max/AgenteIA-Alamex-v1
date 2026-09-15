"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";

const PLATFORMS = ["facebook", "mastodon"];
const MEDIA_GENERATORS = ["local", "leonardo", "fal", "gemini", "higgsfield", "openai"];

export function PlatformsEditor() {
  const [enabledPlatforms, setEnabledPlatforms] = useState<string[] | null>(null);
  const [mediaGenerator, setMediaGenerator] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch("/api/config/settings")
      .then((res) => res.json())
      .then((data) => {
        setEnabledPlatforms(
          data.ENABLED_PLATFORMS.split(",").map((p: string) => p.trim()).filter(Boolean)
        );
        setMediaGenerator(data.MEDIA_GENERATOR);
      });
  }, []);

  function togglePlatform(platform: string, checked: boolean) {
    setEnabledPlatforms((prev) => {
      const current = prev ?? [];
      return checked ? [...current, platform] : current.filter((p) => p !== platform);
    });
  }

  async function handleSave() {
    if (enabledPlatforms === null || mediaGenerator === null) return;
    setSaving(true);
    try {
      const res = await fetch("/api/config/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ENABLED_PLATFORMS: enabledPlatforms.join(","),
          MEDIA_GENERATOR: mediaGenerator,
        }),
      });
      if (!res.ok) throw new Error((await res.json()).error ?? "Error al guardar");
      toast.success("Configuración actualizada — aplica en la próxima corrida.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  }

  const loading = enabledPlatforms === null || mediaGenerator === null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Plataformas y generador de imagen</CardTitle>
        <CardDescription>
          Solo cambia <code>ENABLED_PLATFORMS</code> y <code>MEDIA_GENERATOR</code> en <code>.env</code> —
          las API keys se siguen editando ahí a mano, nunca desde aquí.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {loading ? (
          <Skeleton className="h-32 w-full" />
        ) : (
          <>
            <div className="space-y-2">
              <Label>Plataformas activas</Label>
              <div className="flex gap-4">
                {PLATFORMS.map((platform) => (
                  <div key={platform} className="flex items-center gap-2">
                    <Checkbox
                      id={`platform-${platform}`}
                      checked={enabledPlatforms.includes(platform)}
                      onCheckedChange={(checked) => togglePlatform(platform, checked === true)}
                    />
                    <Label htmlFor={`platform-${platform}`} className="capitalize font-normal">
                      {platform}
                    </Label>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label>Generador de imagen</Label>
              <Select value={mediaGenerator} onValueChange={setMediaGenerator}>
                <SelectTrigger className="w-64">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MEDIA_GENERATORS.map((generator) => (
                    <SelectItem key={generator} value={generator}>
                      {generator}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </>
        )}
      </CardContent>
      <CardFooter>
        <Button onClick={handleSave} disabled={loading || saving}>
          {saving ? "Guardando..." : "Guardar"}
        </Button>
      </CardFooter>
    </Card>
  );
}
