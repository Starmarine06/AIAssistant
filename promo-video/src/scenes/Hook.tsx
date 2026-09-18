import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {Backdrop} from '../components/Backdrop';
import {Words} from '../components/Type';
import {useLayout} from '../LayoutContext';
import {FONT, MONO, MUTED, fadeIn} from '../lib';

export const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const {scale, pad} = useLayout();
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
          gap: 38 * scale,
          padding: pad,
        }}
      >
        <div
          style={{
            opacity: fadeIn(frame, 2, 10),
            fontFamily: MONO,
            fontSize: 30 * scale,
            color: MUTED,
            letterSpacing: 5 * scale,
            border: '1px solid #FFFFFF1A',
            background: '#FFFFFF08',
            padding: `${10 * scale}px ${26 * scale}px`,
            borderRadius: 14 * scale,
          }}
        >
          21:04
        </div>
        <Words text="You just sat down." start={12} size={98} center />
        <div
          style={{
            opacity: fadeIn(frame, 60, 14),
            color: MUTED,
            fontSize: 42 * scale,
            fontWeight: 600,
            fontFamily: FONT,
          }}
        >
          Finally.
        </div>
      </div>
    </AbsoluteFill>
  );
};
