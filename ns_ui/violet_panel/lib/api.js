// Typed fetchers — all return ReturnBlock.v2 or error state

const BASE = process.env.NEXT_PUBLIC_NS_BASE || 'http://127.0.0.1:9000';

export async function fetchEndpoint(path) {
  try {
    const res = await fetch(BASE + path, { signal: AbortSignal.timeout(5000) });
    const data = await res.json();
    if (!res.ok) return { _error: true, status: res.status, detail: data };
    return data;
  } catch (e) {
    return { _error: true, status: 0, detail: String(e) };
  }
}

export const ENDPOINTS = {
  alexandriaEvents:   '/alexandria/events?limit=50',
  canonAxioms:        '/canon/axioms',
  pdpRecent:          '/pdp/recent?limit=20',
  ring5Gates:         '/ring5/gates',
  nerObservation:     '/isr/ner',
  forceGroundState:   '/cps/force_ground/state',
  clearingAbstentions:'/clearing/recent_abstentions',
  canonInvariants:    '/canon/invariants',
  alexandriaReceipts: '/alexandria/receipts?limit=10',
  canonPending:       '/canon/pending',
  autopoiesisState:   '/autopoiesis/state',
};
