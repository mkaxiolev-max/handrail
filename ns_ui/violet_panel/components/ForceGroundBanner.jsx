import { useEffect, useState } from 'react';
import { fetchEndpoint, ENDPOINTS } from '../lib/api.js';
import { isError } from '../lib/error.js';

export default function ForceGroundBanner() {
  const [data, setData] = useState(null);
  useEffect(() => { fetchEndpoint(ENDPOINTS.forceGroundState).then(setData); }, []);
  if (!data || isError(data)) return null;
  const state = data.artifacts?.[0] || {};
  if (!state.active) return null;
  return (
    <div className="banner force-ground">
      ⚡ force_ground ACTIVE — ops must carry ground-truth anchors
    </div>
  );
}
