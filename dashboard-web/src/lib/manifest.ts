import fs from "node:fs";

import { PATHS } from "./repoPaths";
import type { ProductPhoto } from "./types";

export function readManifest(): ProductPhoto[] {
  if (!fs.existsSync(PATHS.manifest)) return [];
  return JSON.parse(fs.readFileSync(PATHS.manifest, "utf-8"));
}

export function writeManifest(entries: ProductPhoto[]): void {
  fs.writeFileSync(PATHS.manifest, `${JSON.stringify(entries, null, 2)}\n`, "utf-8");
}

export function updateManifestEntry(
  filename: string,
  updates: Partial<Pick<ProductPhoto, "tags" | "description">>
): ProductPhoto {
  const entries = readManifest();
  const entry = entries.find((e) => e.filename === filename);
  if (!entry) {
    throw new Error(`No existe la entrada '${filename}' en manifest.json`);
  }
  Object.assign(entry, updates);
  writeManifest(entries);
  return entry;
}
