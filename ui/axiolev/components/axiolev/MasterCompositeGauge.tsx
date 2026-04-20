// MasterCompositeGauge — Master gauge
import React from 'react';
export interface MasterCompositeGaugeProps {
  score:number;
  tier:string;
}
export const MasterCompositeGauge: React.FC<MasterCompositeGaugeProps> = (props) => <div className='axiolev-gauge'/>;
export default MasterCompositeGauge;
