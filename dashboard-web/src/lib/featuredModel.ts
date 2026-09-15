import fs from "node:fs";

import { PATHS } from "./repoPaths";

const SECTION_HEADER = "## Modelo destacado de esta semana";
const NON_MODEL_HEADERS = new Set(["Modelo destacado de esta semana", "Precio / promoción vigente"]);

export function parseAvailableModels(): string[] {
  const content = fs.readFileSync(PATHS.equipmentCatalog, "utf-8");
  const headers = [...content.matchAll(/^## (.+)$/gm)].map((m) => m[1].trim());
  return headers.filter((h) => !NON_MODEL_HEADERS.has(h));
}

export function readFeaturedModel(): string {
  const content = fs.readFileSync(PATHS.equipmentCatalog, "utf-8");
  const idx = content.indexOf(SECTION_HEADER);
  if (idx === -1) return "";
  const rest = content.slice(idx + SECTION_HEADER.length);
  const nextIdx = rest.search(/\n## /);
  const body = (nextIdx === -1 ? rest : rest.slice(0, nextIdx)).trim();
  return body;
}

export function writeFeaturedModel(body: string): void {
  const content = fs.readFileSync(PATHS.equipmentCatalog, "utf-8");
  const idx = content.indexOf(SECTION_HEADER);
  if (idx === -1) {
    throw new Error("No se encontró la sección 'Modelo destacado de esta semana' en equipment_catalog.md");
  }
  const afterHeader = idx + SECTION_HEADER.length;
  const rest = content.slice(afterHeader);
  const nextIdx = rest.search(/\n## /);
  const before = content.slice(0, afterHeader);
  const after = nextIdx === -1 ? "" : rest.slice(nextIdx);
  fs.writeFileSync(PATHS.equipmentCatalog, `${before}\n\n${body.trim()}\n${after}`, "utf-8");
}
