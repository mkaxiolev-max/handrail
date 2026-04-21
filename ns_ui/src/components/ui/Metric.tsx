export function Metric({ label, value, hint, accent = "text-amber-300" }:{
  label:string; value:string|number; hint?:string; accent?:string;
}){
  return (
    <div className="flex flex-col">
      <div className="text-[10px] uppercase tracking-[0.2em] text-white/50">{label}</div>
      <div className={`text-2xl font-semibold ${accent} tabular-nums`}>{value}</div>
      {hint ? <div className="text-xs text-white/40 mt-0.5">{hint}</div> : null}
    </div>
  );
}
