import { spawn } from "node:child_process";
import path from "node:path";

import { NextResponse } from "next/server";

import { PYTHON_VENV_PATH, REPO_ROOT } from "@/lib/repoPaths";

const DEFAULT_INSTRUCTION = "encárgate de la publicidad de esta semana";

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  const instruction = typeof body?.instruction === "string" && body.instruction.trim() ? body.instruction.trim() : DEFAULT_INSTRUCTION;

  const scriptPath = path.join(REPO_ROOT, "main.py");

  // Fire-and-forget — same reasoning as /api/actions/publish-now. This one is slower (analyzes
  // engagement + plans 2-4 posts), can take several minutes.
  const child = spawn(PYTHON_VENV_PATH, [scriptPath, instruction], {
    cwd: REPO_ROOT,
    detached: true,
    stdio: "ignore",
  });
  child.unref();

  return NextResponse.json({ started: true });
}
