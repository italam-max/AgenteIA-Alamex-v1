import { NextResponse } from "next/server";

import { getSupabaseServerClient } from "@/lib/supabaseServer";

export async function GET() {
  const { data, error } = await getSupabaseServerClient()
    .from("growth_snapshots")
    .select("*")
    .order("recorded_at", { ascending: false })
    .limit(60);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json((data ?? []).reverse());
}
