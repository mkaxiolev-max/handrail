import React from "react";

interface TrustStripProps {
  receiptHash: string;
  chainVerified: boolean;
  mode: string;
  pressure?: string | null;
  canonVersion?: number | null;
  canonHash?: string | null;
  memoryAtomsWritten?: number;
  memoryAtomsQueried?: number;
  feedItemsAdded?: number;
  responseShape?: string | null;
  voiceSessionId?: string | null;
}

const pill = (label: string, value: string | number, ok?: boolean) => {
  const color = ok === true ? "#1a7a4a" : ok === false ? "#7a1a1a" : "#1a3a5a";
  return (
    <span key={label} style={{display:"inline-flex",alignItems:"center",gap:"4px",
      background:color,borderRadius:"4px",padding:"2px 7px",fontSize:"10px",
      fontFamily:"monospace",color:"#e8e8e8",margin:"2px",letterSpacing:"0.3px"}}>
      <span style={{opacity:0.6}}>{label}</span>
      <span style={{fontWeight:700}}>{String(value)}</span>
    </span>
  );
};

export function TrustStrip({
  receiptHash, chainVerified, mode, pressure, canonVersion, canonHash,
  memoryAtomsWritten=0, memoryAtomsQueried=0, feedItemsAdded=0,
  responseShape, voiceSessionId,
}: TrustStripProps) {
  return (
    <div style={{borderTop:"1px solid rgba(255,255,255,0.08)",marginTop:"8px",
      paddingTop:"6px",display:"flex",flexWrap:"wrap",gap:"2px"}}>
      {pill("receipt", receiptHash.slice(0,12)+"…")}
      {pill("chain", chainVerified ? "✓" : "BROKEN", chainVerified)}
      {pill("mode", mode)}
      {pressure && pill("pressure", pressure)}
      {responseShape && pill("kind", responseShape)}
      {canonVersion != null && pill("canon", `v${canonVersion}`)}
      {canonHash && pill("canon_hash", canonHash.slice(0,8)+"…")}
      {memoryAtomsWritten > 0 && pill("atoms_written", memoryAtomsWritten)}
      {memoryAtomsQueried > 0 && pill("atoms_queried", memoryAtomsQueried)}
      {feedItemsAdded > 0 && pill("feed+", feedItemsAdded)}
      {voiceSessionId && pill("voice", voiceSessionId.slice(0,8)+"…")}
    </div>
  );
}

export default TrustStrip;
