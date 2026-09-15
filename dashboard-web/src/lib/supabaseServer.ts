import { createClient, type SupabaseClient } from "@supabase/supabase-js";

let cachedClient: SupabaseClient | null = null;

// Server-only: uses the service role key, which must never reach the browser bundle. Every
// caller of this must live in a Route Handler / server component, never in a "use client" file.
export function getSupabaseServerClient(): SupabaseClient {
  if (cachedClient) return cachedClient;

  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) {
    throw new Error("Missing SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY — check dashboard-web/.env.local");
  }

  cachedClient = createClient(url, key, { auth: { persistSession: false } });
  return cachedClient;
}
