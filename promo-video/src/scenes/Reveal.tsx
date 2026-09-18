import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {Bot} from 'lucide-react';
import {Backdrop} from '../components/Backdrop';
import {Words, Sub} from '../components/Type';
import {useLayout} from '../LayoutContext';
import {FONT, clamp, fadeIn, rise, springIn} from '../lib';

const CHIPS = ['Telegram-controlled', 'LLM-powered', 'Runs on Windows'];

export const Reveal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {scale, pad} = useLayout();
  const p = clamp(springIn(frame, fps, 4, 140, 12));
  const tile = 150 * scale;
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
          gap: 40 * scale,
          padding: pad,
        }}
      >
        <div
          style={{
            width: tile,
            height: tile,
            borderRadius: 34 * scale,
            background: 'linear-gradient(135deg,#2AABEE,#4F8CFF)',
            boxShadow: '0 0 110px rgba(79,140,255,0.55)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: p,
            transform: `scale(${0.5 + 0.5 * p}) rotate(${(1 - p) * -14}deg)`,
          }}
        >
          <Bot size={84 * scale} color="#fff" strokeWidth={2} />
        </div>
        <Words text="AI ASSISTANT" start={20} size={108} center step={4} />
        <Sub start={52} size={40}>
          Your Windows PC — inside Telegram.
        </Sub>
        <div
          style={{
            display: 'flex',
            gap: 18 * scale,
            marginTop: 10 * scale,
            flexWrap: 'wrap',
            justifyContent: 'center',
          }}
        >
          {CHIPS.map((c, i) => {
            const t = 72 + i * 12;
            return (
              <div
                key={c}
                style={{
                  opacity: fadeIn(frame, t, 10),
                  transform: `translateY(${rise(frame, t, 18, 10)}px)`,
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
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
