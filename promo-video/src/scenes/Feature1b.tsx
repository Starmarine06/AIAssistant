import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {AppWindow, Keyboard, Lock} from 'lucide-react';
import {Backdrop} from '../components/Backdrop';
import {Kicker, Words, Sub, Split} from '../components/Type';
import {useLayout} from '../LayoutContext';
import {
  FONT,
  MONO,
  MUTED,
  clamp,
  fadeIn,
  rise,
  springIn,
} from '../lib';

const CMD = 'lock my workstation';
const CAPS: Array<{icon: React.ComponentType<{size?: number; color?: string; strokeWidth?: number}>; label: string}> = [
  {icon: Lock, label: 'Lock & unlock'},
  {icon: AppWindow, label: 'Open apps & sites'},
  {icon: Keyboard, label: 'Keys & clicks'},
];

export const Feature1b: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {scale, isPortrait} = useLayout();
  const chars = Math.max(
    0,
    Math.min(CMD.length, Math.floor((frame - 12) / 1.4)),
  );
  const typed = CMD.slice(0, chars);
  const cursorOn = frame % 16 < 10;
  const cardW = (isPortrait ? 860 : 680) * scale;
  return (
    <AbsoluteFill style={{fontFamily: FONT}}>
      <Backdrop />
      <Split
        left={
          <>
            <Kicker start={2}>Real shell</Kicker>
            <Words text="Real commands." start={10} size={84} />
            <Words text="Real output." start={22} size={84} color="#34D399" />
            <Sub start={46} size={32}>
              Natural language meets the command line.
            </Sub>
          </>
        }
        right={
          <div style={{display: 'flex', flexDirection: 'column', gap: 26 * scale}}>
            <div
              style={{
                width: cardW,
                borderRadius: 18 * scale,
                background: '#0B1120',
                border: '1px solid #FFFFFF14',
                boxShadow: '0 40px 90px rgba(0,0,0,0.5)',
                overflow: 'hidden',
                opacity: clamp(springIn(frame, fps, 4)),
                transform: `translateY(${rise(frame, 4, 30, 12)}px)`,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  gap: 8 * scale,
                  padding: `${14 * scale}px ${18 * scale}px`,
                  background: '#0E1526',
                  borderBottom: '1px solid #FFFFFF0D',
                }}
              >
                {['#F87171', '#FBBF24', '#34D399'].map((c) => (
                  <div
                    key={c}
                    style={{
                      width: 14 * scale,
                      height: 14 * scale,
                      borderRadius: '50%',
                      background: c,
                    }}
                  />
                ))}
              </div>
              <div
                style={{
                  padding: 26 * scale,
                  fontFamily: MONO,
                  fontSize: 27 * scale,
                  lineHeight: 1.7,
                }}
              >
                <div style={{color: '#E8EFFA', whiteSpace: 'pre'}}>
                  <span style={{color: '#4F8CFF'}}>{'> '}</span>
                  {typed}
                  {frame < 64 ? (
                    <span
                      style={{
                        opacity: cursorOn ? 1 : 0,
                        color: '#4F8CFF',
                      }}
                    >
                      ▍
                    </span>
                  ) : null}
                </div>
                <div
                  style={{
                    color: '#34D399',
                    opacity: fadeIn(frame, 62, 8),
                  }}
                >
                  Workstation locked.
                </div>
                <div
                  style={{
                    color: MUTED,
                    fontSize: 22 * scale,
                    opacity: fadeIn(frame, 80, 8),
                  }}
                >
                  0.4s · no one was home
                </div>
              </div>
            </div>
            <div
              style={{
                display: 'flex',
                gap: 14 * scale,
                flexWrap: 'wrap',
                justifyContent: 'center',
              }}
            >
              {CAPS.map((c, i) => {
                const t = 88 + i * 10;
                const p = clamp(springIn(frame, fps, t));
                const Icon = c.icon;
                return (
                  <div
                    key={c.label}
                    style={{
                      opacity: p,
                      transform: `translateY(${(1 - p) * 16}px)`,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10 * scale,
                      border: '1px solid #FFFFFF1C',
                      background: '#FFFFFF07',
                      borderRadius: 999,
                      padding: `${10 * scale}px ${20 * scale}px`,
                      color: '#C7D4EA',
                      fontSize: 22 * scale,
                      fontWeight: 600,
                    }}
                  >
                    <Icon size={22 * scale} color="#4F8CFF" strokeWidth={2.2} />
                    {c.label}
                  </div>
                );
              })}
            </div>
          </div>
        }
      />
    </AbsoluteFill>
  );
};

export default Feature1b;
