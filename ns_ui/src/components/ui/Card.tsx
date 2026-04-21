import { ReactNode } from "react";
export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`relative rounded-2xl border border-white/10 bg-gradient-to-br from-black/60 to-black/30 backdrop-blur-md p-5 shadow-[0_0_0_1px_rgba(255,255,255,0.04),0_10px_40px_-10px_rgba(0,0,0,0.5)] ${className}`}>
      {children}
    </div>
  );
}
export function GoldRule({ className = "" }: { className?: string }) {
  return <div className={`h-px w-full bg-gradient-to-r from-transparent via-amber-400/60 to-transparent ${className}`} />;
}
