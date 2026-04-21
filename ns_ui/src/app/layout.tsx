import "./globals.css";
import type { ReactNode } from "react";
import { SECTIONS } from "@/sections/manifest";
import Link from "next/link";

export const metadata = { title: "NS∞ · AXIOLEV Holdings", description: "Constitutional AI operating system" };

export default function Root({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#0a0a0f] text-white antialiased selection:bg-amber-400/30">
        <div className="fixed inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,rgba(251,191,36,0.08),transparent_60%),radial-gradient(ellipse_at_bottom,rgba(99,102,241,0.08),transparent_60%)]" />
        <div className="flex min-h-screen">
          <aside className="w-64 border-r border-white/10 bg-black/40 backdrop-blur-xl">
            <div className="p-5">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-amber-400 to-amber-600 shadow-lg shadow-amber-500/40"/>
                <div>
                  <div className="text-sm font-semibold tracking-wide">NS∞</div>
                  <div className="text-[10px] uppercase tracking-[0.2em] text-white/50">AXIOLEV Holdings</div>
                </div>
              </div>
            </div>
            <nav className="px-3 space-y-0.5">
              {SECTIONS.map(s=>(
                <Link key={s.slug} href={`/${s.slug}`}
                  className="group flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-white/70 hover:text-white hover:bg-white/5 transition-colors">
                  <span className="text-base">{s.icon}</span>
                  <span>{s.title}</span>
                </Link>
              ))}
            </nav>
            <div className="mt-6 mx-4 rounded-lg border border-amber-400/20 bg-amber-400/5 p-3">
              <div className="text-[10px] uppercase tracking-widest text-amber-300/80">MASTER v3.0</div>
              <div className="text-xs text-white/60 mt-1">I₁–I₆ weighted composite live</div>
            </div>
          </aside>
          <main className="flex-1 relative">{children}</main>
        </div>
      </body>
    </html>
  );
}
