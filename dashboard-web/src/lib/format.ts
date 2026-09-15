export const STATUS_LABEL: Record<string, string> = {
  completed: "Completado",
  running: "En curso",
  failed: "Falló",
  published: "Publicado",
  draft: "Borrador",
  generated: "Generado",
};

export const STATUS_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  completed: "default",
  running: "secondary",
  failed: "destructive",
  published: "default",
  draft: "outline",
  generated: "outline",
};

export const NODE_ICON: Record<string, string> = {
  supervisor: "🧭",
  social_media: "📣",
};

export function elapsedSince(iso: string): string {
  const started = new Date(iso).getTime();
  const seconds = Math.max(0, Math.floor((Date.now() - started) / 1000));
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${minutes}m ${remainder}s`;
}

export function formatDateTime(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-MX", { dateStyle: "medium", timeStyle: "short" });
}

export function timeOnly(iso: string | null | undefined): string {
  if (!iso) return "";
  return new Date(iso).toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
