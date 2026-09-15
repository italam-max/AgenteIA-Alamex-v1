import { NextResponse } from "next/server";

import { parseAvailableModels, readFeaturedModel, writeFeaturedModel } from "@/lib/featuredModel";

export async function GET() {
  return NextResponse.json({ models: parseAvailableModels(), featured: readFeaturedModel() });
}

export async function PUT(request: Request) {
  const body = await request.json();
  writeFeaturedModel(typeof body?.body === "string" ? body.body : "");
  return NextResponse.json({ ok: true, featured: readFeaturedModel() });
}
