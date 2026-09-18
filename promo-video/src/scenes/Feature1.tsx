import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {Check} from 'lucide-react';
import {Backdrop} from '../components/Backdrop';
import {Kicker, Words, Sub, Split} from '../components/Type';
import {Phone, Bubble, TypingDots} from '../components/Phone';
import {useLayout} from '../LayoutContext';
import {FONT, MONO, TG, clamp, fadeIn, rise, springIn} from '../lib';

const QUICK = ['/lock', '/screenshot', '/open'];

export const Feature1: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {scale} = useLayout();
  return (
    <AbsoluteFill style={{fontFamily: FONT}}>
      <Backdrop />
      <Split
        left={
          <>
            <Kicker start={2}>Total control</Kicker>
            <Words text="Text your PC." start={10} size={92} />
            <Words text="It obeys." start={24} size={92} color={TG} />
            <Sub start={48} size={34}>
              Commands, apps, locks — one chat away.
            </Sub>
          </>
        }
        right={
          <Phone start={6}>
            <Bubble out start={18} mono>
              /run backup.ps1
            </Bubble>
            <TypingDots start={50} end={70} />
            <Bubble in start={70}>
              Running backup.ps1…
            </Bubble>
            <Bubble in start={94}>
              <Check size={22 * scale} color="#34D399" strokeWidth={3} />
              Done in 1.8s
            </Bubble>
            <div
              style={{
                display: 'flex',
                gap: 10 * scale,
                alignSelf: 'center',
                marginTop: 6 * scale,
              }}
            >
              {QUICK.map((q, i) => {
                const t = 118 + i * 8;
                const p = clamp(springIn(frame, fps, t));
                return (
                  <div
                    key={q}
                    style={{
                      opacity: p,
                      transform: `translateY(${(1 - p) * 14}px)`,
                      fontFamily: MONO,
                      fontSize: 19 * scale,
                      color: TG,
                      border: `1.5px solid ${TG}66`,
                      background: `${TG}12`,
                      borderRadius: 999,
                      padding: `${8 * scale}px ${16 * scale}px`,
                    }}
                  >
                    {q}
                  </div>
                );
              })}
            </div>
          </Phone>
        }
      />
    </AbsoluteFill>
  );
};
