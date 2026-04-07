import React, { useEffect, useState } from 'react'
import axios from 'axios'

const MemoryPage = () => {
  const [atoms, setAtoms] = useState([])
  const [tab, setTab] = useState('atoms')

  useEffect(() => {
    if (tab === 'atoms') {
      axios.get('http://127.0.0.1:9001/atoms').then(r => setAtoms(r.data?.atoms ?? [])).catch(() => {})
    }
  }, [tab])

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Memory / Alexandria</h1>
      <div className="flex gap-2 mb-4 border-b border-gray-700">
        {['atoms', 'edges', 'receipts'].map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm ${tab === t ? 'border-b-2 border-violet-500 text-violet-400' : 'text-gray-400'}`}>
            {t}
          </button>
        ))}
      </div>
      {tab === 'atoms' && (
        <div className="space-y-2">
          {atoms.map((atom, i) => (
            <div key={atom.id ?? i} className="bg-gray-800 rounded p-3 border border-gray-700 text-sm">
              <span className="font-mono text-xs text-gray-500">{atom.type} </span>
              <span>{atom.label ?? atom.id}</span>
            </div>
          ))}
          {atoms.length === 0 && <div className="text-gray-500 text-sm">No atoms found</div>}
        </div>
      )}
    </div>
  )
}

export default MemoryPage
