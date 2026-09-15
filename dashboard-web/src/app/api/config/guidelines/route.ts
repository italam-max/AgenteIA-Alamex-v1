import fs from "node:fs";

import { NextResponse } from "next/server";

import { PATHS } from "@/lib/repoPaths";

export async function GET() {
  const content = fs.readFileSync(PATHS.guidelines, "utf-8");
  return NextResponse.json({ content });
}

export async function PUT(request: Request) {
  const body = await request.json();
  const content = body?.content;
  if (typeof content !== "string" || content.trim().length === 0) {
    return NextResponse.json({ error: "El contenido no puede estar vacío" }, { status: 400 });
  }
  fs.writeFileSync(PATHS.guidelines, content, "utf-8");
  return NextResponse.json({ ok: true });
}
