export function Sparkline({ values, color="#fbbf24" }:{ values:number[]; color?:string }){
  if(!values?.length) return <svg width="120" height="24"/>;
  const w=120,h=24,min=Math.min(...values),max=Math.max(...values),rng=Math.max(1,max-min);
  const pts=values.map((v,i)=>`${(i/(values.length-1))*w},${h-((v-min)/rng)*h}`).join(" ");
  return (
    <svg width={w} height={h} className="opacity-90">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
