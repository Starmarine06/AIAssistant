import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {Bell, CalendarDays} from 'lucide-react';
import {Backdrop} from '../components/Backdrop';
import {Kicker, Words} from '../components/Type';
import {useLayout} from '../LayoutContext';
import {
  FONT,
  MUTED,
  ACCENT,
  CYAN,
  GREEN,
  clamp,
  fadeIn,
  springIn,
} from '../lib';

const DAYS: Array<{d: string; events: Array<{t: string; time: string; c: string}>}> = [
  {d: 'MO', events: [{t: 'Deploy review', time: '14:00', c: ACCENT}]},
  {d: 'TU', events: [{t: 'Gym', time: '07:00', c: GREEN}]},
  {d: 'WE', events: [{t: 'Call Sam', time: '16:30', c: CYAN}]},
  {d: 'TH', events: [{t: 'Dentist', time: '09:00', c: '#93A3C0'}]},
  {d: 'FR', events: [{t: 'Ship v1.2', time: '17:00', c: ACCENT}]},
];

export const Feature4: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {scale, pad, isPortrait} = useLayout();
  const w = (isPortrait ? 900 : 900) * scale;
  const cardP = clamp(springIn(frame, fps, 8));
  const bellRot =
    frame >= 58
      ? 10 * Math.sin((frame - 58) * 0.55) * Math.exp(-(frame - 58) / 14)
      : 0;
  const remP = clamp(springIn(frame, fps, 58));
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
            Calendar
          </Kicker>
          <Words text="Never miss a thing." start={8} size={78} center />
        </div>
        <div style={{position: 'relative'}}>
          <div
            style={{
              width: w,
              borderRadius: 24 * scale,
              background: '#0C1322',
              border: '1px solid #FFFFFF14',
              boxShadow: '0 50px 110px rgba(0,0,0,0.55)',
              padding: 28 * scale,
              opacity: cardP,
              transform: `translateY(${(1 - cardP) * 40}px)`,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 14 * scale,
                marginBottom: 22 * scale,
                color: '#E8EFFA',
                fontSize: 30 * scale,
                fontWeight: 700,
              }}
            >
              <CalendarDays size={32 * scale} color={ACCENT} />
              This week
            </div>
            <div style={{display: 'flex', gap: 16 * scale}}>
              {DAYS.map((day, i) => (
                <div
                  key={day.d}
                  style={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 12 * scale,
                  }}
                >
                  <div
                    style={{
                      fontFamily: '"Cascadia Code", Consolas, monospace',
                      fontSize: 20 * scale,
                      color: MUTED,
                      textAlign: 'center',
                    }}
                  >
                    {day.d}
                  </div>
                  <div
                    style={{
                      minHeight: 220 * scale,
                      borderRadius: 14 * scale,
                      background: '#FFFFFF05',
                      border: '1px solid #FFFFFF0B',
                      padding: 10 * scale,
                    }}
                  >
                    {day.events.map((e, j) => {
                      const t = 14 + (i * 2 + j) * 7;
                      const p = clamp(springIn(frame, fps, t));
                      return (
                        <div
                          key={e.t}
                          style={{
                            opacity: p,
                            transform: `translateY(${(1 - p) * 14}px)`,
                            background: `${e.c}1A`,
                            borderLeft: `3px solid ${e.c}`,
                            borderRadius: 8 * scale,
                            padding: `${8 * scale}px ${10 * scale}px`,
                          }}
                        >
                          <div
                            style={{
                              fontSize: 19 * scale,
                              fontWeight: 700,
                              color: '#EDF3FA',
                            }}
                          >
                            {e.t}
                          </div>
                          <div style={{fontSize: 16 * scale, color: MUTED}}>
                            {e.time}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div
            style={{
              position: 'absolute',
              right: -26 * scale,
              bottom: -34 * scale,
              display: 'flex',
              alignItems: 'center',
              gap: 14 * scale,
              background: '#111A2A',
              border: '1px solid rgba(79,140,255,0.4)',
              borderRadius: 18 * scale,
              padding: `${16 * scale}px ${22 * scale}px`,
              boxShadow: '0 30px 60px rgba(0,0,0,0.5)',
              opacity: remP,
              transform: `translateY(${(1 - remP) * 20}px)`,
            }}
          >
            <div
              style={{
                width: 52 * scale,
                height: 52 * scale,
                borderRadius: '50%',
                background: `${ACCENT}22`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transform: `rotate(${bellRot}deg)`,
              }}
            >
              <Bell size={26 * scale} color={ACCENT} />
            </div>
            <div>
              <div style={{fontSize: 17 * scale, color: MUTED}}>Reminder</div>
              <div
                style={{
                  fontSize: 22 * scale,
                  fontWeight: 700,
                  color: '#EDF3FA',
                }}
              >
                Deploy review — in 15 min
              </div>
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
