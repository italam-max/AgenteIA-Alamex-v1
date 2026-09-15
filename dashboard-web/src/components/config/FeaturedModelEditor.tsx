"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";

export function FeaturedModelEditor() {
  const [models, setModels] = useState<string[] | null>(null);
  const [note, setNote] = useState("");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch("/api/config/featured-model")
      .then((res) => res.json())
      .then((data) => {
        setModels(data.models);
        setNote(data.featured ?? "");
        const match = (data.models as string[]).find((m) => data.featured?.startsWith(m));
        if (match) setSelectedModel(match);
      });
  }, []);

  async function handleSave() {
    setSaving(true);
    try {
      const body = note.trim() || "(Sin definir todavía)";
      const res = await fetch("/api/config/featured-model", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ body }),
      });
      if (!res.ok) throw new Error((await res.json()).error ?? "Error al guardar");
      toast.success("Modelo destacado actualizado.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  }

  function applyModel(model: string) {
    setSelectedModel(model);
    setNote(`${model} — modelo destacado esta semana.`);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Modelo destacado de la semana</CardTitle>
        <CardDescription>
          Edita la sección &ldquo;Modelo destacado&rdquo; de <code>equipment_catalog.md</code>. El Gerente de
          Marketing lo respeta en vez de elegir libremente.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {models === null ? (
          <Skeleton className="h-32 w-full" />
        ) : (
          <>
            <Select value={selectedModel} onValueChange={(value) => value && applyModel(value)}>
              <SelectTrigger className="w-72">
                <SelectValue placeholder="Elegir modelo..." />
              </SelectTrigger>
              <SelectContent>
                {models.map((model) => (
                  <SelectItem key={model} value={model}>
                    {model}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Nota opcional para el Gerente de Marketing"
              className="h-24"
            />
          </>
        )}
      </CardContent>
      <CardFooter>
        <Button onClick={handleSave} disabled={models === null || saving}>
          {saving ? "Guardando..." : "Guardar"}
        </Button>
      </CardFooter>
    </Card>
  );
}
