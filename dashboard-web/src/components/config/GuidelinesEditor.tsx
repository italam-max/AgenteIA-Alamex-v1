"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";

export function GuidelinesEditor() {
  const [content, setContent] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch("/api/config/guidelines")
      .then((res) => res.json())
      .then((data) => setContent(data.content));
  }, []);

  async function handleSave() {
    if (content === null) return;
    setSaving(true);
    try {
      const res = await fetch("/api/config/guidelines", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });
      if (!res.ok) throw new Error((await res.json()).error ?? "Error al guardar");
      toast.success("Guías de marca actualizadas — se aplican en la próxima corrida.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card className="border-l-4 border-l-gold shadow-none">
      <CardHeader>
        <CardTitle>Tono de marca y reglas de contenido</CardTitle>
        <CardDescription>
          Edita directamente <code>brand/guidelines.md</code> — tono de voz, mensajes clave, qué NO
          decir, estilo visual. Los agentes leen este archivo completo en cada corrida, así que el
          cambio aplica de inmediato en la próxima publicación.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {content === null ? (
          <Skeleton className="h-96 w-full" />
        ) : (
          <Textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="h-96 font-mono text-sm"
          />
        )}
      </CardContent>
      <CardFooter>
        <Button onClick={handleSave} disabled={content === null || saving}>
          {saving ? "Guardando..." : "Guardar"}
        </Button>
      </CardFooter>
    </Card>
  );
}
