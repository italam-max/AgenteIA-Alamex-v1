import { NextResponse } from "next/server";

import { startGrowthMission } from "@/lib/growthProcess";

export async function POST() {
  try {
    startGrowthMission();
    return NextResponse.json({ started: true });
  } catch (err) {
    return NextResponse.json({ error: err instanceof Error ? err.message : "No se pudo iniciar" }, { status: 409 });
  }
}
