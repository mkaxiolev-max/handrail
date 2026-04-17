import { useState } from 'react';
import PastTimeline from './components/PastTimeline.jsx';
import PolicyPane from './components/PolicyPane.jsx';
import CathedralPane from './components/CathedralPane.jsx';
import NERTile from './components/NERTile.jsx';
import ForceGroundBanner from './components/ForceGroundBanner.jsx';
import ClearingTile from './components/ClearingTile.jsx';
import InvariantsTile from './components/InvariantsTile.jsx';
import ReceiptChainTile from './components/ReceiptChainTile.jsx';
import CanonPendingTile from './components/CanonPendingTile.jsx';
import AbstentionTile from './components/AbstentionTile.jsx';

export default function App() {
  return (
    <div className="violet-panel">
      <header className="header">
        <span className="logo">NS∞ VIOLET — Baby V1</span>
        <span className="dignity">AXIOLEV · DIGNITY PRESERVED</span>
      </header>

      <ForceGroundBanner />

      <div className="three-truth">
        <PastTimeline />
        <PolicyPane />
        <CathedralPane />
      </div>

      <div className="tiles">
        <NERTile />
        <ForceGroundBanner />
        <ClearingTile />
        <InvariantsTile />
        <ReceiptChainTile />
        <CanonPendingTile />
        <AbstentionTile />
      </div>
    </div>
  );
}
