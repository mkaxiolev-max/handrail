// I1ScorePanel — I₁ composite
import React from 'react';
export interface I1ScorePanelProps {
  score:number;
  domains:DomainBreakdown[];
}
export const I1ScorePanel: React.FC<I1ScorePanelProps> = (props) => <div className='axiolev-panel'/>;
export default I1ScorePanel;
