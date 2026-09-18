import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {useLayout} from '../LayoutContext';
import {FONT, clamp, fadeIn, rise, springIn} from '../lib';

export const Kicker: React.FC<{
  children: React.ReactNode;
  color?: string;
  start?: number;
  center?: boolean;
}> = ({children, color = '#4F8CFF', start = 0, center = false}) => {
  const frame = useCurrentFrame();
  const {scale} = useLayout();
  const o = fadeIn(frame, start, 10);
  const y = rise(frame, start, 16, 10);
  return (
    <div
      style={{
        opacity: o,
        transform: `translateY(${y}px)`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: center ? 'center' : 'flex-start',
        gap: 16 * scale,
        color,
        fontSize: 27 * scale,
        fontWeight: 700,
        letterSpacing: 7 * scale,
        textTransform: 'uppercase',
        fontFamily: FONT,
      }}
    >
      <div
        style={{width: 48 * scale, height: 3, background: color, borderRadius: 2}}
      />
      {children}
    </div>
  );
};

export const Words: React.FC<{
  text: string;
  start?: number;
  size?: number;
  weight?: number;
  color?: string;
  step?: number;
  lineHeight?: number;
  center?: boolean;
  glow?: boolean;
}> = ({
  text,
  start = 0,
  size = 88,
  weight = 800,
  color = '#F2F6FF',
  step = 3,
  lineHeight = 1.08,
  center = false,
  glow = false,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {scale} = useLayout();
  const words = text.split(' ');
  return (
    <div
      style={{
        fontFamily: FONT,
        fontSize: size * scale,
        fontWeight: weight,
        color,
        lineHeight,
        letterSpacing: -1 * scale,
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: center ? 'center' : 'flex-start',
        textShadow: glow ? '0 0 70px rgba(79,140,255,0.65)' : undefined,
      }}
    >
      {words.map((w, i) => {
        const t = start + i * step;
        const p = clamp(springIn(frame, fps, t));
        return (
          <span
            key={i}
            style={{
              display: 'inline-block',
              marginRight: '0.28em',
              opacity: p,
              transform: `translateY(${(1 - p) * 26}px) scale(${
                0.92 + 0.08 * p
              })`,
            }}
          >
            {w}
          </span>
        );
      })}
    </div>
  );
};

export const Sub: React.FC<{
  children: React.ReactNode;
  start?: number;
  size?: number;
  color?: string;
  center?: boolean;
}> = ({children, start = 0, size = 36, color = '#93A3C0', center = false}) => {
  const frame = useCurrentFrame();
  const {scale} = useLayout();
  return (
    <div
      style={{
        opacity: fadeIn(frame, start, 14),
        transform: `translateY(${rise(frame, start, 22, 14)}px)`,
        fontFamily: FONT,
        fontSize: size * scale,
        fontWeight: 500,
        color,
        lineHeight: 1.35,
        textAlign: center ? 'center' : 'left',
      }}
    >
      {children}
    </div>
  );
};

export const Split: React.FC<{
  left: React.ReactNode;
  right: React.ReactNode;
  gap?: number;
}> = ({left, right, gap = 60}) => {
  const {isPortrait, pad, scale} = useLayout();
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: isPortrait ? 'column' : 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: gap * scale,
        padding: pad,
      }}
    >
      <div
        style={{
          flex: isPortrait ? undefined : 1,
          display: 'flex',
          flexDirection: 'column',
          gap: 30 * scale,
          maxWidth: isPortrait ? '100%' : '46%',
          alignItems: isPortrait ? 'center' : 'flex-start',
          textAlign: isPortrait ? 'center' : 'left',
        }}
      >
        {left}
      </div>
      <div
        style={{
          flex: isPortrait ? undefined : 1,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minWidth: 0,
        }}
      >
        {right}
      </div>
    </div>
  );
};
