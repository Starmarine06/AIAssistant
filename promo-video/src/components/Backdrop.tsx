import React from 'react';
import {useCurrentFrame, interpolate} from 'remotion';
import {useLayout} from '../LayoutContext';

export const Backdrop: React.FC<{accent?: string; accent2?: string}> = ({
  accent = '#4F8CFF',
  accent2 = '#22D3EE',
}) => {
  const frame = useCurrentFrame();
  const {width, height} = useLayout();
  const driftX = interpolate(frame, [0, 240], [0, 60], {
    extrapolateRight: 'clamp',
  });
  const driftY = interpolate(frame, [0, 240], [0, -40], {
    extrapolateRight: 'clamp',
  });
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background:
          'linear-gradient(160deg, #070A12 0%, #0A1020 55%, #070A12 100%)',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          width: width * 0.55,
          height: width * 0.55,
          borderRadius: '50%',
          left: -width * 0.12 + driftX,
          top: -height * 0.28 + driftY,
          background: `radial-gradient(circle, ${accent}24, transparent 65%)`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: width * 0.45,
          height: width * 0.45,
          borderRadius: '50%',
          right: -width * 0.15 - driftX,
          bottom: -height * 0.22 - driftY,
          background: `radial-gradient(circle, ${accent2}1C, transparent 65%)`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(#FFFFFF07 1px, transparent 1px), linear-gradient(90deg, #FFFFFF07 1px, transparent 1px)',
          backgroundSize: '80px 80px',
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,0.55) 100%)',
        }}
      />
    </div>
  );
};
