// CalibrationReliabilityDiagram — Reliability diagram
import React from 'react';
export interface CalibrationReliabilityDiagramProps {
  bins:CalibrationBin[];
  ece:number;
  mce:number;
}
export const CalibrationReliabilityDiagram: React.FC<CalibrationReliabilityDiagramProps> = (props) => <div className='axiolev-visualizer'/>;
export default CalibrationReliabilityDiagram;
