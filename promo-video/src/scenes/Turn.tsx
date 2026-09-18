import React from 'react';
import {AbsoluteFill, useCurrentFrame, interpolate} from 'remotion';
import {Backdrop} from '../components/Backdrop';
import {Words} from '../components/Type';
import {useLayout} from '../LayoutContext';
import {FONT, MUTED} from '../lib';

export const Turn: React.FC = () => {
  const frame = useCurrentFrame();
  const {scale, pad} = useLayout();
  const glowOpacity = interpolate(frame, [30, 60, 90, 118], [0, 0.9, 0.9, 0.4], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill style={{fontFamily: FONT}}>
      <Backdrop />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 44 * scale,
          padding: pad,
        }}
      >
        <div
          style={{
            width: 14 * scale,
            height: 14 * scale,
            borderRadius: '50%',
            background: '#4F8CFF',
            opacity: glowOpacity,
            boxShadow: '0 0 40px 12px rgba(79,140,255,0.75)',
          }}
        />
        <Words
          text="What if your PC"
          start={10}
          size={72}
          color={MUTED}
          center
          step={5}
        />
        <Words
          text="lived in your pocket?"
          start={44}
          size={100}
          center
          step={5}
          glow
        />
      </div>
    </AbsoluteFill>
  );
};
