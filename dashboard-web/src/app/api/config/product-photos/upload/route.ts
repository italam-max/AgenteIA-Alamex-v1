import { execFile } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { promisify } from "node:util";

import { NextResponse } from "next/server";

import { updateManifestEntry } from "@/lib/manifest";
import { PATHS, PYTHON_VENV_PATH, REPO_ROOT } from "@/lib/repoPaths";

const execFileAsync = promisify(execFile);

export async function POST(request: Request) {
  const formData = await request.formData();
  const file = formData.get("file");
  const tagsRaw = formData.get("tags");
  const descriptionRaw = formData.get("description");

  if (!(file instanceof File) || file.size === 0) {
    return NextResponse.json({ error: "Falta el archivo de la foto" }, { status: 400 });
  }

  const safeName = file.name.replace(/[^a-zA-Z0-9._-]/g, "_");
  fs.mkdirSync(PATHS.productPhotosRawDir, { recursive: true });
  const rawPath = path.join(PATHS.productPhotosRawDir, safeName);
  fs.writeFileSync(rawPath, Buffer.from(await file.arrayBuffer()));

  try {
    await execFileAsync(PYTHON_VENV_PATH, [PATHS.retouchScript, safeName], {
      cwd: REPO_ROOT,
      timeout: 5 * 60 * 1000,
    });
  } catch (err) {
    return NextResponse.json(
      { error: `El retoque falló: ${err instanceof Error ? err.message : String(err)}` },
      { status: 500 }
    );
  }

  const stem = safeName.replace(/\.[^./]+$/, "");
  const outFilename = `${stem}.png`;
  const tags =
    typeof tagsRaw === "string" && tagsRaw.trim().length > 0
      ? tagsRaw.split(",").map((t) => t.trim()).filter(Boolean)
      : [];
  const description = typeof descriptionRaw === "string" ? descriptionRaw : "";

  try {
    const entry = updateManifestEntry(outFilename, { tags, description });
    return NextResponse.json(entry);
  } catch (err) {
    return NextResponse.json({ error: err instanceof Error ? err.message : String(err) }, { status: 500 });
  }
}
