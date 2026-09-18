import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import {ShieldCheck} from 'lucide-react';
import {Backdrop} from '../components/Backdrop';
import {Words, Sub} from '../components/Type';
import {useLayout} from '../LayoutContext';
import {FONT, clamp, springIn} from '../lib';

export const Trust: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {scale, pad} = useLayout();
  const p = clamp(springIn(frame, fps, 4));
  const loop = (frame % 60) / 60;
  const ring = {
    transform: `scale(${1 + loop * 0.5})`,
    opacity: 0.45 * (1 - loop),
  };
  return (
    <AbsoluteFill style={{fontFamily: FONT}}>
      <Backdrop accent="#34D399" accent2="#4F8CFF" />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 40 * scale,
          padding: pad,
        }}
      >
        <div
          style={{
            position: 'relative',
            width: 150 * scale,
            height: 150 * scale,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              position: 'absolute',
              inset: 0,
              borderRadius: '50%',
              border: '2px solid #34D399',
              ...ring,
            }}
          />
          <div
            style={{
              width: 150 * scale,
              height: 150 * scale,
              borderRadius: 44 * scale,
              background: 'rgba(52,211,153,0.1)',
              border: '1px solid rgba(52,211,153,0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              opacity: p,
              transform: `scale(${0.6 + 0.4 * p})`,
              boxShadow: '0 0 80px rgba(52,211,153,0.25)',
            }}
          >
            <ShieldCheck size={84 * scale} color="#34D399" strokeWidth={1.9} />
          </div>
        </div>
        <Words text="Private by default." start={16} size={96} center />
        <Sub start={48} size={38} center>
          The first Telegram account to message it becomes the owner.
          <br />
          Everyone else is ignored.
        </Sub>
        <div
          style={{
            display: 'flex',
            gap: 18 * scale,
            flexWrap: 'wrap',
            justifyContent: 'center',
            opacity: interpolate(frame, [76, 90], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          {['Open source', 'Runs on your hardware'].map((c) => (
            <div
              key={c}
              style={{
                border: '1px solid #FFFFFF22',
                background: '#FFFFFF08',
                color: '#C7D4EA',
                fontSize: 24 * scale,
                fontWeight: 600,
                padding: `${12 * scale}px ${26 * scale}px`,
                borderRadius: 999,
              }}
            >
              {c}
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};
