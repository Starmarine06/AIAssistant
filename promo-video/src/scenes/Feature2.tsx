import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import {Check, MousePointerClick} from 'lucide-react';
import {Backdrop} from '../components/Backdrop';
import {Kicker, Words, Sub, Split} from '../components/Type';
import {useLayout} from '../LayoutContext';
import {
  FONT,
  MONO,
  ACCENT,
  clamp,
  fadeIn,
  lerp,
  springIn,
} from '../lib';

const COLS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];
const ROWS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'];

export const Feature2: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {scale, isPortrait} = useLayout();
  const w = (isPortrait ? 940 : 1010) * scale;
  const h = w * 0.58;
  const move = clamp(springIn(frame, fps, 22, 110, 200));
  const cx = lerp(76, 35, move);
  const cy = lerp(70, 55, move);
  const cardP = clamp(springIn(frame, fps, 4));
  const ripple = (start: number) => ({
    scale: interpolate(frame, [start, start + 22], [0.2, 2.6], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }),
    opacity: interpolate(frame, [start, start + 22], [0.9, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }),
  });
  const r1 = ripple(50);
  const r2 = ripple(56);
  return (
    <AbsoluteFill style={{fontFamily: FONT}}>
      <Backdrop />
      <Split
        left={
          <>
            <Kicker start={2}>Grid click</Kicker>
            <Words text="Point at anything." start={10} size={80} />
            <Sub start={44} size={33}>
              Screenshot with a grid. Tap a cell — it clicks there.
            </Sub>
          </>
        }
        right={
          <div
            style={{
              width: w,
              height: h,
              borderRadius: 22 * scale,
              background: 'linear-gradient(150deg,#0E1830,#0A1120)',
              border: '1px solid #FFFFFF14',
              boxShadow: '0 50px 110px rgba(0,0,0,0.55)',
              position: 'relative',
              overflow: 'hidden',
              opacity: cardP,
              transform: `translateY(${(1 - cardP) * 40}px)`,
            }}
          >
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                style={{
                  position: 'absolute',
                  left: 26 * scale + i * 62 * scale,
                  top: 26 * scale,
                  width: 46 * scale,
                  height: 46 * scale,
                  borderRadius: 12 * scale,
                  background: '#FFFFFF14',
                  border: '1px solid #FFFFFF1C',
                }}
              />
            ))}
            <div
              style={{
                position: 'absolute',
                left: 0,
                right: 0,
                bottom: 0,
                height: 42 * scale,
                background: '#070C16',
                borderTop: '1px solid #FFFFFF10',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
              }}
            >
              <div
                style={{
                  width: 220 * scale,
                  height: 16 * scale,
                  borderRadius: 8,
                  background: '#FFFFFF10',
                }}
              />
            </div>
            {COLS.slice(0, 9).map((_, i) => (
              <div
                key={'v' + i}
                style={{
                  position: 'absolute',
                  left: `${(i + 1) * 10}%`,
                  top: 0,
                  width: 1,
                  height: '100%',
                  background: '#FFFFFF10',
                }}
              />
            ))}
            {ROWS.slice(0, 9).map((_, i) => (
              <div
                key={'h' + i}
                style={{
                  position: 'absolute',
                  top: `${(i + 1) * 10}%`,
                  left: 0,
                  height: 1,
                  width: '100%',
                  background: '#FFFFFF10',
                }}
              />
            ))}
            {COLS.map((c, i) => (
              <div
                key={'lc' + i}
                style={{
                  position: 'absolute',
                  left: `${(i + 0.5) * 10}%`,
                  top: 6 * scale,
                  transform: 'translateX(-50%)',
                  fontFamily: MONO,
                  fontSize: 15 * scale,
                  color: '#FFFFFF40',
                }}
              >
                {c}
              </div>
            ))}
            {ROWS.map((r, i) => (
              <div
                key={'lr' + i}
                style={{
                  position: 'absolute',
                  top: `${(i + 0.5) * 10}%`,
                  left: 8 * scale,
                  transform: 'translateY(-50%)',
                  fontFamily: MONO,
                  fontSize: 15 * scale,
                  color: '#FFFFFF40',
                }}
              >
                {r}
              </div>
            ))}
            {[r1, r2].map((r, i) => (
              <div
                key={'rip' + i}
                style={{
                  position: 'absolute',
                  left: '35%',
                  top: '55%',
                  width: 90 * scale,
                  height: 90 * scale,
                  marginLeft: -45 * scale,
                  marginTop: -45 * scale,
                  borderRadius: '50%',
                  border: `3px solid ${ACCENT}`,
                  opacity: r.opacity,
                  transform: `scale(${r.scale})`,
                }}
              />
            ))}
            <div
              style={{
                position: 'absolute',
                left: `${cx}%`,
                top: `${cy}%`,
                width: 22 * scale,
                height: 22 * scale,
                marginLeft: -11 * scale,
                marginTop: -11 * scale,
                borderRadius: '50%',
                background: ACCENT,
                boxShadow: '0 0 30px rgba(79,140,255,0.9)',
                border: '3px solid #FFFFFF',
              }}
            />
            <div
              style={{
                position: 'absolute',
                bottom: 18 * scale + 42 * scale,
                right: 18 * scale,
                display: 'flex',
                alignItems: 'center',
                gap: 10 * scale,
                background: '#0A0F1CDD',
                border: '1px solid #FFFFFF1F',
                borderRadius: 14 * scale,
                padding: `${12 * scale}px ${18 * scale}px`,
                fontFamily: MONO,
                fontSize: 21 * scale,
                color: '#E8EFFA',
                opacity: fadeIn(frame, 66, 8),
                transform: `translateY(${interpolate(
                  frame,
                  [66, 76],
                  [14, 0],
                  {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
                )}px)`,
              }}
            >
              <Check size={20 * scale} color="#34D399" strokeWidth={3} />
              Clicked D6 · 0.2s
            </div>
            <div
              style={{
                position: 'absolute',
                top: 16 * scale,
                right: 18 * scale,
                display: 'flex',
                alignItems: 'center',
                gap: 8 * scale,
                fontFamily: MONO,
                fontSize: 17 * scale,
                color: '#FFFFFF55',
                opacity: fadeIn(frame, 30, 10),
              }}
            >
              <MousePointerClick size={18 * scale} color="#FFFFFF55" />
              remote cursor
            </div>
          </div>
        }
      />
    </AbsoluteFill>
  );
};
