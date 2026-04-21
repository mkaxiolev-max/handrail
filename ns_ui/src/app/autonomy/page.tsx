import { Card, GoldRule } from "@/components/ui/Card";

async function get(path:string){
  const base = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:9011";
  try { const r = await fetch(`${base}${path}`, { cache:"no-store" }); return r.ok ? r.json() : null; } catch { return null; }
}

export default async function Autonomy(){
  const d:any = await get("/api/v1/ui/autonomy") ?? {};
  const ceiling = d.current_ceiling ?? 3;
  const tiers = d.tiers ?? [];
  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Autonomy Tiers</h1>
      <GoldRule/>
      <Card>
        <div className="text-sm text-white/70 mb-4">
          Current ceiling: <span className="text-amber-300 font-semibold">Tier {ceiling}</span> — bounded authority (kenosis).
          Tiers 0–3 are production-safe; 4 and 5 require explicit founder escalation.
        </div>
        <div className="grid grid-cols-6 gap-2">
          {tiers.map((t:any)=>(
            <div key={t.n} className={`p-3 rounded-lg border ${t.n<=ceiling?"border-amber-400/30 bg-amber-400/5":"border-white/10 bg-white/5 opacity-60"}`}>
              <div className="text-[10px] uppercase tracking-[0.2em] text-white/50">Tier {t.n}</div>
              <div className="text-xs mt-1">{t.name}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
