import { Card, GoldRule } from "@/components/ui/Card";

async function get(path:string){
  const base = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:9011";
  try { const r = await fetch(`${base}${path}`, { cache:"no-store" }); return r.ok ? r.json() : null; } catch { return null; }
}

export default async function Ring5(){
  const d:any = await get("/api/v1/ui/ring5") ?? {};
  const gates = d.gates ?? [
    { id:"G1", name:"Stripe LLC verification",      status:"open" },
    { id:"G2", name:"Live Stripe secret key",       status:"open" },
    { id:"G3", name:"ROOT/Handrail price IDs",      status:"open" },
    { id:"G4", name:"YubiKey slot 2 enrollment",    status:"open" },
    { id:"G5", name:"DNS CNAME root.axiolev.com",   status:"open" },
  ];
  const open = gates.filter((g:any)=>g.status!=="closed").length;
  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Ring 5 — External Gates</h1>
      <GoldRule/>
      <Card>
        <div className="text-sm text-white/70 mb-4">
          External non-software gates. <span className="text-amber-300">{open}/{gates.length}</span> currently open.
        </div>
        <ul className="divide-y divide-white/5">
          {gates.map((g:any)=>(
            <li key={g.id} className="flex items-center justify-between py-3">
              <div className="flex items-center gap-3">
                <span className="font-mono text-xs text-white/60">{g.id}</span>
                <span>{g.name}</span>
              </div>
              <span className={g.status==="closed"?"text-emerald-300":"text-rose-300"}>{g.status}</span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
