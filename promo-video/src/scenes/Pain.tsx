import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import type {LucideIcon} from 'lucide-react';
import {Backdrop} from '../components/Backdrop';
import {Words} from '../components/Type';
import {useLayout} from '../LayoutContext';
import {FONT, INK, clamp, springIn} from '../lib';

export const Pain: React.FC<{
  icon: LucideIcon;
  lines: Array<[string, string]>;
  accent?: string;
  pulse?: boolean;
}> = ({icon: Icon, lines, accent = '#F87171', pulse = false}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {scale, pad, isPortrait} = useLayout();
  const p = clamp(springIn(frame, fps, 4));
  const beat = pulse ? 1 + 0.06 * Math.sin(frame * 0.35) : 1;
  const tile = 170 * scale;
  return (
    <AbsoluteFill style={{fontFamily: FONT}}>
      <Backdrop accent={accent} accent2={accent} />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: isPortrait ? 'column' : 'row',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 64 * scale,
          padding: pad,
        }}
      >
        <div
          style={{
            width: tile,
            height: tile,
            borderRadius: 36 * scale,
            background: `${accent}14`,
            border: `2px solid ${accent}45`,
            boxShadow: `0 0 90px ${accent}40`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: p,
            transform: `scale(${(0.6 + 0.4 * p) * beat})`,
          }}
        >
          <Icon size={84 * scale} color={accent} strokeWidth={1.8} />
        </div>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 10 * scale,
            alignItems: isPortrait ? 'center' : 'flex-start',
          }}
        >
          {lines.map(([text, color], i) => (
            <Words
              key={i}
              text={text}
              start={12 + i * 10}
              size={84}
              color={color || INK}
              center={isPortrait}
              step={3}
            />
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};
