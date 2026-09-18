import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import {FileCode, MessageCircle} from 'lucide-react';
import {Backdrop} from '../components/Backdrop';
import {Kicker, Words} from '../components/Type';
import {useLayout} from '../LayoutContext';
import {
  FONT,
  MONO,
  MUTED,
  WA,
  clamp,
  fadeIn,
  springIn,
} from '../lib';

const BARS = [60, 88, 44, 72, 96, 52];
const CODE = ['def my_skill():', '    run("deploy.ps1")', '    reply("done")'];

export const Feature5: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {scale, pad, isPortrait} = useLayout();
  const cardW = isPortrait ? '100%' : 460 * scale;
  const cardH = 330 * scale;
  const recOn = Math.sin(frame * 0.25) > 0;
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
          gap: 46 * scale,
          padding: pad,
        }}
      >
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 24 * scale,
          }}
        >
          <Kicker start={0} center>
            Extend it
          </Kicker>
          <Words text="Make it yours." start={8} size={78} center />
        </div>
        <div
          style={{
            display: 'flex',
            flexDirection: isPortrait ? 'column' : 'row',
            gap: 28 * scale,
            width: isPortrait ? '88%' : undefined,
          }}
        >
          {/* WhatsApp */}
          <div
            style={{
              width: cardW,
              height: cardH,
              borderRadius: 24 * scale,
              background: '#0C1322',
              border: '1px solid #FFFFFF12',
              boxShadow: '0 40px 90px rgba(0,0,0,0.5)',
              padding: 26 * scale,
              display: 'flex',
              flexDirection: 'column',
              gap: 18 * scale,
              opacity: clamp(springIn(frame, fps, 10)),
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12 * scale,
                color: '#E8EFFA',
                fontSize: 24 * scale,
                fontWeight: 700,
              }}
            >
              <div
                style={{
                  width: 44 * scale,
                  height: 44 * scale,
                  borderRadius: '50%',
                  background: WA,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <MessageCircle size={24 * scale} color="#fff" />
              </div>
              WhatsApp
            </div>
            <div
              style={{
                alignSelf: 'flex-end',
                background: '#005C4B',
                color: '#E7FFDB',
                borderRadius: 14 * scale,
                padding: `${12 * scale}px ${16 * scale}px`,
                fontSize: 21 * scale,
                opacity: clamp(springIn(frame, fps, 20)),
              }}
            >
              Landed! See you at 7{' '}
              <span style={{color: '#53BDEB'}}>✓✓</span>
            </div>
            <div
              style={{
                fontSize: 18 * scale,
                color: MUTED,
                opacity: fadeIn(frame, 44, 10),
              }}
            >
              → to Maya · delivered from your PC
            </div>
          </div>
          {/* Macro */}
          <div
            style={{
              width: cardW,
              height: cardH,
              borderRadius: 24 * scale,
              background: '#0C1322',
              border: '1px solid #FFFFFF12',
              boxShadow: '0 40px 90px rgba(0,0,0,0.5)',
              padding: 26 * scale,
              display: 'flex',
              flexDirection: 'column',
              gap: 20 * scale,
              opacity: clamp(springIn(frame, fps, 16)),
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12 * scale,
                color: '#E8EFFA',
                fontSize: 24 * scale,
                fontWeight: 700,
              }}
            >
              <div
                style={{
                  width: 16 * scale,
                  height: 16 * scale,
                  borderRadius: '50%',
                  background: '#F87171',
                  opacity: recOn ? 1 : 0.35,
                }}
              />
              Macro recorder
            </div>
            <div
              style={{
                display: 'flex',
                alignItems: 'flex-end',
                gap: 10 * scale,
                height: 110 * scale,
              }}
            >
              {BARS.map((hPct, i) => {
                const t = 24 + i * 5;
                const p = interpolate(frame, [t, t + 12], [0, 1], {
                  extrapolateLeft: 'clamp',
                  extrapolateRight: 'clamp',
                });
                return (
                  <div
                    key={i}
                    style={{
                      width: 26 * scale,
                      height: (hPct / 100) * 110 * scale,
                      borderRadius: 6,
                      background: `linear-gradient(180deg,#4F8CFF,#22D3EE)`,
                      opacity: p,
                      transform: `scaleY(${0.2 + 0.8 * p})`,
                      transformOrigin: 'bottom',
                    }}
                  />
                );
              })}
            </div>
            <div
              style={{
                fontFamily: MONO,
                fontSize: 19 * scale,
                color: MUTED,
                opacity: fadeIn(frame, 56, 10),
              }}
            >
              00:04:12 · captured
            </div>
          </div>
          {/* Python */}
          <div
            style={{
              width: cardW,
              height: cardH,
              borderRadius: 24 * scale,
              background: '#0C1322',
              border: '1px solid #FFFFFF12',
              boxShadow: '0 40px 90px rgba(0,0,0,0.5)',
              padding: 26 * scale,
              display: 'flex',
              flexDirection: 'column',
              gap: 18 * scale,
              opacity: clamp(springIn(frame, fps, 22)),
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12 * scale,
                color: '#E8EFFA',
                fontSize: 24 * scale,
                fontWeight: 700,
              }}
            >
              <FileCode size={30 * scale} color="#34D399" />
              Python skills
            </div>
            <div
              style={{
                background: '#070C16',
                border: '1px solid #FFFFFF0D',
                borderRadius: 14 * scale,
                padding: 18 * scale,
                fontFamily: MONO,
                fontSize: 21 * scale,
                lineHeight: 1.8,
              }}
            >
              {CODE.map((line, i) => (
                <div
                  key={line}
                  style={{
                    color:
                      i === 0 ? '#4F8CFF' : i === 2 ? '#34D399' : '#C7D4EA',
                    opacity: fadeIn(frame, 32 + i * 9, 8),
                    whiteSpace: 'pre',
                  }}
                >
                  {line}
                </div>
              ))}
            </div>
            <div
              style={{
                fontSize: 18 * scale,
                color: MUTED,
                opacity: fadeIn(frame, 64, 10),
              }}
            >
              Drop in a script. It becomes a command.
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
