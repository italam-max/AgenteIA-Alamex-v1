import { NextResponse } from "next/server";

import { getGrowthMissionStatus } from "@/lib/growthProcess";

export async function GET() {
  return NextResponse.json(getGrowthMissionStatus());
}
