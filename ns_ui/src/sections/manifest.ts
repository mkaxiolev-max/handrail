// 11-section founder habitat — AXIOLEV Holdings LLC © 2026
export type Section = {
  slug: string; title: string; icon: string; endpoint: string; accent: string;
};
export const SECTIONS: Section[] = [
  { slug:"home",         title:"Founder Home",       icon:"🏛️", endpoint:"/api/v1/ui/summary",      accent:"from-amber-500/20" },
  { slug:"living",       title:"Living Architecture",icon:"🧬", endpoint:"/api/v1/ui/architecture", accent:"from-emerald-500/20" },
  { slug:"governance",   title:"Governance + Canon", icon:"⚖️", endpoint:"/api/v1/ui/governance",   accent:"from-violet-500/20" },
  { slug:"engine",       title:"Engine Room",        icon:"⚙️", endpoint:"/api/v1/ui/execution",    accent:"from-sky-500/20" },
  { slug:"voice",        title:"Violet (Voice)",     icon:"🎙️", endpoint:"/api/v1/ui/voice",        accent:"from-fuchsia-500/20" },
  { slug:"alexandria",   title:"Alexandria Ledger",  icon:"📜", endpoint:"/api/v1/ui/memory",       accent:"from-yellow-500/20" },
  { slug:"build",        title:"Build + Receipts",   icon:"🧱", endpoint:"/api/v1/ui/build",        accent:"from-orange-500/20" },
  { slug:"timeline",     title:"Timeline",           icon:"🗓️", endpoint:"/api/v1/ui/timeline",     accent:"from-rose-500/20" },
  { slug:"scoring",      title:"Scoring (v2.1/v3.0)",icon:"📊", endpoint:"/api/v1/ui/scoring",      accent:"from-teal-500/20" },
  { slug:"omega_logos",  title:"Ω-Logos (I₆)",       icon:"🕊️", endpoint:"/api/v1/ui/omega_logos",  accent:"from-indigo-500/20" },
  { slug:"ring5",        title:"Ring 5 Gates",       icon:"🗝️", endpoint:"/api/v1/ui/ring5",        accent:"from-red-500/20" },
];
