import { NextResponse } from "next/server";

import { readManifest } from "@/lib/manifest";

export async function GET() {
  return NextResponse.json(readManifest());
}
