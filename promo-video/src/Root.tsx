import React from 'react';
import {Composition} from 'remotion';
import {Promo} from './Promo';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Promo-Landscape"
        component={Promo}
        durationInFrames={1800}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="Promo-Portrait"
        component={Promo}
        durationInFrames={1800}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
