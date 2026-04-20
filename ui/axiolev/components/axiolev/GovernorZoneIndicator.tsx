// GovernorZoneIndicator — Live governor zone display
import React from 'react';
export interface GovernorZoneIndicatorProps {
  zone:string;
  score:number;
  delta:number?;
}
export const GovernorZoneIndicator: React.FC<GovernorZoneIndicatorProps> = (props) => <div className='axiolev-widget'/>;
export default GovernorZoneIndicator;
