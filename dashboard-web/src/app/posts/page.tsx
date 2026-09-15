import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { STATUS_LABEL, STATUS_VARIANT } from "@/lib/format";
import { getSupabaseServerClient } from "@/lib/supabaseServer";
import type { Post } from "@/lib/types";

export const dynamic = "force-dynamic";

async function getPosts(): Promise<Post[]> {
  const { data } = await getSupabaseServerClient()
    .from("posts")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(100);
  return (data ?? []) as Post[];
}

export default async function PostsPage({
  searchParams,
}: {
  searchParams: Promise<{ platform?: string }>;
}) {
  const { platform } = await searchParams;
  const posts = await getPosts();
  const platforms = [...new Set(posts.map((p) => p.platform))].sort();
  const filtered = platform ? posts.filter((p) => p.platform === platform) : posts;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl tracking-tight">Posts</h1>
        <p className="text-sm text-muted-foreground">Todo lo que el agente de Social Media ha generado y publicado.</p>
      </div>

      <div className="flex gap-2 border-b border-border pb-4">
        <FilterLink label="Todas" active={!platform} href="/posts" />
        {platforms.map((p) => (
          <FilterLink key={p} label={p} active={platform === p} href={`/posts?platform=${p}`} />
        ))}
      </div>

      {filtered.length === 0 && <p className="text-sm text-muted-foreground">Todavía no hay posts registrados.</p>}

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((post) => (
          <article key={post.id} className="shadow-card-hover shadow-card group rounded-lg bg-card">
            {/* the "plaque" — a thin rail-colored inset frames the generated media like a mounted piece */}
            <div className="p-2">
              <div className="overflow-hidden rounded-md ring-1 ring-rail/25">
                {post.media_url ? (
                  post.post_type === "video" ? (
                    <video src={post.media_url} controls preload="metadata" className="aspect-square w-full object-cover" />
                  ) : (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={post.media_url} alt="" className="aspect-square w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]" />
                  )
                ) : (
                  <div className="aspect-square bg-muted" />
                )}
              </div>
            </div>
            <div className="space-y-2.5 px-4 pb-4 pt-1">
              <div className="flex flex-wrap items-center justify-between gap-1.5">
                <div className="flex flex-wrap gap-1.5">
                  <Badge variant="outline">{post.platform}</Badge>
                  {post.content_type && <Badge variant="secondary">{post.content_type}</Badge>}
                </div>
                <Badge variant={STATUS_VARIANT[post.status] ?? "outline"}>
                  {STATUS_LABEL[post.status] ?? post.status}
                </Badge>
              </div>
              <p className="text-sm leading-relaxed text-foreground/80 line-clamp-4">{post.caption}</p>
              {post.error && <p className="text-xs text-destructive">{post.error}</p>}
              {post.permalink && (
                <Link
                  href={post.permalink}
                  target="_blank"
                  className="inline-block text-sm font-medium text-navy hover:underline"
                >
                  Ver publicación
                </Link>
              )}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function FilterLink({ label, active, href }: { label: string; active: boolean; href: string }) {
  return (
    <Link
      href={href}
      className={
        "rounded-full border px-3 py-1 text-sm transition-colors " +
        (active ? "border-navy bg-navy text-white" : "border-border text-muted-foreground hover:border-rail/40 hover:text-foreground")
      }
    >
      {label}
    </Link>
  );
}
