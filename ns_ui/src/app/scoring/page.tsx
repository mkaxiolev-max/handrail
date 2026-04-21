import { Card, GoldRule } from "@/components/ui/Card";

async function get(path:string){
  const base = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:9011";
  try { const r = await fetch(`${base}${path}`, { cache:"no-store" }); return r.ok ? r.json() : null; } catch { return null; }
}

export default async function Scoring(){
  const sc:any = await get("/api/v1/ui/scoring") ?? {};
  const v21 = sc.v2_1 ?? {};
  const v30 = sc.v3_0 ?? {};
  const rows = (sc.instruments ?? [
    { id:"I1", name:"Super-Omega v2",       score:88.02, weight_v21:0.15, weight_v30:0.150 },
    { id:"I2", name:"Omega Intelligence v2",score:82.42, weight_v21:0.20, weight_v30:0.200 },
    { id:"I3", name:"UOIE v2",              score:84.60, weight_v21:0.20, weight_v30:0.175 },
    { id:"I4", name:"GPX-Ω",                score:86.80, weight_v21:0.30, weight_v30:0.275 },
    { id:"I5", name:"SAQ",                  score:87.50, weight_v21:0.15, weight_v30:0.150 },
    { id:"I6", name:"Ω-Logos",              score:86.35, weight_v21:0.00, weight_v30:0.100 },
  ]);
  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Scoring — MASTER v2.1 / v3.0</h1>
      <GoldRule/>
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <div className="text-[10px] uppercase tracking-[0.2em] text-white/50">MASTER v2.1</div>
          <div className="text-4xl font-semibold text-amber-300 tabular-nums mt-1">{(v21.master ?? 85.77).toFixed(2)}</div>
          <div className="text-xs text-white/50 mt-1">Certified Advanced</div>
        </Card>
        <Card>
          <div className="text-[10px] uppercase tracking-[0.2em] text-white/50">MASTER v3.0 <span className="text-amber-300">(with I₆)</span></div>
          <div className="text-4xl font-semibold text-amber-300 tabular-nums mt-1">{(v30.master ?? 90.13).toFixed(2)}</div>
          <div className="text-xs text-white/50 mt-1">Omega-Approaching ≥ 90</div>
        </Card>
      </div>
      <Card>
        <table className="w-full text-sm">
          <thead className="text-[10px] uppercase tracking-[0.2em] text-white/50">
            <tr><th className="text-left py-2">ID</th><th className="text-left">Instrument</th><th className="text-right">Score</th><th className="text-right">w(v2.1)</th><th className="text-right">w(v3.0)</th></tr>
          </thead>
          <tbody>
            {rows.map((r:any)=>(
              <tr key={r.id} className="border-t border-white/5">
                <td className="py-2 font-mono text-white/70">{r.id}</td>
                <td>{r.name}</td>
                <td className="text-right tabular-nums text-amber-300">{r.score.toFixed(2)}</td>
                <td className="text-right tabular-nums text-white/60">{r.weight_v21.toFixed(3)}</td>
                <td className="text-right tabular-nums text-white/80">{r.weight_v30.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
