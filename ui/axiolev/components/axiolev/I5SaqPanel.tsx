// I5SaqPanel — I₅ SAQ
import React from 'react';
export interface I5SaqPanelProps {
  axes:SaqAxes;
}
export const I5SaqPanel: React.FC<I5SaqPanelProps> = (props) => <div className='axiolev-panel'/>;
export default I5SaqPanel;
