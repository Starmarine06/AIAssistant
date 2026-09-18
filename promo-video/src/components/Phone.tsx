import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {Bot, Send} from 'lucide-react';
import {useLayout} from '../LayoutContext';
import {FONT, clamp, springIn} from '../lib';

export const Phone: React.FC<{
  children: React.ReactNode;
  start?: number;
  tilt?: boolean;
}> = ({children, start = 0, tilt = true}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {scale, isPortrait} = useLayout();
  const p = clamp(springIn(frame, fps, start));
  const w = (isPortrait ? 560 : 410) * scale;
  const h = w * 1.95;
  return (
    <div
      style={{
        opacity: p,
        transform: `perspective(1500px) ${
          tilt && !isPortrait ? 'rotateY(-9deg) rotateX(3deg) ' : ''
        }translateY(${(1 - p) * 60}px) scale(${0.9 + 0.1 * p})`,
        width: w,
        height: h,
        borderRadius: 54 * scale,
        border: `${Math.max(6, 10 * scale)}px solid #131B29`,
        background: '#0E1621',
        boxShadow:
          '0 60px 120px rgba(0,0,0,0.55), 0 0 90px rgba(79,140,255,0.18)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          height: 34 * scale,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'flex-end',
          paddingBottom: 4,
        }}
      >
        <div
          style={{
            width: 90 * scale,
            height: 8 * scale,
            borderRadius: 6,
            background: '#1E2A38',
          }}
        />
      </div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 14 * scale,
          padding: `${14 * scale}px ${20 * scale}px`,
          background: '#17212B',
        }}
      >
        <div
          style={{
            width: 52 * scale,
            height: 52 * scale,
            minWidth: 52 * scale,
            borderRadius: '50%',
            background: 'linear-gradient(135deg,#2AABEE,#4F8CFF)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Bot size={28 * scale} color="#fff" strokeWidth={2.2} />
        </div>
        <div style={{display: 'flex', flexDirection: 'column', gap: 3 * scale}}>
          <div
            style={{
              color: '#F2F6FF',
              fontSize: 25 * scale,
              fontWeight: 700,
              fontFamily: FONT,
            }}
          >
            AI Assistant
          </div>
          <div
            style={{color: '#4ADE80', fontSize: 17 * scale, fontFamily: FONT}}
          >
            online
          </div>
        </div>
      </div>
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'flex-end',
          gap: 14 * scale,
          padding: 20 * scale,
          backgroundImage: 'radial-gradient(#FFFFFF05 1px, transparent 1px)',
          backgroundSize: '22px 22px',
        }}
      >
        {children}
      </div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12 * scale,
          padding: `${14 * scale}px ${18 * scale}px`,
          background: '#17212B',
        }}
      >
        <div
          style={{
            flex: 1,
            height: 52 * scale,
            borderRadius: 26 * scale,
            background: '#0E1621',
            display: 'flex',
            alignItems: 'center',
            paddingLeft: 22 * scale,
            color: '#5B6B80',
            fontSize: 21 * scale,
            fontFamily: FONT,
          }}
        >
          Message
        </div>
        <div
          style={{
            width: 52 * scale,
            height: 52 * scale,
            borderRadius: '50%',
            background: '#2AABEE',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Send size={24 * scale} color="#fff" strokeWidth={2.2} />
        </div>
      </div>
    </div>
  );
};

export const Bubble: React.FC<{
  out?: boolean;
  start: number;
  children: React.ReactNode;
  accent?: string;
  mono?: boolean;
}> = ({out, start, children, accent, mono}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {scale} = useLayout();
  const p = clamp(springIn(frame, fps, start));
  return (
    <div
      style={{
        alignSelf: out ? 'flex-end' : 'flex-start',
        maxWidth: '88%',
        opacity: p,
        transform: `translateY(${(1 - p) * 22}px) scale(${0.85 + 0.15 * p})`,
        background: out ? accent || '#2B5278' : '#182533',
        color: '#EDF3FA',
        fontSize: 22 * scale,
        lineHeight: 1.35,
        fontFamily: mono ? '"Cascadia Code", Consolas, monospace' : FONT,
        padding: `${14 * scale}px ${18 * scale}px`,
        borderRadius: 18 * scale,
        borderBottomRightRadius: out ? 6 * scale : 18 * scale,
        borderBottomLeftRadius: out ? 18 * scale : 6 * scale,
        boxShadow: '0 6px 18px rgba(0,0,0,0.3)',
        display: 'flex',
        alignItems: 'center',
        gap: 10 * scale,
      }}
    >
      {children}
    </div>
  );
};

export const TypingDots: React.FC<{start: number; end?: number}> = ({
  start,
  end = Infinity,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {scale} = useLayout();
  const p = clamp(springIn(frame, fps, start));
  if (frame < start || frame > end) {
    return null;
  }
  return (
    <div
      style={{
        alignSelf: 'flex-start',
        opacity: p,
        background: '#182533',
        padding: `${16 * scale}px ${20 * scale}px`,
        borderRadius: 18 * scale,
        borderBottomLeftRadius: 6 * scale,
        display: 'flex',
        gap: 7 * scale,
      }}
    >
      {[0, 1, 2].map((i) => {
        const bounce = Math.max(0, Math.sin((frame - start - i * 4) * 0.35));
        return (
          <div
            key={i}
            style={{
              width: 9 * scale,
              height: 9 * scale,
              borderRadius: '50%',
              background: '#8FA3BF',
              transform: `translateY(${-7 * bounce * scale}px)`,
            }}
          />
        );
      })}
    </div>
  );
};
