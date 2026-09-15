"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Agentes" },
  { href: "/corridas", label: "Corridas" },
  { href: "/posts", label: "Posts" },
  { href: "/estrategia", label: "Estrategia" },
  { href: "/crecimiento", label: "Crecimiento" },
  { href: "/configuracion", label: "Configuración" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sticky top-0 flex h-screen w-60 shrink-0 flex-col bg-ink text-white">
      {/* the "cable" — a thin guide-rail running the height of the sidebar */}
      <div className="absolute top-0 right-0 h-full w-px bg-gradient-to-b from-gold/60 via-rail/40 to-transparent" />

      <div className="px-5 pt-6 pb-5">
        <div className="inline-block rounded-md bg-white px-2.5 py-1.5">
          <Image src="/alamex-logo.png" alt="Alamex" width={120} height={34} className="h-6 w-auto" priority />
        </div>
      </div>

      <nav className="flex-1 px-3">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={
                "group relative flex items-center gap-3 rounded-md px-3 py-2.5 text-[0.95rem] transition-colors " +
                (active ? "bg-white/[0.07] text-white" : "text-white/55 hover:bg-white/[0.04] hover:text-white/85")
              }
            >
              <span
                className={
                  "h-1.5 w-1.5 shrink-0 rounded-full transition-colors " +
                  (active ? "bg-gold shadow-[0_0_6px_2px_rgba(214,161,60,0.55)]" : "bg-white/15 group-hover:bg-white/30")
                }
              />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="px-5 pb-6 pt-4 text-xs text-white/35">
        Panel de agentes
        <br />
        Elevadores Alamex
      </div>
    </aside>
  );
}
