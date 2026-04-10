import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { SystemProvider } from './contexts/SystemContext'
import FounderShell from './components/FounderShell'
import BriefingPage from './pages/BriefingPage'
import EnginePage from './pages/EnginePage'
import RuntimePage from './pages/RuntimePage'
import MemoryPage from './pages/MemoryPage'
import GovernancePage from './pages/GovernancePage'
import CallsPage from './pages/CallsPage'
import BuildPage from './pages/BuildPage'
import OmegaPage from './pages/OmegaPage'
import VioletPage from './pages/VioletPage'

function App() {
  return (
    <SystemProvider>
      <Router>
        <FounderShell>
          <Routes>
            <Route path="/" element={<Navigate to="/briefing" replace />} />
            <Route path="/briefing" element={<BriefingPage />} />
            <Route path="/engine" element={<EnginePage />} />
            <Route path="/runtime" element={<RuntimePage />} />
            <Route path="/memory" element={<MemoryPage />} />
            <Route path="/governance" element={<GovernancePage />} />
            <Route path="/calls" element={<CallsPage />} />
            <Route path="/build" element={<BuildPage />} />
            <Route path="/omega" element={<OmegaPage />} />
            <Route path="/violet" element={<VioletPage />} />
          </Routes>
        </FounderShell>
      </Router>
    </SystemProvider>
  )
}
export default App
