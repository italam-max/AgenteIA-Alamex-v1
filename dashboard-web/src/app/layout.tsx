import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

import { Sidebar } from "@/components/Sidebar";
import { Toaster } from "@/components/ui/sonner";

// The exact same two font files integrations/media/template_compositor.py draws with on every
// generated post — the panel and the posts it manages read as one visual system.
const archivoBlack = localFont({
  src: "../fonts/ArchivoBlack-Regular.ttf",
  variable: "--font-display",
  display: "swap",
});

const inter = localFont({
  src: "../fonts/Inter-Variable.ttf",
  variable: "--font-body",
  weight: "100 900",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Agentes de Marketing — Alamex",
  description: "Panel de los agentes de marketing preconfigurados para Alamex.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className={`${archivoBlack.variable} ${inter.variable} antialiased`}>
      <body className="flex min-h-screen bg-paper text-ink">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <main className="mx-auto w-full max-w-5xl flex-1 px-10 py-10">{children}</main>
        </div>
        <Toaster />
      </body>
    </html>
  );
}
