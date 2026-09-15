import { NextResponse } from "next/server";

import { stopGrowthMission } from "@/lib/growthProcess";

export async function POST() {
  stopGrowthMission();
  return NextResponse.json({ stopped: true });
}
