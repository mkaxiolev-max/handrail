import React, { useEffect, useState } from 'react'

const API = 'http://127.0.0.1:9000/api/organism/overview'

const statusTone = {
  live: 'bg-green-500/10 text-green-300 border-green-500/30',
  down: 'bg-red-500/10 text-red-300 border-red-500/30',
  unknown: 'bg-yellow-500/10 text-yellow-200 border-yellow-500/30',
}

function StatusPill({ value }) {
  const tone = statusTone[value] || statusTone.unknown
  return (
    <span className={`inline-flex items-center rounded border px-2 py-1 text-[11px] font-mono uppercase tracking-wide ${tone}`}>
      {value}
    </span>
  )
}

function SectionCard({ title, children, action }) {
  return (
    <section className="rounded-lg border border-gray-700 bg-gray-900/60 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="font-mono text-sm uppercase tracking-[0.2em] text-gray-200">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  )
}

export default function OrganismPage() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [selectedId, setSelectedId] = useState(null)

  useEffect(() => {
    let cancelled = false

    const fetchOverview = async () => {
      try {
        const response = await fetch(API)
        if (!response.ok) {
          throw new Error(`overview request failed: ${response.status}`)
        }
        const payload = await response.json()
        if (!cancelled) {
          setData(payload)
          setError(null)
          if (!selectedId && payload.services?.length) {
            setSelectedId(payload.services[0].id)
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message)
        }
      }
    }

    fetchOverview()
    const intervalId = window.setInterval(fetchOverview, 10000)
    return () => {
      cancelled = true
      window.clearInterval(intervalId)
    }
  }, [selectedId])

  const selectedService = !data?.services?.length
    ? null
    : data.services.find((service) => service.id === selectedId) || data.services[0]

  if (!data && !error) {
    return <div className="font-mono text-sm text-gray-400">Loading organism telemetry...</div>
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-violet-500/20 bg-gradient-to-r from-gray-900 via-gray-900 to-violet-950/40 p-5">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="font-mono text-lg uppercase tracking-[0.25em] text-violet-200">Organism</h1>
          <StatusPill value={(data?.system_state?.state || 'unknown').toLowerCase()} />
          <span className="font-mono text-xs text-gray-400">boot: {data?.system_state?.boot_mode || 'unknown'}</span>
          <span className="font-mono text-xs text-gray-400">commit: {data?.system_state?.git_commit || 'unknown'}</span>
          <span className="font-mono text-xs text-gray-500">captured: {data?.captured_at || 'unknown'}</span>
        </div>
        {error && <p className="mt-3 font-mono text-xs text-red-300">{error}</p>}
        {data?.system_state?.degraded?.length > 0 && (
          <p className="mt-3 font-mono text-xs text-yellow-200">
            degraded: {data.system_state.degraded.join(', ')}
          </p>
        )}
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
        <SectionCard
          title="Services"
          action={<span className="font-mono text-xs text-gray-500">{data?.services?.length || 0} tracked</span>}
        >
          <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
            {(data?.services || []).map((service) => (
              <button
                key={service.id}
                type="button"
                onClick={() => setSelectedId(service.id)}
                className={`rounded border p-3 text-left transition ${
                  selectedService?.id === service.id
                    ? 'border-violet-500/40 bg-violet-500/10'
                    : 'border-gray-700 bg-gray-800/60 hover:border-gray-500'
                }`}
              >
                <div className="mb-2 flex items-center justify-between gap-2">
                  <span className="font-mono text-xs uppercase tracking-wide text-gray-100">{service.label}</span>
                  <StatusPill value={service.status} />
                </div>
                <div className="font-mono text-xs text-gray-400">{service.endpoint}</div>
                <div className="mt-2 font-mono text-xs text-gray-500">
                  latency: {service.latency_ms ?? 'n/a'} ms
                </div>
              </button>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Drilldown">
          {selectedService ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="font-mono text-sm text-gray-100">{selectedService.label}</div>
                  <div className="font-mono text-xs text-gray-500">{selectedService.endpoint}</div>
                </div>
                <StatusPill value={selectedService.status} />
              </div>
              <pre className="max-h-80 overflow-auto rounded border border-gray-700 bg-black/30 p-3 text-xs text-gray-300">
                {JSON.stringify(selectedService.payload ?? {}, null, 2)}
              </pre>
            </div>
          ) : (
            <div className="font-mono text-xs text-gray-500">No live service detail yet.</div>
          )}
        </SectionCard>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <SectionCard title="Providers">
          <div className="space-y-2">
            {(data?.providers || []).map((provider) => (
              <div key={provider.id} className="rounded border border-gray-700 bg-gray-800/60 p-3">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <span className="font-mono text-xs uppercase tracking-wide text-gray-100">{provider.id}</span>
                  <StatusPill value={provider.status} />
                </div>
                <div className="font-mono text-xs text-gray-400">model: {provider.model || 'unknown'}</div>
                <div className="font-mono text-xs text-gray-500">models: {provider.model_count ?? 0}</div>
                <div className="mt-1 font-mono text-[11px] text-gray-500">{provider.endpoint}</div>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Memory">
          <dl className="space-y-2 font-mono text-xs text-gray-300">
            <div className="flex justify-between gap-3"><dt>atoms</dt><dd>{data?.memory?.atoms_total ?? 'unknown'}</dd></div>
            <div className="flex justify-between gap-3"><dt>receipts</dt><dd>{data?.memory?.receipt_files ?? 'unknown'}</dd></div>
            <div className="flex justify-between gap-3"><dt>alexandria</dt><dd>{data?.memory?.alexandria_mounted ? 'mounted' : 'missing'}</dd></div>
            <div className="flex justify-between gap-3"><dt>latest receipt</dt><dd className="truncate">{data?.memory?.latest_receipt || 'none'}</dd></div>
          </dl>
        </SectionCard>

        <SectionCard title="Execution">
          <div className="space-y-2 font-mono text-xs text-gray-300">
            <div className="flex justify-between gap-3"><span>handrail</span><StatusPill value={data?.execution?.status || 'unknown'} /></div>
            <pre className="max-h-36 overflow-auto rounded border border-gray-700 bg-black/30 p-3 text-[11px] text-gray-400">
              {JSON.stringify(data?.execution?.payload ?? {}, null, 2)}
            </pre>
          </div>
        </SectionCard>

        <SectionCard title="Governance">
          <div className="space-y-2 font-mono text-xs text-gray-300">
            <div className="flex justify-between gap-3"><span>hic</span><StatusPill value={data?.governance?.hic?.status || 'unknown'} /></div>
            <div className="flex justify-between gap-3"><span>pdp surface</span><StatusPill value={data?.governance?.pdp?.status || 'unknown'} /></div>
          </div>
        </SectionCard>

        <SectionCard title="Voice">
          <div className="space-y-2 font-mono text-xs text-gray-300">
            <div className="flex justify-between gap-3"><span>violet</span><StatusPill value={data?.voice?.status || 'unknown'} /></div>
            <div className="flex justify-between gap-3"><span>voice sessions</span><span>{data?.voice?.sessions_count ?? 'unknown'}</span></div>
            <pre className="max-h-36 overflow-auto rounded border border-gray-700 bg-black/30 p-3 text-[11px] text-gray-400">
              {JSON.stringify(data?.voice?.violet ?? {}, null, 2)}
            </pre>
          </div>
        </SectionCard>

        <SectionCard title="Body / Mac Adapter">
          <div className="space-y-2 font-mono text-xs text-gray-300">
            <div className="flex justify-between gap-3"><span>gateway</span><StatusPill value={data?.body?.gateway?.status || 'unknown'} /></div>
            <div className="flex justify-between gap-3"><span>adapter</span><StatusPill value={data?.body?.adapter?.status || 'unknown'} /></div>
          </div>
        </SectionCard>

        <SectionCard title="Omega">
          <div className="space-y-2 font-mono text-xs text-gray-300">
            <div className="flex justify-between gap-3"><span>omega</span><StatusPill value={data?.omega?.status || 'unknown'} /></div>
            <div className="flex justify-between gap-3"><span>runs seen</span><span>{data?.omega?.runs_count ?? 'unknown'}</span></div>
            <pre className="max-h-36 overflow-auto rounded border border-gray-700 bg-black/30 p-3 text-[11px] text-gray-400">
              {JSON.stringify(data?.omega?.health ?? {}, null, 2)}
            </pre>
          </div>
        </SectionCard>
      </div>
    </div>
  )
}
