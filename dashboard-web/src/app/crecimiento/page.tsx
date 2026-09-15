import { GrowthDashboard } from "@/components/growth/GrowthDashboard";
import { readEditableEnv } from "@/lib/envFile";
import { getSupabaseServerClient } from "@/lib/supabaseServer";
import type { GrowthAction, GrowthSnapshot } from "@/lib/types";

export const dynamic = "force-dynamic";

async function getGrowthData() {
  const supabase = getSupabaseServerClient();

  const [{ data: snapshots }, { data: actions }] = await Promise.all([
    supabase.from("growth_snapshots").select("*").order("recorded_at", { ascending: false }).limit(60),
    supabase.from("growth_actions").select("*").order("created_at", { ascending: false }).limit(50),
  ]);

  return {
    snapshots: ((snapshots ?? []) as GrowthSnapshot[]).reverse(),
    actions: (actions ?? []) as GrowthAction[],
  };
}

export default async function CrecimientoPage() {
  const { snapshots, actions } = await getGrowthData();
  const env = readEditableEnv();
  const targetFollowers = Number(env.GROWTH_TARGET_FOLLOWERS) || 100;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="font-heading text-3xl tracking-tight">Crecimiento</h1>
        <p className="text-sm text-muted-foreground">
          Misión autónoma en una cuenta de prueba de Mastodon: publica contenido de valor (no solo
          producto), responde menciones en nuestras propias publicaciones, y sigue cuentas afines
          descubiertas por hashtag con criterio (nunca solo para inflar el número). Úsala solo con
          una cuenta de prueba, nunca la cuenta real de la marca.
        </p>
      </div>

      <GrowthDashboard initialSnapshots={snapshots} initialActions={actions} targetFollowers={targetFollowers} />
    </div>
  );
}
