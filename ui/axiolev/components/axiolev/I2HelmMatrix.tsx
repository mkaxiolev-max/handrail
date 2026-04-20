// I2HelmMatrix — 9×5 HELM heatmap
import React from 'react';
export interface I2HelmMatrixProps {
  matrix:number[][];
}
export const I2HelmMatrix: React.FC<I2HelmMatrixProps> = (props) => <div className='axiolev-visualizer'/>;
export default I2HelmMatrix;
