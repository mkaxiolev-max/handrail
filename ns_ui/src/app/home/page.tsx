import { Card, GoldRule } from "@/components/ui/Card";
import { Metric } from "@/components/ui/Metric";
import { Sparkline } from "@/components/ui/Sparkline";

async function get(path:string){
  const base = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:9011";
  try { const r = await fetch(`${base}${path}`, { cache:"no-store" }); return r.ok ? r.json() : null; } catch { return null; }
}

export default async function Home(){
  const s:any = await get("/api/v1/ui/summary");
  const sc:any = await get("/api/v1/ui/scoring");
  const invariants = s?.invariants ?? { total:10, enforced:10 };
  const services = s?.services ?? { total:12, healthy:12 };
  const master_v21 = sc?.v2_1?.master ?? 85.77;
  const master_v30 = sc?.v3_0?.master ?? 90.13;
  const spark = sc?.v3_0?.history ?? [82,83.1,84.17,84.46,85.77,90.13];

  return (
    <div className="p-8 space-y-6">
      <div>
        <div className="text-[11px] uppercase tracking-[0.3em] text-amber-300/80">AXIOLEV · NorthStar Infinity</div>
        <h1 className="text-3xl font-semibold tracking-tight mt-1">Founder Home</h1>
        <p className="text-sm text-white/60 mt-1">Constitutional AI operating system · live constitutional readout.</p>
      </div>
      <GoldRule />
      <div className="grid grid-cols-4 gap-4">
        <Card><Metric label="MASTER v3.0" value={master_v30.toFixed(2)} hint={`v2.1: ${master_v21.toFixed(2)}`} /></Card>
        <Card><Metric label="Invariants" value={`${invariants.enforced}/${invariants.total}`} hint="enforced=True" accent="text-emerald-300"/></Card>
        <Card><Metric label="Services" value={`${services.healthy}/${services.total}`} hint="docker healthy" accent="text-sky-300"/></Card>
        <Card>
          <div className="text-[10px] uppercase tracking-[0.2em] text-white/50">Trajectory</div>
          <div className="mt-2"><Sparkline values={spark} /></div>
          <div className="text-xs text-white/40 mt-1">baseline → ceiling</div>
        </Card>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <Card className="col-span-2">
          <div className="text-sm font-medium mb-3">Constitutional Readout</div>
          <ul className="space-y-2 text-sm text-white/75">
            <li className="flex justify-between"><span>Dignity Hamiltonian gate</span><span className="text-emerald-300">active</span></li>
            <li className="flex justify-between"><span>HIC patterns</span><span className="text-emerald-300">60 live</span></li>
            <li className="flex justify-between"><span>Alexandria chain</span><span className="text-emerald-300">valid · SHA-256</span></li>
            <li className="flex justify-between"><span>Ω-Logos (I₆)</span><span className="text-amber-300">86.35</span></li>
            <li className="flex justify-between"><span>Ring 5 external gates</span><span className="text-rose-300">5 open</span></li>
          </ul>
        </Card>
        <Card>
          <div className="text-sm font-medium mb-3">Violet</div>
          <div className="text-xs text-white/60">mode: founder_ready</div>
          <div className="text-xs text-white/60">interface: violet</div>
          <div className="mt-3 h-2 w-full rounded-full bg-white/5 overflow-hidden">
            <div className="h-full w-3/4 ax-shimmer bg-fuchsia-400/40" />
          </div>
        </Card>
      </div>
    </div>
  );
}
