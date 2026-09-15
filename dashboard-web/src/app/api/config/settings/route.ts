import { NextResponse } from "next/server";

import { readEditableEnv, writeEditableEnv, type EditableEnvKey } from "@/lib/envFile";

export async function GET() {
  return NextResponse.json(readEditableEnv());
}

export async function PUT(request: Request) {
  const body = (await request.json()) as Partial<Record<EditableEnvKey, string>>;
  const updated = writeEditableEnv(body);
  return NextResponse.json(updated);
}
