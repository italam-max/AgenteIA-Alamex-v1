import fs from "node:fs";

import { PATHS } from "./repoPaths";

// Allow-list of .env keys the panel is allowed to see/edit — API keys and secrets are never
// exposed to this list, so they can never be read or overwritten from the browser.
const EDITABLE_KEYS = [
  "ENABLED_PLATFORMS",
  "MEDIA_GENERATOR",
  "GROWTH_TARGET_FOLLOWERS",
  "GROWTH_TICK_MINUTES",
  "GROWTH_MAX_FOLLOWS_PER_TICK",
  "GROWTH_MAX_REPLIES_PER_TICK",
  "GROWTH_HASHTAGS",
] as const;
export type EditableEnvKey = (typeof EDITABLE_KEYS)[number];

export function readEditableEnv(): Record<EditableEnvKey, string> {
  const content = fs.readFileSync(PATHS.envFile, "utf-8");
  const values = {} as Record<EditableEnvKey, string>;
  for (const key of EDITABLE_KEYS) {
    const match = content.match(new RegExp(`^${key}=(.*)$`, "m"));
    values[key] = match ? match[1].trim() : "";
  }
  return values;
}

export function writeEditableEnv(updates: Partial<Record<EditableEnvKey, string>>): Record<EditableEnvKey, string> {
  let content = fs.readFileSync(PATHS.envFile, "utf-8");
  for (const key of EDITABLE_KEYS) {
    const value = updates[key];
    if (value === undefined) continue;
    const line = `${key}=${value}`;
    const pattern = new RegExp(`^${key}=.*$`, "m");
    content = pattern.test(content) ? content.replace(pattern, line) : `${content}\n${line}\n`;
  }
  fs.writeFileSync(PATHS.envFile, content, "utf-8");
  return readEditableEnv();
}
