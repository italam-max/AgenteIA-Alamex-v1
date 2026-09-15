import path from "node:path";

// dashboard-web/ lives as a sibling folder inside the Python project's repo root.
export const REPO_ROOT = path.resolve(process.cwd(), "..");

export const PATHS = {
  guidelines: path.join(REPO_ROOT, "brand", "guidelines.md"),
  equipmentCatalog: path.join(REPO_ROOT, "brand", "equipment_catalog.md"),
  productPhotosDir: path.join(REPO_ROOT, "brand", "product_photos"),
  productPhotosRawDir: path.join(REPO_ROOT, "brand", "product_photos", "raw"),
  manifest: path.join(REPO_ROOT, "brand", "product_photos", "manifest.json"),
  envFile: path.join(REPO_ROOT, ".env"),
  retouchScript: path.join(REPO_ROOT, "scripts", "retouch_product_photos.py"),
  growthMissionScript: path.join(REPO_ROOT, "run_growth_mission.py"),
  growthMissionPidFile: path.join(REPO_ROOT, ".growth_mission.pid"),
  growthMissionLogFile: path.join(REPO_ROOT, ".growth_mission.log"),
};

// This app only ever runs locally (`next dev`/`next start` on the same machine as the Python
// repo) — never deployed — so Turbopack's file-tracing-for-deployment warning here doesn't apply.
export const PYTHON_VENV_PATH = path.resolve(
  /*turbopackIgnore: true*/ process.cwd(),
  process.env.PYTHON_VENV_PATH ?? "..\\.venv\\Scripts\\python.exe"
);
