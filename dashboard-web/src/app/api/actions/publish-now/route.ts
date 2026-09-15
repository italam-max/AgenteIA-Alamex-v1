import { spawn } from "node:child_process";
import path from "node:path";

import { NextResponse } from "next/server";

import { PYTHON_VENV_PATH, REPO_ROOT } from "@/lib/repoPaths";

export async function POST(request: Request) {
  const body = await request.json();
  const brief = typeof body?.brief === "string" ? body.brief.trim() : "";
  if (!brief) {
    return NextResponse.json({ error: "Falta el tema/brief del post" }, { status: 400 });
  }

  const scriptPath = path.join(REPO_ROOT, "post_now.py");

  // Fire-and-forget: post_now.py takes 15-90s (image generation + publish). The frontend polls
  // /api/runs/latest for live progress (agents/social_media.py writes the agent_runs row as soon
  // as it starts) — we don't want this request to hang the browser waiting for it to finish.
  const child = spawn(PYTHON_VENV_PATH, [scriptPath, brief], {
    cwd: REPO_ROOT,
    detached: true,
    stdio: "ignore",
  });
  child.unref();

  return NextResponse.json({ started: true });
}
