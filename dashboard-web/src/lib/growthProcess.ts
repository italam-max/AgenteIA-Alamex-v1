import { spawn } from "node:child_process";
import fs from "node:fs";

import { PATHS, PYTHON_VENV_PATH, REPO_ROOT } from "./repoPaths";

type PidFileContents = { pid: number; startedAt: string };

export type GrowthMissionStatus = {
  running: boolean;
  pid: number | null;
  startedAt: string | null;
};

function readPidFile(): PidFileContents | null {
  try {
    return JSON.parse(fs.readFileSync(PATHS.growthMissionPidFile, "utf-8")) as PidFileContents;
  } catch {
    return null;
  }
}

function isAlive(pid: number): boolean {
  try {
    // Signal 0 sends nothing — it only tests whether the process exists, cross-platform.
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

export function getGrowthMissionStatus(): GrowthMissionStatus {
  const contents = readPidFile();
  if (!contents || !isAlive(contents.pid)) {
    return { running: false, pid: null, startedAt: null };
  }
  return { running: true, pid: contents.pid, startedAt: contents.startedAt };
}

export function startGrowthMission(): void {
  if (getGrowthMissionStatus().running) {
    throw new Error("La misión de crecimiento ya está corriendo");
  }

  // Unlike the one-shot /api/actions/publish-now spawn, this is a multi-hour loop, so it's tied
  // to this (already long-lived) dev server process rather than fully detached — a Windows
  // detached+unref'd process was observed to die silently with no way to see why. Its stdout/
  // stderr go to a log file (appended, never truncated here) so crashes are actually visible.
  const logFd = fs.openSync(PATHS.growthMissionLogFile, "a");
  // "-u": Python block-buffers stdout/stderr when it isn't a TTY (i.e. redirected to a file), so
  // without this, prints sit invisible in-process until it exits — the log would stay empty for
  // the entire run.
  const child = spawn(PYTHON_VENV_PATH, ["-u", PATHS.growthMissionScript], {
    cwd: REPO_ROOT,
    stdio: ["ignore", logFd, logFd],
    // Windows Python defaults stdout/stderr to the system ANSI codepage (mangling accents/emoji)
    // once they're redirected to a file instead of a console — force real UTF-8 for the log.
    env: { ...process.env, PYTHONIOENCODING: "utf-8" },
  });
  fs.closeSync(logFd);

  // Without these, a spawn failure (bad path, EPERM, ...) or an immediate crash throws an
  // unhandled 'error'/'exit' event on `child` — invisible to whoever clicked "start", and the pid
  // file below would still get written pointing at a process that never really ran.
  child.on("error", (err) => {
    fs.appendFileSync(PATHS.growthMissionLogFile, `\n[spawn error] ${err.message}\n`, "utf-8");
  });
  child.on("exit", (code, signal) => {
    if (code !== 0) {
      fs.appendFileSync(
        PATHS.growthMissionLogFile,
        `\n[process exited] code=${code} signal=${signal}\n`,
        "utf-8"
      );
    }
  });

  if (!child.pid) {
    throw new Error("No se pudo iniciar el proceso");
  }
  const contents: PidFileContents = { pid: child.pid, startedAt: new Date().toISOString() };
  fs.writeFileSync(PATHS.growthMissionPidFile, JSON.stringify(contents), "utf-8");
}

export function getGrowthMissionLogTail(maxLines = 80): string {
  try {
    const content = fs.readFileSync(PATHS.growthMissionLogFile, "utf-8");
    const lines = content.split("\n");
    return lines.slice(-maxLines).join("\n");
  } catch {
    return "";
  }
}

export function stopGrowthMission(): void {
  const contents = readPidFile();
  if (!contents) return;
  try {
    process.kill(contents.pid);
  } catch {
    // Already dead — nothing to do. The stale pid file is harmless: the next status check
    // (or start call) will see the pid isn't alive and treat it as not-running.
  }
}
