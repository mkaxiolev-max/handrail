// HormeticProfileWidget — B0-B5 profile line chart
import React from 'react';
export interface HormeticProfileWidgetProps {
  profile:BandScores;
  signature:Signature;
}
export const HormeticProfileWidget: React.FC<HormeticProfileWidgetProps> = (props) => <div className='axiolev-widget'/>;
export default HormeticProfileWidget;
