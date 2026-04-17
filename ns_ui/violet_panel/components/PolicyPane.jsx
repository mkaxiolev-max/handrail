import { useEffect, useState } from 'react';
import { fetchEndpoint, ENDPOINTS } from '../lib/api.js';
import { isError, errorMessage } from '../lib/error.js';

export default function PolicyPane() {
  const [axioms, setAxioms] = useState(null);
  const [decisions, setDecisions] = useState(null);
  useEffect(() => {
    fetchEndpoint(ENDPOINTS.canonAxioms).then(setAxioms);
    fetchEndpoint(ENDPOINTS.pdpRecent).then(setDecisions);
  }, []);

  const axiomsErr = !axioms || isError(axioms);
  const decisionsErr = !decisions || isError(decisions);

  return (
    <div className="pane">
      <h3>PRESENT — Policy + Canon</h3>
      {axiomsErr
        ? <div className="error">Axioms: {axioms ? errorMessage(axioms) : 'loading…'}</div>
        : <div>
            <h4>Axioms ({axioms.artifacts?.[0]?.axioms?.length || 0})</h4>
            {(axioms.artifacts?.[0]?.axioms || []).slice(0, 5).map(ax => (
              <p key={ax.id} className="small">{ax.id}: {ax.name}</p>
            ))}
          </div>
      }
      {decisionsErr
        ? <div className="error">Decisions: {decisions ? errorMessage(decisions) : 'loading…'}</div>
        : <div>
            <h4>Recent Decisions ({(decisions.artifacts || []).length})</h4>
            {(decisions.artifacts || []).slice(0, 3).map((d, i) => (
              <p key={i} className="small">{d.operation}: {d.ok ? 'allow' : 'deny'}</p>
            ))}
          </div>
      }
    </div>
  );
}
