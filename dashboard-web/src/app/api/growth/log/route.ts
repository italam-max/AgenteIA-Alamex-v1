import { NextResponse } from "next/server";

import { getGrowthMissionLogTail } from "@/lib/growthProcess";

export async function GET() {
  return NextResponse.json({ log: getGrowthMissionLogTail() });
}
