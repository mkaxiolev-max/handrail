import { useEffect, useState } from 'react';
import { fetchEndpoint, ENDPOINTS } from '../lib/api.js';
import { isError, errorMessage } from '../lib/error.js';

export default function NERTile() {
  const [data, setData] = useState(null);
  useEffect(() => { fetchEndpoint(ENDPOINTS.nerObservation).then(setData); }, []);
  if (!data) return <div className="tile loading">NER loading…</div>;
  if (isError(data)) return <div className="tile error">NER ERROR: {errorMessage(data)}</div>;
  const obs = data.artifacts?.[0] || {};
  return (
    <div className={`tile ${obs.threshold_crossed ? 'warn' : 'ok'}`}>
      <h4>NER</h4>
      <p>Rate: {obs.rate?.toFixed(3)} | Trend: {obs.trend}</p>
      {obs.threshold_crossed && <p className="alert">⚠ threshold crossed</p>}
    </div>
  );
}
