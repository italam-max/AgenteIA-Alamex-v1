"use client";

import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function ActionBar() {
  const [brief, setBrief] = useState("");
  const [publishing, setPublishing] = useState(false);
  const [planning, setPlanning] = useState(false);

  async function handlePublishNow() {
    if (!brief.trim()) {
      toast.error("Escribe primero el tema del post");
      return;
    }
    setPublishing(true);
    try {
      const res = await fetch("/api/actions/publish-now", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brief }),
      });
      if (!res.ok) throw new Error((await res.json()).error ?? "No se pudo iniciar");
      window.dispatchEvent(new Event("run-started"));
      toast.success("Corrida iniciada — sigue el progreso abajo (~1-2 min).");
      setBrief("");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "No se pudo iniciar");
    } finally {
      setPublishing(false);
    }
  }

  async function handlePlanWeek() {
    setPlanning(true);
    try {
      const res = await fetch("/api/actions/plan-week", { method: "POST" });
      if (!res.ok) throw new Error((await res.json()).error ?? "No se pudo iniciar");
      window.dispatchEvent(new Event("run-started"));
      toast.success("Planeando la semana — sigue el progreso abajo (~3-8 min).");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "No se pudo iniciar");
    } finally {
      setPlanning(false);
    }
  }

  return (
    <div className="flex flex-col gap-2 sm:flex-row">
      <Input
        value={brief}
        onChange={(e) => setBrief(e.target.value)}
        placeholder="Tema del post, ej. la bomba hidráulica del HYD"
        className="bg-white sm:w-80"
        onKeyDown={(e) => e.key === "Enter" && handlePublishNow()}
      />
      <Button onClick={handlePublishNow} disabled={publishing} className="shrink-0 bg-navy hover:bg-navy/90">
        {publishing ? "Iniciando…" : "Publicar ahora"}
      </Button>
      <Button onClick={handlePlanWeek} disabled={planning} variant="outline" className="shrink-0 border-rail/40">
        {planning ? "Iniciando…" : "Planear la semana"}
      </Button>
    </div>
  );
}
