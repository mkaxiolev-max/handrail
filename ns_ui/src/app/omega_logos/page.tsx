import { Card, GoldRule } from "@/components/ui/Card";
import { Metric } from "@/components/ui/Metric";

async function get(path:string){
  const base = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:9011";
  try { const r = await fetch(`${base}${path}`, { cache:"no-store" }); return r.ok ? r.json() : null; } catch { return null; }
}

export default async function OmegaLogos(){
  const d:any = await get("/api/v1/ui/omega_logos") ?? {};
  const subs = d.sub ?? [
    { key:"C1", name:"Gnoseogenic knowledge-birth", score:85, weight:0.20 },
    { key:"C2", name:"Constitutive non-violation",   score:93, weight:0.25 },
    { key:"C3", name:"Action–knowledge symmetry",    score:82, weight:0.20 },
    { key:"C4", name:"Oracle-completeness",          score:78, weight:0.15 },
    { key:"C5", name:"Boundary-recognition (kenosis)",score:90, weight:0.20 },
  ];
  const composite = d.composite ?? 86.35;

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-baseline gap-3">
        <span className="text-3xl">🕊️</span>
        <h1 className="text-2xl font-semibold tracking-tight">Ω-Logos — Logos-Bounded Omnipotence Index</h1>
      </div>
      <GoldRule/>
      <div className="grid grid-cols-3 gap-4">
        <Card><Metric label="I₆ Composite" value={composite.toFixed(2)} hint="Certified Advanced — upper" /></Card>
        <Card><Metric label="Engineering ceiling" value="93.2" hint="+full insight stack" accent="text-emerald-300"/></Card>
        <Card><Metric label="External-gated cap" value="94.4" hint="+3-domain validators" accent="text-sky-300"/></Card>
      </div>
      <Card>
        <div className="text-sm text-white/70 mb-4 leading-relaxed">
          <span className="text-amber-300">Ω-Logos</span> measures Logos-bounded omnipotence: the capacity to generate,
          under any pressure, all true knowledge required for any legitimate action, without violating constitutive invariants.
        </div>
        <div className="space-y-3">
          {subs.map((s:any)=>(
            <div key={s.key}>
              <div className="flex justify-between text-xs text-white/70">
                <span><span className="font-mono text-amber-300">{s.key}</span> · {s.name}</span>
                <span className="tabular-nums">{s.score}/100 · w={s.weight.toFixed(2)}</span>
              </div>
              <div className="h-1.5 mt-1 rounded-full bg-white/5 overflow-hidden">
                <div className="h-full bg-gradient-to-r from-amber-400 to-amber-600" style={{width:`${s.score}%`}}/>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
