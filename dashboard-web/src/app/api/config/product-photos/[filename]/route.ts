import { NextResponse } from "next/server";

import { updateManifestEntry } from "@/lib/manifest";

export async function PUT(request: Request, { params }: { params: Promise<{ filename: string }> }) {
  const { filename } = await params;
  const updates = await request.json();

  try {
    const entry = updateManifestEntry(decodeURIComponent(filename), {
      tags: Array.isArray(updates?.tags) ? updates.tags : undefined,
      description: typeof updates?.description === "string" ? updates.description : undefined,
    });
    return NextResponse.json(entry);
  } catch (err) {
    return NextResponse.json({ error: err instanceof Error ? err.message : String(err) }, { status: 404 });
  }
}
