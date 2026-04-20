// ReceiptChainVisualizer — Merkle receipt chain visualization
import React from 'react';
export interface ReceiptChainVisualizerProps {
  receipts:Receipt[];
  maxVisible:number;
}
export const ReceiptChainVisualizer: React.FC<ReceiptChainVisualizerProps> = (props) => <div className='axiolev-visualizer'/>;
export default ReceiptChainVisualizer;
