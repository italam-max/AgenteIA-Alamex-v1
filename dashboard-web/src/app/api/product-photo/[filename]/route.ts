import fs from "node:fs";
import path from "node:path";

import { NextResponse } from "next/server";

import { PATHS } from "@/lib/repoPaths";

const CONTENT_TYPES: Record<string, string> = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
};

export async function GET(_request: Request, { params }: { params: Promise<{ filename: string }> }) {
  const { filename } = await params;
  const safeName = path.basename(decodeURIComponent(filename)); // defends against path traversal
  const filePath = path.join(PATHS.productPhotosDir, safeName);

  if (!filePath.startsWith(PATHS.productPhotosDir) || !fs.existsSync(filePath)) {
    return new NextResponse("Not found", { status: 404 });
  }

  const ext = path.extname(filePath).toLowerCase();
  return new NextResponse(fs.readFileSync(filePath), {
    headers: { "Content-Type": CONTENT_TYPES[ext] ?? "application/octet-stream" },
  });
}
