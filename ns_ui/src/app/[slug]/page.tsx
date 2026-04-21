import { SECTIONS } from "@/sections/manifest";
import { Card, GoldRule } from "@/components/ui/Card";
import { notFound } from "next/navigation";

async function fetchData(endpoint: string){
  const base = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:9011";
  try{
    const r = await fetch(`${base}${endpoint}`, { cache:"no-store" });
    if(!r.ok) return { _error: `${r.status}` };
    return await r.json();
  }catch(e:any){ return { _error: String(e?.message ?? e) }; }
}

export default async function Section({ params }: { params: { slug: string }}){
  const sec = SECTIONS.find(s => s.slug === params.slug);
  if(!sec) return notFound();
  const data:any = await fetchData(sec.endpoint);
  return (
    <div className="p-8 space-y-6">
      <div className="flex items-baseline gap-3">
        <span className="text-3xl">{sec.icon}</span>
        <h1 className="text-2xl font-semibold tracking-tight">{sec.title}</h1>
        <span className="ml-auto text-[10px] uppercase tracking-widest text-white/40">endpoint {sec.endpoint}</span>
      </div>
      <GoldRule />
      {data?._error ? (
        <Card>
          <div className="text-sm text-rose-300">Endpoint returned an error: <span className="font-mono">{data._error}</span></div>
          <div className="text-xs text-white/50 mt-2">This section will render as soon as the API is live. No client crash.</div>
        </Card>
      ) : (
        <Card>
          <pre className="text-xs text-white/70 overflow-auto max-h-[60vh] leading-relaxed">{JSON.stringify(data,null,2)}</pre>
        </Card>
      )}
    </div>
  );
}
