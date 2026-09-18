import React from 'react';
import {AbsoluteFill, useVideoConfig} from 'remotion';
import {TransitionSeries, linearTiming} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {slide} from '@remotion/transitions/slide';
import {
  FileQuestion,
  LockOpen,
  SquareTerminal,
  Sofa,
} from 'lucide-react';
import {LayoutProvider} from './LayoutContext';
import {Hook} from './scenes/Hook';
import {Pain} from './scenes/Pain';
import {Turn} from './scenes/Turn';
import {Reveal} from './scenes/Reveal';
import {Feature1} from './scenes/Feature1';
import Feature1b from './scenes/Feature1b';
import {Feature2} from './scenes/Feature2';
import {Feature3} from './scenes/Feature3';
import {Feature4} from './scenes/Feature4';
import {Feature5} from './scenes/Feature5';
import {Trust} from './scenes/Trust';
import {Cta} from './scenes/Cta';
import {CYAN, INK, RED} from './lib';

// Timing plan (30fps): sum(1968) - 14 transitions * 12 = 1800 frames = 60.0s
export const Promo: React.FC = () => {
  const {width, height} = useVideoConfig();
  const t12 = linearTiming({durationInFrames: 12});
  const F = fade();
  const S = slide({direction: 'from-right'});
  return (
    <LayoutProvider width={width} height={height}>
      <AbsoluteFill style={{backgroundColor: '#070A12'}}>
        <TransitionSeries>
          <TransitionSeries.Sequence durationInFrames={105}>
            <Hook />
          </TransitionSeries.Sequence>
          <TransitionSeries.Transition presentation={F} timing={t12} />
          <TransitionSeries.Sequence durationInFrames={84}>
            <Pain
              icon={FileQuestion}
              lines={[
                ['The file you need', INK],
                ['is on your home PC.', RED],
              ]}
            />
          </TransitionSeries.Sequence>
          <TransitionSeries.Transition presentation={S} timing={t12} />
          <TransitionSeries.Sequence durationInFrames={72}>
            <Pain
              icon={LockOpen}
              pulse
              lines={[
                ['Did you', INK],
                ['lock it?', RED],
              ]}
            />
          </TransitionSeries.Sequence>
          <TransitionSeries.Transition presentation={S} timing={t12} />
          <TransitionSeries.Sequence durationInFrames={84}>
            <Pain
              icon={SquareTerminal}
              lines={[
                ['That build needed', INK],
                ['to run. An hour ago.', RED],
              ]}
            />
          </TransitionSeries.Sequence>
          <TransitionSeries.Transition presentation={S} timing={t12} />
          <TransitionSeries.Sequence durationInFrames={90}>
            <Pain
              icon={Sofa}
              accent={CYAN}
              lines={[
                ['And the couch is', INK],
                ['really comfortable.', CYAN],
              ]}
            />
          </TransitionSeries.Sequence>
          <TransitionSeries.Transition presentation={F} timing={t12} />
          <TransitionSeries.Sequence durationInFrames={120}>
            <Turn />
          </TransitionSeries.Sequence>
          <TransitionSeries.Transition presentation={F} timing={t12} />
          <TransitionSeries.Sequence durationInFrames={147}>
            <Reveal />
          </TransitionSeries.Sequence>
          <TransitionSeries.Transition presentation={S} timing={t12} />
          <TransitionSeries.Sequence durationInFrames={180}>
            <Feature1 />
          </TransitionSeries.Sequence>
          <TransitionSeries.Transition presentation={S} timing={t12} />
          <TransitionSeries.Sequence durationInFrames={120}>
            <Feature1b />
          </TransitionSeries.Sequence>
          <TransitionSeries.Transition presentation={S} timing={t12} />
          <TransitionSeries.Sequence durationInFrames={186}>
            <Feature2 />
          </TransitionSeries.Sequence>
          <TransitionSeries.Transition presentation={S} timing={t12} />
          <TransitionSeries.Sequence durationInFrames={168}>
            <Feature3 />
          </TransitionSeries.Sequence>
          <TransitionSeries.Transition presentation={S} timing={t12} />
          <TransitionSeries.Sequence durationInFrames={141}>
            <Feature4 />
          </TransitionSeries.Sequence>
          <TransitionSeries.Transition presentation={S} timing={t12} />
          <TransitionSeries.Sequence durationInFrames={141}>
            <Feature5 />
          </TransitionSeries.Sequence>
          <TransitionSeries.Transition presentation={F} timing={t12} />
          <TransitionSeries.Sequence durationInFrames={120}>
            <Trust />
          </TransitionSeries.Sequence>
          <TransitionSeries.Transition presentation={F} timing={t12} />
          <TransitionSeries.Sequence durationInFrames={210}>
            <Cta />
          </TransitionSeries.Sequence>
        </TransitionSeries>
      </AbsoluteFill>
    </LayoutProvider>
  );
};
